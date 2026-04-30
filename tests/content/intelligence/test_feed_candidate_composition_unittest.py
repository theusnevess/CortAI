from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.runtime.scheduler.feed_composition import compose_feed_candidates, summarize_candidate_pool


class FeedCandidateCompositionUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_flag = os.environ.get("CORTAI_EXPERIMENT_FEED_CANDIDATE_COMPOSITION")
        os.environ["CORTAI_EXPERIMENT_FEED_CANDIDATE_COMPOSITION"] = "1"

    def tearDown(self) -> None:
        if self.original_flag is None:
            os.environ.pop("CORTAI_EXPERIMENT_FEED_CANDIDATE_COMPOSITION", None)
            return
        os.environ["CORTAI_EXPERIMENT_FEED_CANDIDATE_COMPOSITION"] = self.original_flag

    def test_balances_hook_type_when_alternatives_exist(self) -> None:
        candidates = [
            {"video_id": "v1", "hook_type": "experiential", "visual_anchor": "door"},
            {"video_id": "v2", "hook_type": "experiential", "visual_anchor": "door"},
            {"video_id": "v3", "hook_type": "experiential", "visual_anchor": "device"},
            {"video_id": "v4", "hook_type": "inferential", "visual_anchor": "document"},
            {"video_id": "v5", "hook_type": "inferential", "visual_anchor": "panel"},
        ]

        composed, note = compose_feed_candidates(candidates, target_size=4)
        metrics = summarize_candidate_pool(composed)

        self.assertEqual(metrics["hook_type_balance"], {"experiential": 2, "inferential": 2})
        self.assertFalse(note["composition_relaxed"])

    def test_reduces_visual_anchor_dominance_when_possible(self) -> None:
        candidates = [
            {"video_id": "v1", "hook_type": "inferential", "visual_anchor": "document"},
            {"video_id": "v2", "hook_type": "inferential", "visual_anchor": "document"},
            {"video_id": "v3", "hook_type": "experiential", "visual_anchor": "door"},
            {"video_id": "v4", "hook_type": "experiential", "visual_anchor": "device"},
            {"video_id": "v5", "hook_type": "inferential", "visual_anchor": "panel"},
        ]

        composed, _ = compose_feed_candidates(candidates, target_size=4)
        metrics = summarize_candidate_pool(composed)

        self.assertLessEqual(metrics["dominant_visual_anchor_share"], 0.5)

    def test_homogeneous_pool_returns_relaxed_reason(self) -> None:
        candidates = [
            {"video_id": "v1", "hook_type": "experiential", "visual_anchor": "door"},
            {"video_id": "v2", "hook_type": "experiential", "visual_anchor": "door"},
            {"video_id": "v3", "hook_type": "experiential", "visual_anchor": "door"},
        ]

        composed, note = compose_feed_candidates(candidates, target_size=2)

        self.assertEqual(len(composed), 2)
        self.assertTrue(note["composition_relaxed"])
        self.assertEqual(note["reason"], "insufficient_hook_type_diversity")
