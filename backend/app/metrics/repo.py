from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.metrics.store_jsonl import append_record, read_all_records


class MetricsConflictError(ValueError):
    pass


def _canonical_payload(record: dict[str, Any]) -> str:
    normalized = dict(record)
    normalized.pop("collected_at", None)
    normalized.pop("age_hours", None)
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def get_by_bucket(publish_id: str, collected_at_bucket: str, *, path: Path | None = None) -> dict[str, Any] | None:
    rows = read_all_records() if path is None else read_all_records(path)
    found: dict[str, Any] | None = None
    for row in rows:
        if row.get("publish_id") == publish_id and row.get("collected_at_bucket") == collected_at_bucket:
            found = row
    return found


def save_if_absent(record: dict[str, Any], *, path: Path | None = None) -> str:
    existing = get_by_bucket(str(record["publish_id"]), str(record["collected_at_bucket"]), path=path)
    if existing is None:
        if path is None:
            append_record(record)
        else:
            append_record(record, path)
        return "WRITTEN"
    if _canonical_payload(existing) == _canonical_payload(record):
        return "NOOP"
    raise MetricsConflictError("VIDEO_METRICS_COLLECTOR_CONFLICT")
