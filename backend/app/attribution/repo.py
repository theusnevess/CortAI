from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.attribution.store_jsonl import append_record, read_all_records


class AttributionConflictError(ValueError):
    pass


def _canonical_payload(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def get_by_key(key_field: str, key_value: str, *, path: Path) -> dict[str, Any] | None:
    found: dict[str, Any] | None = None
    for row in read_all_records(path):
        if row.get(key_field) == key_value:
            found = row
    return found


def save_if_absent(record: dict[str, Any], *, key_field: str, path: Path) -> str:
    existing = get_by_key(key_field, str(record[key_field]), path=path)
    if existing is None:
        append_record(record, path)
        return "WRITTEN"
    if _canonical_payload(existing) == _canonical_payload(record):
        return "NOOP"
    raise AttributionConflictError(f"ADVANCED_ATTRIBUTION_CONFLICT:{key_field}")
