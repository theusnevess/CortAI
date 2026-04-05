from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.runtime.scheduler.dialect_fatigue import reorder_by_hook_type, summarize_dialect_sequence


class DialectFatigueControlUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_flag = os.environ.get("CORTAI_EXPERIMENT_DIALECT_FATIGUE_CONTROL")
        os.environ["CORTAI_EXPERIMENT_DIALECT_FATIGUE_CONTROL"] = "1"

    def tearDown(self) -> None:
        if self.original_flag is None:
            os.environ.pop("CORTAI_EXPERIMENT_DIALECT_FATIGUE_CONTROL", None)
            return
        os.environ["CORTAI_EXPERIMENT_DIALECT_FATIGUE_CONTROL"] = self.original_flag

    def test_reduces_long_hook_type_blocks_when_pool_allows(self) -> None:
        candidates = [
            {"video_id": "v1", "hook_type": "experiential"},
            {"video_id": "v2", "hook_type": "experiential"},
            {"video_id": "v3", "hook_type": "experiential"},
            {"video_id": "v4", "hook_type": "inferential"},
            {"video_id": "v5", "hook_type": "inferential"},
            {"video_id": "v6", "hook_type": "experiential"},
        ]

        controlled, note = reorder_by_hook_type(candidates)
        metrics = summarize_dialect_sequence(controlled)

        self.assertLessEqual(metrics["max_consecutive_same_hook_type"], 2)
        self.assertFalse(note["dialect_control_relaxed"])

    def test_allows_partial_relaxation_when_pool_is_narrow(self) -> None:
        candidates = [
            {"video_id": "v1", "hook_type": "inferential"},
            {"video_id": "v2", "hook_type": "inferential"},
            {"video_id": "v3", "hook_type": "inferential"},
            {"video_id": "v4", "hook_type": "experiential"},
        ]

        controlled, note = reorder_by_hook_type(candidates)
        metrics = summarize_dialect_sequence(controlled)

        self.assertLessEqual(metrics["max_consecutive_same_hook_type"], 3)
        self.assertTrue(note["dialect_control_relaxed"] or metrics["max_consecutive_same_hook_type"] <= 2)

    def test_homogeneous_pool_does_not_deadlock(self) -> None:
        candidates = [
            {"video_id": "v1", "hook_type": "experiential"},
            {"video_id": "v2", "hook_type": "experiential"},
            {"video_id": "v3", "hook_type": "experiential"},
        ]

        controlled, note = reorder_by_hook_type(candidates)

        self.assertEqual([item["video_id"] for item in controlled], ["v1", "v2", "v3"])
        self.assertTrue(note["dialect_control_relaxed"])
        self.assertEqual(note["reason"], "insufficient_hook_type_diversity")
