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
    VisualQuery,
    VoiceDeliveryProfile,
    VoicePlan,
    VoiceRuntimeConstraints,
    VoiceSegmentPlan,
)


class EditorExpressionMotionTests(unittest.TestCase):
    def test_motion_is_intent_driven_for_device_story(self) -> None:
        interpreter = EditorInterpreter()
        voice_plan = VoicePlan(
            provider="kokoro",
            voice_id="am_adam",
            style="investigative",
            delivery_profile=VoiceDeliveryProfile(overall_mode="investigative", overall_rate=1.0, overall_intensity="medium"),
            segments={
                "hook": VoiceSegmentPlan(rate=1.04, emphasis="high"),
                "setup": VoiceSegmentPlan(rate=1.0, emphasis="medium"),
                "payoff": VoiceSegmentPlan(rate=0.96, emphasis="high"),
            },
            runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=["kokoro", "piper"]),
        )
        asset_plan = AssetPlan(
            visual_anchor="warning_display",
            semantic_pattern="active_signal",
            entity="intercom",
            segments={
                "hook": AssetSegmentPlan(
                    background=AssetBackgroundPlan(source="local", path="hook.jpg"),
                    category="warning_display",
                    visual_query=VisualQuery(
                        subject="warning panel",
                        state_or_event="active alert",
                        environment="station corridor",
                        lighting="cold glow",
                        framing="close up",
                        mood="tense",
                        search_query_real="warning panel active alert station corridor",
                    ),
                ),
            },
        )

        plan = interpreter.interpret(
            niche="true_crime",
            topic="station intercom warning",
            script_plan=ScriptPlan(
                hook="The panel started flashing before the station alarms triggered.",
                setup="Operators found the corridor feed looping in reverse.",
                payoff="The breach marker moved after the system was shut down.",
                generation_mode="test",
            ),
            voice_plan=voice_plan,
            asset_plan=asset_plan,
        )

        self.assertEqual(plan.motion_plan.motion_intent, "narrative_attention")
        self.assertTrue(plan.motion_plan.motion_behavior_profile.startswith("tension_device_hold__"))
        self.assertEqual(plan.motion_plan.reveal_motion_profile, "push_reveal")
        self.assertIn(plan.motion_plan.hook_motion_type, {"slow_zoom_in", "subtle_push"})
        self.assertNotEqual(plan.motion_plan.hook_motion_type, plan.motion_plan.setup_motion_type)
        self.assertNotEqual(plan.motion_plan.setup_motion_params["scale_delta"], plan.motion_plan.payoff_motion_params["scale_delta"])


if __name__ == "__main__":
    unittest.main()
