from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta

from app.safety.cooldown import clear_expired_cooldown, is_cooldown_active, start_cooldown
from app.safety.models import AccountMode, AccountSafetyState, RiskSignal, SafetyDecision, SafetyDecisionType
from app.safety.pacing import PacingConfig, evaluate_pacing
from app.safety.risk_detector import detect_risk


def evaluate_publish_safety(
    *,
    account_id: str,
    now: datetime,
    state: AccountSafetyState,
    recent_signals: list[RiskSignal] | None = None,
    pacing_config: PacingConfig | None = None,
) -> tuple[AccountSafetyState, SafetyDecision, list[dict[str, object]]]:
    _ = account_id
    current = clear_expired_cooldown(state, now=now)
    emitted_events: list[dict[str, object]] = []

    for signal in recent_signals or []:
        current, events = detect_risk(signal, current)
        emitted_events.extend(events)

    if is_cooldown_active(current, now=now):
        decision = SafetyDecision(
            decision=SafetyDecisionType.BLOCK,
            reason_code="COOLDOWN_ACTIVE",
            next_allowed_time=current.cooldown_until,
            cooldown_applied=current.cooldown_until,
        )
        emitted_events.append(
            {
                "event_type": "SAFETY/publish_blocked",
                "account_id": current.account_id,
                "severity": "HIGH",
                "ts": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "details": {"reason_code": decision.reason_code},
            }
        )
        return current, decision, emitted_events

    pacing = evaluate_pacing(current, now, config=pacing_config)
    if pacing.decision == SafetyDecisionType.DELAY:
        emitted_events.append(
            {
                "event_type": "SAFETY/pacing_delay",
                "account_id": current.account_id,
                "severity": "WARN",
                "ts": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "details": {"reason_code": pacing.reason_code, "next_allowed_time": pacing.next_allowed_time},
            }
        )
        return current, pacing, emitted_events

    if current.risk_level.value == "HIGH":
        blocked_state = start_cooldown(current, duration_h=6, reason_code="RISK_LEVEL_HIGH", now=now)
        decision = SafetyDecision(
            decision=SafetyDecisionType.BLOCK,
            reason_code="RISK_LEVEL_HIGH",
            next_allowed_time=blocked_state.cooldown_until,
            cooldown_applied=blocked_state.cooldown_until,
        )
        emitted_events.append(
            {
                "event_type": "SAFETY/publish_blocked",
                "account_id": blocked_state.account_id,
                "severity": "HIGH",
                "ts": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "details": {"reason_code": decision.reason_code},
            }
        )
        return blocked_state, decision, emitted_events

    if current.mode == AccountMode.SLOW_MODE:
        jittered_time = now + timedelta(minutes=5)
        decision = SafetyDecision(
            decision=SafetyDecisionType.DELAY,
            reason_code="SLOW_MODE_ACTIVE",
            next_allowed_time=jittered_time.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            cooldown_applied=None,
        )
        emitted_events.append(
            {
                "event_type": "SAFETY/pacing_delay",
                "account_id": current.account_id,
                "severity": "WARN",
                "ts": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "details": {"reason_code": decision.reason_code, "next_allowed_time": decision.next_allowed_time},
            }
        )
        return current, decision, emitted_events

    decision = SafetyDecision(
        decision=SafetyDecisionType.ALLOW,
        reason_code="SAFETY_ALLOW",
        next_allowed_time=None,
        cooldown_applied=None,
    )
    return replace(current), decision, emitted_events
