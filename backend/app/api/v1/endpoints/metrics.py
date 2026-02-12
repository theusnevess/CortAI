import math
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CognitiveMetricsDaily, ObservationRecord
from app.db.session import get_db

router = APIRouter()

# Cleanup SQL (nao executar automaticamente):
# DELETE FROM observations
# WHERE process_id LIKE 'P_METRICS_TEST_%'
#   AND facts->>'event_type' IN ('cognitive_metrics_alert');

# Chaves proibidas de facts para evitar exposicao acidental de paths.
PROHIBITED_FACT_KEYS = {
    "raw_video_minio_path",
    "audio_local_path",
    "video_local_path",
    "file_path",
    "thumbnail_path",
}

CES_VERSION = "CES_v1"
CES_STATUS_WEIGHTS = {"blocked": 1.0, "failed": 0.6, "truncated": 0.3}
CES_COMPONENT_WEIGHTS = {"status": 0.55, "actions": 0.15, "latency": 0.25, "trunc": 0.05}
CES_ACTIONS_GOOD = 1.0
CES_ACTIONS_BAD = 6.0
CES_MIN_OBS_FOR_LATENCY = 10
CES_LATENCY_ACTION_WHITELIST = {
    "collect_video",
    "extract_audio",
    "segment_audio",
    "transcribe_segments",
    "write_artifact",
    "publish_manifest",
}


def _parse_date(value: str | None, label: str) -> date | None:
    """
    Converte string YYYY-MM-DD em date.
    Args:
        value: String no formato YYYY-MM-DD ou None.
        label: Nome do campo para mensagem de erro.
    Returns:
        Data correspondente ou None quando value for None.
    Raises:
        HTTPException 400 se o formato for invalido.
    """
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(status_code=400, detail=f"{label} must be YYYY-MM-DD")


def _filter_facts(facts: dict) -> dict:
    """
    Remove chaves proibidas do dicionario facts.
    """
    if not isinstance(facts, dict):
        return facts
    return {k: v for k, v in facts.items() if k not in PROHIBITED_FACT_KEYS}


def _dedup_and_sort_reasons(reasons: list) -> list:
    """
    Deduplica e ordena a lista de reasons.
    """
    if not isinstance(reasons, list):
        return []
    return sorted(set(str(r) for r in reasons))


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    """
    Limita valor numerico no intervalo [min_value, max_value].
    """
    return max(min_value, min(max_value, value))


