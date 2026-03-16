from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.safety.models import AccountSafetyState, SafetyDecision, SafetyDecisionType


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class PacingConfig:
    min_interval_between_posts_min: int = 90
    max_posts_per_day: int = 6
    max_posts_per_hour: int = 2


def evaluate_pacing(
    state: AccountSafetyState,
    now: datetime,
    *,
    config: PacingConfig | None = None,
) -> SafetyDecision:
    active = config or PacingConfig()
    if state.posts_last_hour >= active.max_posts_per_hour:
        return SafetyDecision(
            decision=SafetyDecisionType.DELAY,
            reason_code="PACING_MAX_POSTS_PER_HOUR",
            next_allowed_time=_to_iso(now + timedelta(hours=1)),
            cooldown_applied=None,
        )
    if state.posts_last_day >= active.max_posts_per_day:
        return SafetyDecision(
            decision=SafetyDecisionType.DELAY,
            reason_code="PACING_MAX_POSTS_PER_DAY",
            next_allowed_time=_to_iso(now + timedelta(days=1)),
            cooldown_applied=None,
        )
    last_publish = _parse_iso(state.last_publish_at)
    if last_publish is not None:
        next_allowed = last_publish + timedelta(minutes=active.min_interval_between_posts_min)
        if now < next_allowed:
            return SafetyDecision(
                decision=SafetyDecisionType.DELAY,
                reason_code="PACING_MIN_INTERVAL",
                next_allowed_time=_to_iso(next_allowed),
                cooldown_applied=None,
            )
    return SafetyDecision(
        decision=SafetyDecisionType.ALLOW,
        reason_code="PACING_OK",
        next_allowed_time=None,
        cooldown_applied=None,
    )
