from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from app.safety.models import AccountMode, AccountSafetyState


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _to_iso(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def start_cooldown(
    state: AccountSafetyState,
    *,
    duration_h: int,
    reason_code: str,
    now: datetime,
) -> AccountSafetyState:
    _ = reason_code
    return replace(
        state,
        mode=AccountMode.COOLDOWN,
        cooldown_until=_to_iso(now + timedelta(hours=duration_h)),
        updated_at=_to_iso(now),
    )


def clear_expired_cooldown(state: AccountSafetyState, *, now: datetime) -> AccountSafetyState:
    expires_at = _parse_iso(state.cooldown_until)
    if expires_at is None or expires_at > now:
        return state
    return replace(
        state,
        mode=AccountMode.NORMAL,
        cooldown_until=None,
        updated_at=_to_iso(now),
    )


def is_cooldown_active(state: AccountSafetyState, *, now: datetime) -> bool:
    expires_at = _parse_iso(state.cooldown_until)
    return expires_at is not None and expires_at > now and state.mode == AccountMode.COOLDOWN
