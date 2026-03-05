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

from app.concurrency.idempotency import IdempotencyManager
from app.concurrency.store_jsonl import append_concurrency_event, read_concurrency_events


class IdempotencyD12Tests(unittest.TestCase):
    def test_reserve_noop_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "concurrency.jsonl"

            manager = IdempotencyManager(
                event_sink=lambda e: append_concurrency_event(e, path=path),
                event_source=lambda: read_concurrency_events(path=path),
            )

            first = manager.idempotency_check_or_reserve("AGG:acc:w1", "hash-a")
            second = manager.idempotency_check_or_reserve("AGG:acc:w1", "hash-a")
            third = manager.idempotency_check_or_reserve("AGG:acc:w1", "hash-b")

            self.assertEqual(first, "WRITTEN")
            self.assertEqual(second, "NOOP")
            self.assertEqual(third, "CONFLICT")

    def test_finalize_registra_evento(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "concurrency.jsonl"
            manager = IdempotencyManager(
                event_sink=lambda e: append_concurrency_event(e, path=path),
                event_source=lambda: read_concurrency_events(path=path),
            )

            manager.idempotency_check_or_reserve("SC:acc:w1", "hash-1")
            manager.finalize_op("SC:acc:w1", "SUCCESS")

            rows = read_concurrency_events(path=path)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[-1]["event_type"], "IDEMPOTENCY/op_finalized")
            self.assertEqual(rows[-1]["status"], "SUCCESS")


if __name__ == "__main__":
    unittest.main()
