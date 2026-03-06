from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_CONTENT_ATTRIBUTION_PATH = Path("OUT/data/content_attribution.jsonl")


def append_attribution(
    record: dict[str, Any],
    *,
    path: Path = DEFAULT_CONTENT_ATTRIBUTION_PATH,
) -> None:
    """Aplica escrita append-only de uma linha de attribution em JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()


def read_all_attributions(path: Path = DEFAULT_CONTENT_ATTRIBUTION_PATH) -> list[dict[str, Any]]:
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

