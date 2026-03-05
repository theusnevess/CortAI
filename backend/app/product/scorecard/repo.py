from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.product.scorecard.schema import validate_scorecard
from app.product.scorecard.store_jsonl import append_record, read_all_records


class ScorecardInvariantError(ValueError):
    """Erro de invariante para idempotência estrutural de scorecard."""


def _canonical_payload(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def get_by_key(
    account_id: str,
    window_id: str,
    *,
    path: Path | None = None,
) -> dict[str, Any] | None:
    rows = read_all_records() if path is None else read_all_records(path)
    found: dict[str, Any] | None = None
    for row in rows:
        if row.get("account_id") == account_id and row.get("window_id") == window_id:
            found = row
    return found


def save_scorecard(
    record: dict[str, Any],
    *,
    path: Path | None = None,
) -> str:
    normalized = validate_scorecard(record)
    existing = get_by_key(normalized["account_id"], normalized["window_id"], path=path)
    if existing is None:
        if path is None:
            append_record(normalized)
        else:
            append_record(normalized, path)
        return "WRITTEN"
    if _canonical_payload(existing) == _canonical_payload(normalized):
        return "NOOP"
    raise ScorecardInvariantError("ContractViolation: conflicting data for same (account_id, window_id)")

