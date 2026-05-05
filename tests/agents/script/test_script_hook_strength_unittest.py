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
from app.creative.agents.script.hook_analysis import ScriptHookStrengthAnalyzer
from app.creative.agents.script.models import ScriptAgentInput
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


def _script(hook: str) -> ScriptPlan:
    return ScriptPlan(
        hook=hook,
        setup="A second timestamp appeared before the guard arrived",
        payoff="The final signature came from inside the locked room",
        generation_mode="test_structured",
    )


class ScriptHookStrengthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = ScriptHookStrengthAnalyzer()

    def test_strong_specific_tense_hook_is_high_strength(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("The archive door logged a locked warning at midnight"),
            data=_input(),
        ).to_dict()

        self.assertTrue(result["hook_present"])
        self.assertEqual(result["strength_level"], "high")
        self.assertTrue(result["tension_detected"])
        self.assertEqual(result["specificity_level"], "high")
        self.assertFalse(result["generic_hook_detected"])
        self.assertFalse(result["unsupported_claim_detected"])

    def test_generic_hook_is_detected_and_low_strength(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("You won't believe what happened next"),
            data=_input(),
        ).to_dict()

        self.assertEqual(result["strength_level"], "low")
        self.assertTrue(result["generic_hook_detected"])
        self.assertIn("GENERIC_HOOK_DETECTED", result["reason_codes"])

    def test_missing_tension_is_visible(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("The archive door log showed timestamp data"),
            data=_input(),
        ).to_dict()

        self.assertIn("HOOK_TENSION_WEAK", result["reason_codes"])
        self.assertFalse(result["tension_detected"])
        self.assertIn(result["strength_level"], {"medium", "low"})

    def test_unsupported_claim_is_detected(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("Scientists confirmed the biggest secret"),
            data=_input(topic="archive door"),
        ).to_dict()

        self.assertTrue(result["unsupported_claim_detected"])
        self.assertEqual(result["strength_level"], "low")
        self.assertIn("UNSUPPORTED_CLAIM_DETECTED", result["reason_codes"])

    def test_claim_with_direct_evidence_terms_is_not_marked_unsupported(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("The archive log confirmed a sealed warning"),
            data=_input(topic="archive log"),
        ).to_dict()

        self.assertFalse(result["unsupported_claim_detected"])
        self.assertIn("HOOK_TENSION_PRESENT", result["reason_codes"])

    def test_missing_hook_gets_low_strength(self) -> None:
        result = self.analyzer.analyze(script_plan=_script(""), data=_input()).to_dict()

        self.assertFalse(result["hook_present"])
        self.assertEqual(result["strength_level"], "low")
        self.assertIn("HOOK_MISSING", result["reason_codes"])

    def test_service_attaches_hook_analysis_without_changing_output(self) -> None:
        plan = _script("The archive door logged a locked warning at midnight")
        service = ScriptAgentService(generator=_StructuredGenerator(plan))

        result = service.generate(_input())

        self.assertEqual(result.script_plan.hook, "THE ARCHIVE DOOR LOGGED A LOCKED WARNING AT MIDNIGHT")
        self.assertIn("hook_analysis", result.to_dict())
        self.assertIn("hook_analysis", result.decision_trace)
        self.assertEqual(result.hook_analysis["strength_level"], "high")

    def test_hook_analysis_is_deterministic(self) -> None:
        plan = _script("The archive door logged a locked warning at midnight")

        first = self.analyzer.analyze(script_plan=plan, data=_input()).to_dict()
        second = self.analyzer.analyze(script_plan=plan, data=_input()).to_dict()

        self.assertEqual(first, second)

    def test_hook_analysis_is_serializable(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("The archive door logged a locked warning at midnight"),
            data=_input(),
        ).to_dict()

        encoded = json.dumps(result, sort_keys=True)

        self.assertIn("script_hook_analysis_v2_6", encoded)

    def test_hook_analysis_does_not_emit_rewrite_or_prediction_fields(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("The archive door logged a locked warning at midnight"),
            data=_input(),
        ).to_dict()
        encoded = json.dumps(result).lower()

        self.assertNotIn("rewritten", encoded)
        self.assertNotIn("expected_performance", encoded)
        self.assertNotIn("prediction", encoded)
        self.assertNotIn("publishable", encoded)


if __name__ == "__main__":
    unittest.main()
