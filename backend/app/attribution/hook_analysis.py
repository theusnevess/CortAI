from __future__ import annotations

from hashlib import sha256

from app.attribution.models import HookPerformance


def classify_hook_type(hook: str) -> str:
    text = hook.strip().lower()
    if not text:
        return "STATEMENT"
    if "?" in text:
        return "QUESTION"
    if text[:1].isdigit():
        return "LISTICLE"
    if any(token in text for token in ("por que", "o que", "como")):
        return "CURIOSITY"
    return "STATEMENT"


def build_hook_performance(
    *,
    account_id: str,
    publish_id: str,
    creative_pack_id: str,
    hook_key: str,
    views: int,
    completion_rate: float,
    watch_3s_rate: float,
    experiment_variant: str | None,
    generated_at: str,
) -> HookPerformance:
    key = f"{account_id}|{publish_id}|{hook_key}"
    record_id = f"hook_{sha256(key.encode('utf-8')).hexdigest()[:16]}"
    return HookPerformance(
        hook_performance_id=record_id,
        account_id=account_id,
        publish_id=publish_id,
        creative_pack_id=creative_pack_id,
        hook_key=hook_key,
        hook_type=classify_hook_type(hook_key),
        views=views,
        completion_rate=completion_rate,
        watch_3s_rate=watch_3s_rate,
        experiment_variant=experiment_variant,
        generated_at=generated_at,
    )
