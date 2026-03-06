from __future__ import annotations

import json
from dataclasses import dataclass
import heapq
from pathlib import Path
from typing import Iterable, Iterator

from app.observability.event_query.models import (
    EventQueryFilters,
    EventQueryResult,
    EventQueryStats,
    EventRecord,
    parse_iso_utc,
)


@dataclass(frozen=True)
class _ParsedLine:
    record: EventRecord | None
    invalid_json: bool = False
    invalid_shape: bool = False
    source_file: str | None = None
    source_line: int = 0


def _safe_details(raw: object) -> dict | None:
    """Aplica redacao minima de details para saida publica."""
    if not isinstance(raw, dict):
        return None
    safe_keys = {
        "reason_code",
        "summary",
        "hint",
        "status",
        "source_kind_used",
        "op_key",
        "window_id",
        "account_id",
        "publish_id",
        "job_id",
        "task_id",
        "task_type",
        "worker_id",
    }
    details: dict = {}
    for key in sorted(raw.keys()):
        if key in safe_keys:
            details[key] = raw[key]
    return details or None


class EventIndexer:
    """Indexador leve para consultar trilhas JSONL sem persistencia adicional."""

    def __init__(self, base_dir: Path = Path("OUT"), source_dirs: list[str] | None = None) -> None:
        self.base_dir = base_dir
        self.source_dirs = source_dirs or ["events", "audit", "data"]

    def iter_jsonl_files(self, paths: Iterable[str] | None = None) -> Iterator[Path]:
        """Itera arquivos JSONL das fontes configuradas em ordem deterministica."""
        directories = list(paths) if paths is not None else list(self.source_dirs)
        files: list[Path] = []
        for rel in directories:
            directory = self.base_dir / rel
            if not directory.exists():
                continue
            files.extend(sorted(directory.glob("*.jsonl")))
        for path in sorted(files):
            yield path

    def parse_event(self, raw: dict) -> EventRecord | None:
        """Converte payload cru para EventRecord normalizado."""
        event_type = raw.get("event_type")
        ts = raw.get("ts")
        if not isinstance(event_type, str) or not event_type.strip():
            return None
        if not isinstance(ts, str) or not ts.strip():
            return None
        event_id = raw.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip():
            event_id = ""
        return EventRecord(
            event_id=event_id,
            ts=ts,
            event_type=event_type,
            writer_id=raw.get("writer_id") if isinstance(raw.get("writer_id"), str) else None,
            severity=raw.get("severity") if isinstance(raw.get("severity"), str) else None,
            action_taken=raw.get("action_taken") if isinstance(raw.get("action_taken"), str) else None,
            account_id=raw.get("account_id") if isinstance(raw.get("account_id"), str) else None,
            window_id=raw.get("window_id") if isinstance(raw.get("window_id"), str) else None,
            job_id=raw.get("job_id") if isinstance(raw.get("job_id"), str) else None,
            publish_id=raw.get("publish_id") if isinstance(raw.get("publish_id"), str) else None,
            op_key=raw.get("op_key") if isinstance(raw.get("op_key"), str) else None,
            details=_safe_details(raw.get("details")),
        )

    def iter_events(self, paths: Iterable[str] | None = None) -> Iterator[_ParsedLine]:
        """Itera linhas parseadas sem falhar por JSONL invalido."""
        yield from self.iter_events_with_source(paths)

    def iter_events_with_source(self, paths: Iterable[str] | None = None) -> Iterator[_ParsedLine]:
        """Itera eventos preservando arquivo e linha para rebuild/indexacao."""
        for file_path in self.iter_jsonl_files(paths):
            with file_path.open("r", encoding="utf-8") as f:
                for line_number, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw = json.loads(line)
                    except json.JSONDecodeError:
                        yield _ParsedLine(
                            record=None,
                            invalid_json=True,
                            source_file=str(file_path),
                            source_line=line_number,
                        )
                        continue
                    if not isinstance(raw, dict):
                        yield _ParsedLine(
                            record=None,
                            invalid_shape=True,
                            source_file=str(file_path),
                            source_line=line_number,
                        )
                        continue
                    parsed = self.parse_event(raw)
                    if parsed is None:
                        yield _ParsedLine(
                            record=None,
                            invalid_shape=True,
                            source_file=str(file_path),
                            source_line=line_number,
                        )
                        continue
                    yield _ParsedLine(
                        record=parsed,
                        source_file=str(file_path),
                        source_line=line_number,
                    )

    def scan(
        self,
        filters: EventQueryFilters,
        limit: int = 200,
        *,
        cursor_last: tuple[str, str] | None = None,
    ) -> EventQueryResult:
        """Executa varredura deterministica com filtros, seek e limit+1."""
        start_dt = filters.start_dt()
        end_dt = filters.end_dt()
        scanned_files = sum(1 for _ in self.iter_jsonl_files())
        heap: list[tuple[tuple[str, str], int, EventRecord]] = []
        capacity = max(limit + 1, 1)
        scanned_lines = 0
        invalid_json = 0
        invalid_shape = 0
        seq = 0

        for parsed in self.iter_events():
            scanned_lines += 1
            if parsed.invalid_json:
                invalid_json += 1
                continue
            if parsed.invalid_shape or parsed.record is None:
                invalid_shape += 1
                continue
            record = parsed.record
            if not self._matches(record, filters, start_dt, end_dt):
                continue
            if not self._matches_cursor(record, cursor_last):
                continue
            key = (record.ts, record.event_id or "")
            seq += 1
            if len(heap) < capacity:
                heapq.heappush(heap, (key, seq, record))
            else:
                if key > heap[0][0]:
                    heapq.heapreplace(heap, (key, seq, record))

        selected = [item for _, _, item in heap]
        selected.sort(key=lambda item: (item.ts, item.event_id or ""), reverse=True)
        has_more = len(selected) > limit
        items = selected[:limit] if limit > 0 else selected

        return EventQueryResult(
            items=items,
            stats=EventQueryStats(
                scanned_files=scanned_files,
                scanned_lines=scanned_lines,
                invalid_jsonl_lines=invalid_json,
                invalid_shape_lines=invalid_shape,
            ),
            has_more=has_more,
        )

    def _matches_cursor(self, record: EventRecord, cursor_last: tuple[str, str] | None) -> bool:
        """Aplica seek estrito para paginacao DESC sem duplicar boundary."""
        if cursor_last is None:
            return True
        cursor_ts, cursor_event_id = cursor_last
        record_event_id = record.event_id or ""
        if record.ts < cursor_ts:
            return True
        if record.ts == cursor_ts and record_event_id < cursor_event_id:
            return True
        return False

    def _matches(self, record: EventRecord, filters: EventQueryFilters, start_dt, end_dt) -> bool:
        try:
            ts = parse_iso_utc(record.ts)
        except Exception:  # noqa: BLE001
            return False
        if ts < start_dt or ts >= end_dt:
            return False
        if filters.account_id and record.account_id != filters.account_id:
            return False
        if filters.window_id and record.window_id != filters.window_id:
            return False
        if filters.job_id and record.job_id != filters.job_id:
            return False
        if filters.publish_id and record.publish_id != filters.publish_id:
            return False
        if filters.op_key and record.op_key != filters.op_key:
            return False
        if filters.event_type and record.event_type != filters.event_type:
            return False
        if filters.event_type_prefix and not record.event_type.startswith(filters.event_type_prefix):
            return False
        if filters.severity and record.severity != filters.severity:
            return False
        if filters.action_taken and record.action_taken != filters.action_taken:
            return False
        return True
