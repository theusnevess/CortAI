from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_STRATEGY_PATCH_APPLICATIONS_PATH = Path("OUT/data/strategy_patch_applications.jsonl")


def append_application(
    record: dict[str, Any],
    path: Path = DEFAULT_STRATEGY_PATCH_APPLICATIONS_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()


def read_all_applications(
    path: Path = DEFAULT_STRATEGY_PATCH_APPLICATIONS_PATH,
) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def get_existing_application(
    account_id: str,
    window_id: str,
    policy_stage: str,
    *,
    path: Path = DEFAULT_STRATEGY_PATCH_APPLICATIONS_PATH,
) -> dict[str, Any] | None:
    rows = read_all_applications(path)
    for row in reversed(rows):
        if (
            row.get("account_id") == account_id
            and row.get("window_id") == window_id
            and row.get("policy_stage") == policy_stage
            and row.get("status") in {"APPLIED", "ROLLED_BACK"}
        ):
            return row
    return None

