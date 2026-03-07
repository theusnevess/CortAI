from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_CREATIVE_PACKS_PATH = Path("OUT/content/creative_packs/creative_packs.jsonl")


def append_pack(record: dict[str, Any], path: Path = DEFAULT_CREATIVE_PACKS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()


def read_all_packs(path: Path = DEFAULT_CREATIVE_PACKS_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows
