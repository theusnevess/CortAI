from __future__ import annotations

from dataclasses import dataclass

from app.observability.event_query.indexer import EventIndexer
from app.observability.event_query.index_store.writer import EventIndexWriter


@dataclass(frozen=True)
class EventIndexRebuildResult:
    written: int = 0
    noop: int = 0
    invalid_jsonl_lines: int = 0
    invalid_shape_lines: int = 0


def rebuild_event_index(
    *,
    indexer: EventIndexer,
    writer: EventIndexWriter,
) -> EventIndexRebuildResult:
    """Reconstrui o indice a partir dos JSONL configurados sem duplicar entradas."""
    written = 0
    noop = 0
    invalid_json = 0
    invalid_shape = 0

    for parsed in indexer.iter_events_with_source():
        if parsed.invalid_json:
            invalid_json += 1
            continue
        if parsed.invalid_shape or parsed.record is None or parsed.source_file is None:
            invalid_shape += 1
            continue
        status = writer.write(
            parsed.record,
            source_file=parsed.source_file,
            source_line=parsed.source_line,
        )
        if status == "WRITTEN":
            written += 1
        else:
            noop += 1

    return EventIndexRebuildResult(
        written=written,
        noop=noop,
        invalid_jsonl_lines=invalid_json,
        invalid_shape_lines=invalid_shape,
    )
