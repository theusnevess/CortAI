from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.runtime.scheduler.investigation_density import (
    reorder_investigation_stream_by_density,
    summarize_investigation_density,
)


class InvestigationStreamDialectDensityUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_flag = os.environ.get("CORTAI_EXPERIMENT_INVESTIGATION_DIALECT_DENSITY")
        os.environ["CORTAI_EXPERIMENT_INVESTIGATION_DIALECT_DENSITY"] = "1"

    def tearDown(self) -> None:
        if self.original_flag is None:
            os.environ.pop("CORTAI_EXPERIMENT_INVESTIGATION_DIALECT_DENSITY", None)
            return
        os.environ["CORTAI_EXPERIMENT_INVESTIGATION_DIALECT_DENSITY"] = self.original_flag

    def test_breaks_inferential_window_when_experiential_exists(self) -> None:
        candidates = [
            {"video_id": "v1", "stream_id": "investigation_stream", "hook_type": "inferential"},
            {"video_id": "v2", "stream_id": "investigation_stream", "hook_type": "inferential"},
            {"video_id": "v3", "stream_id": "investigation_stream", "hook_type": "inferential"},
            {"video_id": "v4", "stream_id": "investigation_stream", "hook_type": "inferential"},
            {"video_id": "v5", "stream_id": "investigation_stream", "hook_type": "experiential"},
            {"video_id": "v6", "stream_id": "investigation_stream", "hook_type": "inferential"},
        ]

        controlled, note = reorder_investigation_stream_by_density(candidates)
        metrics = summarize_investigation_density(controlled)

        self.assertLessEqual(metrics["max_consecutive_same_hook_type"], 3)
        self.assertEqual(metrics["windows_with_at_least_one_experiential"], 1.0)
        self.assertEqual(note["reason"], "insufficient_experiential_supply_in_window")

    def test_relaxes_when_window_has_no_experiential_left(self) -> None:
        candidates = [
            {"video_id": "v1", "stream_id": "investigation_stream", "hook_type": "inferential"},
            {"video_id": "v2", "stream_id": "investigation_stream", "hook_type": "experiential"},
            {"video_id": "v3", "stream_id": "investigation_stream", "hook_type": "inferential"},
            {"video_id": "v4", "stream_id": "investigation_stream", "hook_type": "inferential"},
            {"video_id": "v5", "stream_id": "investigation_stream", "hook_type": "inferential"},
            {"video_id": "v6", "stream_id": "investigation_stream", "hook_type": "inferential"},
            {"video_id": "v7", "stream_id": "investigation_stream", "hook_type": "inferential"},
        ]

        controlled, note = reorder_investigation_stream_by_density(candidates)
        metrics = summarize_investigation_density(controlled)

        self.assertGreaterEqual(metrics["windows_with_at_least_one_experiential"], 0.5)
        self.assertTrue(note["density_control_relaxed"])
        self.assertEqual(note["reason"], "insufficient_experiential_supply_in_window")

    def test_non_target_stream_is_left_untouched(self) -> None:
        candidates = [
            {"video_id": "v1", "stream_id": "mystery_dark_stream", "hook_type": "inferential"},
            {"video_id": "v2", "stream_id": "mystery_dark_stream", "hook_type": "experiential"},
        ]

        controlled, note = reorder_investigation_stream_by_density(candidates)

        self.assertEqual(controlled, candidates)
        self.assertTrue(note["density_control_relaxed"])
        self.assertEqual(note["reason"], "non_target_stream")


if __name__ == "__main__":
    unittest.main()
