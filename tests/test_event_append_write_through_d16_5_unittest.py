from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.observability.event_append.errors import EventAppendJsonlError
from app.observability.event_append.service import append_event
from app.observability.event_query.index_store.rebuild import rebuild_event_index
from app.observability.event_query.index_store.repo import EventIndexRepo
from app.observability.event_query.index_store.writer import EventIndexWriter
from app.observability.event_query.indexer import EventIndexer
from app.observability.event_query.models import EventQueryFilters


class EventAppendWriteThroughD165Tests(unittest.TestCase):
    def _tmp_paths(self) -> tuple[Path, Path]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name) / "OUT"
        event_path = out / "events" / "events.jsonl"
        index_path = out / "index" / "event_index.sqlite3"
        return event_path, index_path

    def _event(self, event_id: str = "evt_001") -> dict:
        return {
            "event_id": event_id,
            "ts": "2026-03-06T10:00:00Z",
            "event_type": "SL/strategy_patch_applied",
            "writer_id": "strategy_apply",
            "severity": "INFO",
            "account_id": "acc_001",
            "window_id": "w_001",
            "job_id": "job_001",
            "publish_id": "pub_001",
            "op_key": "SPA:acc_001:w_001:GROWTH",
            "details": {"reason_code": "PATCH_APPLIED"},
        }

    def _filters(self) -> EventQueryFilters:
        return EventQueryFilters(
            start_ts="2026-03-01T00:00:00Z",
            end_ts="2026-03-10T00:00:00Z",
            account_id="acc_001",
        )

    def test_evento_entra_no_jsonl_e_no_indice(self) -> None:
        event_path, index_path = self._tmp_paths()

        result = append_event(
            self._event(),
            path=event_path,
            index_writer=EventIndexWriter(index_path),
        )

        self.assertTrue(result.jsonl_written)
        self.assertTrue(result.index_written)
        with event_path.open("r", encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        self.assertEqual(len(rows), 1)
        repo = EventIndexRepo(index_path)
        search = repo.search(self._filters(), limit=10)
        self.assertEqual([item.event_id for item in search.items], ["evt_001"])

    def test_indice_falha_jsonl_continua_gravando(self) -> None:
        event_path, _ = self._tmp_paths()

        class BrokenWriter:
            def write(self, record, *, source_file: str, source_line: int) -> str:
                raise RuntimeError("INDEX_WRITE_FAILED")

        result = append_event(
            self._event(),
            path=event_path,
            index_writer=BrokenWriter(),  # type: ignore[arg-type]
        )

        self.assertTrue(result.jsonl_written)
        self.assertFalse(result.index_written)
        self.assertEqual(result.index_error, "INDEX_WRITE_FAILED")
        with event_path.open("r", encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        self.assertEqual(len(rows), 1)

    def test_rebuild_reconcilia_log_e_indice(self) -> None:
        event_path, index_path = self._tmp_paths()

        class BrokenWriter:
            def write(self, record, *, source_file: str, source_line: int) -> str:
                raise RuntimeError("INDEX_WRITE_FAILED")

        append_event(
            self._event(),
            path=event_path,
            index_writer=BrokenWriter(),  # type: ignore[arg-type]
        )

        out = event_path.parents[1]
        rebuild = rebuild_event_index(
            indexer=EventIndexer(base_dir=out),
            writer=EventIndexWriter(index_path),
        )
        repo = EventIndexRepo(index_path)
        result = repo.search(self._filters(), limit=10)

        self.assertEqual(rebuild.written, 1)
        self.assertEqual([item.event_id for item in result.items], ["evt_001"])

    def test_idempotencia_do_indice_por_source_file_source_line(self) -> None:
        event_path, index_path = self._tmp_paths()
        writer = EventIndexWriter(index_path)

        first = append_event(self._event("evt_001"), path=event_path, index_writer=writer)
        second = writer.write(
            EventIndexer().parse_event(self._event("evt_001")),
            source_file=first.source_file,
            source_line=first.source_line,
        )

        self.assertEqual(second, "NOOP")
        with sqlite3.connect(index_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM events_index").fetchone()[0]
        self.assertEqual(count, 1)

    def test_append_event_nunca_retorna_sucesso_se_jsonl_falhar(self) -> None:
        event_path, index_path = self._tmp_paths()

        def broken_store(event: dict, path: Path) -> tuple[str, int]:
            raise EventAppendJsonlError("JSONL_WRITE_FAILED")

        with self.assertRaises(EventAppendJsonlError):
            append_event(
                self._event(),
                path=event_path,
                jsonl_store=broken_store,
                index_writer=EventIndexWriter(index_path),
            )


if __name__ == "__main__":
    unittest.main()
