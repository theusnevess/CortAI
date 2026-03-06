from __future__ import annotations

from pathlib import Path
from typing import Any

from app.data.video_metrics.store_jsonl import read_all_records


def get_by_provider_key(
    provider: str,
    external_video_id: str,
    captured_window_id: str,
    *,
    path: Path | None = None,
) -> dict[str, Any] | None:
    records = read_all_records() if path is None else read_all_records(path)
    matches = [
        item
        for item in records
        if item.get("provider") == provider
        and item.get("external_video_id") == external_video_id
        and item.get("captured_window_id") == captured_window_id
    ]
    if not matches:
        return None
    return matches[-1]