def _compute_ces_fields(item: dict) -> dict:
    """
    Calcula CES diario com componentes explicitos e budgets auditaveis.
    Regras:
    - total_runs == 0 => CES nulo com reason "no_runs"
    - latency so considera acoes com n >= CES_MIN_OBS_FOR_LATENCY
    """
    total_runs = int(item.get("total_runs") or 0)
    if total_runs <= 0:
        return {
            "ces": None,
            "ces_reason": "no_runs",
            "ces_version": CES_VERSION,
            "ces_components": {
                "status": None,
                "actions": None,
                "latency": None,
                "trunc": None,
            },
            "budgets_used": {},
        }

    blocked_runs = int(item.get("blocked_runs") or 0)
    failed_runs = int(item.get("failed_runs") or 0)
    truncated_runs = int(item.get("truncated_runs") or 0)

    r_b = blocked_runs / total_runs
    r_f = failed_runs / total_runs
    r_t = truncated_runs / total_runs

    s_status = _clamp(
        1.0
        - (
            CES_STATUS_WEIGHTS["blocked"] * r_b
            + CES_STATUS_WEIGHTS["failed"] * r_f
            + CES_STATUS_WEIGHTS["truncated"] * r_t
        )
    )

    avg_actions = float(item.get("avg_actions_executed") or 0.0)
    denom_actions = CES_ACTIONS_BAD - CES_ACTIONS_GOOD
    if denom_actions <= 0:
        s_actions = 1.0
    else:
        s_actions = _clamp((CES_ACTIONS_BAD - avg_actions) / denom_actions)

    s_trunc = _clamp(1.0 - r_t)

    latency_by_action = item.get("latency_by_action") or {}
    eligible: dict[str, dict] = {}
    total_n = 0
    for action_name, payload in latency_by_action.items():
        if not isinstance(payload, dict):
            continue
        if action_name not in CES_LATENCY_ACTION_WHITELIST:
            continue
        n_obs = int(payload.get("n") or 0)
        p95_ms = int(payload.get("p95_ms") or 0)
        if n_obs < CES_MIN_OBS_FOR_LATENCY or p95_ms <= 0:
            continue
        budget_ms = int(math.ceil(p95_ms * 1.10))
        eligible[action_name] = {"n": n_obs, "p95_ms": p95_ms, "budget_ms": budget_ms}
        total_n += n_obs

    if total_n <= 0:
        s_latency = 1.0
        budgets_used = {}
    else:
        s_latency = 0.0
        budgets_used = {}
        for action_name, payload in sorted(eligible.items()):
            weight = payload["n"] / total_n
            action_score = _clamp(payload["budget_ms"] / payload["p95_ms"])
            s_latency += weight * action_score
            budgets_used[action_name] = {
                "n": payload["n"],
                "p95_ms": payload["p95_ms"],
                "budget_ms": payload["budget_ms"],
                "weight": round(weight, 6),
            }
        s_latency = _clamp(s_latency)

    ces_value = 100.0 * (
        CES_COMPONENT_WEIGHTS["status"] * s_status
        + CES_COMPONENT_WEIGHTS["actions"] * s_actions
        + CES_COMPONENT_WEIGHTS["latency"] * s_latency
        + CES_COMPONENT_WEIGHTS["trunc"] * s_trunc
    )

    return {
        "ces": round(_clamp(ces_value, 0.0, 100.0), 2),
        "ces_reason": None,
        "ces_version": CES_VERSION,
        "ces_components": {
            "status": round(s_status, 4),
            "actions": round(s_actions, 4),
            "latency": round(s_latency, 4),
            "trunc": round(s_trunc, 4),
        },
        "budgets_used": budgets_used,
    }


def _build_alerts_by_date(alert_rows: list[tuple]) -> dict[str, dict]:
    """
    Agrega alertas de forma deterministica por metric_date.
    Mantem:
      - alert_count: quantidade de alertas no dia
      - alert_reasons: dedupe + ordenacao
      - alert_observation_id: id mais recente por timestamp
    """
    alerts_by_date: dict[str, dict] = {}
    for obs_id, ts, facts in alert_rows:
        if not isinstance(facts, dict):
            continue
        metric_date = facts.get("metric_date")
        if not metric_date:
            continue
        reasons = _dedup_and_sort_reasons(facts.get("reasons", []))
        payload = alerts_by_date.setdefault(
            metric_date,
            {
                "alert_count": 0,
                "alert_reasons": set(),
                "alert_observation_id": None,
                "latest_ts": None,
            },
        )
        payload["alert_count"] += 1
        payload["alert_reasons"].update(reasons)
        if payload["latest_ts"] is None or (ts and ts >= payload["latest_ts"]):
            payload["latest_ts"] = ts
            payload["alert_observation_id"] = obs_id

    for metric_date, payload in alerts_by_date.items():
        payload["alert_reasons"] = sorted(payload["alert_reasons"])
        payload.pop("latest_ts", None)

    return alerts_by_date


