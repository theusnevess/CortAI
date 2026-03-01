from __future__ import annotations

import inspect
import logging
import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select

from app.db.models import DecisionAuditLog

_BLOCKLIST_KEYS = ("source_ref", "job_id", "minio", "tmp", "key=", "/tmp", "/storage/")
DEDUP_WINDOW_SECONDS = 60

logger = logging.getLogger(__name__)


def decision_audit_enabled() -> bool:
    return str(os.getenv("DECISION_AUDIT_LOG") or "0").strip() == "1"


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _is_blocked_key(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in _BLOCKLIST_KEYS)


def _score_bucket(score: Any) -> int:
    try:
        return max(0, int(score) // 5)
    except Exception:
        return 0


def _policy_fingerprint(policy: dict[str, Any]) -> tuple[str, str, int]:
    return (
        str(policy.get("state") or ""),
        str(policy.get("decision") or ""),
        _score_bucket(policy.get("score")),
    )


def _normalize_dt(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _scrub_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _scrub_value(inner)
            for key, inner in value.items()
            if isinstance(key, str) and not _is_blocked_key(key)
        }
    if isinstance(value, list):
        return [_scrub_value(item) for item in value]
    if isinstance(value, str):
        if any(token in value.lower() for token in _BLOCKLIST_KEYS):
            return "[redacted]"
    return value


def sanitize_decision_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitiza o snapshot antes de persistir:
    - remove chaves proibidas
    - remove strings com tokens proibidos
    - garante signals apenas com escalares ou lista de escalares
    """
    out = _scrub_value(payload)
    policy = out.get("policy")
    if isinstance(policy, dict):
        signals = policy.get("signals")
        if isinstance(signals, dict):
            sanitized_signals: dict[str, Any] = {}
            for key, value in signals.items():
                if not isinstance(key, str) or _is_blocked_key(key):
                    continue
                if _is_scalar(value):
                    sanitized_signals[key] = value
                elif isinstance(value, list) and all(_is_scalar(item) for item in value):
                    sanitized_signals[key] = value
                else:
                    sanitized_signals[key] = "[redacted]"
            policy["signals"] = sanitized_signals
    return out


async def _maybe_await(result: Any) -> Any:
    if inspect.isawaitable(result):
        return await result
    return result


async def _load_latest_audit_signature(session: Any) -> tuple[datetime, str, str, int] | None:
    stmt = (
        select(
            DecisionAuditLog.ts,
            DecisionAuditLog.policy_state,
            DecisionAuditLog.policy_decision,
            DecisionAuditLog.policy_score,
        )
        .order_by(desc(DecisionAuditLog.ts), desc(DecisionAuditLog.id))
        .limit(1)
    )
    row = (await _maybe_await(session.execute(stmt))).first()
    if not row:
        return None
    return (
        _normalize_dt(row.ts),
        str(row.policy_state or ""),
        str(row.policy_decision or ""),
        _score_bucket(row.policy_score),
    )


async def _should_skip_duplicate(
    session: Any,
    *,
    policy: dict[str, Any],
    now: datetime,
) -> bool:
    try:
        latest = await _load_latest_audit_signature(session)
    except Exception:
        return False
    if latest is None:
        return False

    latest_ts, latest_state, latest_decision, latest_bucket = latest
    current_fp = _policy_fingerprint(policy)
    latest_fp = (latest_state, latest_decision, latest_bucket)
    age_seconds = (_normalize_dt(now) - latest_ts).total_seconds()
    return current_fp == latest_fp and age_seconds <= DEDUP_WINDOW_SECONDS


async def append_decision_audit(
    session: Any,
    *,
    source: str,
    request_id: str | None,
    policy: dict[str, Any],
    operational_decision: dict[str, Any] | None,
    as_of: str | None,
    now: datetime | None = None,
) -> None:
    """
    Append-only best-effort: nunca quebra o overview.
    """
    try:
        now_utc = _normalize_dt(now or datetime.now(timezone.utc))
        if await _should_skip_duplicate(session, policy=policy, now=now_utc):
            logger.info(
                "decision_audit_skipped",
                extra={
                    "decision_audit_skipped": True,
                    "reason": "dedup_window",
                    "state": str(policy.get("state") or ""),
                    "decision": str(policy.get("decision") or ""),
                    "score_bucket": _score_bucket(policy.get("score")),
                },
            )
            return
        payload = sanitize_decision_payload(
            {
                "as_of": as_of,
                "policy": policy,
                "operational_decision": operational_decision,
            }
        )
        row = DecisionAuditLog(
            ts=now_utc,
            source=source,
            request_id=request_id,
            policy_version=str(policy.get("version") or ""),
            policy_state=str(policy.get("state") or ""),
            policy_score=int(policy.get("score") or 0),
            policy_decision=str(policy.get("decision") or ""),
            decision_state=(operational_decision or {}).get("state"),
            decision_action=(operational_decision or {}).get("action"),
            payload=payload,
        )
        session.add(row)
        await _maybe_await(session.commit())
    except Exception:
        try:
            await _maybe_await(session.rollback())
        except Exception:
            pass


async def maybe_append_decision_audit(
    session: Any,
    *,
    source: str,
    request_id: str | None,
    response: dict[str, Any],
) -> bool:
    if not decision_audit_enabled():
        return False
    policy = response.get("policy")
    if not isinstance(policy, dict):
        return False
    await append_decision_audit(
        session,
        source=source,
        request_id=request_id,
        policy=policy,
        operational_decision=response.get("operational_decision"),
        as_of=response.get("as_of"),
    )
    return True
