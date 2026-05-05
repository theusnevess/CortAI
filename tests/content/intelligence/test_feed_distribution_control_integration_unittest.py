from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.runtime.queue import InMemoryTaskQueue
from app.runtime.scheduler.service import SchedulerService


class FeedDistributionControlIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_flag = os.environ.get("CORTAI_EXPERIMENT_FEED_DISTRIBUTION_CONTROL")
        self.scheduler = SchedulerService(queue=InMemoryTaskQueue(), scheduler_id="sched-feed")

    def tearDown(self) -> None:
        if self.original_flag is None:
            os.environ.pop("CORTAI_EXPERIMENT_FEED_DISTRIBUTION_CONTROL", None)
            return
        os.environ["CORTAI_EXPERIMENT_FEED_DISTRIBUTION_CONTROL"] = self.original_flag

    def test_flag_off_preserves_original_order(self) -> None:
        os.environ["CORTAI_EXPERIMENT_FEED_DISTRIBUTION_CONTROL"] = "0"
        candidates = [
            {"video_id": "v1", "hook_type": "experiential", "visual_anchor": "door"},
            {"video_id": "v2", "hook_type": "inferential", "visual_anchor": "document"},
            {"video_id": "v3", "hook_type": "experiential", "visual_anchor": "device"},
        ]

        sequence, relaxation_count = self.scheduler.reorder_feed_candidates(candidates)

        self.assertEqual(sequence, candidates)
        self.assertEqual(relaxation_count, 0)

    def test_flag_on_reorders_only_when_needed(self) -> None:
        os.environ["CORTAI_EXPERIMENT_FEED_DISTRIBUTION_CONTROL"] = "1"
        candidates = [
            {"video_id": "v1", "hook_type": "experiential", "visual_anchor": "door"},
            {"video_id": "v2", "hook_type": "experiential", "visual_anchor": "door"},
            {"video_id": "v3", "hook_type": "inferential", "visual_anchor": "document"},
            {"video_id": "v4", "hook_type": "experiential", "visual_anchor": "device"},
        ]

        sequence, relaxation_count = self.scheduler.reorder_feed_candidates(candidates)

        self.assertEqual([item["video_id"] for item in sequence], ["v1", "v2", "v3", "v4"])
        self.assertEqual(relaxation_count, 0)

    def test_flag_on_moves_earliest_valid_candidate_when_loop_would_continue(self) -> None:
        os.environ["CORTAI_EXPERIMENT_FEED_DISTRIBUTION_CONTROL"] = "1"
        candidates = [
            {"video_id": "v1", "hook_type": "experiential", "visual_anchor": "door"},
            {"video_id": "v2", "hook_type": "experiential", "visual_anchor": "device"},
            {"video_id": "v3", "hook_type": "experiential", "visual_anchor": "door"},
            {"video_id": "v4", "hook_type": "inferential", "visual_anchor": "document"},
        ]

        sequence, relaxation_count = self.scheduler.reorder_feed_candidates(candidates)

        self.assertEqual([item["video_id"] for item in sequence], ["v1", "v2", "v4", "v3"])
        self.assertEqual(relaxation_count, 0)


if __name__ == "__main__":
    unittest.main()
