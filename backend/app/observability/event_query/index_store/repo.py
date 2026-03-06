from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.observability.event_query.models import (
    EventQueryFilters,
    EventQueryResult,
    EventQueryStats,
    EventRecord,
)


class EventIndexRepo:
    """Consulta eventos a partir do indice SQLite mantendo o contrato do scanner."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def is_available(self) -> bool:
        return self.db_path.exists()

    def search(
        self,
        filters: EventQueryFilters,
        limit: int,
        *,
        cursor_last: tuple[str, str] | None = None,
    ) -> EventQueryResult:
        if not self.is_available():
            raise FileNotFoundError(self.db_path)

        where = ["ts >= ?", "ts < ?"]
        params: list[object] = [filters.start_ts, filters.end_ts]

        if filters.account_id:
            where.append("account_id = ?")
            params.append(filters.account_id)
        if filters.window_id:
            where.append("window_id = ?")
            params.append(filters.window_id)
        if filters.job_id:
            where.append("job_id = ?")
            params.append(filters.job_id)
        if filters.publish_id:
            where.append("publish_id = ?")
            params.append(filters.publish_id)
        if filters.op_key:
            where.append("op_key = ?")
            params.append(filters.op_key)
        if filters.event_type:
            where.append("event_type = ?")
            params.append(filters.event_type)
        if filters.event_type_prefix:
            where.append("event_type LIKE ?")
            params.append(f"{filters.event_type_prefix}%")
        if filters.severity:
            where.append("severity = ?")
            params.append(filters.severity)
        if filters.action_taken:
            where.append("action_taken = ?")
            params.append(filters.action_taken)
        if cursor_last is not None:
            cursor_ts, cursor_event_id = cursor_last
            where.append("(ts < ? OR (ts = ? AND event_id < ?))")
            params.extend([cursor_ts, cursor_ts, cursor_event_id])

        sql = f"""
        SELECT
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
        FROM events_index
        WHERE {" AND ".join(where)}
        ORDER BY ts DESC, event_id DESC
        LIMIT ?
        """
        params.append(limit + 1)

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(sql, params).fetchall()

        items = [self._row_to_record(row) for row in rows[:limit]]
        has_more = len(rows) > limit
        return EventQueryResult(
            items=items,
            stats=EventQueryStats(scanned_files=0, scanned_lines=0),
            has_more=has_more,
        )

    def _row_to_record(self, row: tuple[object, ...]) -> EventRecord:
        details_raw = row[11]
        details = json.loads(details_raw) if isinstance(details_raw, str) and details_raw else None
        return EventRecord(
            event_id=str(row[0] or ""),
            ts=str(row[1] or ""),
            event_type=str(row[2] or ""),
            writer_id=str(row[3]) if row[3] is not None else None,
            severity=str(row[4]) if row[4] is not None else None,
            action_taken=str(row[5]) if row[5] is not None else None,
            account_id=str(row[6]) if row[6] is not None else None,
            window_id=str(row[7]) if row[7] is not None else None,
            job_id=str(row[8]) if row[8] is not None else None,
            publish_id=str(row[9]) if row[9] is not None else None,
            op_key=str(row[10]) if row[10] is not None else None,
            details=details,
        )
