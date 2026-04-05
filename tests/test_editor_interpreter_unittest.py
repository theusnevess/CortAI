from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.editor.interpreter import EditorInterpreter
from app.creative.contracts.creative_pack import (
    AssetBackgroundPlan,
    AssetPlan,
    AssetSegmentPlan,
    ScriptPlan,
    StrategyProfile,
    TrendProfile,
    VisualQuery,
    VoiceDeliveryProfile,
    VoicePlan,
    VoiceRuntimeConstraints,
    VoiceSegmentPlan,
)


class EditorInterpreterTests(unittest.TestCase):
    def _voice_plan(self) -> VoicePlan:
        return VoicePlan(
            provider="kokoro",
            voice_id="am_adam",
            style="investigative",
            delivery_profile=VoiceDeliveryProfile(overall_mode="investigative", overall_rate=1.0, overall_intensity="medium"),
            segments={
                "hook": VoiceSegmentPlan(rate=1.04, emphasis="high", pause_after_ms=140),
                "setup": VoiceSegmentPlan(rate=1.0, emphasis="medium", pause_after_ms=180),
                "payoff": VoiceSegmentPlan(rate=0.96, emphasis="high", pause_before_ms=120),
            },
            runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=["kokoro", "piper"]),
        )

    def _asset_plan(self) -> AssetPlan:
        return AssetPlan(
            visual_anchor="warning_display",
            semantic_pattern="active_signal",
            entity="intercom_panel",
            segments={
                "hook": AssetSegmentPlan(
                    background=AssetBackgroundPlan(source="local", path="assets/imports/pexels/warning_display/pexels_warning_display_panel_1.jpg"),
                    category="warning_display",
                    visual_query=VisualQuery(
                        subject="institutional intercom panel",
                        state_or_event="active red warning light",
                        environment="dark transit corridor",
                        lighting="cold fluorescent lighting",
                        framing="close-up",
                        mood="tense",
                        search_query_real="institutional intercom panel active red warning light",
                    ),
                ),
                "setup": AssetSegmentPlan(
                    background=AssetBackgroundPlan(source="local", path="assets/imports/pexels/intercom_recorder/pexels_intercom_panel_wall_13.jpg"),
                    category="institutional_space",
                    visual_query=VisualQuery(subject="corridor", state_or_event="hazard spill", environment="transit interior", lighting="cold fluorescent", framing="medium", mood="uneasy", search_query_real="corridor hazard spill"),
                ),
                "payoff": AssetSegmentPlan(
                    background=AssetBackgroundPlan(source="local", path="assets/imports/pexels/sealed_access/pexels_security_door_access_control_dark_4.jpg"),
                    category="sealed_access",
                    visual_query=VisualQuery(subject="restricted access door", state_or_event="broken seal", environment="institutional hallway", lighting="cold overhead light", framing="medium", mood="ominous", search_query_real="restricted access door broken seal"),
                ),
            },
        )

    def test_generates_operational_edit_plan(self) -> None:
        interpreter = EditorInterpreter()
        plan = interpreter.interpret(
            niche="true_crime",
            topic="camera blackout signal desync",
            script_plan=ScriptPlan(
                hook="Every camera on the lower level failed at the same second.",
                setup="One monitor kept running, but its timestamp started drifting backward.",
                payoff="Security found the manual override key still engaged.",
                generation_mode="test",
            ),
            voice_plan=self._voice_plan(),
            asset_plan=self._asset_plan(),
            strategy_profile=StrategyProfile(),
            trend_profile=TrendProfile(niche="true_crime"),
        )

        self.assertEqual(plan.caption_plan.timing_alignment_mode, "voice_segment_locked")
        self.assertTrue(plan.caption_plan.segment_caption_blocks["hook"])
        self.assertEqual(plan.caption_plan.caption_animation_mode, "progressive_word_reveal")
        self.assertEqual(plan.caption_plan.emphasis_animation_mode, "scale_pulse")
        self.assertTrue(plan.caption_plan.emphasis_timing_points)
        self.assertTrue(plan.music_plan.ducking_enabled)
        self.assertIn(plan.motion_plan.hook_motion_type, {"subtle_push", "slow_zoom_in"})
        self.assertEqual(plan.motion_plan.motion_intent, "narrative_attention")
        self.assertEqual(plan.transition_plan.setup_to_payoff_type, "crossfade")
        self.assertIn(plan.color_plan.grade_preset, {"institutional_cold", "device_alert_tense", "neutral_investigative"})
        self.assertTrue(plan.color_plan.atmosphere_profile)
        self.assertTrue(plan.timing_plan.emphasis_sync_points)
        self.assertEqual(plan.editor_version, "editor-agent-v2_2")
        self.assertIn("__", plan.editor_style_profile)
        self.assertGreater(plan.timing_plan.total_duration_s, 0.0)

    def test_variation_profile_produces_multiple_deterministic_styles(self) -> None:
        interpreter = EditorInterpreter()
        profiles = set()
        for topic in (
            "camera blackout signal desync",
            "archived intercom replay named locked floor",
            "sealed ward phone rang after shutdown",
            "missing corridor blueprint mismatch",
        ):
            plan = interpreter.interpret(
                niche="true_crime",
                topic=topic,
                script_plan=ScriptPlan(hook="A", setup="B", payoff="C", generation_mode="test"),
                voice_plan=self._voice_plan(),
                asset_plan=self._asset_plan(),
            )
            profiles.add(plan.editor_style_profile)

        self.assertGreaterEqual(len(profiles), 2)

    def test_strategy_profile_changes_editor_plan_deterministically(self) -> None:
        interpreter = EditorInterpreter()
        script_plan = ScriptPlan(
            hook="Every camera on the lower level failed at the same second.",
            setup="One monitor kept running, but its timestamp started drifting backward.",
            payoff="Security found the manual override key still engaged.",
            generation_mode="test",
        )
        conservative = interpreter.interpret(
            niche="true_crime",
            topic="camera blackout signal desync",
            script_plan=script_plan,
            voice_plan=self._voice_plan(),
            asset_plan=self._asset_plan(),
            strategy_profile=StrategyProfile(content_mode="conservative", target_duration_range="8-10s", variation_policy="low"),
            trend_profile=TrendProfile(niche="true_crime"),
        )
        exploratory = interpreter.interpret(
            niche="true_crime",
            topic="camera blackout signal desync",
            script_plan=script_plan,
            voice_plan=self._voice_plan(),
            asset_plan=self._asset_plan(),
            strategy_profile=StrategyProfile(content_mode="standard", target_duration_range="8-12s", variation_policy="medium"),
            trend_profile=TrendProfile(niche="true_crime"),
        )

        self.assertNotEqual(conservative.editor_style_profile, exploratory.editor_style_profile)
        self.assertNotEqual(conservative.caption_plan.caption_behavior_profile, exploratory.caption_plan.caption_behavior_profile)
        self.assertNotEqual(conservative.motion_plan.motion_behavior_profile, exploratory.motion_plan.motion_behavior_profile)
        self.assertNotEqual(conservative.transition_plan.hook_to_setup_duration_ms, exploratory.transition_plan.hook_to_setup_duration_ms)
        self.assertNotEqual(conservative.motion_plan.setup_motion_params, exploratory.motion_plan.setup_motion_params)


if __name__ == "__main__":
    unittest.main()
