from __future__ import annotations

from hashlib import sha256

from app.attribution.models import DurationAnalysis, PatternPerformance


def classify_duration_bucket(duration_s: int) -> str:
    if duration_s <= 30:
        return "SHORT"
    if duration_s <= 60:
        return "MEDIUM"
    return "LONG"


def infer_pattern_key(*, hook_key: str, structure_key: str, title: str) -> str:
    normalized_title = title.strip().lower()
    if hook_key[:1].isdigit() or normalized_title[:1].isdigit():
        return "FACT_LIST"
    if "ANGLE" in structure_key and any(token in hook_key.lower() for token in ("por que", "o que", "como")):
        return "CURIOSITY_ARC"
    if "PAYOFF" in structure_key:
        return "STORY_BREAKDOWN"
    return "GENERAL"


def build_duration_analysis(
    *,
    account_id: str,
    publish_id: str,
    creative_pack_id: str,
    duration_s: int,
    completion_rate: float,
    generated_at: str,
) -> DurationAnalysis:
    key = f"{account_id}|{publish_id}|{duration_s}"
    record_id = f"dur_{sha256(key.encode('utf-8')).hexdigest()[:16]}"
    dropoff = round(max(duration_s * (1.0 - completion_rate), 0.0), 2)
    return DurationAnalysis(
        duration_analysis_id=record_id,
        account_id=account_id,
        publish_id=publish_id,
        creative_pack_id=creative_pack_id,
        duration_s=duration_s,
        duration_bucket=classify_duration_bucket(duration_s),
        completion_rate=completion_rate,
        dropoff_point=dropoff,
        generated_at=generated_at,
    )


def build_pattern_performance(
    *,
    account_id: str,
    publish_id: str,
    creative_pack_id: str,
    pattern_key: str,
    views: int,
    completion_rate: float,
    experiment_variant: str | None,
    generated_at: str,
) -> PatternPerformance:
    key = f"{account_id}|{publish_id}|{pattern_key}"
    record_id = f"pat_{sha256(key.encode('utf-8')).hexdigest()[:16]}"
    return PatternPerformance(
        pattern_performance_id=record_id,
        account_id=account_id,
        publish_id=publish_id,
        creative_pack_id=creative_pack_id,
        pattern_key=pattern_key,
        views=views,
        completion_rate=completion_rate,
        experiment_variant=experiment_variant,
        generated_at=generated_at,
    )
