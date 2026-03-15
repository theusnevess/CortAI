from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from app.safety.events import emit_safety_event
from app.safety.models import AccountMode, AccountSafetyState, RiskLevel, RiskSignal, SafetyDecision
from app.safety.safety_gate import evaluate_publish_safety
from app.safety.store_jsonl import (
    DEFAULT_ACCOUNT_STATE_PATH,
    DEFAULT_COOLDOWNS_PATH,
    DEFAULT_PACING_EVENTS_PATH,
    append_account_state,
    append_cooldown_event,
    append_pacing_event,
    reconstruct_latest_state,
)


def _to_iso(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


class SafetyService:
    """Persistência e emissão operacional do safety layer."""

    def __init__(
        self,
        *,
        safety_dir: Path = Path("OUT/safety"),
        event_path: Path = Path("OUT/events/events.jsonl"),
    ) -> None:
        self.safety_dir = safety_dir
        self.event_path = event_path
        self.account_state_path = safety_dir / DEFAULT_ACCOUNT_STATE_PATH.name
        self.cooldowns_path = safety_dir / DEFAULT_COOLDOWNS_PATH.name
        self.pacing_events_path = safety_dir / DEFAULT_PACING_EVENTS_PATH.name

    def get_state(self, account_id: str, *, now: datetime | None = None) -> AccountSafetyState:
        current = reconstruct_latest_state(account_id, path=self.account_state_path)
        if current is not None:
            return AccountSafetyState(
                account_id=str(current["account_id"]),
                mode=AccountMode(str(current["mode"])),
                cooldown_until=current.get("cooldown_until"),
                last_publish_at=current.get("last_publish_at"),
                posts_last_hour=int(current.get("posts_last_hour") or 0),
                posts_last_day=int(current.get("posts_last_day") or 0),
                risk_level=RiskLevel(str(current.get("risk_level") or "LOW")),
                updated_at=str(current.get("updated_at") or _to_iso(now or datetime.now(timezone.utc))),
            )
        ts = _to_iso(now or datetime.now(timezone.utc))
        return AccountSafetyState(
            account_id=account_id,
            mode=AccountMode.NORMAL,
            cooldown_until=None,
            last_publish_at=None,
            posts_last_hour=0,
            posts_last_day=0,
            risk_level=RiskLevel.LOW,
            updated_at=ts,
        )

    def evaluate_before_publish(
        self,
        *,
        account_id: str,
        now: datetime,
        recent_signals: list[RiskSignal] | None = None,
    ) -> tuple[AccountSafetyState, SafetyDecision]:
        state = self.get_state(account_id, now=now)
        updated_state, decision, events = evaluate_publish_safety(
            account_id=account_id,
            now=now,
            state=state,
            recent_signals=recent_signals,
        )
        append_account_state(updated_state, path=self.account_state_path)
        self._persist_events(events)
        return updated_state, decision

    def record_publish_success(self, *, account_id: str, published_at: datetime) -> AccountSafetyState:
        current = self.get_state(account_id, now=published_at)
        updated = replace(
            current,
            mode=AccountMode.NORMAL if current.mode != AccountMode.COOLDOWN else current.mode,
            last_publish_at=_to_iso(published_at),
            posts_last_hour=current.posts_last_hour + 1,
            posts_last_day=current.posts_last_day + 1,
            updated_at=_to_iso(published_at),
        )
        append_account_state(updated, path=self.account_state_path)
        return updated

    def record_provider_signal(
        self,
        *,
        account_id: str,
        risk_type: str,
        severity: str,
        ts: datetime,
        details: dict | None = None,
    ) -> AccountSafetyState:
        signal = RiskSignal(
            account_id=account_id,
            risk_type=risk_type,
            severity=severity,
            ts=_to_iso(ts),
            details=details,
        )
        updated_state, _ = self.evaluate_before_publish(
            account_id=account_id,
            now=ts,
            recent_signals=[signal],
        )
        return updated_state

    def _persist_events(self, events: list[dict[str, object]]) -> None:
        for event in events:
            emit_safety_event(
                str(event["event_type"]),
                {
                    "account_id": event.get("account_id"),
                    "severity": event.get("severity"),
                    "ts": event.get("ts"),
                    **dict(event.get("details") or {}),
                },
                event_path=self.event_path,
            )
            event_type = str(event["event_type"])
            if event_type == "SAFETY/cooldown_started":
                append_cooldown_event(event, path=self.cooldowns_path)
            if event_type == "SAFETY/pacing_delay":
                append_pacing_event(event, path=self.pacing_events_path)
