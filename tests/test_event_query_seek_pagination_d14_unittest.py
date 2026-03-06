from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.observability.event_query.cursor import decode_cursor, validate_cursor_signature
from app.observability.event_query.cursor_signing import SigningPolicy
from app.observability.event_query.indexer import EventIndexer
from app.observability.event_query.models import EventQueryFilters
from app.observability.event_query.query_service import EventQueryService


class EventQuerySeekPaginationD14Tests(unittest.TestCase):
    def _tmp_out(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name) / "OUT"
        (out / "events").mkdir(parents=True, exist_ok=True)
        (out / "audit").mkdir(parents=True, exist_ok=True)
        (out / "data").mkdir(parents=True, exist_ok=True)
        return out

    def _write_events(self, out: Path, rows: list[dict]) -> None:
        path = out / "events" / "events.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")

    def _append_events(self, out: Path, rows: list[dict]) -> None:
        path = out / "events" / "events.jsonl"
        with path.open("a", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")

    def _event(self, event_id: str, ts: str, *, account_id: str = "acc_001") -> dict:
        return {
            "event_id": event_id,
            "ts": ts,
            "event_type": "PIPE/D10_FINISHED",
            "account_id": account_id,
            "severity": "INFO",
            "details": {"reason_code": "OK"},
        }

    def _service(self, out: Path, policy: SigningPolicy | None = None) -> EventQueryService:
        return EventQueryService(indexer=EventIndexer(base_dir=out), cursor_signing_policy=policy)

    def _filters(self) -> EventQueryFilters:
        return EventQueryFilters(
            start_ts="2026-03-01T00:00:00Z",
            end_ts="2026-03-10T00:00:00Z",
            account_id="acc_001",
        )

    def test_sem_cursor_limit_plus_one_has_more(self) -> None:
        out = self._tmp_out()
        rows = [self._event(f"evt_{i:03d}", f"2026-03-05T10:{i:02d}:00Z") for i in range(7)]
        self._write_events(out, rows)
        service = self._service(out)

        result = service.get_events(self._filters(), limit=5)

        self.assertEqual(len(result.items), 5)
        self.assertTrue(result.has_more)
        self.assertIsNotNone(result.next_cursor)
        cursor = decode_cursor(result.next_cursor or "")
        last = result.items[-1]
        self.assertEqual(cursor.last.ts, last.ts)
        self.assertEqual(cursor.last.event_id, last.event_id)

    def test_com_cursor_proxima_pagina_sem_duplicar(self) -> None:
        out = self._tmp_out()
        rows = [self._event(f"evt_{i:03d}", f"2026-03-05T10:{i:02d}:00Z") for i in range(7)]
        self._write_events(out, rows)
        service = self._service(out)

        page1 = service.get_events(self._filters(), limit=5)
        page2 = service.get_events(self._filters(), limit=5, cursor=page1.next_cursor)

        ids1 = {item.event_id for item in page1.items}
        ids2 = {item.event_id for item in page2.items}
        self.assertEqual(len(ids1.intersection(ids2)), 0)

    def test_tie_break_por_ts_event_id(self) -> None:
        out = self._tmp_out()
        rows = [
            self._event("evt_a", "2026-03-05T10:00:00Z"),
            self._event("evt_c", "2026-03-05T10:00:00Z"),
            self._event("evt_b", "2026-03-05T10:00:00Z"),
        ]
        self._write_events(out, rows)
        service = self._service(out)

        page1 = service.get_events(self._filters(), limit=2)
        self.assertEqual([i.event_id for i in page1.items], ["evt_c", "evt_b"])
        page2 = service.get_events(self._filters(), limit=2, cursor=page1.next_cursor)
        self.assertEqual([i.event_id for i in page2.items], ["evt_a"])

    def test_insercoes_concorrentes_simuladas_sem_duplicar(self) -> None:
        out = self._tmp_out()
        baseline = [self._event(f"old_{i:03d}", f"2026-03-05T10:{i:02d}:00Z") for i in range(10)]
        self._write_events(out, baseline)
        service = self._service(out)

        page1 = service.get_events(self._filters(), limit=5)
        cursor = page1.next_cursor

        new_rows = [
            self._event("new_001", "2026-03-05T10:59:00Z"),
            self._event("new_002", "2026-03-05T10:58:00Z"),
        ]
        self._append_events(out, new_rows)

        page2 = service.get_events(self._filters(), limit=5, cursor=cursor)
        ids1 = {item.event_id for item in page1.items}
        ids2 = {item.event_id for item in page2.items}
        self.assertEqual(len(ids1.intersection(ids2)), 0)
        self.assertFalse(any(event_id.startswith("new_") for event_id in ids2))
        self.assertEqual(len(ids2), 5)

    def test_profile_b_next_cursor_assinado(self) -> None:
        out = self._tmp_out()
        rows = [self._event(f"evt_{i:03d}", f"2026-03-05T10:{i:02d}:00Z") for i in range(6)]
        self._write_events(out, rows)
        policy = SigningPolicy(enabled=True, secret=b"secret")
        service = self._service(out, policy=policy)

        result = service.get_events(self._filters(), limit=5)
        self.assertIsNotNone(result.next_cursor)
        cursor = decode_cursor(result.next_cursor or "")
        validate_cursor_signature(cursor, policy)


if __name__ == "__main__":
    unittest.main()
