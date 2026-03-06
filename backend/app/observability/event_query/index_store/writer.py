from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.observability.event_query.index_store.schema import SCHEMA_SQL
from app.observability.event_query.models import EventRecord


class EventIndexWriter:
    """Escreve eventos normalizados em um indice SQLite idempotente."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    def write(self, record: EventRecord, *, source_file: str, source_line: int) -> str:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO events_index (
                    source_file,
                    source_line,
                    event_id,
                    ts,
                    event_type,
                    writer_id,
                    severity,
                    action_taken,
                    account_id,
                    window_id,
                    job_id,
                    publish_id,
                    op_key,
                    details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_file,
                    int(source_line),
                    record.event_id,
                    record.ts,
                    record.event_type,
                    record.writer_id,
                    record.severity,
                    record.action_taken,
                    record.account_id,
                    record.window_id,
                    record.job_id,
                    record.publish_id,
                    record.op_key,
                    json.dumps(record.details, ensure_ascii=False, sort_keys=True)
                    if record.details is not None
                    else None,
                ),
            )
            conn.commit()
        return "WRITTEN" if cursor.rowcount else "NOOP"
