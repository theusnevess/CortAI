from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.runtime.queue import InMemoryTaskQueue
from app.runtime.scheduler.service import SchedulerService


class DialectFatigueControlIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_flag = os.environ.get("CORTAI_EXPERIMENT_DIALECT_FATIGUE_CONTROL")
        self.scheduler = SchedulerService(queue=InMemoryTaskQueue(), scheduler_id="sched-dialect")

    def tearDown(self) -> None:
        if self.original_flag is None:
            os.environ.pop("CORTAI_EXPERIMENT_DIALECT_FATIGUE_CONTROL", None)
            return
        os.environ["CORTAI_EXPERIMENT_DIALECT_FATIGUE_CONTROL"] = self.original_flag

    def test_flag_off_preserves_sequence(self) -> None:
        os.environ["CORTAI_EXPERIMENT_DIALECT_FATIGUE_CONTROL"] = "0"
        candidates = [
            {"video_id": "v1", "hook_type": "experiential"},
            {"video_id": "v2", "hook_type": "inferential"},
            {"video_id": "v3", "hook_type": "experiential"},
        ]

        controlled, note = self.scheduler.reorder_for_dialect_fatigue(candidates)

        self.assertEqual(controlled, candidates)
        self.assertFalse(note["dialect_control_relaxed"])

    def test_flag_on_reorders_by_hook_type_only(self) -> None:
        os.environ["CORTAI_EXPERIMENT_DIALECT_FATIGUE_CONTROL"] = "1"
        candidates = [
            {"video_id": "v1", "hook_type": "experiential"},
            {"video_id": "v2", "hook_type": "experiential"},
            {"video_id": "v3", "hook_type": "experiential"},
            {"video_id": "v4", "hook_type": "inferential"},
        ]

        controlled, _ = self.scheduler.reorder_for_dialect_fatigue(candidates)

        self.assertEqual([item["video_id"] for item in controlled], ["v1", "v2", "v4", "v3"])


if __name__ == "__main__":
    unittest.main()
