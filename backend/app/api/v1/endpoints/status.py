from datetime import datetime
from time import perf_counter_ns
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.metrics import _emit_metrics_endpoint_timing
from app.db.session import engine
from app.db.session import get_db
from app.slo_contract import (
    SLO_ENDPOINT_THRESHOLDS,
    SLO_STATUS_WINDOW_DAYS_DEFAULT,
    SLO_STATUS_WINDOW_DAYS_MAX,
)

router = APIRouter()

_C1_HEALTH_STATUS_WINDOW_MINUTES = 15
_C1_HEALTH_ENDPOINTS = {
    "overview": "/api/v1/metrics/overview",
    "runs": "/api/v1/metrics/runs",
    "report": "/api/v1/observability/report",
}
_C1_HEALTH_THRESHOLDS = {
    "overview": {"warn_p99_ms": 1500, "fail_p99_ms": 2500},
    "runs": {"warn_p99_ms": 1500, "fail_p99_ms": 2500},
    "report": {"warn_p99_ms": 1500, "fail_p99_ms": 2500},
}
_C1_HEALTH_PCT5XX_FAIL = 1.0


def _new_db_stats() -> dict[str, int]:
    """
    Inicializa acumuladores de custo de banco por request.
    """
    return {"db_us": 0, "db_queries": 0, "db_pool_wait_us": 0}


def _env_flag_enabled(name: str, default: str = "0") -> bool:
    raw = str(os.getenv(name, default)).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _should_include_c1_health(request: Request) -> bool:
    if not _env_flag_enabled("EXPOSE_C1_HEALTH_STATUS", "0"):
        return False
    return str(request.headers.get("X-Internal-Status", "")).strip() == "1"


def _classify_c1_health_row(
    *,
    endpoint: str,
    p99_ms: float | None,
    rps: float,
    timeouts: int,
    pct_429: float,
    pct_503: float,
    pct_5xx: float,
) -> dict[str, Any]:
    thresholds = _C1_HEALTH_THRESHOLDS.get(endpoint, {"warn_p99_ms": 1500, "fail_p99_ms": 2500})
    reasons: list[str] = []
    decision = "PASS"

    if timeouts > 0:
        decision = "FAIL"
        reasons.append("timeouts>0")
    elif rps < 1:
        decision = "FAIL"
        reasons.append("rps<1")
    elif pct_5xx >= _C1_HEALTH_PCT5XX_FAIL:
        decision = "FAIL"
        reasons.append("pct_5xx>=limit")
    elif p99_ms is not None and p99_ms > float(thresholds["fail_p99_ms"]):
        decision = "FAIL"
        reasons.append("p99>fail_limit")
    elif p99_ms is None:
        decision = "WARN"
        reasons.append("p99_missing")
    elif p99_ms > float(thresholds["warn_p99_ms"]):
        decision = "WARN"
        reasons.append("p99>warn_limit")
    elif pct_429 > 0:
        decision = "WARN"
        reasons.append("pct_429>0")
    elif pct_503 > 0:
        decision = "WARN"
        reasons.append("pct_503>0")

    return {"decision": decision, "reasons": reasons, "thresholds": thresholds}


def _build_c1_health_payload(rows: list[dict[str, Any]], *, as_of: datetime, window_minutes: int) -> dict[str, Any]:
    score = "PASS"
    if any(row["decision"] == "FAIL" for row in rows):
        score = "FAIL"
    elif any(row["decision"] == "WARN" for row in rows):
        score = "WARN"
    return {
        "enabled": True,
        "score": score,
        "as_of": as_of.replace(microsecond=0).isoformat() + "Z",
        "inputs": {"window_minutes": int(window_minutes), "source": "metrics_endpoint_timing"},
        "rows": rows,
    }


