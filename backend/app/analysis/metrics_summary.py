from __future__ import annotations

from typing import Any


def build_pilot_metrics_summary(
    *,
    generated_at: str,
    publish_records: list[dict[str, Any]],
    video_metrics: list[dict[str, Any]],
) -> dict[str, Any]:
    account_ids = sorted(
        {
            str(row.get("account_id") or "")
            for row in publish_records
            if str(row.get("account_id") or "")
        }
    )
    valid_metrics = [row for row in video_metrics if row.get("publish_id")]

    total_views = sum(int(row.get("views") or 0) for row in valid_metrics)
    watch_times = [float(row.get("avg_watch_time") or 0.0) for row in valid_metrics]
    completion_rates = [float(row.get("completion_rate") or 0.0) for row in valid_metrics]
    view_3s_rates = [
        float(
            row.get("view_3s_rate")
            or row.get("retention_3s")
            or 0.0
        )
        for row in valid_metrics
    ]

    account_views: dict[str, int] = {}
    for row in valid_metrics:
        account_id = str(row.get("account_id") or "")
        if not account_id:
            continue
        account_views[account_id] = account_views.get(account_id, 0) + int(row.get("views") or 0)

    top_account_id = None
    if account_views:
        top_account_id = sorted(account_views.items(), key=lambda item: (-item[1], item[0]))[0][0]

    return {
        "generated_at": generated_at,
        "total_accounts": len(account_ids),
        "total_videos": len(
            {
                str(row.get("video_id") or row.get("external_video_id") or row.get("publish_id") or "")
                for row in publish_records
                if str(row.get("video_id") or row.get("external_video_id") or row.get("publish_id") or "")
            }
        ),
        "total_views": total_views,
        "avg_watch_time": _avg_or_none(watch_times),
        "avg_completion_rate": _avg_or_none(completion_rates),
        "avg_3s_view_rate": _avg_or_none(view_3s_rates),
        "top_account_id": top_account_id,
    }


def _avg_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)
