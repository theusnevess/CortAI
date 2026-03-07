from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from app.intelligence.models import PublishWindowRecommendation


def _parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def analyze_publish_windows(
    *,
    account_id: str,
    publish_records: list[dict[str, Any]],
    video_metrics: list[dict[str, Any]],
    generated_at: str,
) -> PublishWindowRecommendation:
    metrics_by_video = {
        str(row.get("external_video_id") or row.get("video_id") or ""): row
        for row in video_metrics
        if row.get("external_video_id") or row.get("video_id")
    }
    hourly: dict[int, dict[str, float]] = defaultdict(lambda: {"count": 0.0, "views": 0.0, "completion": 0.0})

    for row in publish_records:
        ts = _parse_ts(str(row.get("published_at") or row.get("created_at") or ""))
        if ts is None:
            continue
        hour = ts.hour
        hourly[hour]["count"] += 1.0
        metric = metrics_by_video.get(str(row.get("video_id") or ""))
        if isinstance(metric, dict):
            hourly[hour]["views"] += float(metric.get("views") or 0.0)
            hourly[hour]["completion"] += float(metric.get("completion_rate") or 0.0)

    ranked = sorted(
        hourly.items(),
        key=lambda item: (
            (item[1]["views"] / item[1]["count"]) if item[1]["count"] else 0.0,
            (item[1]["completion"] / item[1]["count"]) if item[1]["count"] else 0.0,
            item[1]["count"],
            -item[0],
        ),
        reverse=True,
    )
    best_hours = [f"{hour:02d}:00" for hour, _ in ranked[:3]]
    if not best_hours:
        best_hours = ["12:00", "18:00"]

    signature = f"{account_id}|{'|'.join(best_hours)}"
    rec_id = f"pwr_{sha256(signature.encode('utf-8')).hexdigest()[:16]}"
    return PublishWindowRecommendation(
        recommendation_id=rec_id,
        account_id=account_id,
        generated_at=generated_at,
        best_publish_windows=best_hours,
        source_publish_count=len(publish_records),
        source_metric_count=len(video_metrics),
    )
