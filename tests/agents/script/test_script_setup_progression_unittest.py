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
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.script.setup_analysis import ScriptSetupProgressionAnalyzer
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


def _script(setup: str) -> ScriptPlan:
    return ScriptPlan(
        hook="The archive door logged a sealed warning",
        setup=setup,
        payoff="The warning signature came from inside the archive room",
        generation_mode="test_structured",
    )


class ScriptSetupProgressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = ScriptSetupProgressionAnalyzer()

    def test_setup_connects_hook_to_payoff_with_high_progression(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("After the archive warning appeared, the signature moved toward the room"),
            data=_input(),
        ).to_dict()

        self.assertTrue(result["setup_present"])
        self.assertEqual(result["progression_level"], "high")
        self.assertTrue(result["connects_hook_to_payoff"])
        self.assertFalse(result["repetition_detected"])
        self.assertFalse(result["unsupported_context_detected"])
        self.assertIn("SETUP_CONNECTS_HOOK_TO_PAYOFF", result["reason_codes"])

    def test_repeated_hook_setup_is_detected(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("The archive door logged a sealed warning"),
            data=_input(),
        ).to_dict()

        self.assertTrue(result["repetition_detected"])
        self.assertEqual(result["progression_level"], "low")
        self.assertIn("SETUP_REPETITION_DETECTED", result["reason_codes"])

    def test_unsupported_context_is_detected(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("Scientists guaranteed a viral government alien signal"),
            data=_input(topic="archive door"),
        ).to_dict()

        self.assertTrue(result["unsupported_context_detected"])
        self.assertEqual(result["progression_level"], "low")
        self.assertIn("SETUP_UNSUPPORTED_CONTEXT_DETECTED", result["reason_codes"])

    def test_partial_connection_gets_medium_progression(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("The archive file changed after midnight"),
            data=_input(),
        ).to_dict()

        self.assertEqual(result["progression_level"], "medium")
        self.assertFalse(result["connects_hook_to_payoff"])
        self.assertIn("SETUP_CONNECTION_INCOMPLETE", result["reason_codes"])

    def test_missing_setup_gets_low_progression(self) -> None:
        result = self.analyzer.analyze(script_plan=_script(""), data=_input()).to_dict()

        self.assertFalse(result["setup_present"])
        self.assertEqual(result["progression_level"], "low")
        self.assertIn("SETUP_MISSING", result["reason_codes"])

    def test_service_attaches_setup_analysis_without_changing_output(self) -> None:
        plan = _script("After the archive warning appeared, the signature moved toward the room")
        service = ScriptAgentService(generator=_StructuredGenerator(plan))

        result = service.generate(_input())

        self.assertEqual(
            result.script_plan.setup,
            "AFTER THE ARCHIVE WARNING APPEARED, THE SIGNATURE MOVED TOWARD THE ROOM",
        )
        self.assertIn("setup_analysis", result.to_dict())
        self.assertIn("setup_analysis", result.decision_trace)
        self.assertEqual(result.setup_analysis["progression_level"], "high")

    def test_setup_analysis_is_deterministic(self) -> None:
        plan = _script("After the archive warning appeared, the signature moved toward the room")

        first = self.analyzer.analyze(script_plan=plan, data=_input()).to_dict()
        second = self.analyzer.analyze(script_plan=plan, data=_input()).to_dict()

        self.assertEqual(first, second)

    def test_setup_analysis_is_serializable(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("After the archive warning appeared, the signature moved toward the room"),
            data=_input(),
        ).to_dict()

        encoded = json.dumps(result, sort_keys=True)

        self.assertIn("script_setup_analysis_v2_6", encoded)

    def test_setup_analysis_does_not_emit_rewrite_or_prediction_fields(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script("After the archive warning appeared, the signature moved toward the room"),
            data=_input(),
        ).to_dict()
        encoded = json.dumps(result).lower()

        self.assertNotIn("rewritten", encoded)
        self.assertNotIn("expected_performance", encoded)
        self.assertNotIn("prediction", encoded)
        self.assertNotIn("publishable", encoded)


if __name__ == "__main__":
    unittest.main()