@router.get("/daily")
async def get_daily_metrics(
    days: int = 7,
    start_date: str | None = None,
    end_date: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna metricas diarias agregadas por data (read-only).
    Args:
        days: quantidade de dias para retornar (default 7, max 365)
        start_date: filtra metricas a partir dessa data (YYYY-MM-DD)
        end_date: filtra metricas ate essa data (YYYY-MM-DD)
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
            ObservationRecord.timestamp,
            ObservationRecord.facts,
        )
        .where(ObservationRecord.facts["event_type"].astext == "cognitive_metrics_alert")
        .where(ObservationRecord.facts["metric_date"].astext >= start.isoformat())
        .where(ObservationRecord.facts["metric_date"].astext <= end.isoformat())
    )
    alert_rows = (await db.execute(alert_stmt)).all()
    alerts_by_date = _build_alerts_by_date(alert_rows)

    items = []
    for r in rows:
        metric_key = r.metric_date.isoformat()
        alert_info = alerts_by_date.get(metric_key, None)
        alert_count = alert_info["alert_count"] if alert_info else 0
        alerted = alert_count > 0
        item = {
            "metric_date": r.metric_date.isoformat(),
            "total_runs": r.total_runs,
            "completed_runs": r.completed_runs,
            "failed_runs": r.failed_runs,
            "blocked_runs": r.blocked_runs,
            "truncated_runs": getattr(r, "truncated_runs", 0),
            "truncated_ratio": float(r.truncated_ratio)
            if getattr(r, "truncated_ratio", None) is not None
            else None,
            "avg_actions_executed": float(r.avg_actions_executed)
            if r.avg_actions_executed is not None
            else None,
            "last_action_type_distribution": r.last_action_type_distribution,
            "latency_by_action": getattr(r, "latency_by_action", {}) or {},
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "alerted": alerted,
            "alert_count": alert_count,
            "alert_reasons": alert_info["alert_reasons"] if alert_info else [],
            "alert_observation_id": alert_info["alert_observation_id"] if alert_info else None,
        }
        # Invariantes do contrato de alerta.
        if not item["alerted"]:
            item["alert_count"] = 0
            item["alert_reasons"] = []
            item["alert_observation_id"] = None
        elif item["alert_observation_id"] is None:
            item["alerted"] = False
            item["alert_count"] = 0
            item["alert_reasons"] = []
        item.update(_compute_ces_fields(item))
        items.append(item)

    return {"items": items}


@router.get("/overview")
async def get_metrics_overview(
    days: int = 7,
    start_date: str | None = None,
    end_date: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna metricas diarias com resumo agregado.
    Args:
        days: quantidade de dias para retornar (default 7, max 365)
        start_date: filtra metricas a partir dessa data (YYYY-MM-DD)
        end_date: filtra metricas ate essa data (YYYY-MM-DD)
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
        .order_by(CognitiveMetricsDaily.metric_date.asc())
    )
    rows = (await db.execute(stmt)).scalars().all()

    alert_stmt = (
        select(
            ObservationRecord.observation_id,
            ObservationRecord.timestamp,
            ObservationRecord.facts,
        )
        .where(ObservationRecord.facts["event_type"].astext == "cognitive_metrics_alert")
        .where(ObservationRecord.facts["metric_date"].astext >= start.isoformat())
        .where(ObservationRecord.facts["metric_date"].astext <= end.isoformat())
    )
    alert_rows = (await db.execute(alert_stmt)).all()
    alerts_by_date = _build_alerts_by_date(alert_rows)

    items = []
    for r in rows:
        metric_key = r.metric_date.isoformat()
        alert_info = alerts_by_date.get(metric_key, None)
        alert_count = alert_info["alert_count"] if alert_info else 0
        alerted = alert_count > 0
        item = {
            "metric_date": r.metric_date.isoformat(),
            "total_runs": r.total_runs,
            "completed_runs": r.completed_runs,
            "failed_runs": r.failed_runs,
            "blocked_runs": r.blocked_runs,
            "truncated_runs": getattr(r, "truncated_runs", 0),
            "truncated_ratio": float(r.truncated_ratio)
            if getattr(r, "truncated_ratio", None) is not None
            else None,
            "avg_actions_executed": float(r.avg_actions_executed)
            if r.avg_actions_executed is not None
            else None,
            "last_action_type_distribution": r.last_action_type_distribution,
            "latency_by_action": getattr(r, "latency_by_action", {}) or {},
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "alerted": alerted,
            "alert_count": alert_count,
            "alert_reasons": alert_info["alert_reasons"] if alert_info else [],
            "alert_observation_id": alert_info["alert_observation_id"] if alert_info else None,
        }
        if not item["alerted"]:
            item["alert_count"] = 0
            item["alert_reasons"] = []
            item["alert_observation_id"] = None
        elif item["alert_observation_id"] is None:
            item["alerted"] = False
            item["alert_count"] = 0
            item["alert_reasons"] = []
        item.update(_compute_ces_fields(item))
        items.append(item)

    # Resumo agregado do periodo.
    summary = {
        "total_runs": sum(item["total_runs"] for item in items),
        "completed_runs": sum(item["completed_runs"] for item in items),
        "failed_runs": sum(item["failed_runs"] for item in items),
        "blocked_runs": sum(item["blocked_runs"] for item in items),
        "truncated_runs": sum(item["truncated_runs"] for item in items),
        "alert_days": sum(1 for item in items if item["alerted"]),
    }

    total_runs = summary["total_runs"]
    if total_runs > 0:
        summary["failed_ratio"] = round(summary["failed_runs"] / total_runs, 4)
        summary["blocked_ratio"] = round(summary["blocked_runs"] / total_runs, 4)
        summary["truncated_ratio"] = round(summary["truncated_runs"] / total_runs, 4)
    else:
        summary["failed_ratio"] = 0.0
        summary["blocked_ratio"] = 0.0
        summary["truncated_ratio"] = 0.0

    # CES agregado do periodo (media ponderada por total_runs).
    items_with_runs = [item for item in items if item["ces"] is not None and item["total_runs"] > 0]
    weighted_runs = sum(item["total_runs"] for item in items_with_runs)
    if weighted_runs > 0:
        summary["ces"] = round(
            sum(float(item["ces"]) * item["total_runs"] for item in items_with_runs)
            / weighted_runs,
            2,
        )
        summary["ces_reason"] = None
        summary["ces_version"] = CES_VERSION
        summary["ces_components"] = {
            key: round(
                sum(float(item["ces_components"][key]) * item["total_runs"] for item in items_with_runs)
                / weighted_runs,
                4,
            )
            for key in ("status", "actions", "latency", "trunc")
        }
    else:
        summary["ces"] = None
        summary["ces_reason"] = "no_runs"
        summary["ces_version"] = CES_VERSION
        summary["ces_components"] = {
            "status": None,
            "actions": None,
            "latency": None,
            "trunc": None,
        }

    return {"items": items, "summary": summary}


