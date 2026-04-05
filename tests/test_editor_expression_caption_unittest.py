from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.editor.interpreter import EditorInterpreter
from app.content.pipeline.render import StubRenderAdapter
from app.content.screen_text.service import ScreenTextCue
from app.creative.contracts.edit_plan import CaptionPlan
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


class EditorExpressionCaptionTests(unittest.TestCase):
    def test_caption_expression_fields_are_populated(self) -> None:
        interpreter = EditorInterpreter()
        voice_plan = VoicePlan(
            provider="kokoro",
            voice_id="am_adam",
            style="investigative",
            delivery_profile=VoiceDeliveryProfile(overall_mode="investigative", overall_rate=1.0, overall_intensity="medium"),
            segments={
                "hook": VoiceSegmentPlan(rate=1.04, emphasis="high", pause_after_ms=160),
                "setup": VoiceSegmentPlan(rate=1.0, emphasis="medium", pause_after_ms=220),
                "payoff": VoiceSegmentPlan(rate=0.96, emphasis="high", pause_before_ms=140),
            },
            runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=["kokoro", "piper"]),
        )
        asset_plan = AssetPlan(
            visual_anchor="device",
            semantic_pattern="warning",
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
            topic="dispatch recording captured impossible reply",
            script_plan=ScriptPlan(
                hook="What answered after the line went dead?",
                setup="Dispatch replay found a second voice under the operator.",
                payoff="The reply named the exact locked floor before anyone said it.",
                generation_mode="test",
            ),
            voice_plan=voice_plan,
            asset_plan=asset_plan,
        )

        self.assertEqual(plan.caption_plan.caption_animation_mode, "progressive_word_reveal")
        self.assertEqual(plan.caption_plan.emphasis_animation_mode, "scale_pulse")
        self.assertTrue(plan.caption_plan.caption_behavior_profile.startswith("forensic_emphasis__"))
        self.assertTrue(plan.caption_plan.key_word_emphasis_rules)
        self.assertTrue(plan.caption_plan.emphasis_timing_points)
        self.assertIn("hook", plan.caption_plan.segment_caption_animation_profile)

    def test_key_words_receive_stronger_render_markup(self) -> None:
        interpreter = EditorInterpreter()
        plan = interpreter.interpret(
            niche="true_crime",
            topic="dispatch recording captured impossible reply",
            script_plan=ScriptPlan(
                hook="The intercom replied after the line went dead.",
                setup="Operators found the locked floor in the archived logs.",
                payoff="The reply named the sealed floor before dispatch said it.",
                generation_mode="test",
            ),
            voice_plan=VoicePlan(
                provider="kokoro",
                voice_id="am_adam",
                style="investigative",
                delivery_profile=VoiceDeliveryProfile(overall_mode="investigative", overall_rate=1.0, overall_intensity="medium"),
                segments={},
                runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=["kokoro", "piper"]),
            ),
            asset_plan=AssetPlan(visual_anchor="device"),
        )
        adapter = StubRenderAdapter()
        cue = ScreenTextCue(
            text="THE INTERCOM REPLIED",
            start=0.0,
            end=2.0,
            style_role="hook",
        )

        rendered = adapter._render_caption_text(cue, caption_plan=plan.caption_plan)  # noqa: SLF001

        self.assertIn(r"\fscx108", rendered)
        self.assertIn(r"\1c&H6CB1F3&", rendered)

    def test_payoff_last_caption_block_gets_more_landing_time(self) -> None:
        adapter = StubRenderAdapter()
        plan = CaptionPlan(
            segment_caption_blocks={
                "hook": ["ONE BLOCK"],
                "setup": ["SETUP BLOCK"],
                "payoff": ["THE DOOR OPENED", "FROM THE INSIDE"],
            }
        )
        cues = adapter._build_caption_cues(  # noqa: SLF001
            caption_plan=plan,
            segment_texts={"hook": "", "setup": "", "payoff": ""},
            timings=[(0.0, 2.0), (2.0, 5.0), (5.0, 9.0)],
        )
        payoff_cues = [cue for cue in cues if cue.style_role == "payoff"]

        self.assertEqual(len(payoff_cues), 2)
        first_duration = round(payoff_cues[0].end - payoff_cues[0].start, 2)
        second_duration = round(payoff_cues[1].end - payoff_cues[1].start, 2)
        self.assertGreater(second_duration, first_duration)


if __name__ == "__main__":
    unittest.main()
