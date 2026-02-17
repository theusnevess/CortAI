import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.metrics import CES_DEFAULT_VERSION, _emit_metrics_endpoint_timing
from app.db.session import get_db

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


def _validate_report_params(
    *,
    window_days: int,
    timing_minutes: int,
    limit_alerts: int,
    limit_receipts: int,
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


def _status_from_checks(checks: list[dict], runs_worst_empty: bool) -> str:
    hard_failed = any((not c.get("pass")) and c.get("hard") for c in checks)
    if hard_failed:
        return "FAIL"
    if runs_worst_empty:
        return "WARN"
    return "PASS"


@router.get("/report")
async def get_observability_report(
    window_days: int = Query(REPORT_WINDOW_DAYS_DEFAULT, ge=1),
    timing_minutes: int = Query(REPORT_TIMING_MINUTES_DEFAULT, ge=1),
    limit_alerts: int = Query(REPORT_LIMIT_ALERTS_DEFAULT, ge=1),
    limit_receipts: int = Query(REPORT_LIMIT_RECEIPTS_DEFAULT, ge=1),
    db: AsyncSession = Depends(get_db),
):
    """
    Consolida report read-only de observabilidade com base no runbook operacional.
    """
    started_at = datetime.utcnow()
    status_code = 500
    query_fingerprint = (
        f"window_days={window_days}&timing_minutes={timing_minutes}"
        f"&limit_alerts={limit_alerts}&limit_receipts={limit_receipts}"
    )
    try:
        _validate_report_params(
            window_days=window_days,
            timing_minutes=timing_minutes,
            limit_alerts=limit_alerts,
            limit_receipts=limit_receipts,
        )

        generated_at_utc = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        api_version = os.getenv("APP_VERSION", "1.8.2")
        git_tag = os.getenv("GIT_TAG")
        git_commit = os.getenv("GIT_COMMIT")

        alembic_head = None
        try:
            alembic_row = (await db.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))).first()
            if alembic_row:
                alembic_head = str(alembic_row[0])
        except Exception:
            alembic_head = None

        timing_row = (
            await db.execute(
                text(
                    """
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
                    """
                ),
                {"timing_minutes": timing_minutes},
            )
        ).mappings().one()

        slo_daily_items = (
            await db.execute(
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

        slo_daily_summary = (
            await db.execute(
                text(
                    """
                    SELECT
                      endpoint,
                      SUM(count_requests)::int AS total_requests,
                      AVG(p95_ms)::float AS avg_p95_ms,
                      AVG(p99_ms)::float AS avg_p99_ms,
                      AVG(error_rate)::float AS avg_error_rate
                    FROM metrics_endpoint_daily
                    WHERE metric_date >= (CURRENT_DATE - make_interval(days => :window_days))::date
                    GROUP BY endpoint
                    ORDER BY total_requests DESC
                    """
                ),
                {"window_days": window_days},
            )
        ).mappings().all()
        slo_daily_summary_json = [
            {
                "endpoint": str(r["endpoint"]),
                "total_requests": int(r["total_requests"]),
                "avg_p95_ms": round(float(r["avg_p95_ms"] or 0), 4),
                "avg_p99_ms": round(float(r["avg_p99_ms"] or 0), 4),
                "avg_error_rate": round(float(r["avg_error_rate"] or 0), 6),
            }
            for r in slo_daily_summary
        ]

        alerts_rows = (
            await db.execute(
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

        worst_runs_rows = (
            await db.execute(
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
                {
                    "runs_window_days": REPORT_RUNS_WINDOW_DAYS,
                    "worst_runs_limit": REPORT_WORST_RUNS_LIMIT,
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

        receipts_errors_rows = (
            await db.execute(
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
                )
            )
        ).mappings().all()
        receipts_errors_json = [
            {"error_type": r["error_type"], "n": int(r["n"])}
            for r in receipts_errors_rows
        ]

        receipts_latest_rows = (
            await db.execute(
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

        path_leaks_30d = (
            await db.execute(
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
                )
            )
        ).scalar() or 0

        timing_events = int(timing_row["events"] or 0)
        timing_min_ts = timing_row["min_ts"].isoformat() if timing_row["min_ts"] else None
        timing_max_ts = timing_row["max_ts"].isoformat() if timing_row["max_ts"] else None
        bad_duration = int(timing_row["bad_duration"] or 0)

        has_requests = any(int(item["count_requests"]) > 0 for item in slo_daily_items_json)
        alerts_reasons_shape_ok = all(isinstance(item.get("reasons"), list) for item in alerts_json)
        runs_worst_empty = len(worst_runs_json) == 0

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
                "pass": not runs_worst_empty,
                "value": len(worst_runs_json),
                "threshold": f"> 0 (window={REPORT_RUNS_WINDOW_DAYS}d)",
                "hard": False,
                "note": "empty_is_ok_when_missing_projection",
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
                "count": len(alerts_json),
            },
            "runs": {
                "window_days": REPORT_RUNS_WINDOW_DAYS,
                "worst": worst_runs_json,
                "note": "empty_is_ok_when_missing_projection",
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
        )
