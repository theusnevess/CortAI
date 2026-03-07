from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_INTELLIGENCE_DIR = Path("OUT/intelligence")
PUBLISH_WINDOWS_PATH = DEFAULT_INTELLIGENCE_DIR / "publish_windows.jsonl"
PACING_PROFILES_PATH = DEFAULT_INTELLIGENCE_DIR / "pacing_profiles.jsonl"
RISK_PROFILES_PATH = DEFAULT_INTELLIGENCE_DIR / "risk_profiles.jsonl"
ACCOUNT_HEALTH_PATH = DEFAULT_INTELLIGENCE_DIR / "account_health.jsonl"


def append_record(record: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()


def read_all_records(path: Path) -> list[dict[str, Any]]:
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
