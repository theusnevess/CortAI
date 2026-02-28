import os
from datetime import datetime
from time import monotonic, perf_counter_ns
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.metrics import CES_DEFAULT_VERSION, _emit_metrics_endpoint_timing
from app.db.session import get_db
from app.observability.collector_summary import get_collector_summary
from app.observability.policy_engine import derive_operational_policy, derive_policy_bridge
from app.observability.runtime_health import get_runtime_c1_health_cached, should_include_internal_status
from app.version import get_app_version

router = APIRouter()

REPORT_WINDOW_DAYS_DEFAULT = 7
REPORT_WINDOW_DAYS_MAX = 30
REPORT_TIMING_MINUTES_DEFAULT = 15
REPORT_TIMING_MINUTES_MAX = 60
REPORT_LIMIT_ALERTS_DEFAULT = 200
REPORT_LIMIT_ALERTS_MAX = 500
REPORT_LIMIT_RECEIPTS_DEFAULT = 50
REPORT_LIMIT_RECEIPTS_MAX = 200
REPORT_RUNS_WINDOW_DAYS = 2
REPORT_ALERTS_WINDOW_DAYS = 14
REPORT_WORST_RUNS_LIMIT = 20
REPORT_WORST_RUNS_LIMIT_MAX = 200
REPORT_WORST_RUNS_WINDOW_DAYS_MAX = 7
REPORT_ALEMBIC_CACHE_TTL_SECONDS = 60
REPORT_PATH_LEAKS_CACHE_TTL_SECONDS = 30

_TRUST_DECISION_RANK: dict[str, int] = {"healthy": 0, "degraded": 1, "action_required": 2}
_TRUST_STATE_RANK: dict[str, int] = {"green": 0, "yellow": 1, "red": 2}
_POLICY_STATE_RANK: dict[str, int] = {"stable": 0, "degraded": 1, "action_required": 2}
_POLICY_STATE_TO_TRUST_DECISION: dict[str, str] = {
    "stable": "healthy",
    "degraded": "degraded",
    "action_required": "action_required",
}
_POLICY_STATE_TO_TRUST_STATE: dict[str, str] = {
    "stable": "green",
    "degraded": "yellow",
    "action_required": "red",
}
_POLICY_DECISION_TO_RECO_ACTION: dict[str, str] = {
    "monitor": "monitor",
    "inspect": "open_report",
    "investigate_now": "inspect_upstream_path",
}


_alembic_head_cache: dict[str, object] = {"value": None, "expires_at": 0.0}
_path_leaks_cache: dict[str, object] = {"value": 0, "expires_at": 0.0}


def _new_db_stats() -> dict[str, int]:
    """
    Inicializa acumuladores de custo de banco por request.
    """
    return {"db_us": 0, "db_queries": 0, "db_pool_wait_us": 0}


def _is_cache_valid(cache: dict[str, object]) -> bool:
    """
    Retorna True quando o cache local ainda esta dentro do TTL configurado.
    """
    # Em pytest o cache e desligado para evitar acoplamento entre casos.
    if os.getenv("PYTEST_CURRENT_TEST"):
        return False
    return monotonic() < float(cache.get("expires_at", 0.0))


def _rank(mapping: dict[str, int], value: str | None) -> int:
    if not value:
        return -1
    return mapping.get(str(value), -1)


def _harmonize_policy_trust_recommendation(response: dict[str, Any]) -> None:
    """
    Harmonizacao conservadora do overview.

    Regras:
    - `policy.state` pode piorar `trust.state`/`trust.decision`, nunca melhorar.
    - `policy.decision` so preenche `recommendation.action` quando ela estiver
      ausente ou for `none`.
    """
    policy = response.get("policy") or {}
    trust = response.get("trust") or {}
    recommendation = response.get("recommendation") or {}

    policy_state = policy.get("state")
    policy_decision = policy.get("decision")

    desired_trust_decision = _POLICY_STATE_TO_TRUST_DECISION.get(str(policy_state), None)
    desired_trust_state = _POLICY_STATE_TO_TRUST_STATE.get(str(policy_state), None)

    if desired_trust_decision:
        current = trust.get("decision")
        if _rank(_TRUST_DECISION_RANK, desired_trust_decision) > _rank(_TRUST_DECISION_RANK, current):
            trust["decision"] = desired_trust_decision
            trust["derived_from"] = ["policy_harmonized"]

    if desired_trust_state:
        current = trust.get("state")
        if _rank(_TRUST_STATE_RANK, desired_trust_state) > _rank(_TRUST_STATE_RANK, current):
            trust["state"] = desired_trust_state
            trust["derived_from"] = ["policy_harmonized"]

    desired_action = _POLICY_DECISION_TO_RECO_ACTION.get(str(policy_decision), None)
    if desired_action:
        current_action = recommendation.get("action")
        if (not current_action) or (str(current_action) == "none"):
            recommendation["action"] = desired_action
            recommendation["derived_from"] = ["policy_harmonized"]

    response["trust"] = trust
    response["recommendation"] = recommendation


def _set_cache(cache: dict[str, object], value: object, ttl_seconds: int) -> None:
    """
    Atualiza valor + expiracao em cache in-memory para reduzir queries repetidas.
    """
    if os.getenv("PYTEST_CURRENT_TEST"):
        return
    cache["value"] = value
    cache["expires_at"] = monotonic() + float(ttl_seconds)


