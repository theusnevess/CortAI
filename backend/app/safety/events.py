from __future__ import annotations

from pathlib import Path
from typing import Any

from app.observability.event_append.service import append_event, build_event_record


def emit_safety_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    event_path: Path = Path("OUT/events/events.jsonl"),
) -> None:
    event = build_event_record(event_type, payload, writer_id="safety")
    append_event(event, path=event_path)
