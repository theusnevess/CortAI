from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from app.safety.cooldown import start_cooldown
from app.safety.models import AccountMode, AccountSafetyState, RiskLevel, RiskSignal

_HIGH_RISK_TYPES = {"PUBLISH_RATE_LIMIT", "ACCOUNT_RESTRICTED", "PUBLISH_REJECTED"}
_MEDIUM_RISK_TYPES = {"PUBLISH_TIMEOUT", "ACCOUNT_WARNING", "PUBLISH_TIMEOUT_REPEATED"}
_LOW_RISK_TYPES = {"LOW_VIEW_SIGNAL"}


def _to_iso(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def detect_risk(
    signal: RiskSignal,
    state: AccountSafetyState,
) -> tuple[AccountSafetyState, list[dict[str, object]]]:
    now = datetime.fromisoformat(signal.ts.replace("Z", "+00:00")).astimezone(timezone.utc)
    events: list[dict[str, object]] = [
        {
            "event_type": "SAFETY/risk_detected",
            "account_id": signal.account_id,
            "risk_type": signal.risk_type,
            "severity": signal.severity,
            "ts": signal.ts,
            "details": signal.details or {},
        }
    ]
    risk_type = signal.risk_type.upper()
    if risk_type in _HIGH_RISK_TYPES:
        updated = start_cooldown(state, duration_h=24, reason_code=risk_type, now=now)
        updated = replace(updated, risk_level=RiskLevel.HIGH, updated_at=_to_iso(now))
        events.append(
            {
                "event_type": "SAFETY/cooldown_started",
                "account_id": signal.account_id,
                "severity": "HIGH",
                "ts": signal.ts,
                "details": {"risk_type": risk_type, "cooldown_until": updated.cooldown_until},
            }
        )
        return updated, events
    if risk_type in _MEDIUM_RISK_TYPES:
        updated = replace(state, mode=AccountMode.SLOW_MODE, risk_level=RiskLevel.MEDIUM, updated_at=_to_iso(now))
        events.append(
            {
                "event_type": "SAFETY/slow_mode_activated",
                "account_id": signal.account_id,
                "severity": "MEDIUM",
                "ts": signal.ts,
                "details": {"risk_type": risk_type},
            }
        )
        return updated, events
    if risk_type in _LOW_RISK_TYPES:
        updated = replace(state, risk_level=RiskLevel.LOW, updated_at=_to_iso(now))
        return updated, events
    return replace(state, updated_at=_to_iso(now)), events
