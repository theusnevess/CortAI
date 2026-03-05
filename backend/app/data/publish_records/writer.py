from __future__ import annotations

from pathlib import Path
from typing import Any

from app.data.publish_records.store_jsonl import append_record, read_all_records
from app.data.schemas.publish_record import validate_publish_record


def write_publish_record(
    record: dict[str, Any],
    *,
    path: Path | None = None,
) -> dict[str, Any]:
    normalized = validate_publish_record(record)
    target_path = path

    existing = read_all_records() if target_path is None else read_all_records(target_path)
    for item in existing:
        if item.get("publish_id") == normalized["publish_id"]:
            # Idempotent replay: do not append duplicates.
            return item

    if target_path is None:
        append_record(normalized)
    else:
        append_record(normalized, target_path)
    return normalized
