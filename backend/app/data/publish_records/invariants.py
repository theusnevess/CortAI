from __future__ import annotations

from pathlib import Path
from typing import Any

from app.data.publish_records.store_jsonl import read_all_records


class PublishRecordInvariantError(ValueError):
    """Invariant violation for publish_records contract."""


def enforce_no_ambiguous_active_mapping(records: list[dict[str, Any]]) -> None:
    active_keys: dict[tuple[str, str, str], str] = {}
    for item in records:
        if item.get("status") != "posted":
            continue
        key = (
            str(item.get("job_id", "")),
            str(item.get("account_id", "")),
            str(item.get("platform", "")),
        )
        current_publish_id = str(item.get("publish_id", ""))
        if key in active_keys and active_keys[key] != current_publish_id:
            raise PublishRecordInvariantError("ContractViolation: ambiguous_publish_mapping")
        active_keys[key] = current_publish_id


def assert_file_invariants(path: Path) -> None:
    records = read_all_records(path)
    enforce_no_ambiguous_active_mapping(records)
