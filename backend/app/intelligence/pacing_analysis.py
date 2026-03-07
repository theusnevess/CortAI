from __future__ import annotations

from collections import Counter
from hashlib import sha256
from typing import Any

from app.intelligence.models import AccountHealthSnapshot, PacingRecommendation, RiskProfile


def analyze_risk_profile(
    *,
    account_id: str,
    safety_events: list[dict[str, Any]],
    generated_at: str,
) -> RiskProfile:
    counts = Counter()
    latest_ts: str | None = None
    risk_level = "LOW"
    reason_codes: list[str] = []

    for row in safety_events:
        event_type = str(row.get("event_type") or "")
        counts[event_type] += 1
        ts = str(row.get("ts") or row.get("timestamp") or "")
        if ts:
            latest_ts = max(latest_ts or ts, ts)
        if event_type == "SAFETY/cooldown_started":
            risk_level = "HIGH"
            reason_codes.append("COOLDOWN_SIGNAL")
        elif event_type == "SAFETY/risk_detected" and risk_level != "HIGH":
            risk_level = "MEDIUM"
            reason_codes.append("RISK_SIGNAL")
        elif event_type == "SAFETY/pacing_delay" and risk_level == "LOW":
            risk_level = "MEDIUM"
            reason_codes.append("PACING_PRESSURE")

    profile_signature = f"{account_id}|{risk_level}|{latest_ts or 'none'}"
    profile_id = f"risk_{sha256(profile_signature.encode('utf-8')).hexdigest()[:16]}"
    return RiskProfile(
        profile_id=profile_id,
        account_id=account_id,
        generated_at=generated_at,
        risk_level=risk_level,
        signal_counts=dict(counts),
        latest_risk_ts=latest_ts,
        reason_codes=reason_codes,
    )


def analyze_pacing(
    *,
    account_id: str,
    publish_records: list[dict[str, Any]],
    safety_events: list[dict[str, Any]],
    generated_at: str,
) -> PacingRecommendation:
    min_interval = 90
    max_posts_day = 6
    max_posts_hour = 2
    reason_codes: list[str] = []

    if any(str(row.get("event_type") or "") == "SAFETY/pacing_delay" for row in safety_events):
        min_interval = 120
        max_posts_day = 5
        max_posts_hour = 1
        reason_codes.append("PACING_DELAY_SEEN")
    if any(str(row.get("event_type") or "") == "SAFETY/cooldown_started" for row in safety_events):
        min_interval = 180
        max_posts_day = 3
        max_posts_hour = 1
        reason_codes.append("COOLDOWN_SEEN")
    if len(publish_records) >= 10 and not reason_codes:
        reason_codes.append("STABLE_HISTORY")

    recommendation_id = f"pace_{sha256(f'{account_id}|{min_interval}|{max_posts_day}|{max_posts_hour}'.encode('utf-8')).hexdigest()[:16]}"
    return PacingRecommendation(
        recommendation_id=recommendation_id,
        account_id=account_id,
        generated_at=generated_at,
        recommended_min_interval_minutes=min_interval,
        recommended_max_posts_per_day=max_posts_day,
        recommended_max_posts_per_hour=max_posts_hour,
        reason_codes=reason_codes,
    )


def analyze_account_health(
    *,
    account_id: str,
    publish_records: list[dict[str, Any]],
    video_metrics: list[dict[str, Any]],
    risk_profile: RiskProfile,
    generated_at: str,
) -> AccountHealthSnapshot:
    avg_views = 0.0
    avg_completion = 0.0
    reason_codes: list[str] = []
    if video_metrics:
        avg_views = sum(float(row.get("views") or 0.0) for row in video_metrics) / len(video_metrics)
        avg_completion = sum(float(row.get("completion_rate") or 0.0) for row in video_metrics) / len(video_metrics)

    if risk_profile.risk_level == "HIGH":
        health = "AT_RISK"
        reason_codes.append("RISK_HIGH")
    elif avg_completion >= 0.45 and avg_views >= 1000:
        health = "HEALTHY"
        reason_codes.append("METRICS_STRONG")
    else:
        health = "WATCH"
        reason_codes.append("METRICS_NEUTRAL")

    snapshot_id = f"health_{sha256(f'{account_id}|{health}|{avg_views:.2f}|{avg_completion:.4f}'.encode('utf-8')).hexdigest()[:16]}"
    return AccountHealthSnapshot(
        snapshot_id=snapshot_id,
        account_id=account_id,
        generated_at=generated_at,
        account_health=health,
        avg_views=avg_views,
        avg_completion_rate=avg_completion,
        publish_count=len(publish_records),
        risk_level=risk_profile.risk_level,
        reason_codes=reason_codes,
    )
