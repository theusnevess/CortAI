from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.runtime.scheduler.feed_distribution import reorder_feed_candidates, summarize_feed_sequence


class FeedDistributionControlUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_flag = os.environ.get("CORTAI_EXPERIMENT_FEED_DISTRIBUTION_CONTROL")
        os.environ["CORTAI_EXPERIMENT_FEED_DISTRIBUTION_CONTROL"] = "1"

    def tearDown(self) -> None:
        if self.original_flag is None:
            os.environ.pop("CORTAI_EXPERIMENT_FEED_DISTRIBUTION_CONTROL", None)
            return
        os.environ["CORTAI_EXPERIMENT_FEED_DISTRIBUTION_CONTROL"] = self.original_flag

    def test_reduces_hook_type_and_visual_loops_when_alternatives_exist(self) -> None:
        candidates = [
            {"video_id": "v1", "hook_type": "experiential", "visual_anchor": "door"},
            {"video_id": "v2", "hook_type": "experiential", "visual_anchor": "door"},
            {"video_id": "v3", "hook_type": "experiential", "visual_anchor": "device"},
            {"video_id": "v4", "hook_type": "inferential", "visual_anchor": "document"},
            {"video_id": "v5", "hook_type": "inferential", "visual_anchor": "document"},
            {"video_id": "v6", "hook_type": "experiential", "visual_anchor": "door"},
        ]

        sequence, relaxation_count = reorder_feed_candidates(candidates)

        self.assertEqual([item["video_id"] for item in sequence], ["v1", "v2", "v4", "v3", "v5", "v6"])
        metrics = summarize_feed_sequence(sequence)
        self.assertLessEqual(metrics["max_consecutive_same_hook_type"], 2)
        self.assertLessEqual(metrics["max_consecutive_same_visual_anchor"], 2)
        self.assertEqual(relaxation_count, 0)

    def test_respects_window_diversity_when_possible(self) -> None:
        candidates = [
            {"video_id": "v1", "hook_type": "experiential", "visual_anchor": "door"},
            {"video_id": "v2", "hook_type": "experiential", "visual_anchor": "device"},
            {"video_id": "v3", "hook_type": "experiential", "visual_anchor": "door"},
            {"video_id": "v4", "hook_type": "experiential", "visual_anchor": "device"},
            {"video_id": "v5", "hook_type": "inferential", "visual_anchor": "document"},
        ]

        sequence, relaxation_count = reorder_feed_candidates(candidates)

        window_types = {item["hook_type"] for item in sequence[:5]}
        self.assertEqual(window_types, {"experiential", "inferential"})
        self.assertEqual(relaxation_count, 0)

    def test_homogeneous_queue_relaxes_without_deadlock(self) -> None:
        candidates = [
            {"video_id": "v1", "hook_type": "inferential", "visual_anchor": "document"},
            {"video_id": "v2", "hook_type": "inferential", "visual_anchor": "document"},
            {"video_id": "v3", "hook_type": "inferential", "visual_anchor": "document"},
        ]

        sequence, relaxation_count = reorder_feed_candidates(candidates)

        self.assertEqual([item["video_id"] for item in sequence], ["v1", "v2", "v3"])
        self.assertGreater(relaxation_count, 0)


if __name__ == "__main__":
    unittest.main()
