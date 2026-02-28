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
