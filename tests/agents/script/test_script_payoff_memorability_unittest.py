from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.script_gen.models import ScriptGenerationResponse, StructuredScriptPayload
from app.creative.agents.script.models import ScriptAgentInput
from app.creative.agents.script.payoff_analysis import ScriptPayoffMemorabilityAnalyzer
from app.creative.agents.script.service import ScriptAgentService
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import ScriptPlan


class _StructuredGenerator:
    def __init__(self, script_plan: ScriptPlan) -> None:
        self.script_plan = script_plan

    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        return ScriptGenerationResponse(
            script_plan=self.script_plan,
            payload=StructuredScriptPayload(
                hook=self.script_plan.hook,
                setup=self.script_plan.setup,
                payoff=self.script_plan.payoff,
                narrative_mode="official_warning",
            ),
            provider_used="test",
            model_used="test",
            prompt_used="prompt",
            raw_output="{}",
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )


def _input(topic: str = "archive door timestamp") -> ScriptAgentInput:
    return ScriptAgentInput(
        account_id="acc_1",
        niche="horror",
        topic=topic,
        account_health_status="SAFE",
    )


def _script(payoff: str) -> ScriptPlan:
    return ScriptPlan(
        hook="The archive door logged a sealed warning",
        setup="After the archive warning appeared, the signature moved toward the room",
        payoff=payoff,
        generation_mode="test_structured",
    )


class ScriptPayoffMemorabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = ScriptPayoffMemorabilityAnalyzer()

    def test_specific_resolving_payoff_is_high_memorability(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("The final signature came from inside the locked archive room"),
            data=_input(),
        ).to_dict()

        self.assertTrue(result["payoff_present"])
        self.assertEqual(result["memorability_level"], "high")
        self.assertEqual(result["specificity_level"], "high")
        self.assertTrue(result["resolves_or_reframes_hook"])
        self.assertIn(result["resolution_mode"], {"resolve", "reframe", "resolve_and_reframe"})

    def test_generic_payoff_is_detected(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("The truth was revealed and everything changed"),
            data=_input(),
        ).to_dict()

        self.assertTrue(result["generic_payoff_detected"])
        self.assertEqual(result["memorability_level"], "low")
        self.assertIn("GENERIC_PAYOFF_DETECTED", result["reason_codes"])

    def test_vague_motivational_payoff_is_detected(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("Believe in success because life is amazing"),
            data=_input(),
        ).to_dict()

        self.assertTrue(result["vague_motivational_detected"])
        self.assertEqual(result["specificity_level"], "low")
        self.assertIn("VAGUE_MOTIVATIONAL_PAYOFF_DETECTED", result["reason_codes"])

    def test_payoff_that_repeats_hook_is_low(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("The archive door logged a sealed warning"),
            data=_input(),
        ).to_dict()

        self.assertEqual(result["resolution_mode"], "repeats_hook")
        self.assertEqual(result["memorability_level"], "low")
        self.assertIn("PAYOFF_REPEATS_HOOK", result["reason_codes"])

    def test_missing_payoff_is_low(self) -> None:
        result = self.analyzer.analyze(script_plan=_script(""), data=_input()).to_dict()

        self.assertFalse(result["payoff_present"])
        self.assertEqual(result["memorability_level"], "low")
        self.assertIn("PAYOFF_MISSING", result["reason_codes"])

    def test_specific_but_unresolved_payoff_is_medium(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("The camera timestamp showed server room nine"),
            data=_input(topic="camera timestamp"),
        ).to_dict()

        self.assertEqual(result["specificity_level"], "high")
        self.assertFalse(result["resolves_or_reframes_hook"])
        self.assertEqual(result["memorability_level"], "medium")

    def test_service_attaches_payoff_analysis_without_changing_output(self) -> None:
        plan = _script("The final signature came from inside the locked archive room")
        service = ScriptAgentService(generator=_StructuredGenerator(plan))

        result = service.generate(_input())

        self.assertEqual(
            result.script_plan.payoff,
            "THE FINAL SIGNATURE CAME FROM INSIDE THE LOCKED ARCHIVE ROOM",
        )
        self.assertIn("payoff_analysis", result.to_dict())
        self.assertIn("payoff_analysis", result.decision_trace)
        self.assertEqual(result.payoff_analysis["memorability_level"], "high")

    def test_payoff_analysis_is_deterministic(self) -> None:
        plan = _script("The final signature came from inside the locked archive room")

        first = self.analyzer.analyze(script_plan=plan, data=_input()).to_dict()
        second = self.analyzer.analyze(script_plan=plan, data=_input()).to_dict()

        self.assertEqual(first, second)

    def test_payoff_analysis_is_serializable(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("The final signature came from inside the locked archive room"),
            data=_input(),
        ).to_dict()

        encoded = json.dumps(result, sort_keys=True)

        self.assertIn("script_payoff_analysis_v2_6", encoded)

    def test_payoff_analysis_does_not_emit_rewrite_or_prediction_fields(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("The final signature came from inside the locked archive room"),
            data=_input(),
        ).to_dict()
        encoded = json.dumps(result).lower()

        self.assertNotIn("rewritten", encoded)
        self.assertNotIn("expected_performance", encoded)
        self.assertNotIn("prediction", encoded)
        self.assertNotIn("publishable", encoded)


if __name__ == "__main__":
    unittest.main()
