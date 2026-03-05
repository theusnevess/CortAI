from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_WINDOW_METRICS_PATH = Path("OUT/data/window_metrics.jsonl")


def append_record(record: dict[str, Any], path: Path = DEFAULT_WINDOW_METRICS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_all_records(path: Path = DEFAULT_WINDOW_METRICS_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records

