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


class EditorExpressionAtmosphereTests(unittest.TestCase):
    def test_atmosphere_profiles_are_selected_from_context(self) -> None:
        interpreter = EditorInterpreter()
        voice_plan = VoicePlan(
            provider="kokoro",
            voice_id="af_heart",
            style="lowkey",
            delivery_profile=VoiceDeliveryProfile(overall_mode="immersive", overall_rate=0.95, overall_intensity="high"),
            segments={
                "hook": VoiceSegmentPlan(rate=1.02, emphasis="high"),
                "setup": VoiceSegmentPlan(rate=0.98, emphasis="medium"),
                "payoff": VoiceSegmentPlan(rate=0.94, emphasis="high"),
            },
            runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=["kokoro", "piper"]),
        )
        asset_plan = AssetPlan(
            visual_anchor="sealed_access",
            semantic_pattern="breach",
            entity="sealed_door",
            segments={
                "hook": AssetSegmentPlan(
                    background=AssetBackgroundPlan(source="local", path="hook.jpg"),
                    category="sealed_access",
                    visual_query=VisualQuery(
                        subject="sealed door",
                        state_or_event="broken tape",
                        environment="abandoned ward corridor",
                        lighting="low key fluorescent",
                        framing="medium",
                        mood="dread",
                        search_query_real="sealed door broken tape abandoned ward corridor",
                    ),
                ),
            },
        )

        plan = interpreter.interpret(
            niche="horror",
            topic="sealed room whisper phone rang inside",
            script_plan=ScriptPlan(
                hook="The phone rang inside the room that had been welded shut.",
                setup="Dust on the threshold showed a fresh drag mark.",
                payoff="The final ring stopped exactly when the seal tape snapped.",
                generation_mode="test",
            ),
            voice_plan=voice_plan,
            asset_plan=asset_plan,
        )

        self.assertEqual(plan.color_plan.atmosphere_behavior_profile, "lowkey_dread")
        self.assertEqual(plan.color_plan.polish_intensity, "high")
        self.assertTrue(plan.color_plan.atmosphere_profile)
        self.assertEqual(plan.editor_style_profile, "immersive_dread")


if __name__ == "__main__":
    unittest.main()
