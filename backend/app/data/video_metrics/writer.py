from __future__ import annotations

from pathlib import Path
from typing import Any

from app.data.schemas.video_metrics import validate_video_metrics
from app.data.video_metrics.repo import get_by_provider_key
from app.data.video_metrics.store_jsonl import append_record


class VideoMetricsConflictError(ValueError):
    """Conflito para a mesma chave externa de video_metrics."""


def write_video_metrics(
    record: dict[str, Any],
    *,
    path: Path | None = None,
) -> dict[str, Any]:
    normalized = validate_video_metrics(record)
    existing = get_by_provider_key(
        str(normalized.get("provider") or ""),
        str(normalized.get("external_video_id") or ""),
        normalized["captured_window_id"],
        path=path,
    )
    if existing is not None:
        if _semantic_record(existing) == _semantic_record(normalized):
            return existing
        raise VideoMetricsConflictError("VIDEO_METRICS_CONFLICT")

    if path is None:
        append_record(normalized)
    else:
        append_record(normalized, path)
    return normalized


def _semantic_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    normalized.pop("ingested_at", None)
    return normalized
