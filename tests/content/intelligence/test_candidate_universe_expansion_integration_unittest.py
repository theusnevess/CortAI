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


class CandidateUniverseExpansionIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_flag = os.environ.get("CORTAI_EXPERIMENT_CANDIDATE_UNIVERSE_EXPANSION")
        self.scheduler = SchedulerService(queue=InMemoryTaskQueue(), scheduler_id="sched-expand")

    def tearDown(self) -> None:
        if self.original_flag is None:
            os.environ.pop("CORTAI_EXPERIMENT_CANDIDATE_UNIVERSE_EXPANSION", None)
            return
        os.environ["CORTAI_EXPERIMENT_CANDIDATE_UNIVERSE_EXPANSION"] = self.original_flag

    def test_flag_off_keeps_universe_unchanged(self) -> None:
        os.environ["CORTAI_EXPERIMENT_CANDIDATE_UNIVERSE_EXPANSION"] = "0"
        rows = [
            {"video_id": "v1", "hook_text": "THE BUNKER MAP WAS MISSING A CORRIDOR", "hook_type": "experiential", "visual_anchor": "document"}
        ]

        expanded, note = self.scheduler.expand_candidate_universe(rows)

        self.assertEqual(expanded[0]["hook_type"], "experiential")
        self.assertFalse(note["expansion_applied"])

    def test_flag_on_expands_metadata_only(self) -> None:
        os.environ["CORTAI_EXPERIMENT_CANDIDATE_UNIVERSE_EXPANSION"] = "1"
        rows = [
            {"video_id": "v1", "hook_text": "THE ARCHIVE LOG SHOWED AN UNAUTHORIZED OVERRIDE ON SERVER 9", "hook_type": "inferential", "visual_anchor": "document"}
        ]

        expanded, note = self.scheduler.expand_candidate_universe(rows)

        self.assertEqual(expanded[0]["hook_type"], "inferential")
        self.assertEqual(expanded[0]["visual_anchor"], "terminal_log")
        self.assertTrue(note["expansion_applied"])


if __name__ == "__main__":
    unittest.main()
