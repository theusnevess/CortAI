from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.observability.event_append.service import append_event, build_event_record


@dataclass(frozen=True)
class CreativeEventEmitter:
    event_path: Path = Path("OUT/events/events.jsonl")

    def emit(self, event_type: str, payload: dict[str, Any]) -> None:
        event = build_event_record(event_type, dict(payload), writer_id="creative_orchestrator")
        append_event(event, path=self.event_path)
