from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class AnalysisJsonStore:
    def __init__(self, base_dir: str | Path = "OUT/analysis"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_json(self, filename: str, payload: dict[str, Any]) -> Path:
        target = self.base_dir / filename
        tmp_path = target.with_suffix(target.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=True, indent=2, sort_keys=True)
            handle.write("\n")
        tmp_path.replace(target)
        return target

    def load_json(self, filename: str) -> dict[str, Any] | None:
        target = self.base_dir / filename
        if not target.exists():
            return None
        with target.open("r", encoding="utf-8") as handle:
            return json.load(handle)
