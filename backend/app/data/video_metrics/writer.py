from __future__ import annotations

from pathlib import Path
from typing import Any

from app.data.schemas.video_metrics import validate_video_metrics
from app.data.video_metrics.store_jsonl import append_record


def write_video_metrics(
    record: dict[str, Any],
    *,
    path: Path | None = None,
) -> dict[str, Any]:
    normalized = validate_video_metrics(record)
    if path is None:
        append_record(normalized)
    else:
        append_record(normalized, path)
    return normalized
