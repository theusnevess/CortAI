from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def derive_operational_policy(collector_summary: dict[str, Any] | None) -> dict[str, Any]:
    """
    Operational Policy Engine v0.1.

    Deriva um sinal deterministico de saude operacional a partir do bloco
    `collector` ja presente no overview. Nao executa queries e nao altera os
    sinais existentes de trust/recommendation.
    """
    if not collector_summary:
        return {
            "trust_score": 100,
            "system_state": "healthy",
            "recommendation": "normal_operation",
            "as_of": _utc_now_iso(),
        }

    score = 100

    events = collector_summary.get("events") or {}
    success = int(events.get("success") or 0)
    failed = int(events.get("failed") or 0)
    total = success + failed

    if total > 0:
        failure_rate = failed / total
        if failure_rate > 0.5:
            score -= 30
        elif failure_rate > 0.3:
            score -= 20

    by_error_type = collector_summary.get("by_error_type") or {}
    for error_type, count in by_error_type.items():
        try:
            c = int(count or 0)
        except Exception:
            c = 0
        if c <= 0:
            continue
        if error_type == "ssl_cert_verify_failed":
            score -= 25 * c
        elif error_type == "upstream_blocked":
            score -= 20 * c
        elif error_type == "invalid_input":
            score -= 10 * c

    last_events = collector_summary.get("last_events") or []
    for event in last_events:
        if not isinstance(event, dict):
            continue
        if event.get("status") != "failed":
            continue
        if event.get("retryable") is True:
            score -= 5
        else:
            score -= 15

    score = max(0, min(100, score))

    if score >= 85:
        system_state = "healthy"
        recommendation = "normal_operation"
    elif score >= 65:
        system_state = "degraded"
        recommendation = "monitor_collector"
    elif score >= 40:
        system_state = "attention_required"
        recommendation = "inspect_recent_errors"
    else:
        system_state = "action_required"
        recommendation = "manual_intervention_required"

    return {
        "trust_score": score,
        "system_state": system_state,
        "recommendation": recommendation,
        "as_of": _utc_now_iso(),
    }


def derive_policy_bridge(
    collector_summary: dict[str, Any] | None,
    *,
    as_of: str | None = None,
) -> dict[str, Any] | None:
    """
    Policy bridge v0.2.

    Gera um bloco operacional aditivo e acionavel para o overview sem alterar
    trust/recommendation existentes e sem depender de banco.
    """
    if not collector_summary:
        return None

    events = collector_summary.get("events") or {}
    success = int(events.get("success") or 0)
    failed = int(events.get("failed") or 0)

    by_error_type = collector_summary.get("by_error_type") or {}
    normalized_errors: dict[str, int] = {}
    for key, value in by_error_type.items():
        if key is None:
            continue
        try:
            normalized_errors[str(key)] = int(value or 0)
        except Exception:
            continue

    total = success + failed
    failure_rate = (failed / total) if total > 0 else 0.0

    severity = "info"
    if failed >= 3 or (failed >= 2 and failed > success) or failure_rate >= 0.50:
        severity = "critical"
    elif failed >= 1 or failure_rate >= 0.10:
        severity = "warn"

    if normalized_errors.get("ssl_cert_verify_failed", 0) > 0:
        severity = "critical"
    elif normalized_errors.get("dns_failed", 0) > 0 or normalized_errors.get("timeout", 0) > 0:
        severity = "warn"

    if severity == "info":
        headline = "Coleta estavel na janela recente."
        next_actions = ["Manter monitoramento."]
    else:
        headline = "Coleta com falhas na janela recente."
        next_actions = [
            "Verificar ultimos eventos do coletor e confirmar se e flake ou padrao.",
            "Reduzir variaveis: testar com smoke-assets e comparar com URL real.",
            "Se persistir, abrir report com exemplos (error_type + http_status).",
        ]

        if normalized_errors.get("ssl_cert_verify_failed", 0) > 0:
            headline = "Falhas de TLS/CA detectadas no coletor."
            next_actions = [
                "Verificar CA bundle do container (SSL_CERT_FILE/REQUESTS_CA_BUNDLE).",
                "Revalidar smoke-assets e uma URL real com TLS.",
                "Se persistir, coletar chain/issuer e registrar incidente.",
            ]
        elif normalized_errors.get("http_4xx", 0) > 0:
            headline = "Falhas HTTP 4xx detectadas no coletor."
            next_actions = [
                "Confirmar URL/redirects e se o recurso existe (4xx nao e instabilidade do sistema).",
                "Testar com smoke-assets para isolar rede vs origem.",
                "Se 4xx for recorrente em fontes reais, ajustar estrategia de coleta.",
            ]
        elif normalized_errors.get("http_5xx", 0) > 0:
            headline = "Falhas HTTP 5xx detectadas no coletor."
            next_actions = [
                "Verificar disponibilidade do upstream (5xx pode ser intermitente).",
                "Reexecutar apos curto intervalo e comparar taxa de falha.",
                "Se persistir, registrar e mitigar com backoff/fila (proximo ciclo).",
            ]

    cleaned_actions = [
        action.strip()
        for action in next_actions
        if isinstance(action, str) and action.strip()
    ][:3]
    if not cleaned_actions:
        cleaned_actions = ["Manter monitoramento."]

    return {
        "version": "v0.2",
        "severity": severity,
        "headline": headline,
        "next_actions": cleaned_actions,
        "as_of": as_of,
    }
