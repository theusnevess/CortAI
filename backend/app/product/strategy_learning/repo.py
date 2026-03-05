from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.product.strategy_learning.errors import StrategyPatchConflictError
from app.product.strategy_learning.schema import validate_strategy_patch
from app.product.strategy_learning.store_jsonl import append_patch, read_all_patches


def _canonical_payload(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def get_by_key(
    account_id: str,
    window_id: str,
    policy_stage: str,
    *,
    path: Path | None = None,
) -> dict[str, Any] | None:
    rows = read_all_patches() if path is None else read_all_patches(path)
    found: dict[str, Any] | None = None
    for row in rows:
        if (
            row.get("account_id") == account_id
            and row.get("window_id") == window_id
            and row.get("policy_stage") == policy_stage
            and row.get("patch_kind") == "STRATEGY_V1"
        ):
            found = row
    return found


def save_if_absent(
    patch: dict[str, Any],
    *,
    path: Path | None = None,
) -> str:
    normalized = validate_strategy_patch(patch)
    existing = get_by_key(
        normalized["account_id"],
        normalized["window_id"],
        normalized["policy_stage"],
        path=path,
    )
    if existing is None:
        if path is None:
            append_patch(normalized)
        else:
            append_patch(normalized, path)
        return "WRITTEN"
    if _canonical_payload(existing) == _canonical_payload(normalized):
        return "NOOP"
    raise StrategyPatchConflictError()

