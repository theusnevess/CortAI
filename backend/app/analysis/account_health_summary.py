from __future__ import annotations

from typing import Any


def build_account_health_summary(
    *,
    generated_at: str,
    publish_records: list[dict[str, Any]],
    safety_events: list[dict[str, Any]],
    account_health_snapshots: list[dict[str, Any]] | None = None,
    risk_profiles: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    account_health_snapshots = account_health_snapshots or []
    risk_profiles = risk_profiles or []

    account_ids = sorted(
        {
            str(row.get("account_id") or "")
            for row in publish_records + safety_events + account_health_snapshots + risk_profiles
            if str(row.get("account_id") or "")
        }
    )

    latest_publish = _latest_by_account(publish_records, field="published_at")
    latest_health = _latest_row_by_account(account_health_snapshots)
    latest_risk = _latest_row_by_account(risk_profiles)

    accounts = []
    for account_id in account_ids:
        events = [row for row in safety_events if str(row.get("account_id") or "") == account_id]
        health_row = latest_health.get(account_id, {})
        risk_row = latest_risk.get(account_id, {})
        cooldown_active = bool(
            health_row.get("cooldown_active")
            or any(str(row.get("event_type") or "") == "SAFETY/cooldown_started" for row in events)
        )
        pacing_delays_count = sum(
            1 for row in events if str(row.get("event_type") or "") == "SAFETY/pacing_delay"
        )
        recent_risk_events_count = sum(
            1
            for row in events
            if str(row.get("event_type") or "") in {"SAFETY/risk_detected", "SAFETY/publish_blocked"}
        )
        risk_level = str(
            health_row.get("risk_level")
            or risk_row.get("risk_level")
            or _derive_risk_level(events)
        )
        accounts.append(
            {
                "account_id": account_id,
                "risk_level": risk_level,
                "cooldown_active": cooldown_active,
                "last_publish_at": latest_publish.get(account_id),
                "pacing_delays_count": pacing_delays_count,
                "recent_risk_events_count": recent_risk_events_count,
                "health_status": _health_status(
                    risk_level=risk_level,
                    cooldown_active=cooldown_active,
                    recent_risk_events_count=recent_risk_events_count,
                ),
            }
        )

    return {"generated_at": generated_at, "accounts": accounts}


def _latest_by_account(rows: list[dict[str, Any]], *, field: str) -> dict[str, str | None]:
    latest: dict[str, str | None] = {}
    for row in sorted(rows, key=lambda item: str(item.get(field) or item.get("created_at") or "")):
        account_id = str(row.get("account_id") or "")
        if account_id:
            latest[account_id] = str(row.get(field) or row.get("created_at") or "") or None
    return latest


def _latest_row_by_account(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in sorted(rows, key=lambda item: str(item.get("generated_at") or item.get("snapshot_id") or item.get("profile_id") or "")):
        account_id = str(row.get("account_id") or "")
        if account_id:
            latest[account_id] = row
    return latest


def _derive_risk_level(events: list[dict[str, Any]]) -> str:
    if any(str(row.get("event_type") or "") == "SAFETY/publish_blocked" for row in events):
        return "HIGH"
    if any(str(row.get("event_type") or "") == "SAFETY/risk_detected" for row in events):
        return "MEDIUM"
    return "LOW"


def _health_status(*, risk_level: str, cooldown_active: bool, recent_risk_events_count: int) -> str:
    if cooldown_active:
        return "COOLDOWN"
    if risk_level == "HIGH":
        return "AT_RISK"
    if risk_level == "MEDIUM" or recent_risk_events_count > 0:
        return "CAUTION"
    return "HEALTHY"
