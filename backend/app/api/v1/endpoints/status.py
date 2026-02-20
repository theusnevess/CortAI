from datetime import datetime
from time import perf_counter_ns
import os

from fastapi import APIRouter, Depends, HTTPException, Query
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


def _new_db_stats() -> dict[str, int]:
    """
    Inicializa acumuladores de custo de banco por request.
    """
    return {"db_us": 0, "db_queries": 0, "db_pool_wait_us": 0}


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


@router.get("/status")
async def get_status(
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
            "read_path": {
                "overview_freshness_seconds": None,
            },
        }
        # Exibe freshness do read model para auditoria do caminho materializado.
        try:
            fresh_stmt = (
                text(
                    """
                    SELECT EXTRACT(EPOCH FROM (NOW() - MAX(refreshed_at)))::int AS freshness_seconds
                    FROM metrics_overview_read_model
                    """
                )
            )
            freshness = (
                await _execute_with_db_stats(
                    db,
                    fresh_stmt,
                    db_stats,
                )
            ).scalar()
            if freshness is not None:
                response["read_path"]["overview_freshness_seconds"] = max(0, int(freshness))
        except Exception:
            # Em ambientes sem migration aplicada, mantem campo nulo.
            response["read_path"]["overview_freshness_seconds"] = None
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
