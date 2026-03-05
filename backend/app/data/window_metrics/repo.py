from __future__ import annotations

from pathlib import Path
from typing import Any

from app.data.schemas.window_metrics import validate_window_metrics
from app.data.window_metrics.invariants import WindowMetricsInvariantError, decide_idempotency_action
from app.data.window_metrics.store_jsonl import append_record, read_all_records


def get_by_key(
    account_id: str,
    window_id: str,
    *,
    path: Path | None = None,
) -> dict[str, Any] | None:
    records = read_all_records() if path is None else read_all_records(path)
    found: dict[str, Any] | None = None
    for item in records:
        if item.get("account_id") == account_id and item.get("window_id") == window_id:
            found = item
    return found


def save_window_metrics(
    record: dict[str, Any],
    *,
    path: Path | None = None,
) -> str:
    normalized = validate_window_metrics(record)
    existing = get_by_key(normalized["account_id"], normalized["window_id"], path=path)
    action = decide_idempotency_action(existing=existing, candidate=normalized)
    if action == "NOOP":
        return "NOOP"
    if action != "WRITE":
        raise WindowMetricsInvariantError("ContractViolation: invalid idempotency action")
    if path is None:
        append_record(normalized)
    else:
        append_record(normalized, path)
    return "WRITTEN"

