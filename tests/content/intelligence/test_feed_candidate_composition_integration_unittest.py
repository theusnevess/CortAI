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


class FeedCandidateCompositionIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_flag = os.environ.get("CORTAI_EXPERIMENT_FEED_CANDIDATE_COMPOSITION")
        self.scheduler = SchedulerService(queue=InMemoryTaskQueue(), scheduler_id="sched-compose")

    def tearDown(self) -> None:
        if self.original_flag is None:
            os.environ.pop("CORTAI_EXPERIMENT_FEED_CANDIDATE_COMPOSITION", None)
            return
        os.environ["CORTAI_EXPERIMENT_FEED_CANDIDATE_COMPOSITION"] = self.original_flag

    def test_flag_off_preserves_pool_order(self) -> None:
        os.environ["CORTAI_EXPERIMENT_FEED_CANDIDATE_COMPOSITION"] = "0"
        candidates = [
            {"video_id": "v1", "hook_type": "experiential", "visual_anchor": "door"},
            {"video_id": "v2", "hook_type": "inferential", "visual_anchor": "document"},
            {"video_id": "v3", "hook_type": "experiential", "visual_anchor": "device"},
        ]

        composed, note = self.scheduler.compose_feed_candidates(candidates, target_size=2)

        self.assertEqual(composed, candidates[:2])
        self.assertEqual(note["reason"], "disabled")

    def test_flag_on_applies_composition_before_sequencing(self) -> None:
        os.environ["CORTAI_EXPERIMENT_FEED_CANDIDATE_COMPOSITION"] = "1"
        candidates = [
            {"video_id": "v1", "hook_type": "experiential", "visual_anchor": "door"},
            {"video_id": "v2", "hook_type": "experiential", "visual_anchor": "door"},
            {"video_id": "v3", "hook_type": "inferential", "visual_anchor": "document"},
            {"video_id": "v4", "hook_type": "inferential", "visual_anchor": "panel"},
        ]

        composed, note = self.scheduler.compose_feed_candidates(candidates, target_size=3)

        self.assertEqual([item["video_id"] for item in composed], ["v1", "v3", "v4"])
        self.assertFalse(note["composition_relaxed"])


if __name__ == "__main__":
    unittest.main()
