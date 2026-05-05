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

from app.observability.event_append.service import append_event
from app.observability.event_query.index_store.rebuild import rebuild_event_index
from app.observability.event_query.index_store.repo import EventIndexRepo
from app.observability.event_query.index_store.writer import EventIndexWriter
from app.observability.event_query.indexer import EventIndexer
from app.observability.event_query.models import EventQueryFilters
from app.observability.event_query.query_service import EventQueryService
from app.observability.hot_store.rebuild import rebuild_hot_store
from app.observability.hot_store.repo import HotStoreRepo
from app.observability.hot_store.writer import HotStoreWriter


class HotStorageD17Tests(unittest.TestCase):
    def _tmp_out(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name) / "OUT"
        for name in ["events", "audit", "data", "index", "hot_store"]:
            (out / name).mkdir(parents=True, exist_ok=True)
        return out

    def _filters(self) -> EventQueryFilters:
        return EventQueryFilters(
            start_ts="2026-03-01T00:00:00Z",
            end_ts="2026-03-10T00:00:00Z",
            account_id="acc_001",
        )

    def _event(self, event_id: str, ts: str) -> dict:
        return {
            "event_id": event_id,
            "ts": ts,
            "event_type": "PIPE/D10_FINISHED",
            "writer_id": "runner",
            "severity": "INFO",
            "action_taken": "OBSERVE",
            "account_id": "acc_001",
            "window_id": "w_001",
            "job_id": "job_001",
            "publish_id": "pub_001",
            "op_key": "AGG:acc_001:w_001",
            "details": {"reason_code": "OK"},
        }

    def _write_jsonl(self, out: Path, rows: list[dict]) -> None:
        path = out / "events" / "events.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")

    def test_write_e_read_no_hot_store(self) -> None:
        out = self._tmp_out()
        hot_path = out / "hot_store" / "events_hot.sqlite3"

        result = append_event(
            self._event("evt_001", "2026-03-05T10:00:00Z"),
            path=out / "events" / "events.jsonl",
            index_writer=EventIndexWriter(out / "index" / "event_index.sqlite3"),
            hot_store_writer=HotStoreWriter(hot_path),
        )

        self.assertTrue(result.hot_store_written)
        repo = HotStoreRepo(hot_path)
        search = repo.search(self._filters(), limit=10)
        self.assertEqual([item.event_id for item in search.items], ["evt_001"])

    def test_idempotencia_por_event_id(self) -> None:
        out = self._tmp_out()
        hot_path = out / "hot_store" / "events_hot.sqlite3"
        writer = HotStoreWriter(hot_path)

        first = writer.write(EventIndexer().parse_event(self._event("evt_001", "2026-03-05T10:00:00Z")))
        second = writer.write(EventIndexer().parse_event(self._event("evt_001", "2026-03-05T10:00:00Z")))

        self.assertEqual(first, "WRITTEN")
        self.assertEqual(second, "NOOP")
        with sqlite3.connect(hot_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM events_hot").fetchone()[0]
        self.assertEqual(count, 1)

    def test_fallback_para_indice_quando_hot_store_indisponivel(self) -> None:
        out = self._tmp_out()
        rows = [self._event("evt_001", "2026-03-05T10:00:00Z")]
        self._write_jsonl(out, rows)
        rebuild_event_index(
            indexer=EventIndexer(base_dir=out),
            writer=EventIndexWriter(out / "index" / "event_index.sqlite3"),
        )
        service = EventQueryService(
            indexer=EventIndexer(base_dir=out),
            hot_store_repo=HotStoreRepo(out / "hot_store" / "missing.sqlite3"),
            index_repo=EventIndexRepo(out / "index" / "event_index.sqlite3"),
        )

        result = service.get_events(self._filters(), limit=10)
        self.assertEqual([item.event_id for item in result.items], ["evt_001"])

    def test_fallback_para_scanner_quando_indice_tambem_indisponivel(self) -> None:
        out = self._tmp_out()
        rows = [self._event("evt_001", "2026-03-05T10:00:00Z")]
        self._write_jsonl(out, rows)
        service = EventQueryService(
            indexer=EventIndexer(base_dir=out),
            hot_store_repo=HotStoreRepo(out / "hot_store" / "missing.sqlite3"),
            index_repo=EventIndexRepo(out / "index" / "missing.sqlite3"),
        )

        result = service.get_events(self._filters(), limit=10)
        self.assertEqual([item.event_id for item in result.items], ["evt_001"])

    def test_rebuild_replay_a_partir_do_log_canonico(self) -> None:
        out = self._tmp_out()
        rows = [
            self._event("evt_001", "2026-03-05T10:00:00Z"),
            self._event("evt_002", "2026-03-05T10:01:00Z"),
        ]
        self._write_jsonl(out, rows)

        rebuild = rebuild_hot_store(
            indexer=EventIndexer(base_dir=out),
            writer=HotStoreWriter(out / "hot_store" / "events_hot.sqlite3"),
        )
        repo = HotStoreRepo(out / "hot_store" / "events_hot.sqlite3")
        result = repo.search(self._filters(), limit=10)

        self.assertEqual(rebuild.written, 2)
        self.assertEqual([item.event_id for item in result.items], ["evt_002", "evt_001"])


if __name__ == "__main__":
    unittest.main()
