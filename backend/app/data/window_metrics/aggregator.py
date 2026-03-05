from __future__ import annotations

from pathlib import Path
from typing import Any

from app.data.video_metrics.repo import get_best


def _avg(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def aggregate_window_metrics(
    *,
    account_id: str,
    window_id: str,
    video_ids: list[str],
    computed_at: str,
    video_metrics_path: Path | None = None,
) -> dict[str, Any]:
    """Agrega métricas de uma janela de forma determinística."""
    metrics_rows: list[dict[str, Any]] = []
    for video_id in video_ids:
        row = get_best(account_id, video_id, window_id, path=video_metrics_path)
        if row is not None:
            metrics_rows.append(row)

    views_values = [float(item["views"]) for item in metrics_rows if item.get("views") is not None]
    retention_values = [float(item["retention_3s"]) for item in metrics_rows if item.get("retention_3s") is not None]
    completion_values = [
        float(item["completion_rate"]) for item in metrics_rows if item.get("completion_rate") is not None
    ]
    rpm_values = [float(item["rpm"]) for item in metrics_rows if item.get("rpm") is not None]
    follows_values = [int(item["follows"]) for item in metrics_rows if item.get("follows") is not None]

    avg_views = _avg(views_values)
    total_follows = sum(follows_values) if follows_values else None

    return {
        "window_id": window_id,
        "account_id": account_id,
        "videos_considered": len(video_ids),
        "avg_views": avg_views if avg_views is not None else 0.0,
        "avg_retention_3s": _avg(retention_values),
        "avg_completion_rate": _avg(completion_values),
        "avg_rpm": _avg(rpm_values),
        "total_views": int(sum(views_values)),
        "total_follows": total_follows,
        "computed_at": computed_at,
    }
