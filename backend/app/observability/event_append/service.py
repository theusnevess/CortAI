from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.observability.event_query.index_store.writer import EventIndexWriter
from app.observability.event_query.indexer import EventIndexer
from app.observability.event_query.models import EventRecord
from app.observability.event_append.errors import EventAppendJsonlError


@dataclass(frozen=True)
class AppendResult:
    """Resultado do write-through centralizado."""

    jsonl_written: bool
    index_written: bool
    index_error: str | None
    source_file: str
    source_line: int


JsonlStore = Callable[[dict[str, Any], Path], tuple[str, int]]


def default_event_path() -> Path:
    return Path("OUT/events/events.jsonl")


def default_event_index_writer() -> EventIndexWriter:
    return EventIndexWriter(Path("OUT/index/event_index.sqlite3"))


def append_jsonl_event(event: dict[str, Any], path: Path) -> tuple[str, int]:
    """Anexa um evento no JSONL canonico e retorna arquivo/linha escritos."""
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_lines = 0
    if path.exists():
        with path.open("r", encoding="utf-8") as reader:
            for existing_lines, _ in enumerate(reader, start=1):
                pass
    source_line = existing_lines + 1
    try:
        with path.open("a", encoding="utf-8") as writer:
            writer.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
            writer.flush()
    except Exception as exc:  # noqa: BLE001
        raise EventAppendJsonlError(str(exc)) from exc
    return str(path), source_line


def append_event(
    event: dict[str, Any],
    *,
    path: Path | None = None,
    jsonl_store: JsonlStore | None = None,
    index_writer: EventIndexWriter | None = None,
) -> AppendResult:
    """Persiste o evento no log canonico e tenta indexacao write-through."""
    target_path = path or default_event_path()
    store = jsonl_store or append_jsonl_event

    source_file, source_line = store(event, target_path)

    parsed = EventIndexer().parse_event(event)
    if parsed is None:
        return AppendResult(
            jsonl_written=True,
            index_written=False,
            index_error="EVENT_INVALID_SHAPE",
            source_file=source_file,
            source_line=source_line,
        )

    writer = index_writer or default_event_index_writer()
    try:
        status = writer.write(parsed, source_file=source_file, source_line=source_line)
        index_written = status in {"WRITTEN", "NOOP"}
        index_error = None
    except Exception as exc:  # noqa: BLE001
        index_written = False
        index_error = str(exc) or exc.__class__.__name__

    return AppendResult(
        jsonl_written=True,
        index_written=index_written,
        index_error=index_error,
        source_file=source_file,
        source_line=source_line,
    )


def build_event_record(event_type: str, payload: dict[str, Any], *, writer_id: str | None = None) -> dict[str, Any]:
    """Normaliza payload para o contrato publico de eventos."""
    event: dict[str, Any] = {
        "event_type": event_type,
        "ts": str(payload.get("timestamp") or payload.get("ts") or ""),
        "writer_id": writer_id,
    }
    for key in ("event_id", "severity", "action_taken", "account_id", "window_id", "job_id", "publish_id", "op_key"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            event[key] = value
    details = dict(payload)
    details.pop("event_id", None)
    details.pop("ts", None)
    if "timestamp" in details:
        details.pop("timestamp", None)
    if details:
        event["details"] = details
    return event
