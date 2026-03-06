from __future__ import annotations

from dataclasses import dataclass

from app.observability.event_query.indexer import EventIndexer
from app.observability.hot_store.writer import HotStoreWriter


@dataclass(frozen=True)
class HotStoreRebuildResult:
    written: int = 0
    noop: int = 0
    invalid_jsonl_lines: int = 0
    invalid_shape_lines: int = 0


def rebuild_hot_store(
    *,
    indexer: EventIndexer,
    writer: HotStoreWriter,
) -> HotStoreRebuildResult:
    """Reconstrui o hot store a partir do log canonico."""
    written = 0
    noop = 0
    invalid_json = 0
    invalid_shape = 0

    for parsed in indexer.iter_events_with_source():
        if parsed.invalid_json:
            invalid_json += 1
            continue
        if parsed.invalid_shape or parsed.record is None:
            invalid_shape += 1
            continue
        status = writer.write(parsed.record)
        if status == "WRITTEN":
            written += 1
        else:
            noop += 1

    return HotStoreRebuildResult(
        written=written,
        noop=noop,
        invalid_jsonl_lines=invalid_json,
        invalid_shape_lines=invalid_shape,
    )
