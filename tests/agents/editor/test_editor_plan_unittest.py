from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.contracts.edit_plan import CaptionPlan, EditPlan, MusicPlan, TimingPlan


class EditPlanContractTests(unittest.TestCase):
    def test_serializes_and_deserializes_without_loss(self) -> None:
        plan = EditPlan(
            caption_plan=CaptionPlan(
                style_id="investigative_readable",
                max_words_per_block=4,
                emphasis_words=["BLACKOUT", "OVERRIDE"],
                emphasis_strength="high",
                emphasis_style="highlight_pulse",
                caption_animation_mode="progressive_word_reveal",
                segment_caption_blocks={"hook": ["THE CAMERA FAILED"], "setup": ["THE TIMESTAMP DRIFTED"], "payoff": ["THE KEY WAS ENGAGED"]},
            ),
            music_plan=MusicPlan(track_type="investigative_pulse", track_path_or_id="preset:investigative_pulse"),
            timing_plan=TimingPlan(
                hook_duration_s=2.5,
                setup_duration_s=3.1,
                payoff_duration_s=3.4,
                total_duration_s=9.0,
                cut_points=[2.5, 5.6],
                voice_sync_points=[0.0, 2.5, 5.6, 9.0],
                caption_sync_points=[0.0, 2.5, 5.6, 9.0],
                emphasis_sync_points=[0.9, 4.1, 8.2],
                transition_windows=[{"from": "hook", "to": "setup", "start": 2.3, "end": 2.5}],
            ),
            generated_at="2026-03-27T00:00:00Z",
            editor_version="editor-agent-v2_2",
            rationale="test",
            editor_style_profile="evidence_pressure",
        )

        payload = plan.to_dict()
        restored = EditPlan.from_dict(payload)

        self.assertEqual(restored.to_dict(), payload)
        self.assertEqual(restored.caption_plan.style_id, "investigative_readable")
        self.assertEqual(restored.caption_plan.caption_animation_mode, "progressive_word_reveal")
        self.assertEqual(restored.music_plan.track_path_or_id, "preset:investigative_pulse")
        self.assertEqual(restored.timing_plan.cut_points, [2.5, 5.6])
        self.assertEqual(restored.timing_plan.emphasis_sync_points, [0.9, 4.1, 8.2])
        self.assertEqual(restored.editor_style_profile, "evidence_pressure")


if __name__ == "__main__":
    unittest.main()
