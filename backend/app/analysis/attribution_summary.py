from __future__ import annotations

from typing import Any


def build_hook_performance_summary(
    *,
    generated_at: str,
    hook_performance: list[dict[str, Any]],
    creative_packs: list[dict[str, Any]] | None = None,
    video_metrics: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    creative_packs = creative_packs or []
    video_metrics = video_metrics or []
    hook_groups: dict[tuple[str | None, str | None], dict[str, Any]] = {}

    metrics_by_publish = {
        str(row.get("publish_id") or ""): row
        for row in video_metrics
        if str(row.get("publish_id") or "")
    }
    hook_type_by_pack = {
        str(row.get("creative_pack_id") or ""): _infer_hook_type(row)
        for row in creative_packs
        if str(row.get("creative_pack_id") or "")
    }

    for row in hook_performance:
        hook_id = _normalize_optional(row.get("hook_id") or row.get("hook_key"))
        creative_pack_id = str(row.get("creative_pack_id") or "")
        hook_type = _normalize_optional(row.get("hook_type") or hook_type_by_pack.get(creative_pack_id))
        publish_id = str(row.get("publish_id") or "")
        metric = metrics_by_publish.get(publish_id, {})
        completion_rate = float(
            row.get("avg_completion_rate")
            or row.get("completion_rate")
            or metric.get("completion_rate")
            or 0.0
        )
        watch_time = float(
            row.get("avg_watch_time")
            or row.get("watch_time")
            or metric.get("avg_watch_time")
            or 0.0
        )
        key = (hook_id, hook_type)
        bucket = hook_groups.setdefault(
            key,
            {
                "hook_id": hook_id,
                "hook_type": hook_type,
                "video_count": 0,
                "completion_total": 0.0,
                "watch_time_total": 0.0,
            },
        )
        bucket["video_count"] += 1
        bucket["completion_total"] += completion_rate
        bucket["watch_time_total"] += watch_time

    ranked = []
    for item in hook_groups.values():
        count = item["video_count"]
        ranked.append(
            {
                "hook_id": item["hook_id"],
                "hook_type": item["hook_type"],
                "video_count": count,
                "avg_completion_rate": round(item["completion_total"] / count, 6) if count else None,
                "avg_watch_time": round(item["watch_time_total"] / count, 6) if count else None,
            }
        )

    ranked.sort(
        key=lambda item: (
            -(item["avg_completion_rate"] or 0.0),
            -(item["avg_watch_time"] or 0.0),
            str(item["hook_type"] or ""),
            str(item["hook_id"] or ""),
        )
    )
    for index, item in enumerate(ranked, start=1):
        item["performance_rank"] = index

    return {"generated_at": generated_at, "hooks": ranked}


def _infer_hook_type(creative_pack: dict[str, Any]) -> str | None:
    hooks = creative_pack.get("hook_candidates")
    if not isinstance(hooks, list) or not hooks:
        return None
    hook = str(hooks[0]).strip().lower()
    if "?" in hook:
        return "QUESTION"
    if any(token in hook for token in ("why", "secret", "what happened", "you won't")):
        return "CURIOSITY"
    return "STATEMENT"


def _normalize_optional(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None
