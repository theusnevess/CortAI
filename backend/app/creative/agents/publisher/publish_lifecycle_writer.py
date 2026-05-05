from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PublishLifecycleWriter:
    """Append-only JSONL writer for Publisher lifecycle evidence."""

    path: Path | str

    def append_event(self, event: Any) -> Path:
        payload = event.to_dict() if hasattr(event, "to_dict") else dict(event)
        target = Path(self.path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, sort_keys=True, ensure_ascii=True))
            handle.write("\n")
        return target

    def read_events(self) -> list[dict[str, Any]]:
        target = Path(self.path)
        if not target.exists():
            return []
        events: list[dict[str, Any]] = []
        with target.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped:
                    events.append(json.loads(stripped))
        return events
