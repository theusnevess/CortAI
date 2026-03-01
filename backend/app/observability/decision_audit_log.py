from __future__ import annotations

import inspect
import os
from datetime import datetime, timezone
from typing import Any

from app.db.models import DecisionAuditLog

_BLOCKLIST_KEYS = ("source_ref", "job_id", "minio", "tmp", "key=", "/tmp", "/storage/")


def decision_audit_enabled() -> bool:
    return str(os.getenv("DECISION_AUDIT_LOG") or "0").strip() == "1"


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _is_blocked_key(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in _BLOCKLIST_KEYS)


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


async def append_decision_audit(
    session: Any,
    *,
    source: str,
    request_id: str | None,
    policy: dict[str, Any],
    operational_decision: dict[str, Any] | None,
    as_of: str | None,
) -> None:
    """
    Append-only best-effort: nunca quebra o overview.
    """
    try:
        payload = sanitize_decision_payload(
            {
                "as_of": as_of,
                "policy": policy,
                "operational_decision": operational_decision,
            }
        )
        row = DecisionAuditLog(
            ts=datetime.now(timezone.utc),
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
