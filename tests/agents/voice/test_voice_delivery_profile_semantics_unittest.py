from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.voice.delivery_semantics import VoiceDeliverySemanticsMapper
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.contracts.creative_pack import (
    ScriptPlan,
    VoiceDeliveryProfile,
    VoicePlan,
    VoiceRuntimeConstraints,
    VoiceSegmentPlan,
)


def _script() -> ScriptPlan:
    return ScriptPlan(
        hook="The recording starts after the door locks itself",
        setup="Every timestamp before midnight disappears from the log",
        payoff="The final entry was written after the power failed",
        generation_mode="test_structured",
    )


class VoiceDeliveryProfileSemanticsTests(unittest.TestCase):
    def test_service_exposes_delivery_semantics_without_changing_voice_plan(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="true_crime", script_plan=_script())

        semantics = result.delivery_semantics

        self.assertEqual(semantics["semantics_version"], "voice_delivery_semantics_v2_6")
        self.assertEqual(result.voice_plan.provider, "kokoro")
        self.assertEqual(result.voice_plan.voice_id, "af_heart")
        self.assertEqual(result.voice_plan.runtime_constraints.fallback_order, ["kokoro", "piper"])
        self.assertFalse(result.fallback.used)

    def test_delivery_intent_explains_profile_style_rate_and_intensity(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="true_crime", script_plan=_script())

        delivery_intent = result.delivery_semantics["delivery_intent"]

        self.assertEqual(delivery_intent["style"], "investigative")
        self.assertEqual(delivery_intent["narrative_intent"], "evidence_led_tension")
        self.assertEqual(delivery_intent["rate_intent"], "measured")
        self.assertEqual(delivery_intent["intensity_intent"], "heightened_tension")

    def test_hook_setup_payoff_are_mapped_to_voice_roles(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        segment_semantics = result.delivery_semantics["segment_semantics"]

        self.assertEqual(segment_semantics["hook"]["script_role"], "attention_capture")
        self.assertEqual(segment_semantics["hook"]["voice_role"], "open_tension")
        self.assertEqual(segment_semantics["setup"]["script_role"], "context_bridge")
        self.assertEqual(segment_semantics["setup"]["voice_role"], "controlled_progression")
        self.assertEqual(segment_semantics["payoff"]["script_role"], "resolution_or_reframe")
        self.assertEqual(segment_semantics["payoff"]["voice_role"], "memorable_close")

    def test_hook_pause_and_payoff_pause_intents_are_explicit(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        segment_semantics = result.delivery_semantics["segment_semantics"]

        self.assertEqual(segment_semantics["hook"]["pause_intent"], "post_tension_space")
        self.assertEqual(segment_semantics["payoff"]["pause_intent"], "pre_landing_space")

    def test_empty_script_segment_degrades_semantic_support(self) -> None:
        script = ScriptPlan(
            hook="",
            setup="The setup remains usable",
            payoff="The payoff remains usable",
            generation_mode="test_structured",
        )

        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=script)

        semantics = result.delivery_semantics
        self.assertFalse(semantics["semantics_complete"])
        self.assertIn("script_plan.hook_empty", semantics["missing_or_degraded_inputs"])
        self.assertFalse(semantics["segment_semantics"]["hook"]["mapping_supported"])

    def test_invalid_segment_delivery_field_degrades_semantics(self) -> None:
        plan = VoicePlan(
            provider="kokoro",
            voice_id="af_heart",
            style="dark_calm",
            delivery_profile=VoiceDeliveryProfile(overall_mode="dark_calm", overall_rate=1.0, overall_intensity="medium"),
            segments={
                "hook": VoiceSegmentPlan(rate=0.0, emphasis=""),
                "setup": VoiceSegmentPlan(rate=1.0, emphasis="medium"),
                "payoff": VoiceSegmentPlan(rate=1.0, emphasis="high"),
            },
            runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=["kokoro", "piper"]),
        )

        semantics = VoiceDeliverySemanticsMapper().map(voice_plan=plan, script_plan=_script()).to_dict()

        self.assertFalse(semantics["semantics_complete"])
        self.assertIn("voice_plan.segments.hook.rate_invalid", semantics["missing_or_degraded_inputs"])
        self.assertIn("voice_plan.segments.hook.emphasis_empty", semantics["missing_or_degraded_inputs"])
        self.assertEqual(semantics["segment_semantics"]["hook"]["rate_intent"], "unknown")

    def test_missing_delivery_profile_is_visible_without_fabrication(self) -> None:
        plan = VoicePlan(
            provider="kokoro",
            voice_id="af_heart",
            style="dark_calm",
            delivery_profile=None,
            segments={
                "hook": VoiceSegmentPlan(rate=1.0, emphasis="high"),
                "setup": VoiceSegmentPlan(rate=1.0, emphasis="medium"),
                "payoff": VoiceSegmentPlan(rate=1.0, emphasis="high"),
            },
            runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=["kokoro", "piper"]),
        )

        semantics = VoiceDeliverySemanticsMapper().map(voice_plan=plan, script_plan=_script()).to_dict()

        self.assertFalse(semantics["semantics_complete"])
        self.assertIn("voice_plan.delivery_profile_missing", semantics["missing_or_degraded_inputs"])
        self.assertEqual(semantics["delivery_intent"]["rate_intent"], "unknown")

    def test_boundary_statement_keeps_semantics_out_of_synthesis(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="facts", script_plan=_script())

        self.assertEqual(
            result.delivery_semantics["boundary_statement"],
            "Voice explains delivery intent only; TTS Router performs synthesis.",
        )
        self.assertNotIn("tts_provider_executed", result.delivery_semantics)
        self.assertNotIn("confidence", result.delivery_semantics)

    def test_result_payload_remains_backward_compatible_and_serializable(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="facts", script_plan=_script())

        payload = result.to_dict()
        encoded = json.dumps(payload, sort_keys=True)

        self.assertIn("voice_plan", payload)
        self.assertIn("fallback", payload)
        self.assertIn("voice_plan_governance", payload)
        self.assertIn("delivery_semantics", payload)
        self.assertIn("voice_delivery_semantics_v2_6", encoded)

    def test_delivery_semantics_are_deterministic(self) -> None:
        service = VoiceAgentService()

        first = service.resolve(account_id="acc_1", niche="horror", script_plan=_script()).delivery_semantics
        second = service.resolve(account_id="acc_1", niche="horror", script_plan=_script()).delivery_semantics

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
