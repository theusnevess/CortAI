from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.data.window_snapshots.store_jsonl import get_window_snapshot, save_window_snapshot_if_absent
from app.jobs.window_snapshot import ensure_window_snapshot


class WindowSnapshotD12Tests(unittest.TestCase):
    def test_snapshot_criado_uma_vez_e_reexecucao_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "window_snapshots.jsonl"
            kwargs = {
                "account_id": "acc_001",
                "window_id": "w_001",
                "publish_ids": ["pub_1", "pub_2"],
                "video_ids": ["vid_1", "vid_2"],
                "captured_range": {"start": "2026-03-01T00:00:00Z", "end": "2026-03-04T00:00:00Z"},
                "source_refs": {"publish_records": "sha256:a", "video_metrics": "sha256:b"},
                "path": path,
            }

            first = ensure_window_snapshot(**kwargs)
            second = ensure_window_snapshot(**kwargs)

            self.assertEqual(first["status"], "WRITTEN")
            self.assertEqual(second["status"], "NOOP")
            self.assertIsNotNone(get_window_snapshot("acc_001", "w_001", path=path))

    def test_snapshot_conflito_mesma_chave_payload_diferente(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "window_snapshots.jsonl"
            base = {
                "account_id": "acc_001",
                "window_id": "w_001",
                "publish_ids": ["pub_1"],
                "video_ids": ["vid_1"],
                "captured_range": {"start": "2026-03-01T00:00:00Z", "end": "2026-03-04T00:00:00Z"},
                "source_refs": {"publish_records": "sha256:a", "video_metrics": "sha256:b"},
                "generated_at": "2026-03-05T00:00:00Z",
            }
            status = save_window_snapshot_if_absent(base, path=path)
            self.assertEqual(status, "WRITTEN")

            modified = dict(base)
            modified["video_ids"] = ["vid_1", "vid_2"]
            with self.assertRaisesRegex(ValueError, "SNAPSHOT_CONFLICT"):
                save_window_snapshot_if_absent(modified, path=path)


if __name__ == "__main__":
    unittest.main()