@router.get("/alerts")
async def get_alerts(
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna alertas de metricas cognitivas com paginacao.
    Args:
        start_date: filtra alertas a partir dessa data (YYYY-MM-DD)
        end_date: filtra alertas ate essa data (YYYY-MM-DD)
        limit: quantidade maxima de alertas a retornar
        offset: quantidade de alertas para pular (paginacao)
    """
    start = _parse_date(start_date, "start_date")
    end = _parse_date(end_date, "end_date")

    if end is None:
        end = datetime.utcnow().date()
    if start is None:
        start = end - timedelta(days=7)

    if start > end:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")

    # Conta total para paginacao.
    count_stmt = (
        select(func.count(ObservationRecord.observation_id))
        .where(ObservationRecord.facts["event_type"].astext == "cognitive_metrics_alert")
        .where(ObservationRecord.facts["metric_date"].astext >= start.isoformat())
        .where(ObservationRecord.facts["metric_date"].astext <= end.isoformat())
    )
    total = (await db.execute(count_stmt)).scalar() or 0

    # Busca alertas paginados ordenados por timestamp DESC.
    stmt = (
        select(ObservationRecord)
        .where(ObservationRecord.facts["event_type"].astext == "cognitive_metrics_alert")
        .where(ObservationRecord.facts["metric_date"].astext >= start.isoformat())
        .where(ObservationRecord.facts["metric_date"].astext <= end.isoformat())
        .order_by(desc(ObservationRecord.timestamp))
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).scalars().all()

    items = []
    for r in rows:
        facts = r.facts if isinstance(r.facts, dict) else {}
        metric_date = facts.get("metric_date", "")
        raw_reasons = facts.get("reasons", [])
        reasons = _dedup_and_sort_reasons(raw_reasons)

        items.append(
            {
                "observation_id": r.observation_id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "metric_date": metric_date,
                "reasons": reasons,
                "facts": _filter_facts(facts),
            }
        )

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
