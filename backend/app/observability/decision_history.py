from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DecisionAuditLog

BLOCKLIST_TOKENS = (
    "source_ref",
    "minio",
    "job_id",
    "key=",
    "path",
    "token",
    "secret",
)

SCALAR_TYPES = (str, int, float, bool)


def _is_safe_scalar(value: Any) -> bool:
    return value is None or isinstance(value, SCALAR_TYPES)


def _looks_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in BLOCKLIST_TOKENS)


def sanitize_signals(signals: Any) -> dict[str, Any]:
    if not isinstance(signals, dict):
        return {}
    out: dict[str, Any] = {}
    for key, value in signals.items():
        if not isinstance(key, str):
            continue
        if _looks_sensitive_key(key):
            continue
        if _is_safe_scalar(value):
            out[key] = value
            continue
        if isinstance(value, list) and all(_is_safe_scalar(item) for item in value):
            out[key] = value
    return out


def sanitize_policy(policy: Any) -> dict[str, Any]:
    if not isinstance(policy, dict):
        return {}

    safe: dict[str, Any] = {}
    for key in ("version", "score", "state", "decision"):
        value = policy.get(key)
        if _is_safe_scalar(value):
            safe[key] = value
    safe["signals"] = sanitize_signals(policy.get("signals"))
    return safe


def sanitize_projection(operational_decision: Any) -> dict[str, Any]:
    if not isinstance(operational_decision, dict):
        return {}

    state = operational_decision.get("state")
    decision = operational_decision.get("decision")
    if not isinstance(state, str) and not isinstance(decision, str):
        return {}

    return {
        "status_public": {
            "state": state if isinstance(state, str) else None,
            "action": decision if isinstance(decision, str) else None,
        }
    }


def _to_utc_z(ts: datetime) -> str:
    if ts.tzinfo is None:
        return ts.replace(microsecond=0).isoformat() + "Z"
    return ts.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def to_item(*, decision_id: str, ts: datetime, payload: Any) -> dict[str, Any]:
    payload_dict = payload if isinstance(payload, dict) else {}
    return {
        "decision_id": decision_id,
        "ts": _to_utc_z(ts),
        "policy": sanitize_policy(payload_dict.get("policy")),
        "projection": sanitize_projection(payload_dict.get("operational_decision")),
    }


def parse_since_ts(since_ts: str | None) -> datetime | None:
    if not since_ts:
        return None
    try:
        return datetime.fromisoformat(since_ts.strip().replace("Z", ""))
    except Exception:
        return None


def clamp_limit(limit: int | None, default: int = 50, max_value: int = 200) -> int:
    if limit is None:
        return default
    try:
        n = int(limit)
    except Exception:
        return default
    if n <= 0:
        return default
    return min(n, max_value)


async def list_decision_history(
    db: AsyncSession,
    *,
    limit: int = 50,
    since_ts: str | None = None,
    state: str | None = None,
) -> list[dict[str, Any]]:
    lim = clamp_limit(limit)
    since_dt = parse_since_ts(since_ts)

    stmt = select(
        DecisionAuditLog.id,
        DecisionAuditLog.ts,
        DecisionAuditLog.payload,
    )

    if since_dt is not None:
        stmt = stmt.where(DecisionAuditLog.ts >= since_dt)
    if state:
        stmt = stmt.where(DecisionAuditLog.policy_state == state)

    stmt = stmt.order_by(desc(DecisionAuditLog.ts), desc(DecisionAuditLog.id)).limit(lim)
    rows = (await db.execute(stmt)).all()
    return [
        to_item(
            decision_id=str(row.id),
            ts=row.ts,
            payload=row.payload,
        )
        for row in rows
    ]


async def get_decision_history_item(
    db: AsyncSession,
    *,
    decision_id: str,
) -> dict[str, Any] | None:
    stmt = select(
        DecisionAuditLog.id,
        DecisionAuditLog.ts,
        DecisionAuditLog.payload,
    ).where(DecisionAuditLog.id == decision_id)

    row = (await db.execute(stmt)).first()
    if not row:
        return None
    item = to_item(
        decision_id=str(row.id),
        ts=row.ts,
        payload=row.payload,
    )
    return {
        "version": "v1",
        "decision_id": item["decision_id"],
        "ts": item["ts"],
        "policy": item["policy"],
    }
