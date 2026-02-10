from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CognitiveMetricsDaily, ObservationRecord
from app.db.session import get_db

router = APIRouter()

# Cleanup SQL (nao executar automaticamente):
# DELETE FROM observations
# WHERE process_id LIKE 'P_METRICS_TEST_%'
#   AND facts->>'event_type' IN ('cognitive_metrics_alert');


def _parse_date(value: str | None, label: str) -> date | None:
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(status_code=400, detail=f"{label} must be YYYY-MM-DD")


@router.get("/daily")
async def get_daily_metrics(
    days: int = 7,
    start_date: str | None = None,
    end_date: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna métricas diárias agregadas por data (read-only).
    """
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="days must be between 1 and 365")

    start = _parse_date(start_date, "start_date")
    end = _parse_date(end_date, "end_date")

    if end is None:
        end = datetime.utcnow().date()
    if start is None:
        start = end - timedelta(days=days - 1)

    if start > end:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")

    stmt = (
        select(CognitiveMetricsDaily)
        .where(CognitiveMetricsDaily.metric_date >= start)
        .where(CognitiveMetricsDaily.metric_date <= end)
        .order_by(CognitiveMetricsDaily.metric_date.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()

    alert_stmt = (
        select(
            ObservationRecord.observation_id,
            ObservationRecord.facts,
        )
        .where(ObservationRecord.facts["event_type"].astext == "cognitive_metrics_alert")
        .where(ObservationRecord.facts["metric_date"].astext >= start.isoformat())
        .where(ObservationRecord.facts["metric_date"].astext <= end.isoformat())
    )
    alert_rows = (await db.execute(alert_stmt)).all()
    alerts_by_date: dict[str, dict] = {}
    for obs_id, facts in alert_rows:
        metric_date = None
        reasons = []
        if isinstance(facts, dict):
            metric_date = facts.get("metric_date")
            raw_reasons = facts.get("reasons")
            if isinstance(raw_reasons, list):
                reasons = raw_reasons
        if metric_date:
            alerts_by_date[metric_date] = {
                "alert_observation_id": obs_id,
                "alert_reasons": reasons,
            }

    return [
        {
            "metric_date": r.metric_date.isoformat(),
            "total_runs": r.total_runs,
            "completed_runs": r.completed_runs,
            "failed_runs": r.failed_runs,
            "blocked_runs": r.blocked_runs,
            "avg_actions_executed": float(r.avg_actions_executed)
            if r.avg_actions_executed is not None
            else None,
            "last_action_type_distribution": r.last_action_type_distribution,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "alerted": r.metric_date.isoformat() in alerts_by_date,
            "alert_reasons": alerts_by_date.get(r.metric_date.isoformat(), {}).get(
                "alert_reasons", []
            ),
            "alert_observation_id": alerts_by_date.get(
                r.metric_date.isoformat(), {}
            ).get("alert_observation_id"),
        }
        for r in rows
    ]
