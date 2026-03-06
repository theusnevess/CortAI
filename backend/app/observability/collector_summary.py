from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_collector_summary(
    db: AsyncSession,
    db_stats: dict[str, int],
    *,
    execute_with_db_stats,
    window_minutes: int = 15,
    last_events_limit: int = 5,
) -> dict | None:
    """
    Resume eventos collector_run em janela curta para o painel operacional.

    Retorna um shape consistente ou None em caso de falha, sem quebrar o overview.
    """
    try:
        counts_row = (
            await execute_with_db_stats(
                db,
                text(
                    """
                    SELECT
                      SUM(CASE WHEN facts->>'status' = 'success' THEN 1 ELSE 0 END)::int AS success_count,
                      SUM(CASE WHEN facts->>'status' = 'failed' THEN 1 ELSE 0 END)::int AS failed_count
                    FROM observations
                    WHERE facts->>'event_type' = 'collector_run'
                      AND timestamp >= NOW() - make_interval(mins => :window_minutes)
                    """
                ),
                db_stats,
                {"window_minutes": int(window_minutes)},
            )
        ).mappings().first()

        error_rows = (
            await execute_with_db_stats(
                db,
                text(
                    """
                    SELECT
                      facts->>'error_type' AS error_type,
                      COUNT(*)::int AS n
                    FROM observations
                    WHERE facts->>'event_type' = 'collector_run'
                      AND timestamp >= NOW() - make_interval(mins => :window_minutes)
                      AND NULLIF(facts->>'error_type', '') IS NOT NULL
                    GROUP BY facts->>'error_type'
                    ORDER BY n DESC, error_type ASC
                    """
                ),
                db_stats,
                {"window_minutes": int(window_minutes)},
            )
        ).mappings().all()

        last_rows = (
            await execute_with_db_stats(
                db,
                text(
                    """
                    SELECT
                      timestamp,
                      facts->>'status' AS status,
                      facts->>'error_type' AS error_type,
                      NULLIF(facts->>'http_status', '')::int AS http_status,
                      CASE
                        WHEN LOWER(COALESCE(facts->>'retryable', 'false')) = 'true' THEN TRUE
                        ELSE FALSE
                      END AS retryable,
                      NULLIF(facts->>'job_id', '') AS job_id
                    FROM observations
                    WHERE facts->>'event_type' = 'collector_run'
                      AND timestamp >= NOW() - make_interval(mins => :window_minutes)
                    ORDER BY timestamp DESC
                    LIMIT :limit_rows
                    """
                ),
                db_stats,
                {
                    "window_minutes": int(window_minutes),
                    "limit_rows": int(last_events_limit),
                },
            )
        ).mappings().all()

        return {
            "window_minutes": int(window_minutes),
            "events": {
                "success": int((counts_row or {}).get("success_count") or 0),
                "failed": int((counts_row or {}).get("failed_count") or 0),
            },
            "by_error_type": {
                str(row["error_type"]): int(row["n"])
                for row in error_rows
                if row.get("error_type")
            },
            "last_events": [
                {
                    "ts": row["timestamp"].isoformat() if row.get("timestamp") else None,
                    "status": row.get("status"),
                    "error_type": row.get("error_type"),
                    "http_status": int(row["http_status"]) if row.get("http_status") is not None else None,
                    "retryable": bool(row.get("retryable")),
                    "job_id": row.get("job_id"),
                }
                for row in last_rows
            ],
        }
    except Exception:
        return None
