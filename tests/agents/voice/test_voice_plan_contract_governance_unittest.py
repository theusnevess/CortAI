from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.voice.service import VoiceAgentService
from app.creative.agents.voice.voice_plan_governance import VoicePlanGovernanceEvaluator
from app.creative.contracts.creative_pack import (
    ScriptPlan,
    StrategyProfile,
    VoiceDeliveryProfile,
    VoicePlan,
    VoiceRuntimeConstraints,
    VoiceSegmentPlan,
)


def _script() -> ScriptPlan:
    return ScriptPlan(
        hook="The archive door logged a locked warning",
        setup="The warning moved after the second camera failed",
        payoff="The final timestamp came from inside the room",
        generation_mode="test_structured",
    )


class VoicePlanContractGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_service_exposes_requested_provider_voice_style_and_fallback_order(self) -> None:
        result = VoiceAgentService().resolve(
            account_id="acc_1",
            niche="true_crime",
            script_plan=_script(),
            strategy_profile=StrategyProfile(content_mode="standard"),
        )

        governance = result.voice_plan_governance

        self.assertEqual(governance["contract_version"], "voice_plan_governance_v2_6")
        self.assertEqual(governance["provider_requested"], "kokoro")
        self.assertEqual(governance["voice_id_requested"], "af_heart")
        self.assertEqual(governance["style_requested"], "investigative")
        self.assertEqual(governance["fallback_order"], ["kokoro", "piper"])
        self.assertTrue(governance["fallback_allowed"])

    def test_delivery_profile_and_all_required_segments_are_complete(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        governance = result.voice_plan_governance

        self.assertTrue(governance["delivery_profile_complete"])
        self.assertEqual(governance["segments_present"], ["hook", "setup", "payoff"])
        self.assertTrue(governance["contract_complete"])
        self.assertTrue(governance["policy_respected"])
        for segment in ("hook", "setup", "payoff"):
            self.assertTrue(governance["segment_completeness"][segment]["complete"])

    def test_missing_fields_are_visible_without_fabrication(self) -> None:
        plan = VoicePlan(
            provider="",
            voice_id="",
            style="",
            delivery_profile=VoiceDeliveryProfile(overall_mode="", overall_rate=0.0, overall_intensity=""),
            segments={},
            runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=[]),
        )

        governance = VoicePlanGovernanceEvaluator().evaluate(voice_plan=plan).to_dict()

        self.assertFalse(governance["contract_complete"])
        self.assertFalse(governance["policy_respected"])
        self.assertIn("voice_plan.runtime_constraints.fallback_order", governance["missing_fields"])
        self.assertIn("voice_plan.segments.hook", governance["missing_fields"])
        self.assertIn("voice_plan.provider_empty", governance["degraded_fields"])
        self.assertIn("voice_plan.voice_id_empty", governance["degraded_fields"])
        self.assertIn("voice_plan.style_empty", governance["degraded_fields"])
        self.assertIn("voice_plan.fallback_order_empty", governance["degraded_fields"])
        self.assertIn("voice_plan.delivery_profile.overall_rate_invalid", governance["degraded_fields"])
        self.assertFalse(governance["fallback_order_non_empty"])
        self.assertFalse(governance["fallback_policy_coherent"])

    def test_degraded_provider_order_is_visible_but_not_rewritten(self) -> None:
        plan = VoicePlan(
            provider="piper",
            voice_id="piper.onnx",
            style="dark_calm",
            delivery_profile=VoiceDeliveryProfile(overall_mode="dark_calm", overall_rate=1.0, overall_intensity="medium"),
            segments={
                "hook": VoiceSegmentPlan(rate=1.0, emphasis="high"),
                "setup": VoiceSegmentPlan(rate=1.0, emphasis="medium"),
                "payoff": VoiceSegmentPlan(rate=1.0, emphasis="high"),
            },
            runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=["piper"]),
        )

        governance = VoicePlanGovernanceEvaluator().evaluate(voice_plan=plan).to_dict()

        self.assertEqual(governance["provider_requested"], "piper")
        self.assertEqual(governance["fallback_order"], ["piper"])
        self.assertIn("voice_plan.provider_not_current_primary", governance["degraded_fields"])
        self.assertIn("voice_plan.fallback_order_primary_not_first", governance["degraded_fields"])
        self.assertIn("voice_plan.fallback_allowed_without_fallback_provider", governance["degraded_fields"])
        self.assertTrue(governance["provider_in_fallback_order"])
        self.assertFalse(governance["fallback_policy_coherent"])
        self.assertFalse(governance["policy_respected"])

    def test_single_kokoro_fallback_order_is_degraded_because_no_real_fallback_exists(self) -> None:
        plan = VoicePlan(
            provider="kokoro",
            voice_id="af_heart",
            style="dark_calm",
            delivery_profile=VoiceDeliveryProfile(overall_mode="dark_calm", overall_rate=1.0, overall_intensity="medium"),
            segments={
                "hook": VoiceSegmentPlan(rate=1.0, emphasis="high"),
                "setup": VoiceSegmentPlan(rate=1.0, emphasis="medium"),
                "payoff": VoiceSegmentPlan(rate=1.0, emphasis="high"),
            },
            runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=["kokoro"]),
        )

        governance = VoicePlanGovernanceEvaluator().evaluate(voice_plan=plan).to_dict()

        self.assertTrue(governance["provider_in_fallback_order"])
        self.assertFalse(governance["fallback_policy_coherent"])
        self.assertIn("voice_plan.fallback_order_missing_piper", governance["degraded_fields"])
        self.assertIn("voice_plan.fallback_allowed_without_fallback_provider", governance["degraded_fields"])
        self.assertFalse(governance["contract_complete"])

    def test_requested_provider_must_be_present_in_fallback_order(self) -> None:
        plan = VoicePlan(
            provider="kokoro",
            voice_id="af_heart",
            style="dark_calm",
            delivery_profile=VoiceDeliveryProfile(overall_mode="dark_calm", overall_rate=1.0, overall_intensity="medium"),
            segments={
                "hook": VoiceSegmentPlan(rate=1.0, emphasis="high"),
                "setup": VoiceSegmentPlan(rate=1.0, emphasis="medium"),
                "payoff": VoiceSegmentPlan(rate=1.0, emphasis="high"),
            },
            runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=False, fallback_order=["piper"]),
        )

        governance = VoicePlanGovernanceEvaluator().evaluate(voice_plan=plan).to_dict()

        self.assertFalse(governance["provider_in_fallback_order"])
        self.assertIn("voice_plan.provider_not_in_fallback_order", governance["degraded_fields"])
        self.assertIn("voice_plan.fallback_order_primary_not_first", governance["degraded_fields"])
        self.assertFalse(governance["contract_complete"])

    def test_fallback_allowed_must_match_fallback_order_depth(self) -> None:
        plan = VoicePlan(
            provider="kokoro",
            voice_id="af_heart",
            style="dark_calm",
            delivery_profile=VoiceDeliveryProfile(overall_mode="dark_calm", overall_rate=1.0, overall_intensity="medium"),
            segments={
                "hook": VoiceSegmentPlan(rate=1.0, emphasis="high"),
                "setup": VoiceSegmentPlan(rate=1.0, emphasis="medium"),
                "payoff": VoiceSegmentPlan(rate=1.0, emphasis="high"),
            },
            runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=False, fallback_order=["kokoro", "piper"]),
        )

        governance = VoicePlanGovernanceEvaluator().evaluate(voice_plan=plan).to_dict()

        self.assertFalse(governance["fallback_policy_coherent"])
        self.assertIn("voice_plan.fallback_disabled_with_fallback_order", governance["degraded_fields"])
        self.assertFalse(governance["contract_complete"])

    def test_present_but_invalid_segment_fields_are_degraded(self) -> None:
        plan = VoicePlan(
            provider="kokoro",
            voice_id="af_heart",
            style="dark_calm",
            delivery_profile=VoiceDeliveryProfile(overall_mode="dark_calm", overall_rate=1.0, overall_intensity="medium"),
            segments={
                "hook": VoiceSegmentPlan(rate=None, emphasis=""),
                "setup": VoiceSegmentPlan(rate=1.0, emphasis="medium"),
                "payoff": VoiceSegmentPlan(rate=1.0, emphasis="high"),
            },
            runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=["kokoro", "piper"]),
        )

        governance = VoicePlanGovernanceEvaluator().evaluate(voice_plan=plan).to_dict()

        self.assertIn("voice_plan.segments.hook.rate_invalid", governance["degraded_fields"])
        self.assertIn("voice_plan.segments.hook.emphasis_empty", governance["degraded_fields"])
        self.assertFalse(governance["segment_completeness"]["hook"]["complete"])
        self.assertFalse(governance["contract_complete"])

    def test_present_but_non_segment_object_is_degraded(self) -> None:
        plan = VoicePlan(
            provider="kokoro",
            voice_id="af_heart",
            style="dark_calm",
            delivery_profile=VoiceDeliveryProfile(overall_mode="dark_calm", overall_rate=1.0, overall_intensity="medium"),
            segments={
                "hook": "",
                "setup": VoiceSegmentPlan(rate=1.0, emphasis="medium"),
                "payoff": VoiceSegmentPlan(rate=1.0, emphasis="high"),
            },
            runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=["kokoro", "piper"]),
        )

        governance = VoicePlanGovernanceEvaluator().evaluate(voice_plan=plan).to_dict()

        self.assertIn("voice_plan.segments.hook.segment_invalid", governance["degraded_fields"])
        self.assertFalse(governance["segment_completeness"]["hook"]["complete"])
        self.assertFalse(governance["contract_complete"])

    def test_delivery_profile_values_must_be_usable(self) -> None:
        plan = VoicePlan(
            provider="kokoro",
            voice_id="af_heart",
            style="dark_calm",
            delivery_profile=VoiceDeliveryProfile(overall_mode="", overall_rate=None, overall_intensity=""),
            segments={
                "hook": VoiceSegmentPlan(rate=1.0, emphasis="high"),
                "setup": VoiceSegmentPlan(rate=1.0, emphasis="medium"),
                "payoff": VoiceSegmentPlan(rate=1.0, emphasis="high"),
            },
            runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=["kokoro", "piper"]),
        )

        governance = VoicePlanGovernanceEvaluator().evaluate(voice_plan=plan).to_dict()

        self.assertFalse(governance["delivery_profile_complete"])
        self.assertIn("voice_plan.delivery_profile.overall_mode_empty", governance["degraded_fields"])
        self.assertIn("voice_plan.delivery_profile.overall_rate_invalid", governance["degraded_fields"])
        self.assertIn("voice_plan.delivery_profile.overall_intensity_empty", governance["degraded_fields"])
        self.assertFalse(governance["contract_complete"])

    def test_negative_segment_pause_is_degraded(self) -> None:
        plan = VoicePlan(
            provider="kokoro",
            voice_id="af_heart",
            style="dark_calm",
            delivery_profile=VoiceDeliveryProfile(overall_mode="dark_calm", overall_rate=1.0, overall_intensity="medium"),
            segments={
                "hook": VoiceSegmentPlan(rate=1.0, emphasis="high", pause_after_ms=-1),
                "setup": VoiceSegmentPlan(rate=1.0, emphasis="medium"),
                "payoff": VoiceSegmentPlan(rate=1.0, emphasis="high"),
            },
            runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=["kokoro", "piper"]),
        )

        governance = VoicePlanGovernanceEvaluator().evaluate(voice_plan=plan).to_dict()

        self.assertIn("voice_plan.segments.hook.pause_after_ms_negative", governance["degraded_fields"])
        self.assertFalse(governance["policy_respected"])

    def test_boundary_statement_keeps_voice_planning_separate_from_tts_execution(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        governance = result.voice_plan_governance

        self.assertEqual(governance["boundary_statement"], "Voice plans delivery only; TTS Router executes providers.")
        self.assertFalse(governance["execution_boundary"]["voice_agent_executes_tts"])
        self.assertTrue(governance["execution_boundary"]["tts_router_executes_provider"])
        self.assertFalse(governance["execution_boundary"]["executed_provider_reported_by_voice_agent"])

    def test_governance_appears_in_result_payload(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        payload = result.to_dict()

        self.assertIn("voice_plan_governance", payload)
        self.assertEqual(payload["voice_plan_governance"], result.voice_plan_governance)

    def test_existing_voice_plan_output_is_preserved(self) -> None:
        os.environ["CORTAI_PREMIUM_TTS_PROVIDER"] = "elevenlabs"
        os.environ["CORTAI_PREMIUM_TTS_VOICE"] = "adam"

        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        self.assertEqual(result.voice_plan.provider, "kokoro")
        self.assertEqual(result.voice_plan.voice_id, "af_heart")
        self.assertEqual(result.voice_plan.runtime_constraints.fallback_order, ["kokoro", "piper"])
        self.assertFalse(result.fallback.used)

    def test_governance_is_deterministic(self) -> None:
        service = VoiceAgentService()

        first = service.resolve(account_id="acc_1", niche="horror", script_plan=_script()).voice_plan_governance
        second = service.resolve(account_id="acc_1", niche="horror", script_plan=_script()).voice_plan_governance

        self.assertEqual(first, second)

    def test_governance_is_serializable(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        encoded = json.dumps(result.to_dict(), sort_keys=True)

        self.assertIn("voice_plan_governance_v2_6", encoded)


if __name__ == "__main__":
    unittest.main()
