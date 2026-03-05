from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_CONCURRENCY_PATH = Path("OUT/data/concurrency_ops.jsonl")


def append_concurrency_event(
    event: dict[str, Any],
    *,
    path: Path = DEFAULT_CONCURRENCY_PATH,
) -> None:
    """Registra evento append-only para auditoria de concorrencia."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        f.flush()


def read_concurrency_events(*, path: Path = DEFAULT_CONCURRENCY_PATH) -> list[dict[str, Any]]:
    """Le todos os eventos de concorrencia preservando ordem de gravacao."""
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
