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


class InvestigationStreamDialectDensityIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_flag = os.environ.get("CORTAI_EXPERIMENT_INVESTIGATION_DIALECT_DENSITY")
        self.scheduler = SchedulerService(queue=InMemoryTaskQueue(), scheduler_id="sched-investigation-density")

    def tearDown(self) -> None:
        if self.original_flag is None:
            os.environ.pop("CORTAI_EXPERIMENT_INVESTIGATION_DIALECT_DENSITY", None)
            return
        os.environ["CORTAI_EXPERIMENT_INVESTIGATION_DIALECT_DENSITY"] = self.original_flag

    def test_flag_off_preserves_sequence(self) -> None:
        os.environ["CORTAI_EXPERIMENT_INVESTIGATION_DIALECT_DENSITY"] = "0"
        candidates = [
            {"video_id": "v1", "stream_id": "investigation_stream", "hook_type": "inferential"},
            {"video_id": "v2", "stream_id": "investigation_stream", "hook_type": "inferential"},
            {"video_id": "v3", "stream_id": "investigation_stream", "hook_type": "experiential"},
        ]

        controlled, note = self.scheduler.reorder_investigation_stream_density(candidates)

        self.assertEqual(controlled, candidates)
        self.assertFalse(note["density_control_relaxed"])

    def test_flag_on_applies_local_density_control(self) -> None:
        os.environ["CORTAI_EXPERIMENT_INVESTIGATION_DIALECT_DENSITY"] = "1"
        candidates = [
            {"video_id": "v1", "stream_id": "investigation_stream", "hook_type": "inferential"},
            {"video_id": "v2", "stream_id": "investigation_stream", "hook_type": "inferential"},
            {"video_id": "v3", "stream_id": "investigation_stream", "hook_type": "inferential"},
            {"video_id": "v4", "stream_id": "investigation_stream", "hook_type": "experiential"},
            {"video_id": "v5", "stream_id": "investigation_stream", "hook_type": "inferential"},
        ]

        controlled, _ = self.scheduler.reorder_investigation_stream_density(candidates)

        self.assertEqual([item["video_id"] for item in controlled], ["v1", "v2", "v4", "v3", "v5"])


if __name__ == "__main__":
    unittest.main()