async def _execute_with_db_stats(
    db: AsyncSession,
    statement,
    db_stats: dict[str, int],
    params: dict | None = None,
):
    """
    Executa query contabilizando custo de DB para diagnostico de contensao.
    """
    # Instrumentacao minima para separar custo de DB de fila/CPU.
    started_ns = perf_counter_ns()
    if params is None:
        result = await db.execute(statement)
    else:
        result = await db.execute(statement, params)
    elapsed_us = max(0, (perf_counter_ns() - started_ns) // 1000)
    db_stats["db_us"] = int(db_stats.get("db_us", 0)) + int(elapsed_us)
    db_stats["db_queries"] = int(db_stats.get("db_queries", 0)) + 1
    return result


async def _get_alembic_head_cached(db: AsyncSession, db_stats: dict[str, int]) -> str | None:
    """
    Busca alembic head com cache curto para remover query fixa do request path.
    """
    if _is_cache_valid(_alembic_head_cache):
        return _alembic_head_cache.get("value")  # type: ignore[return-value]
    alembic_head: str | None = None
    try:
        alembic_row = (
            await _execute_with_db_stats(
                db,
                text("SELECT version_num FROM alembic_version LIMIT 1"),
                db_stats,
            )
        ).first()
        if alembic_row:
            alembic_head = str(alembic_row[0])
    except Exception:
        alembic_head = None
    _set_cache(_alembic_head_cache, alembic_head, REPORT_ALEMBIC_CACHE_TTL_SECONDS)
    return alembic_head


async def _get_path_leaks_30d_cached(db: AsyncSession, db_stats: dict[str, int]) -> int:
    """
    Retorna leak-check 30d com cache curto para reduzir custo recorrente do report.
    """
    if _is_cache_valid(_path_leaks_cache):
        return int(_path_leaks_cache.get("value", 0))
    leaks = (
        await _execute_with_db_stats(
            db,
            text(
                """
                SELECT
                  COUNT(*)::int AS leaks
                FROM publish_receipts
                WHERE created_at >= NOW() - INTERVAL '30 days'
                  AND (
                    error_message ILIKE '%/tmp%' OR
                    error_message ILIKE '%storage/%' OR
                    error_message ILIKE '%videos-raw%' OR
                    error_message ILIKE '%.mp4%' OR
                    error_message ILIKE '%.wav%' OR
                    error_message ILIKE '%.json%' OR
                    error_message ILIKE '%agent_output%'
                  )
                """
            ),
            db_stats,
        )
    ).scalar() or 0
    leak_count = int(leaks)
    _set_cache(_path_leaks_cache, leak_count, REPORT_PATH_LEAKS_CACHE_TTL_SECONDS)
    return leak_count


def _build_slo_daily_summary(items: list[dict]) -> list[dict]:
    """
    Deriva summary por endpoint a partir de items para evitar query extra no report.
    """
    grouped: dict[str, dict[str, float]] = {}
    for item in items:
        endpoint = str(item["endpoint"])
        agg = grouped.setdefault(
            endpoint,
            {"total_requests": 0.0, "sum_p95": 0.0, "sum_p99": 0.0, "sum_error_rate": 0.0, "count": 0.0},
        )
        agg["total_requests"] += float(item["count_requests"])
        agg["sum_p95"] += float(item["p95_ms"])
        agg["sum_p99"] += float(item["p99_ms"])
        agg["sum_error_rate"] += float(item["error_rate"])
        agg["count"] += 1.0
    summary = []
    for endpoint, agg in grouped.items():
        count = max(1.0, agg["count"])
        summary.append(
            {
                "endpoint": endpoint,
                "total_requests": int(agg["total_requests"]),
                "avg_p95_ms": round(agg["sum_p95"] / count, 4),
                "avg_p99_ms": round(agg["sum_p99"] / count, 4),
                "avg_error_rate": round(agg["sum_error_rate"] / count, 6),
            }
        )
    summary.sort(key=lambda row: row["total_requests"], reverse=True)
    return summary


def _map_panel_decision_from_score(score: str) -> str:
    normalized = str(score or "").upper()
    if normalized == "FAIL":
        return "action_required"
    if normalized == "WARN":
        return "degraded"
    return "healthy"


def _derive_trust_banner(
    *,
    overall: dict,
    read_path: dict,
    guardrails: dict,
) -> dict:
    """
    Deriva um sinal de confianca de produto (MVP) sem consultas extras.

    Regras:
    - RED se houver falha operacional clara (health FAIL, snapshot missing, 503 recente).
    - YELLOW se houver degradacao controlada (health WARN, snapshot stale, excesso de 429).
    - GREEN quando health PASS + read-path fresh + guardrails criticos zerados.
    """
    overall_score = str(overall.get("score", "FAIL")).upper()
    overview_snapshot_status = str(read_path.get("overview_snapshot_status") or "missing").lower()
    guardrail_events = dict(guardrails.get("events") or {})
    snapshot_missing_503 = int(guardrail_events.get("snapshot_missing_503") or 0)
    rate_limited_429 = int(guardrail_events.get("rate_limited_429") or 0)

    derived_from: list[str] = []

    # RED: operador deve agir; prioriza sinais de indisponibilidade/erro de snapshot.
    if overall_score == "FAIL":
        return {
            "state": "red",
            "decision": "action_required",
            "message": "Saude operacional falhou. Acao necessaria.",
            "derived_from": ["c1_health"],
        }
    if overview_snapshot_status == "missing":
        return {
            "state": "red",
            "decision": "action_required",
            "message": "Snapshot ausente. Execute warm-up para restaurar dados.",
            "derived_from": ["read_path"],
        }
    if snapshot_missing_503 > 0:
        return {
            "state": "red",
            "decision": "action_required",
            "message": "Eventos de snapshot missing observados. Execute warm-up.",
            "derived_from": ["guardrails"],
        }

    # YELLOW: sistema responde, mas ha sinal de degradacao que merece atencao.
    if overall_score == "WARN":
        derived_from.append("c1_health")
    if overview_snapshot_status == "stale":
        derived_from.append("read_path")
    if rate_limited_429 >= 3:
        derived_from.append("guardrails")
    if derived_from:
        message = "Sinais de degradacao observados."
        if "read_path" in derived_from and overall_score == "PASS":
            message = "Dados possivelmente desatualizados. Verifique atualizacao recente."
        elif "guardrails" in derived_from and overall_score == "PASS":
            message = "Muitas solicitacoes recentes. Reduza chamadas force_live."
        return {
            "state": "yellow",
            "decision": "degraded",
            "message": message,
            "derived_from": derived_from,
        }

    # GREEN: health PASS, overview fresh e sem guardrails criticos recentes.
    return {
        "state": "green",
        "decision": "healthy",
        "message": "Sistema saudavel e responsivo.",
        "derived_from": ["c1_health", "read_path", "guardrails"],
    }


_ALLOWED_RECOMMENDATION_ACTIONS = {
    "run_warmup",
    "monitor",
    "investigate_read_path",
    "reduce_force_live_burst",
    "inspect_upstream_path",
    "open_report",
    "none",
}


def _derive_action_recommendation(
    *,
    trust: dict,
    read_path: dict,
    guardrails: dict,
    c1_health: dict,
) -> dict:
    """
    Deriva recomendacao de acao (MVP) a partir do payload do painel, sem queries extras.

    Precedencia (early-return, auditavel):
    1. snapshot missing (read_path)
    2. jobs queued (read_path)
    3. snapshot_missing_503 recente (guardrails)
    4. rate_limited_429 recente (guardrails)
    5. trust red por health FAIL/rps<1 (c1_health/trust)
    6. fallback de diagnostico (open_report)
    7. none (green)
    """
    trust_state = str(trust.get("state") or "red").lower()
    trust_decision = str(trust.get("decision") or "action_required").lower()
    trust_reasons = [str(r) for r in (trust.get("derived_from") or [])]
    overall_reasons = [str(r) for r in (c1_health.get("reasons") or [])]

    overview_snapshot_status = str(read_path.get("overview_snapshot_status") or "missing").lower()
    jobs_queued_count = int(read_path.get("jobs_queued_count") or 0)

    guardrail_events = dict(guardrails.get("events") or {})
    snapshot_missing_503 = int(guardrail_events.get("snapshot_missing_503") or 0)
    rate_limited_429 = int(guardrail_events.get("rate_limited_429") or 0)

    # 1) Snapshot ausente: acao imediata e deterministica de recuperacao.
    if overview_snapshot_status == "missing":
        recommendation = {
            "action": "run_warmup",
            "priority": "high",
            "message": "Snapshot ausente. Execute warm-up do read-path agora.",
            "derived_from": ["read_path"],
        }
    # 2) Jobs em fila: sistema ja reagiu; operador deve monitorar conclusao.
    elif jobs_queued_count > 0:
        recommendation = {
            "action": "monitor",
            "priority": "medium",
            "message": "Atualizacao em andamento. Monitore a fila e aguarde concluir.",
            "derived_from": ["read_path"],
        }
    # 3) Eventos 503 recentes: indica churn de snapshot e exige acao no read-path.
    elif snapshot_missing_503 > 0:
        recommendation = {
            "action": "run_warmup",
            "priority": "high",
            "message": "Snapshot missing recente. Execute warm-up do read-path.",
            "derived_from": ["guardrails"],
        }
    # 4) Eventos 429 recentes: reduzir burst de force_live e manter degradacao controlada.
    elif rate_limited_429 > 0:
        recommendation = {
            "action": "reduce_force_live_burst",
            "priority": "medium",
            "message": "Muitas solicitacoes recentes. Aguarde ou reduza chamadas force_live.",
            "derived_from": ["guardrails"],
        }
    # 5) Trust red por falha operacional (tipicamente rps<1) sem sinais de snapshot/fila.
    elif trust_state == "red" and trust_decision == "action_required":
        recommendation = {
            "action": "inspect_upstream_path",
            "priority": "high",
            "message": "Saude operacional falhou. Verifique upstream e caminho de infra.",
            "derived_from": ["trust", "c1_health"],
        }
    # 6) Fallback para casos degradados nao classificados (ex.: WARN por p99).
    elif trust_state == "yellow":
        recommendation = {
            "action": "open_report",
            "priority": "medium",
            "message": "Degradacao detectada. Abra o report para diagnostico.",
            "derived_from": ["trust", "c1_health"],
        }
    # 7) Estado saudavel: sem acao necessaria.
    else:
        recommendation = {
            "action": "none",
            "priority": "low",
            "message": "Sistema saudavel. Nenhuma acao necessaria.",
            "derived_from": ["trust"],
        }

    # Normaliza derived_from e valida enum para evitar drift silencioso.
    recommendation["derived_from"] = [str(x) for x in recommendation.get("derived_from", []) if str(x)]
    if not recommendation["derived_from"]:
        recommendation["derived_from"] = ["trust"]
    if str(recommendation.get("action")) not in _ALLOWED_RECOMMENDATION_ACTIONS:
        recommendation["action"] = "open_report"
        recommendation["priority"] = "medium"
        recommendation["message"] = "Recomendacao invalida. Abra o report para diagnostico."
        recommendation["derived_from"] = ["trust"]
    # Mantem hook para futuras regras sem mudar o contrato atual.
    if overall_reasons and recommendation["action"] == "none":
        recommendation["derived_from"] = ["trust"]
    return recommendation


def _project_operational_decision(policy: dict[str, Any] | None) -> dict[str, Any] | None:
    """
    Projeta um bloco read-only a partir de `policy` sem recalcular regra alguma.
    """
    if not isinstance(policy, dict):
        return None
    return {
        "version": policy.get("version"),
        "score": policy.get("score"),
        "state": policy.get("state"),
        "decision": policy.get("decision"),
        "signals": policy.get("signals"),
    }


async def _get_guardrails_summary(
    db: AsyncSession,
    db_stats: dict[str, int],
    *,
    window_minutes: int = 15,
    last_events_limit: int = 5,
) -> dict:
    """
    Resume guardrails recentes (202/429/503) a partir de metrics_endpoint_timing.
    Mantem custo previsivel em 2 queries leves: agregacao + ultimos eventos.
    """
    endpoint_paths = [
        "/api/v1/metrics/overview",
        "/api/v1/metrics/runs",
        "/api/v1/observability/report",
    ]
    counts_row = (
        await _execute_with_db_stats(
            db,
            text(
                """
                SELECT
                  SUM(CASE WHEN (facts->>'status_code')::int = 202 THEN 1 ELSE 0 END)::int AS accepted_202,
                  SUM(CASE WHEN (facts->>'status_code')::int = 429 THEN 1 ELSE 0 END)::int AS rate_limited_429,
                  SUM(CASE WHEN (facts->>'status_code')::int = 503 THEN 1 ELSE 0 END)::int AS snapshot_missing_503
                FROM observations
                WHERE facts->>'event_type' = 'metrics_endpoint_timing'
                  AND timestamp >= NOW() - make_interval(mins => :window_minutes)
                  AND facts->>'endpoint' IN (:endpoint_overview, :endpoint_runs, :endpoint_report)
                  AND (facts->>'status_code') IN ('202', '429', '503')
                """
            ),
            db_stats,
            {
                "window_minutes": int(window_minutes),
                "endpoint_overview": endpoint_paths[0],
                "endpoint_runs": endpoint_paths[1],
                "endpoint_report": endpoint_paths[2],
            },
        )
    ).mappings().first()

    last_rows = (
        await _execute_with_db_stats(
            db,
            text(
                """
                SELECT
                  timestamp,
                  facts->>'endpoint' AS endpoint,
                  (facts->>'status_code')::int AS status_code,
                  COALESCE(NULLIF(facts->>'scope', ''), NULL) AS scope,
                  COALESCE(NULLIF(facts->>'snapshot_status', ''), NULL) AS snapshot_status
                FROM observations
                WHERE facts->>'event_type' = 'metrics_endpoint_timing'
                  AND timestamp >= NOW() - make_interval(mins => :window_minutes)
                  AND facts->>'endpoint' IN (:endpoint_overview, :endpoint_runs, :endpoint_report)
                  AND (facts->>'status_code') IN ('202', '429', '503')
                ORDER BY timestamp DESC
                LIMIT :limit_rows
                """
            ),
            db_stats,
            {
                "window_minutes": int(window_minutes),
                "limit_rows": int(last_events_limit),
                "endpoint_overview": endpoint_paths[0],
                "endpoint_runs": endpoint_paths[1],
                "endpoint_report": endpoint_paths[2],
            },
        )
    ).mappings().all()

    events = {
        "accepted_202": int((counts_row or {}).get("accepted_202") or 0),
        "rate_limited_429": int((counts_row or {}).get("rate_limited_429") or 0),
        "snapshot_missing_503": int((counts_row or {}).get("snapshot_missing_503") or 0),
    }
    last_events = [
        {
            "ts": r["timestamp"].isoformat() if r.get("timestamp") else None,
            "endpoint": r.get("endpoint"),
            "status_code": int(r["status_code"]) if r.get("status_code") is not None else None,
            "scope": r.get("scope"),
            "snapshot_status": r.get("snapshot_status"),
        }
        for r in last_rows
    ]
    return {
        "window_minutes": int(window_minutes),
        "events": events,
        "last_events": last_events,
    }


async def _get_read_path_compact(
    db: AsyncSession,
    db_stats: dict[str, int],
) -> dict:
    """
    Retorna bloco enxuto de read_path em 1 query (subqueries) para manter custo previsivel.
    """
    defaults = {
        "overview_freshness_seconds": None,
        "overview_snapshot_status": "missing",
        "overview_last_refreshed_at": None,
        "runs_freshness_seconds": None,
        "runs_snapshot_status": "missing",
        "runs_last_refreshed_at": None,
        "runs_key_count": 0,
        "jobs_queued_count": 0,
    }
    try:
        row = (
            await _execute_with_db_stats(
                db,
                text(
                    """
                    WITH overview AS (
                      SELECT
                        EXTRACT(EPOCH FROM (NOW() - MAX(refreshed_at)))::int AS freshness_seconds,
                        MAX(refreshed_at) AS last_refreshed_at
                      FROM metrics_overview_read_model
                    ),
                    runs AS (
                      SELECT
                        EXTRACT(EPOCH FROM (NOW() - MAX(refreshed_at)))::int AS freshness_seconds,
                        MAX(refreshed_at) AS last_refreshed_at,
                        COUNT(*)::int AS key_count
                      FROM metrics_runs_read_model
                    ),
                    jobs AS (
                      SELECT COUNT(*)::int AS queued_count
                      FROM metrics_read_refresh_jobs
                      WHERE status = 'queued' AND expires_at > NOW()
                    )
                    SELECT
                      overview.freshness_seconds AS overview_freshness_seconds,
                      overview.last_refreshed_at AS overview_last_refreshed_at,
                      runs.freshness_seconds AS runs_freshness_seconds,
                      runs.last_refreshed_at AS runs_last_refreshed_at,
                      runs.key_count AS runs_key_count,
                      jobs.queued_count AS jobs_queued_count
                    FROM overview
                    CROSS JOIN runs
                    CROSS JOIN jobs
                    """
                ),
                db_stats,
            )
        ).mappings().first()
        if row is None:
            return defaults
        overview_freshness = row.get("overview_freshness_seconds")
        runs_freshness = row.get("runs_freshness_seconds")
        overview_last = row.get("overview_last_refreshed_at")
        runs_last = row.get("runs_last_refreshed_at")
        runs_key_count = int(row.get("runs_key_count") or 0)
        jobs_queued_count = int(row.get("jobs_queued_count") or 0)
        return {
            "overview_freshness_seconds": None if overview_freshness is None else max(0, int(overview_freshness)),
            "overview_snapshot_status": (
                "missing"
                if overview_last is None
                else ("fresh" if int(overview_freshness or 0) <= 60 else "stale")
            ),
            "overview_last_refreshed_at": overview_last.isoformat() if overview_last else None,
            "runs_freshness_seconds": None if runs_freshness is None else max(0, int(runs_freshness)),
            "runs_snapshot_status": (
                "missing" if runs_last is None else ("fresh" if int(runs_freshness or 0) <= 60 else "stale")
            ),
            "runs_last_refreshed_at": runs_last.isoformat() if runs_last else None,
            "runs_key_count": max(0, runs_key_count),
            "jobs_queued_count": max(0, jobs_queued_count),
        }
    except DBAPIError:
        return defaults


def _validate_report_params(
    *,
    window_days: int,
    timing_minutes: int,
    limit_alerts: int,
    limit_receipts: int,
    include_worst_runs: bool,
    limit_worst_runs: int,
) -> None:
    if window_days > REPORT_WINDOW_DAYS_MAX:
        raise HTTPException(
            status_code=400,
            detail={
                "error_type": "RangeTooLarge",
                "window_days_requested": window_days,
                "window_days_max": REPORT_WINDOW_DAYS_MAX,
            },
        )
    if timing_minutes > REPORT_TIMING_MINUTES_MAX:
        raise HTTPException(
            status_code=400,
            detail={
                "error_type": "RangeTooLarge",
                "timing_minutes_requested": timing_minutes,
                "timing_minutes_max": REPORT_TIMING_MINUTES_MAX,
            },
        )
    if limit_alerts > REPORT_LIMIT_ALERTS_MAX:
        raise HTTPException(
            status_code=400,
            detail={
                "error_type": "LimitTooHigh",
                "limit_alerts_requested": limit_alerts,
                "limit_alerts_max": REPORT_LIMIT_ALERTS_MAX,
            },
        )
    if limit_receipts > REPORT_LIMIT_RECEIPTS_MAX:
        raise HTTPException(
            status_code=400,
            detail={
                "error_type": "LimitTooHigh",
                "limit_receipts_requested": limit_receipts,
                "limit_receipts_max": REPORT_LIMIT_RECEIPTS_MAX,
            },
        )
    if limit_worst_runs > REPORT_WORST_RUNS_LIMIT_MAX:
        raise HTTPException(
            status_code=400,
            detail={
                "error_type": "LimitTooHigh",
                "limit_worst_runs_requested": limit_worst_runs,
                "limit_worst_runs_max": REPORT_WORST_RUNS_LIMIT_MAX,
            },
        )
    if include_worst_runs and window_days > REPORT_WORST_RUNS_WINDOW_DAYS_MAX:
        raise HTTPException(
            status_code=400,
            detail={
                "error_type": "RangeTooLarge",
                "window_days_requested": window_days,
                "window_days_max_for_worst_runs": REPORT_WORST_RUNS_WINDOW_DAYS_MAX,
            },
        )


def _status_from_checks(checks: list[dict], runs_worst_empty: bool) -> str:
    hard_failed = any((not c.get("pass")) and c.get("hard") for c in checks)
    if hard_failed:
        return "FAIL"
    if runs_worst_empty:
        return "WARN"
    return "PASS"


async def _build_observability_overview_payload(
    *,
    db: AsyncSession,
    db_stats: dict[str, int],
) -> dict:
    """
    Monta o payload do Operational Insights Panel (MVP).

    Esta funcao centraliza o builder para reuso por:
    - endpoint JSON (`/api/v1/observability/overview`)
    - UI interna (`/internal/observability`)

    Nao faz checagem de gate. O chamador decide a exposicao.
    """
    c1_health = await get_runtime_c1_health_cached(db=db, db_stats=db_stats)
    read_path = await _get_read_path_compact(db=db, db_stats=db_stats)
    guardrails = await _get_guardrails_summary(db=db, db_stats=db_stats, window_minutes=15, last_events_limit=5)
    try:
        collector = await get_collector_summary(
            db=db,
            db_stats=db_stats,
            execute_with_db_stats=_execute_with_db_stats,
            window_minutes=15,
            last_events_limit=5,
        )
    except Exception:
        collector = None

    score = str(c1_health.get("score", "FAIL"))
    response = {
        "as_of": c1_health.get("as_of") or (datetime.utcnow().replace(microsecond=0).isoformat() + "Z"),
        "panel_version": "v1",
        "source": {
            "c1_health": "runtime_status",
            "guardrails": "metrics_endpoint_timing",
            "window_minutes": int((c1_health.get("inputs") or {}).get("window_minutes") or 15),
        },
        "overall": {
            "score": score,
            "decision": _map_panel_decision_from_score(score),
            "reasons": list(c1_health.get("reasons") or []),
        },
        "c1_health": c1_health,
        "read_path": read_path,
        "guardrails": guardrails,
        "collector": collector,
    }
    response["policy"] = derive_operational_policy(collector)
    response["operational_decision"] = _project_operational_decision(response.get("policy"))
    try:
        response["policy_bridge"] = derive_policy_bridge(
            collector,
            as_of=response.get("as_of"),
        )
    except Exception:
        response["policy_bridge"] = None
    # Trust Banner e derivado do payload ja montado (O(1), sem consultas extras).
    response["trust"] = _derive_trust_banner(
        overall=response["overall"],
        read_path=response["read_path"],
        guardrails=response["guardrails"],
    )
    # Recommendation e derivada de trust/read_path/guardrails/c1_health (tambem O(1)).
    response["recommendation"] = _derive_action_recommendation(
        trust=response["trust"],
        read_path=response["read_path"],
        guardrails=response["guardrails"],
        c1_health=response["c1_health"],
    )
    _harmonize_policy_trust_recommendation(response)
    return response


@router.get("/overview")
async def get_observability_overview(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Painel operacional enxuto (MVP) para consumo interno: c1_health + read_path + overall.
    Gate restrito por env + header. Nao substitui o /report.
    """
    started_at = datetime.utcnow()
    status_code = 500
    query_fingerprint = "panel_version=v1&window=15m"
    db_stats = _new_db_stats()
    try:
        if not should_include_internal_status(request):
            status_code = 404
            raise HTTPException(status_code=404, detail="Not Found")

        response = await _build_observability_overview_payload(db=db, db_stats=db_stats)
        status_code = 200
        return response
    except HTTPException:
        raise
    finally:
        duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
        _emit_metrics_endpoint_timing(
            endpoint="/api/v1/observability/overview",
            method="GET",
            status_code=status_code,
            duration_ms=duration_ms,
            query_fingerprint=query_fingerprint,
            db_us=db_stats["db_us"],
            db_queries=db_stats["db_queries"],
            db_pool_wait_us=db_stats["db_pool_wait_us"],
        )


@router.get("/report")
async def get_observability_report(
    window_days: int = Query(REPORT_WINDOW_DAYS_DEFAULT, ge=1),
    timing_minutes: int = Query(REPORT_TIMING_MINUTES_DEFAULT, ge=1),
    limit_alerts: int = Query(REPORT_LIMIT_ALERTS_DEFAULT, ge=1),
    limit_receipts: int = Query(REPORT_LIMIT_RECEIPTS_DEFAULT, ge=1),
    include_worst_runs: bool = Query(False),
    include_receipts: bool = Query(False),
    include_alert_items: bool = Query(False),
    limit_worst_runs: int = Query(REPORT_WORST_RUNS_LIMIT, ge=1),
    db: AsyncSession = Depends(get_db),
):
    """
    Consolida report read-only de observabilidade com base no runbook operacional.
    Contrato v1.3.1: modo lean por default; blocos pesados sao opt-in.
    """
    started_at = datetime.utcnow()
    status_code = 500
    query_fingerprint = (
        f"window_days={window_days}&timing_minutes={timing_minutes}"
        f"&limit_alerts={limit_alerts}&limit_receipts={limit_receipts}"
        f"&include_worst_runs={int(include_worst_runs)}"
        f"&include_receipts={int(include_receipts)}"
        f"&include_alert_items={int(include_alert_items)}"
        f"&limit_worst_runs={limit_worst_runs}"
    )
    db_stats = _new_db_stats()
    try:
        _validate_report_params(
            window_days=window_days,
            timing_minutes=timing_minutes,
            limit_alerts=limit_alerts,
            limit_receipts=limit_receipts,
            include_worst_runs=include_worst_runs,
            limit_worst_runs=limit_worst_runs,
        )

        generated_at_utc = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        api_version = get_app_version()
        git_tag = os.getenv("GIT_TAG")
        git_commit = os.getenv("GIT_COMMIT")

        alembic_head = await _get_alembic_head_cached(db, db_stats)

        timing_and_alerts_row = (
            await _execute_with_db_stats(
                db,
                text(
                    """
                    WITH timing AS (
                      SELECT
                        COUNT(*)::int AS events,
                        MIN(timestamp) AS min_ts,
                        MAX(timestamp) AS max_ts,
                        SUM(
                          CASE
                            WHEN (facts->>'duration_ms') IS NULL
                              OR (facts->>'duration_ms') = ''
                              OR (facts->>'duration_ms')::numeric < 0
                            THEN 1 ELSE 0
                          END
                        )::int AS bad_duration
                      FROM observations
                      WHERE facts->>'event_type' = 'metrics_endpoint_timing'
                        AND timestamp >= NOW() - make_interval(mins => :timing_minutes)
                    ),
                    alerts AS (
                      SELECT COUNT(*)::int AS alerts_count
                      FROM observations
                      WHERE facts->>'event_type' = 'metrics_slo_alert'
                        AND timestamp >= NOW() - make_interval(days => :alert_window_days)
                    )
                    SELECT
                      timing.events,
                      timing.min_ts,
                      timing.max_ts,
                      timing.bad_duration,
                      alerts.alerts_count
                    FROM timing
                    CROSS JOIN alerts
                    """
                ),
                db_stats,
                {
                    "timing_minutes": timing_minutes,
                    "alert_window_days": REPORT_ALERTS_WINDOW_DAYS,
                },
            )
        ).mappings().one()

        slo_daily_items = (
            await _execute_with_db_stats(
                db,
                text(
                    """
                    SELECT
                      metric_date,
                      endpoint,
                      count_requests,
                      p50_ms,
                      p95_ms,
                      p99_ms,
                      error_rate
                    FROM metrics_endpoint_daily
                    WHERE metric_date >= (CURRENT_DATE - make_interval(days => :window_days))::date
                    ORDER BY metric_date ASC, endpoint ASC
                    """
                ),
                db_stats,
                {"window_days": window_days},
            )
        ).mappings().all()
        slo_daily_items_json = [
            {
                "metric_date": str(r["metric_date"]),
                "endpoint": str(r["endpoint"]),
                "count_requests": int(r["count_requests"]),
                "p50_ms": int(r["p50_ms"]),
                "p95_ms": int(r["p95_ms"]),
                "p99_ms": int(r["p99_ms"]),
                "error_rate": float(r["error_rate"]),
            }
            for r in slo_daily_items
        ]

        # Summary derivado em memoria para manter o report em 1 query para slo_daily.
        slo_daily_summary_json = _build_slo_daily_summary(slo_daily_items_json)

        # Count de alertas vem junto da query de timing para reduzir db_queries no modo default.
        alerts_count = int(timing_and_alerts_row["alerts_count"] or 0)
        alerts_json: list[dict] = []
        if include_alert_items:
            alerts_rows = (
                await _execute_with_db_stats(
                    db,
                    text(
                        """
                        SELECT
                          timestamp,
                          process_id,
                          facts->>'metric_date' AS metric_date,
                          facts->>'endpoint' AS endpoint,
                          facts->'reasons' AS reasons
                        FROM observations
                        WHERE facts->>'event_type' = 'metrics_slo_alert'
                          AND timestamp >= NOW() - make_interval(days => :alert_window_days)
                        ORDER BY timestamp DESC
                        LIMIT :limit_alerts
                        """
                    ),
                    db_stats,
                    {
                        "alert_window_days": REPORT_ALERTS_WINDOW_DAYS,
                        "limit_alerts": limit_alerts,
                    },
                )
            ).mappings().all()
            alerts_json = [
                {
                    "timestamp": r["timestamp"].isoformat() if r["timestamp"] else None,
                    "process_id": r["process_id"],
                    "metric_date": r["metric_date"],
                    "endpoint": r["endpoint"],
                    "reasons": r["reasons"],
                }
                for r in alerts_rows
            ]

        # "worst runs" e o bloco mais caro; executa apenas sob opt-in.
        worst_runs_json: list[dict] = []
        if include_worst_runs:
            worst_runs_rows = (
                await _execute_with_db_stats(
                    db,
                    text(
                        """
                        WITH finished AS (
                          SELECT
                            process_id,
                            timestamp,
                            facts,
                            ROW_NUMBER() OVER (PARTITION BY process_id ORDER BY timestamp DESC) AS rn
                          FROM observations
                          WHERE facts->>'event_type' = 'cognitive_loop_finished'
                            AND timestamp >= NOW() - make_interval(days => :runs_window_days)
                        )
                        SELECT
                          process_id,
                          timestamp AS finished_ts,
                          COALESCE(facts->>'pipeline_status', 'unknown') AS pipeline_status,
                          facts->>'execution_status' AS execution_status,
                          facts->>'ces_run_version' AS ces_run_version,
                          NULLIF(facts->>'ces_run','')::numeric AS ces_run,
                          NULLIF(facts->'ces_run_components'->>'status','')::numeric AS s_status,
                          NULLIF(facts->'ces_run_components'->>'actions','')::numeric AS s_actions,
                          NULLIF(facts->'ces_run_components'->>'latency','')::numeric AS s_latency,
                          NULLIF(facts->'ces_run_components'->>'trunc','')::numeric AS s_trunc,
                          facts->>'ces_run_reason' AS ces_run_reason
                        FROM finished
                        WHERE rn = 1
                          AND NULLIF(facts->>'ces_run','') IS NOT NULL
                        ORDER BY ces_run ASC
                        LIMIT :worst_runs_limit
                        """
                    ),
                    db_stats,
                    {
                        "runs_window_days": REPORT_RUNS_WINDOW_DAYS,
                        "worst_runs_limit": limit_worst_runs,
                    },
                )
            ).mappings().all()
            worst_runs_json = [
                {
                    "process_id": r["process_id"],
                    "finished_ts": r["finished_ts"].isoformat() if r["finished_ts"] else None,
                    "pipeline_status": r["pipeline_status"],
                    "execution_status": r["execution_status"],
                    "ces_run_version": r["ces_run_version"],
                    "ces_run": float(r["ces_run"]) if r["ces_run"] is not None else None,
                    "s_status": float(r["s_status"]) if r["s_status"] is not None else None,
                    "s_actions": float(r["s_actions"]) if r["s_actions"] is not None else None,
                    "s_latency": float(r["s_latency"]) if r["s_latency"] is not None else None,
                    "s_trunc": float(r["s_trunc"]) if r["s_trunc"] is not None else None,
                    "ces_run_reason": r["ces_run_reason"],
                }
                for r in worst_runs_rows
            ]

        # Receipts detalhados tambem ficam fora do caminho default para reduzir db_us.
        receipts_errors_json: list[dict] = []
        receipts_latest_json: list[dict] = []
        if include_receipts:
            receipts_errors_rows = (
                await _execute_with_db_stats(
                    db,
                    text(
                        """
                        SELECT
                          COALESCE(error_type, 'unknown') AS error_type,
                          COUNT(*)::int AS n
                        FROM publish_receipts
                        WHERE created_at >= NOW() - INTERVAL '7 days'
                          AND pipeline_status IN ('blocked','failed')
                        GROUP BY 1
                        ORDER BY n DESC
                        """
                    ),
                    db_stats,
                )
            ).mappings().all()
            receipts_errors_json = [
                {"error_type": r["error_type"], "n": int(r["n"])}
                for r in receipts_errors_rows
            ]

            receipts_latest_rows = (
                await _execute_with_db_stats(
                    db,
                    text(
                        """
                        SELECT
                          process_id,
                          publish_decision_id,
                          manifest_decision_id,
                          pipeline_status,
                          error_type,
                          error_message,
                          created_at
                        FROM publish_receipts
                        WHERE created_at >= NOW() - INTERVAL '7 days'
                          AND pipeline_status IN ('blocked','failed')
                        ORDER BY created_at DESC
                        LIMIT :limit_receipts
                        """
                    ),
                    db_stats,
                    {"limit_receipts": limit_receipts},
                )
            ).mappings().all()
            receipts_latest_json = [
                {
                    "process_id": r["process_id"],
                    "publish_decision_id": r["publish_decision_id"],
                    "manifest_decision_id": r["manifest_decision_id"],
                    "pipeline_status": r["pipeline_status"],
                    "error_type": r["error_type"],
                    "error_message": r["error_message"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                }
                for r in receipts_latest_rows
            ]

        path_leaks_30d = await _get_path_leaks_30d_cached(db, db_stats)

        timing_events = int(timing_and_alerts_row["events"] or 0)
        timing_min_ts = timing_and_alerts_row["min_ts"].isoformat() if timing_and_alerts_row["min_ts"] else None
        timing_max_ts = timing_and_alerts_row["max_ts"].isoformat() if timing_and_alerts_row["max_ts"] else None
        bad_duration = int(timing_and_alerts_row["bad_duration"] or 0)

        has_requests = any(int(item["count_requests"]) > 0 for item in slo_daily_items_json)
        alerts_reasons_shape_ok = all(isinstance(item.get("reasons"), list) for item in alerts_json)
        runs_worst_empty = include_worst_runs and len(worst_runs_json) == 0

        checks = [
            {
                "id": "timing_events_window",
                "pass": timing_events > 0,
                "value": timing_events,
                "threshold": "> 0",
                "hard": True,
            },
            {
                "id": "timing_bad_duration_window",
                "pass": bad_duration == 0,
                "value": bad_duration,
                "threshold": "= 0",
                "hard": True,
            },
            {
                "id": "daily_has_requests_window",
                "pass": has_requests,
                "value": has_requests,
                "threshold": "true",
                "hard": True,
            },
            {
                "id": "receipts_path_leaks_30d",
                "pass": int(path_leaks_30d) == 0,
                "value": int(path_leaks_30d),
                "threshold": "= 0",
                "hard": True,
            },
            {
                "id": "alerts_reasons_shape",
                "pass": alerts_reasons_shape_ok,
                "value": alerts_reasons_shape_ok,
                "threshold": "list",
                "hard": True,
            },
            {
                "id": "worst_runs_present",
                "pass": (not runs_worst_empty) if include_worst_runs else True,
                "value": len(worst_runs_json) if include_worst_runs else None,
                "threshold": f"> 0 (window={REPORT_RUNS_WINDOW_DAYS}d)"
                if include_worst_runs
                else "skipped_default",
                "hard": False,
                "note": "empty_is_ok_when_missing_projection"
                if include_worst_runs
                else "skipped_by_default_use_include_worst_runs=true",
            },
        ]

        final_status = _status_from_checks(checks, runs_worst_empty=runs_worst_empty)

        report = {
            "generated_at_utc": generated_at_utc,
            "version": {
                "api_version": api_version,
                "ces_default_version": CES_DEFAULT_VERSION,
                "git_tag": git_tag,
                "git_commit": git_commit,
                "alembic_head": alembic_head,
            },
            "timing": {
                "window_minutes": timing_minutes,
                "events": timing_events,
                "min_ts": timing_min_ts,
                "max_ts": timing_max_ts,
                "bad_duration": bad_duration,
            },
            "slo_daily": {
                "window_days": window_days,
                "items": slo_daily_items_json,
                "summary": slo_daily_summary_json,
                "has_requests": has_requests,
            },
            "slo_alerts": {
                "window_days": REPORT_ALERTS_WINDOW_DAYS,
                "items": alerts_json,
                "count": alerts_count if not include_alert_items else len(alerts_json),
            },
            "runs": {
                "window_days": REPORT_RUNS_WINDOW_DAYS,
                "worst": worst_runs_json,
                "note": "empty_is_ok_when_missing_projection"
                if include_worst_runs
                else "disabled_by_default_use_include_worst_runs=true",
            },
            "publish_receipts": {
                "errors_7d": receipts_errors_json,
                "latest_7d": receipts_latest_json,
                "path_leaks_30d": int(path_leaks_30d),
            },
            "checks": checks,
            "status": final_status,
        }
        status_code = 200
        return report
    except HTTPException as exc:
        status_code = exc.status_code
        raise
    finally:
        duration_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
        _emit_metrics_endpoint_timing(
            endpoint="/api/v1/observability/report",
            method="GET",
            status_code=status_code,
            duration_ms=duration_ms,
            query_fingerprint=query_fingerprint,
            db_us=db_stats["db_us"],
            db_queries=db_stats["db_queries"],
            db_pool_wait_us=db_stats["db_pool_wait_us"],
        )
