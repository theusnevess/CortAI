from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.observability.event_query.index_store.repo import EventIndexRepo
from app.observability.event_query.index_store.rebuild import rebuild_event_index
from app.observability.event_query.index_store.writer import EventIndexWriter
from app.observability.event_query.indexer import EventIndexer
from app.observability.event_query.models import EventQueryFilters, EventRecord
from app.observability.event_query.query_service import EventQueryService


class EventIndexD16Tests(unittest.TestCase):
    def _tmp_out(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name) / "OUT"
        for name in ["events", "audit", "data"]:
            (out / name).mkdir(parents=True, exist_ok=True)
        return out

    def _filters(self) -> EventQueryFilters:
        return EventQueryFilters(
            start_ts="2026-03-01T00:00:00Z",
            end_ts="2026-03-10T00:00:00Z",
            account_id="acc_001",
        )

    def _record(self, event_id: str, ts: str) -> EventRecord:
        return EventRecord(
            event_id=event_id,
            ts=ts,
            event_type="PIPE/D10_FINISHED",
            writer_id="runner",
            severity="INFO",
            action_taken="OBSERVE",
            account_id="acc_001",
            window_id="w_001",
            job_id="job_001",
            publish_id="pub_001",
            op_key="AGG:acc_001:w_001",
            details={"reason_code": "OK"},
        )

    def _write_jsonl(self, out: Path, rows: list[dict]) -> None:
        path = out / "events" / "events.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")

    def test_insert_e_query_no_indice(self) -> None:
        out = self._tmp_out()
        db_path = out / "event_index.sqlite3"
        writer = EventIndexWriter(db_path)
        repo = EventIndexRepo(db_path)

        writer.write(self._record("evt_001", "2026-03-05T10:00:00Z"), source_file="events.jsonl", source_line=1)
        writer.write(self._record("evt_002", "2026-03-05T10:01:00Z"), source_file="events.jsonl", source_line=2)

        result = repo.search(self._filters(), limit=10)

        self.assertEqual([item.event_id for item in result.items], ["evt_002", "evt_001"])

    def test_rebuild_index_a_partir_do_jsonl(self) -> None:
        out = self._tmp_out()
        rows = [
            {
                "event_id": "evt_001",
                "ts": "2026-03-05T10:00:00Z",
                "event_type": "PIPE/D10_STARTED",
                "account_id": "acc_001",
                "details": {"reason_code": "START"},
            },
            {
                "event_id": "evt_002",
                "ts": "2026-03-05T10:01:00Z",
                "event_type": "PIPE/D10_FINISHED",
                "account_id": "acc_001",
                "details": {"reason_code": "OK"},
            },
        ]
        self._write_jsonl(out, rows)
        indexer = EventIndexer(base_dir=out)
        db_path = out / "event_index.sqlite3"
        writer = EventIndexWriter(db_path)
        repo = EventIndexRepo(db_path)

        rebuild = rebuild_event_index(indexer=indexer, writer=writer)
        result = repo.search(self._filters(), limit=10)

        self.assertEqual(rebuild.written, 2)
        self.assertEqual([item.event_id for item in result.items], ["evt_002", "evt_001"])

    def test_rebuild_idempotente_nao_duplica(self) -> None:
        out = self._tmp_out()
        self._write_jsonl(
            out,
            [
                {
                    "event_id": "evt_001",
                    "ts": "2026-03-05T10:00:00Z",
                    "event_type": "PIPE/D10_STARTED",
                    "account_id": "acc_001",
                }
            ],
        )
        indexer = EventIndexer(base_dir=out)
        db_path = out / "event_index.sqlite3"
        writer = EventIndexWriter(db_path)

        first = rebuild_event_index(indexer=indexer, writer=writer)
        second = rebuild_event_index(indexer=indexer, writer=writer)

        with sqlite3.connect(db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM events_index").fetchone()[0]

        self.assertEqual(first.written, 1)
        self.assertEqual(second.noop, 1)
        self.assertEqual(count, 1)

    def test_service_faz_fallback_para_scanner_sem_indice(self) -> None:
        out = self._tmp_out()
        self._write_jsonl(
            out,
            [
                {
                    "event_id": "evt_001",
                    "ts": "2026-03-05T10:00:00Z",
                    "event_type": "PIPE/D10_STARTED",
                    "account_id": "acc_001",
                }
            ],
        )
        service = EventQueryService(
            indexer=EventIndexer(base_dir=out),
            index_repo=EventIndexRepo(out / "event_index.sqlite3"),
        )

        result = service.get_events(self._filters(), limit=10)

        self.assertEqual([item.event_id for item in result.items], ["evt_001"])

    def test_ordering_consistente_entre_indice_e_scanner(self) -> None:
        out = self._tmp_out()
        rows = [
            {
                "event_id": "evt_a",
                "ts": "2026-03-05T10:00:00Z",
                "event_type": "PIPE/D10_FINISHED",
                "account_id": "acc_001",
            },
            {
                "event_id": "evt_c",
                "ts": "2026-03-05T10:00:00Z",
                "event_type": "PIPE/D10_FINISHED",
                "account_id": "acc_001",
            },
            {
                "event_id": "evt_b",
                "ts": "2026-03-05T10:00:00Z",
                "event_type": "PIPE/D10_FINISHED",
                "account_id": "acc_001",
            },
        ]
        self._write_jsonl(out, rows)
        indexer = EventIndexer(base_dir=out)
        db_path = out / "event_index.sqlite3"
        rebuild_event_index(indexer=indexer, writer=EventIndexWriter(db_path))

        scanner_service = EventQueryService(indexer=indexer)
        index_service = EventQueryService(indexer=indexer, index_repo=EventIndexRepo(db_path))

        scanner_result = scanner_service.get_events(self._filters(), limit=10)
        index_result = index_service.get_events(self._filters(), limit=10)

        self.assertEqual(
            [item.event_id for item in index_result.items],
            [item.event_id for item in scanner_result.items],
        )


if __name__ == "__main__":
    unittest.main()