async def _compute_runtime_c1_health(
    *,
    db: AsyncSession,
    db_stats: dict[str, int],
    window_minutes: int = _C1_HEALTH_STATUS_WINDOW_MINUTES,
) -> dict[str, Any]:
    endpoint_paths = list(_C1_HEALTH_ENDPOINTS.values())
    timing_rows = (
        await _execute_with_db_stats(
            db,
            text(
                """
                WITH timing AS (
                  SELECT
                    facts->>'endpoint' AS endpoint,
                    NULLIF(facts->>'duration_ms', '')::float AS duration_ms,
                    COALESCE(NULLIF(facts->>'status_code', '')::int, 0) AS status_code
                  FROM observations
                  WHERE facts->>'event_type' = 'metrics_endpoint_timing'
                    AND timestamp >= NOW() - make_interval(mins => :window_minutes)
                    AND facts->>'endpoint' IN (:endpoint_overview, :endpoint_runs, :endpoint_report)
                )
                SELECT
                  endpoint,
                  COUNT(*)::int AS events,
                  percentile_cont(0.99) WITHIN GROUP (ORDER BY duration_ms) AS p99_ms,
                  SUM(CASE WHEN status_code = 429 THEN 1 ELSE 0 END)::int AS c429,
                  SUM(CASE WHEN status_code = 503 THEN 1 ELSE 0 END)::int AS c503,
                  SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END)::int AS c5xx
                FROM timing
                GROUP BY endpoint
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
    ).mappings().all()

    rows_by_path = {str(r["endpoint"]): r for r in timing_rows}
    runtime_rows: list[dict[str, Any]] = []
    window_seconds = max(1, int(window_minutes) * 60)
    as_of = datetime.utcnow()

    for short_name in ("overview", "runs", "report"):
        path = _C1_HEALTH_ENDPOINTS[short_name]
        row = rows_by_path.get(path)
        events = int((row or {}).get("events") or 0)
        p99_val = None if row is None or row.get("p99_ms") is None else float(row["p99_ms"])
        rps = round(events / float(window_seconds), 3)
        timeouts = 0  # Fonte runtime (timing server-side) nao observa timeout do cliente.
        pct_429 = round((int(row["c429"] or 0) / events) * 100.0, 2) if events > 0 else 0.0
        pct_503 = round((int(row["c503"] or 0) / events) * 100.0, 2) if events > 0 else 0.0
        pct_5xx = round((int(row["c5xx"] or 0) / events) * 100.0, 2) if events > 0 else 0.0
        classified = _classify_c1_health_row(
            endpoint=short_name,
            p99_ms=p99_val,
            rps=rps,
            timeouts=timeouts,
            pct_429=pct_429,
            pct_503=pct_503,
            pct_5xx=pct_5xx,
        )
        runtime_rows.append(
            {
                "endpoint": short_name,
                "path": "direct",
                "p99_ms": None if p99_val is None else round(p99_val, 2),
                "rps": rps,
                "timeouts": timeouts,
                "pct_429": pct_429,
                "pct_503": pct_503,
                "pct_5xx": pct_5xx,
                "decision": classified["decision"],
                "reasons": classified["reasons"],
            }
        )

    return _build_c1_health_payload(runtime_rows, as_of=as_of, window_minutes=window_minutes)


async def _execute_with_db_stats(
    db: AsyncSession,
    statement,
    db_stats: dict[str, int],
    params: dict | None = None,
):
    """
    Executa query contabilizando tempo e volume de chamadas ao banco.
    """
    started_ns = perf_counter_ns()
    if params is None:
        result = await db.execute(statement)
    else:
        result = await db.execute(statement, params)
    elapsed_us = max(0, (perf_counter_ns() - started_ns) // 1000)
    db_stats["db_us"] = int(db_stats.get("db_us", 0)) + int(elapsed_us)
    db_stats["db_queries"] = int(db_stats.get("db_queries", 0)) + 1
    return result


def _read_capacity_config() -> dict:
    """
    Retorna configuracao efetiva de capacidade para auditoria operacional.
    """
    pool = engine.sync_engine.pool
    # Usa metodos do pool quando disponiveis; fallback para envs conhecidos.
    def _pool_int(method_name: str, env_name: str, default: int) -> int:
        method = getattr(pool, method_name, None)
        if callable(method):
            try:
                return int(method())
            except Exception:
                pass
        raw = os.getenv(env_name)
        try:
            return int(raw) if raw is not None else default
        except Exception:
            return default

    def _pool_float(method_name: str, env_name: str, default: float) -> float:
        method = getattr(pool, method_name, None)
        if callable(method):
            try:
                return float(method())
            except Exception:
                pass
        raw = os.getenv(env_name)
        try:
            return float(raw) if raw is not None else default
        except Exception:
            return default

    def _effective_api_workers(default: int = 1) -> int:
        """
        Prioriza workers efetivos do processo (cmdline) e cai para env vars.
        """
        try:
            with open("/proc/1/cmdline", "rb") as fh:
                parts = [p.decode("utf-8", errors="ignore") for p in fh.read().split(b"\x00") if p]
            for idx, part in enumerate(parts):
                if part == "--workers" and idx + 1 < len(parts):
                    return int(parts[idx + 1])
        except Exception:
            pass
        raw = os.getenv("API_WORKERS") or os.getenv("WEB_CONCURRENCY")
        try:
            return int(raw) if raw is not None else default
        except Exception:
            return default

    def _pool_max_overflow(default: int = 10) -> int:
        """
        Expondo max_overflow configurado (nao overflow atual, que pode ser negativo).
        """
        raw_attr = getattr(pool, "_max_overflow", None)
        try:
            if raw_attr is not None:
                return int(raw_attr)
        except Exception:
            pass
        raw_env = os.getenv("DB_MAX_OVERFLOW")
        try:
            return int(raw_env) if raw_env is not None else default
        except Exception:
            return default

    return {
        "db_pool_size": _pool_int("size", "DB_POOL_SIZE", 5),
        "db_max_overflow": _pool_max_overflow(10),
        "db_pool_timeout": _pool_float("timeout", "DB_POOL_TIMEOUT", 30.0),
        "db_checked_out": _pool_int("checkedout", "DB_CHECKEDOUT", 0),
        "api_workers": _effective_api_workers(1),
    }


def _read_read_api_config() -> dict:
    """
    Exibe configuracao declarativa do read-api para auditoria operacional.
    """
    enabled_raw = str(os.getenv("READ_API_ENABLED", "false")).strip().lower()
    enabled = enabled_raw in {"1", "true", "yes", "on"}
    base_url = os.getenv("READ_API_BASE_URL", "")
    return {
        "enabled": enabled,
        "up": enabled,
        "base_url": base_url,
    }


@router.get("/status")
async def get_status(
    request: Request,
    window_days: int = Query(SLO_STATUS_WINDOW_DAYS_DEFAULT, ge=1),
    db: AsyncSession = Depends(get_db),
):
    started_at = datetime.utcnow()
    status_code = 500
    query_fingerprint = f"window_days={window_days}"
    db_stats = _new_db_stats()
    try:
        if window_days > SLO_STATUS_WINDOW_DAYS_MAX:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_type": "RangeTooLarge",
                    "window_days_requested": window_days,
                    "window_days_max": SLO_STATUS_WINDOW_DAYS_MAX,
                },
            )

        # Reaproveita agregado diario para evitar query pesada no endpoint executivo.
        rows = (
            await _execute_with_db_stats(
                db,
                text(
                    """
                    SELECT
                      endpoint,
                      SUM(count_requests)::int AS total_requests,
                      MAX(p95_ms)::int AS p95_ms,
                      MAX(p99_ms)::int AS p99_ms,
                      CASE
                        WHEN SUM(count_requests) > 0
                        THEN SUM((error_rate::float * count_requests)) / SUM(count_requests)
                        ELSE 0
                      END AS error_rate
                    FROM metrics_endpoint_daily
                    WHERE metric_date >= (CURRENT_DATE - make_interval(days => :window_days))::date
                    GROUP BY endpoint
                    """
                ),
                db_stats,
                {"window_days": window_days},
            )
        ).mappings().all()

        rows_by_endpoint = {str(row["endpoint"]): row for row in rows}
        endpoints_payload: list[dict] = []
        hard_fail = False
        missing_endpoints: list[str] = []
        total_requests = 0
        total_allowed_errors = 0.0
        total_estimated_errors = 0.0

        for endpoint in sorted(SLO_ENDPOINT_THRESHOLDS.keys()):
            slo = SLO_ENDPOINT_THRESHOLDS[endpoint]
            row = rows_by_endpoint.get(endpoint)
            if row is None:
                # Endpoint sem dados no periodo vira WARN, nao FAIL.
                missing_endpoints.append(endpoint)
                endpoints_payload.append(
                    {
                        "endpoint": endpoint,
                        "status": "WARN",
                        "reason": "no_data",
                        "slo": slo,
                        "observed": None,
                        "error_budget": None,
                    }
                )
                continue

            observed = {
                "total_requests": int(row["total_requests"] or 0),
                "p95_ms": int(row["p95_ms"] or 0),
                "p99_ms": int(row["p99_ms"] or 0),
                "error_rate": round(float(row["error_rate"] or 0.0), 6),
            }
            breaches: list[str] = []
            if observed["p95_ms"] > int(slo["p95_ms"]):
                breaches.append("p95_slo_breach")
            if observed["p99_ms"] > int(slo["p99_ms"]):
                breaches.append("p99_slo_breach")
            if observed["error_rate"] > float(slo["error_rate"]):
                breaches.append("error_rate_breach")

            endpoint_total_requests = observed["total_requests"]
            allowed_errors = endpoint_total_requests * float(slo["error_rate"])
            estimated_errors = endpoint_total_requests * observed["error_rate"]
            remaining_errors = round(allowed_errors - estimated_errors, 2)
            remaining_ratio = 1.0
            if float(slo["error_rate"]) > 0:
                remaining_ratio = round(
                    (float(slo["error_rate"]) - observed["error_rate"]) / float(slo["error_rate"]),
                    4,
                )

            total_requests += endpoint_total_requests
            total_allowed_errors += allowed_errors
            total_estimated_errors += estimated_errors

            endpoint_status = "PASS"
            if breaches:
                endpoint_status = "FAIL"
                hard_fail = True

            endpoints_payload.append(
                {
                    "endpoint": endpoint,
                    "status": endpoint_status,
                    "slo": slo,
                    "observed": observed,
                    "breaches": breaches,
                    "error_budget": {
                        "allowed_errors": round(allowed_errors, 2),
                        "estimated_errors": round(estimated_errors, 2),
                        "remaining_errors": remaining_errors,
                        "remaining_ratio": remaining_ratio,
                    },
                }
            )

        remaining_global_errors = round(total_allowed_errors - total_estimated_errors, 2)
        remaining_global_ratio = 1.0
        if total_allowed_errors > 0:
            remaining_global_ratio = round(
                (total_allowed_errors - total_estimated_errors) / total_allowed_errors, 4
            )

        # Status global segue regra deterministica: FAIL > WARN > PASS.
        overall_status = "PASS"
        if hard_fail:
            overall_status = "FAIL"
        elif missing_endpoints:
            overall_status = "WARN"

        response = {
            "generated_at_utc": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            "window_days": window_days,
            "overall_status": overall_status,
            "slo_status": {
                "status": "FAIL" if hard_fail else ("WARN" if missing_endpoints else "PASS"),
                "missing_endpoints": missing_endpoints,
                "endpoints": endpoints_payload,
            },
            "error_budget_remaining": {
                "status": "FAIL" if remaining_global_errors < 0 else "PASS",
                "window_days": window_days,
                "total_requests": int(total_requests),
                "allowed_errors": round(total_allowed_errors, 2),
                "estimated_errors": round(total_estimated_errors, 2),
                "remaining_errors": remaining_global_errors,
                "remaining_ratio": remaining_global_ratio,
            },
            "ces_trend_status": {
                "status": "INFO",
                "reason": "not_evaluated_in_status_v1",
            },
            # Config efetiva para correlacionar contensao C2 sem inspecao manual.
            "capacity_config": _read_capacity_config(),
            "read_api": _read_read_api_config(),
            "read_path": {
                "overview_freshness_seconds": None,
                "overview_snapshot_status": "missing",
                "overview_last_refreshed_at": None,
                "runs_freshness_seconds": None,
                "runs_snapshot_status": "missing",
                "runs_last_refreshed_at": None,
                "runs_key_count": 0,
                "jobs_queued_count": 0,
            },
        }
        # Exibe freshness do read model para auditoria do caminho materializado.
        try:
            fresh_stmt = (
                text(
                    """
                    SELECT
                      EXTRACT(EPOCH FROM (NOW() - MAX(refreshed_at)))::int AS freshness_seconds,
                      MAX(refreshed_at) AS last_refreshed_at
                    FROM metrics_overview_read_model
                    """
                )
            )
            row = (
                await _execute_with_db_stats(
                    db,
                    fresh_stmt,
                    db_stats,
                )
            ).mappings().first()
            if row is not None:
                freshness = row.get("freshness_seconds")
                last_refreshed_at = row.get("last_refreshed_at")
                if freshness is not None:
                    response["read_path"]["overview_freshness_seconds"] = max(0, int(freshness))
                if last_refreshed_at is not None:
                    response["read_path"]["overview_last_refreshed_at"] = last_refreshed_at.isoformat()
                    response["read_path"]["overview_snapshot_status"] = (
                        "fresh" if int(freshness or 0) <= 60 else "stale"
                    )
        except Exception:
            # Em ambientes sem migration aplicada, mantem campo nulo.
            response["read_path"]["overview_freshness_seconds"] = None
            response["read_path"]["overview_snapshot_status"] = "missing"
            response["read_path"]["overview_last_refreshed_at"] = None
        try:
            runs_stmt = text(
                """
                SELECT
                  EXTRACT(EPOCH FROM (NOW() - MAX(refreshed_at)))::int AS freshness_seconds,
                  MAX(refreshed_at) AS last_refreshed_at,
                  COUNT(*)::int AS key_count
                FROM metrics_runs_read_model
                """
            )
            row = (
                await _execute_with_db_stats(
                    db,
                    runs_stmt,
                    db_stats,
                )
            ).mappings().first()
            if row is not None:
                freshness = row.get("freshness_seconds")
                last_refreshed_at = row.get("last_refreshed_at")
                key_count = row.get("key_count")
                if freshness is not None:
                    response["read_path"]["runs_freshness_seconds"] = max(0, int(freshness))
                if last_refreshed_at is not None:
                    response["read_path"]["runs_last_refreshed_at"] = last_refreshed_at.isoformat()
                    response["read_path"]["runs_snapshot_status"] = (
                        "fresh" if int(freshness or 0) <= 60 else "stale"
                    )
                if key_count is not None:
                    response["read_path"]["runs_key_count"] = max(0, int(key_count))
        except Exception:
            # Em ambientes sem migration aplicada, mantem campos default.
            response["read_path"]["runs_freshness_seconds"] = None
            response["read_path"]["runs_snapshot_status"] = "missing"
            response["read_path"]["runs_last_refreshed_at"] = None
            response["read_path"]["runs_key_count"] = 0
        try:
            jobs_stmt = text(
                """
                SELECT COUNT(*)::int AS queued_count
                FROM metrics_read_refresh_jobs
                WHERE status = 'queued' AND expires_at > NOW()
                """
            )
            queued_count = (
                await _execute_with_db_stats(
                    db,
                    jobs_stmt,
                    db_stats,
                )
            ).scalar()
            if queued_count is not None:
                response["read_path"]["jobs_queued_count"] = max(0, int(queued_count))
        except Exception:
            response["read_path"]["jobs_queued_count"] = 0
        if _should_include_c1_health(request):
            try:
                response["c1_health"] = await _compute_runtime_c1_health(db=db, db_stats=db_stats)
            except Exception:
                response["c1_health"] = _build_c1_health_payload(
                    [
                        {
                            "endpoint": ep,
                            "path": "direct",
                            "p99_ms": None,
                            "rps": 0.0,
                            "timeouts": 0,
                            "pct_429": 0.0,
                            "pct_503": 0.0,
                            "pct_5xx": 0.0,
                            "decision": "FAIL",
                            "reasons": ["runtime_c1_health_unavailable"],
                        }
                        for ep in ("overview", "runs", "report")
                    ],
                    as_of=datetime.utcnow(),
                    window_minutes=_C1_HEALTH_STATUS_WINDOW_MINUTES,
                )
        status_code = 200
        return response
    except HTTPException as e:
        status_code = e.status_code
        raise
    finally:
        duration_ms = int(max(0.0, (datetime.utcnow() - started_at).total_seconds() * 1000.0))
        _emit_metrics_endpoint_timing(
            endpoint="/api/v1/status",
            method="GET",
            status_code=status_code,
            duration_ms=duration_ms,
            query_fingerprint=query_fingerprint,
            db_us=db_stats["db_us"],
            db_queries=db_stats["db_queries"],
            db_pool_wait_us=db_stats["db_pool_wait_us"],
        )
