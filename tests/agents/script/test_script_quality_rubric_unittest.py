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
from app.creative.agents.script.quality_rubric import ScriptQualityRubricEvaluator
from app.creative.agents.script.service import ScriptAgentService
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import (
    LearningInsights,
    ScriptPlan,
    StrategyProfile,
    TrendProfile,
)


REQUIRED_COMPONENTS = {
    "hook_clarity",
    "hook_specificity",
    "setup_coherence",
    "setup_progression",
    "payoff_specificity",
    "payoff_memorability",
    "cta_fit",
    "trend_alignment",
    "strategy_alignment",
    "repetition_risk",
    "cliche_risk",
}


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
        strategy_profile=StrategyProfile(goal="retention", hook_aggressiveness="high"),
        trend_profile=TrendProfile(
            niche="horror",
            dominant_hooks=["archive warning"],
            trend_source="manual_curation",
            confidence_scores={"overall": 0.84},
            sample_size=10,
        ),
        learning_insights=LearningInsights(
            recommended_hook_type="official_warning",
            recommendations=["avoid_cliche"],
            confidence=0.8,
        ),
    )


def _strong_script() -> ScriptPlan:
    return ScriptPlan(
        hook="The archive door logged a warning at midnight",
        setup="A second timestamp appeared before the guard arrived",
        payoff="The final signature came from inside the locked room",
        generation_mode="test_structured",
    )


class ScriptQualityRubricTests(unittest.TestCase):
    def setUp(self) -> None:
        self.evaluator = ScriptQualityRubricEvaluator()

    def test_rubric_includes_all_required_components(self) -> None:
        result = self.evaluator.evaluate(script_plan=_strong_script(), data=_input()).to_dict()

        self.assertEqual(set(result["components"]), REQUIRED_COMPONENTS)
        for component in result["components"].values():
            self.assertIn("score", component)
            self.assertIn("level", component)
            self.assertIn("reason_code", component)
            self.assertIn("evidence", component)
            self.assertIn("rationale", component)

    def test_strong_script_gets_high_overall_construction_score(self) -> None:
        result = self.evaluator.evaluate(script_plan=_strong_script(), data=_input()).to_dict()

        self.assertEqual(result["overall_level"], "high")
        self.assertGreaterEqual(result["overall_score"], 0.7)
        self.assertEqual(result["rubric_meaning"], "script_construction_quality_not_publishability")

    def test_generic_hook_is_low_specificity(self) -> None:
        script = ScriptPlan(
            hook="You won't believe what happened next",
            setup="The archive log changed after midnight",
            payoff="The timestamp named the locked room",
            generation_mode="test",
        )

        result = self.evaluator.evaluate(script_plan=script, data=_input()).to_dict()

        hook_specificity = result["components"]["hook_specificity"]
        self.assertEqual(hook_specificity["level"], "low")
        self.assertEqual(hook_specificity["reason_code"], "HOOK_GENERIC_PHRASE")

    def test_setup_repetition_is_detected(self) -> None:
        script = ScriptPlan(
            hook="The archive door logged a warning",
            setup="The archive door logged a warning",
            payoff="The final signature came from inside the room",
            generation_mode="test",
        )

        result = self.evaluator.evaluate(script_plan=script, data=_input()).to_dict()

        self.assertEqual(result["components"]["setup_coherence"]["reason_code"], "SETUP_DUPLICATES_OTHER_BLOCK")
        self.assertEqual(result["components"]["setup_progression"]["reason_code"], "SETUP_REPEATS_HOOK")

    def test_generic_payoff_reduces_payoff_specificity(self) -> None:
        script = ScriptPlan(
            hook="The archive door logged a warning",
            setup="A second timestamp appeared before the guard arrived",
            payoff="The truth was shocking and unbelievable",
            generation_mode="test",
        )

        result = self.evaluator.evaluate(script_plan=script, data=_input()).to_dict()

        self.assertEqual(result["components"]["payoff_specificity"]["level"], "low")
        self.assertIn("shocking", result["components"]["payoff_specificity"]["evidence"]["weak_terms"])

    def test_cta_missing_is_neutral_and_explicit(self) -> None:
        result = self.evaluator.evaluate(script_plan=_strong_script(), data=_input()).to_dict()

        cta = result["components"]["cta_fit"]
        self.assertEqual(cta["score"], 0.5)
        self.assertEqual(cta["level"], "medium")
        self.assertEqual(cta["reason_code"], "CTA_FIELD_NOT_PRESENT")
        self.assertIn("cta_fit", result["missing_components"])

    def test_trend_and_strategy_alignment_are_audit_only_components(self) -> None:
        result = self.evaluator.evaluate(script_plan=_strong_script(), data=_input()).to_dict()

        self.assertEqual(result["components"]["trend_alignment"]["reason_code"], "TREND_ALIGNMENT_VISIBLE")
        self.assertEqual(
            result["components"]["strategy_alignment"]["reason_code"],
            "STRATEGY_HOOK_AGGRESSIVENESS_ALIGNED",
        )
        self.assertIn("QC remains", result["boundary_statement"])

    def test_service_attaches_quality_rubric_without_changing_script_output(self) -> None:
        service = ScriptAgentService(generator=_StructuredGenerator(_strong_script()))

        result = service.generate(_input())

        self.assertEqual(result.script_plan.hook, "THE ARCHIVE DOOR LOGGED A WARNING AT MIDNIGHT")
        self.assertIn("quality_rubric", result.to_dict())
        self.assertIn("quality_rubric", result.decision_trace)
        self.assertEqual(set(result.quality_rubric["components"]), REQUIRED_COMPONENTS)

    def test_quality_rubric_is_deterministic(self) -> None:
        first = self.evaluator.evaluate(script_plan=_strong_script(), data=_input()).to_dict()
        second = self.evaluator.evaluate(script_plan=_strong_script(), data=_input()).to_dict()

        self.assertEqual(first, second)

    def test_quality_rubric_is_serializable(self) -> None:
        payload = self.evaluator.evaluate(script_plan=_strong_script(), data=_input()).to_dict()

        encoded = json.dumps(payload, sort_keys=True)

        self.assertIn("script_quality_rubric_v2_6", encoded)

    def test_rubric_does_not_emit_publishability_or_prediction_fields(self) -> None:
        result = self.evaluator.evaluate(script_plan=_strong_script(), data=_input()).to_dict()
        encoded = json.dumps(result).lower()

        self.assertNotIn("publishable", encoded)
        self.assertNotIn("expected_performance", encoded)
        self.assertNotIn("prediction", encoded)


if __name__ == "__main__":
    unittest.main()
