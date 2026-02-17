from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.metrics import _emit_metrics_endpoint_timing
from app.db.session import get_db
from app.slo_contract import (
    SLO_ENDPOINT_THRESHOLDS,
    SLO_STATUS_WINDOW_DAYS_DEFAULT,
    SLO_STATUS_WINDOW_DAYS_MAX,
)

router = APIRouter()


@router.get("/status")
async def get_status(
    window_days: int = Query(SLO_STATUS_WINDOW_DAYS_DEFAULT, ge=1),
    db: AsyncSession = Depends(get_db),
):
    started_at = datetime.utcnow()
    status_code = 500
    query_fingerprint = f"window_days={window_days}"
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
            await db.execute(
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
        }
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
        )
