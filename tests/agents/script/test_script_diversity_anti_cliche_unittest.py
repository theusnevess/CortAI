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
from app.creative.agents.script.diversity_analysis import ScriptDiversityAnalyzer
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


def _input() -> ScriptAgentInput:
    return ScriptAgentInput(
        account_id="acc_1",
        niche="horror",
        topic="archive door timestamp",
        account_health_status="SAFE",
    )


def _script(*, hook: str, setup: str, payoff: str) -> ScriptPlan:
    return ScriptPlan(hook=hook, setup=setup, payoff=payoff, generation_mode="test_structured")


class ScriptDiversityAntiClicheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = ScriptDiversityAnalyzer()

    def test_clean_specific_script_has_low_risks(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script(
                hook="The archive door logged a sealed warning",
                setup="A second timestamp appeared before the guard arrived",
                payoff="The final signature came from inside the locked room",
            ),
            data=_input(),
        ).to_dict()

        self.assertEqual(result["cliche_risk_level"], "low")
        self.assertEqual(result["repetition_risk_level"], "low")
        self.assertFalse(result["generic_phrase_detected"])
        self.assertFalse(result["structural_repetition_detected"])

    def test_generic_phrase_is_detected(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script(
                hook="You won't believe what happened next",
                setup="The archive log changed after midnight",
                payoff="The timestamp named the locked room",
            ),
            data=_input(),
        ).to_dict()

        self.assertTrue(result["generic_phrase_detected"])
        self.assertEqual(result["cliche_risk_level"], "high")
        self.assertIn("GENERIC_PHRASE_DETECTED", result["reason_codes"])

    def test_duplicate_blocks_create_high_repetition_risk(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script(
                hook="The archive door logged a sealed warning",
                setup="The archive door logged a sealed warning",
                payoff="The timestamp named the locked room",
            ),
            data=_input(),
        ).to_dict()

        self.assertTrue(result["structural_repetition_detected"])
        self.assertEqual(result["repetition_risk_level"], "high")
        self.assertIn("duplicate_hook_setup", result["evidence"]["duplicate_blocks"])

    def test_repeated_openings_are_detected(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script(
                hook="Archive door logged a sealed warning",
                setup="Archive door showed a second timestamp",
                payoff="Archive door hid the final signature",
            ),
            data=_input(),
        ).to_dict()

        self.assertTrue(result["structural_repetition_detected"])
        self.assertEqual(result["repetition_risk_level"], "high")
        self.assertTrue(result["evidence"]["repeated_openings"])

    def test_generic_cta_is_detected_inside_script_text(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script(
                hook="The archive door logged a sealed warning",
                setup="A second timestamp appeared before the guard arrived",
                payoff="The final signature came from inside the locked room follow for more",
            ),
            data=_input(),
        ).to_dict()

        self.assertTrue(result["generic_cta_detected"])
        self.assertEqual(result["cliche_risk_level"], "high")
        self.assertIn("GENERIC_CTA_DETECTED", result["reason_codes"])

    def test_analysis_scope_is_current_script_only(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script(
                hook="The archive door logged a sealed warning",
                setup="A second timestamp appeared before the guard arrived",
                payoff="The final signature came from inside the locked room",
            ),
            data=_input(),
        ).to_dict()

        self.assertEqual(result["evidence"]["analysis_scope"], "current_script_only")
        self.assertIn("NO_EXTERNAL_MEMORY_USED", result["reason_codes"])
        self.assertIn("NO_RANDOMNESS_USED", result["reason_codes"])

    def test_service_attaches_diversity_analysis_without_changing_output(self) -> None:
        plan = _script(
            hook="The archive door logged a sealed warning",
            setup="A second timestamp appeared before the guard arrived",
            payoff="The final signature came from inside the locked room",
        )
        service = ScriptAgentService(generator=_StructuredGenerator(plan))

        result = service.generate(_input())

        self.assertEqual(result.script_plan.hook, "THE ARCHIVE DOOR LOGGED A SEALED WARNING")
        self.assertIn("diversity_analysis", result.to_dict())
        self.assertIn("diversity_analysis", result.decision_trace)
        self.assertEqual(result.diversity_analysis["cliche_risk_level"], "low")

    def test_diversity_analysis_is_deterministic(self) -> None:
        plan = _script(
            hook="The archive door logged a sealed warning",
            setup="A second timestamp appeared before the guard arrived",
            payoff="The final signature came from inside the locked room",
        )

        first = self.analyzer.analyze(script_plan=plan, data=_input()).to_dict()
        second = self.analyzer.analyze(script_plan=plan, data=_input()).to_dict()

        self.assertEqual(first, second)

    def test_diversity_analysis_is_serializable(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script(
                hook="The archive door logged a sealed warning",
                setup="A second timestamp appeared before the guard arrived",
                payoff="The final signature came from inside the locked room",
            ),
            data=_input(),
        ).to_dict()

        encoded = json.dumps(result, sort_keys=True)

        self.assertIn("script_diversity_analysis_v2_6", encoded)

    def test_diversity_analysis_does_not_emit_rewrite_or_prediction_fields(self) -> None:
        result = self.analyzer.analyze(
            script_plan=_script(
                hook="The archive door logged a sealed warning",
                setup="A second timestamp appeared before the guard arrived",
                payoff="The final signature came from inside the locked room",
            ),
            data=_input(),
        ).to_dict()
        encoded = json.dumps(result).lower()

        self.assertNotIn("rewritten", encoded)
        self.assertNotIn("expected_performance", encoded)
        self.assertNotIn("prediction", encoded)
        self.assertNotIn("publishable", encoded)


if __name__ == "__main__":
    unittest.main()
