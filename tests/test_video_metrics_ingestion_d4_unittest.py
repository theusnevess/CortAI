from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.data.schemas.video_metrics import VideoMetricsValidationError, validate_video_metrics
from app.data.video_metrics.invariants import decide_ingestion_action
from app.data.video_metrics.repo import get_best
from app.data.video_metrics.writer import write_video_metrics


def _base_metrics(**overrides):
    record = {
        "video_id": "vid_001",
        "account_id": "acc_ca_001",
        "captured_at": "2026-03-04T18:00:00Z",
        "captured_window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
        "source_kind": "MANUAL_ENTRY",
        "views": 100,
        "retention_3s": 0.40,
        "completion_rate": 0.30,
        "likes": 10,
        "follows": 2,
        "rpm": 0.5,
        "ingested_at": "2026-03-04T18:01:00Z",
    }
    record.update(overrides)
    return record


class VideoMetricsIngestionD4Tests(unittest.TestCase):
    def test_dedup_key_repo_returns_single_best_for_same_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "video_metrics.jsonl"
            write_video_metrics(_base_metrics(source_kind="MANUAL_ENTRY", views=90), path=path)
            write_video_metrics(_base_metrics(source_kind="SCRAPED_ANALYTICS", views=120), path=path)

            best = get_best(
                "acc_ca_001",
                "vid_001",
                "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
                path=path,
            )
            self.assertIsNotNone(best)
            self.assertEqual(best["source_kind"], "SCRAPED_ANALYTICS")

    def test_precedence_manual_scraped_platform(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "video_metrics.jsonl"
            write_video_metrics(_base_metrics(source_kind="MANUAL_ENTRY", views=80), path=path)
            write_video_metrics(_base_metrics(source_kind="SCRAPED_ANALYTICS", views=100), path=path)
            write_video_metrics(_base_metrics(source_kind="PLATFORM_ANALYTICS", views=130), path=path)

            best = get_best(
                "acc_ca_001",
                "vid_001",
                "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
                path=path,
            )
            self.assertEqual(best["source_kind"], "PLATFORM_ANALYTICS")
            self.assertEqual(best["views"], 130)

    def test_worse_source_is_noop_on_best(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "video_metrics.jsonl"
            better = _base_metrics(source_kind="PLATFORM_ANALYTICS", views=200)
            worse = _base_metrics(source_kind="MANUAL_ENTRY", views=50, ingested_at="2026-03-04T18:05:00Z")
            write_video_metrics(better, path=path)
            write_video_metrics(worse, path=path)

            best = get_best(
                "acc_ca_001",
                "vid_001",
                "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
                path=path,
            )
            self.assertEqual(best["source_kind"], "PLATFORM_ANALYTICS")
            self.assertEqual(best["views"], 200)

            action = decide_ingestion_action(new_record=worse, current_best=better)
            self.assertEqual(action, "NOOP_WORSE_SOURCE")

    def test_invalid_retention_or_completion_range_fails(self) -> None:
        with self.assertRaises(VideoMetricsValidationError):
            validate_video_metrics(_base_metrics(retention_3s=1.5))
        with self.assertRaises(VideoMetricsValidationError):
            validate_video_metrics(_base_metrics(completion_rate=-0.2))

    def test_captured_window_id_required(self) -> None:
        with self.assertRaises(VideoMetricsValidationError):
            validate_video_metrics(_base_metrics(captured_window_id=""))


if __name__ == "__main__":
    unittest.main()
