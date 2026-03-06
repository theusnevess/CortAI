from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_STRATEGY_PATCHES_PATH = Path("OUT/data/strategy_patches.jsonl")


def append_patch(record: dict[str, Any], path: Path = DEFAULT_STRATEGY_PATCHES_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()


def read_all_patches(path: Path = DEFAULT_STRATEGY_PATCHES_PATH) -> list[dict[str, Any]]:
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

