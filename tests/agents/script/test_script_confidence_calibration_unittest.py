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
from app.content.script_gen.service import ScriptGenerationError
from app.creative.agents.script.confidence_calibration import ScriptConfidenceCalibrator
from app.creative.agents.script.models import ScriptAgentInput
from app.creative.agents.script.service import ScriptAgentService
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import (
    ExperimentPlan,
    LearningInsights,
    ScriptPlan,
    StrategyProfile,
    TrendProfile,
)


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
            provider_used="groq",
            model_used="test-model",
            prompt_used="prompt",
            raw_output="{}",
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
            provider_attempt_trace=(),
        )


class _FailingGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        raise ScriptGenerationError("forced_provider_failure")


def _input(full: bool = True) -> ScriptAgentInput:
    if not full:
        return ScriptAgentInput(account_id="acc_1", niche="horror", topic="archive door timestamp")
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
        experiment_plan=ExperimentPlan(fallback_used=False),
    )


def _strong_script() -> ScriptPlan:
    return ScriptPlan(
        hook="The archive door logged a locked warning at midnight",
        setup="After the archive warning appeared, the signature moved toward the room",
        payoff="The final signature came from inside the locked archive room",
        generation_mode="test_structured",
    )


def _weak_script() -> ScriptPlan:
    return ScriptPlan(
        hook="You won't believe what happened next",
        setup="You won't believe what happened next",
        payoff="The truth was revealed and everything changed",
        generation_mode="test_structured",
    )


class ScriptConfidenceCalibrationTests(unittest.TestCase):
    def test_strong_provider_script_with_full_context_gets_high_confidence(self) -> None:
        service = ScriptAgentService(generator=_StructuredGenerator(_strong_script()))

        result = service.generate(_input(full=True))

        self.assertEqual(result.confidence_level, "high")
        self.assertGreaterEqual(result.confidence, 0.7)
        self.assertEqual(result.confidence_rationale["confidence_meaning"], "trust_in_script_construction")
        self.assertFalse(result.confidence_rationale["fallback_used"])

    def test_fallback_script_gets_medium_or_low_confidence_with_fallback_penalty(self) -> None:
        service = ScriptAgentService(generator=_FailingGenerator())

        result = service.generate(_input(full=False))

        self.assertIn(result.confidence_level, {"low", "medium"})
        self.assertLess(result.confidence, 0.7)
        self.assertIn("SCRIPT_FALLBACK_USED", result.confidence_rationale["penalties"])
        self.assertLess(result.confidence_components["fallback_penalty"], 1.0)

    def test_generic_repetitive_script_reduces_confidence(self) -> None:
        service = ScriptAgentService(generator=_StructuredGenerator(_weak_script()))

        result = service.generate(_input(full=True))

        self.assertIn(result.confidence_level, {"low", "medium"})
        self.assertLess(result.confidence_components["genericity_penalty"], 1.0)
        self.assertIn("GENERIC_HOOK_PRESENT", result.confidence_rationale["penalties"])
        self.assertIn("HIGH_CLICHE_RISK", result.confidence_rationale["penalties"])

    def test_missing_optional_context_reduces_context_component(self) -> None:
        service = ScriptAgentService(generator=_StructuredGenerator(_strong_script()))

        result = service.generate(_input(full=False))

        self.assertLess(result.confidence_components["context_completeness"], 1.0)
        self.assertGreater(result.confidence, 0.0)

    def test_confidence_components_are_complete(self) -> None:
        service = ScriptAgentService(generator=_StructuredGenerator(_strong_script()))

        result = service.generate(_input(full=True))

        self.assertEqual(
            set(result.confidence_components),
            {
                "context_completeness",
                "provider_reliability",
                "structure_integrity",
                "rubric_strength",
                "fallback_penalty",
                "genericity_penalty",
                "upstream_alignment",
            },
        )

    def test_confidence_is_not_constant_across_scenarios(self) -> None:
        strong = ScriptAgentService(generator=_StructuredGenerator(_strong_script())).generate(_input(full=True))
        weak = ScriptAgentService(generator=_StructuredGenerator(_weak_script())).generate(_input(full=True))
        fallback = ScriptAgentService(generator=_FailingGenerator()).generate(_input(full=False))

        self.assertGreater(len({strong.confidence, weak.confidence, fallback.confidence}), 1)

    def test_confidence_appears_in_result_and_decision_trace(self) -> None:
        service = ScriptAgentService(generator=_StructuredGenerator(_strong_script()))

        result = service.generate(_input(full=True))

        payload = result.to_dict()
        self.assertIn("confidence", payload)
        self.assertIn("confidence_level", payload)
        self.assertIn("confidence_components", payload)
        self.assertIn("confidence_rationale", payload)
        self.assertIn("confidence_calibration", result.decision_trace)

    def test_confidence_is_deterministic(self) -> None:
        service = ScriptAgentService(generator=_StructuredGenerator(_strong_script()))

        first = service.generate(_input(full=True)).to_dict()
        second = service.generate(_input(full=True)).to_dict()

        self.assertEqual(first["confidence"], second["confidence"])
        self.assertEqual(first["confidence_components"], second["confidence_components"])
        self.assertEqual(first["confidence_rationale"], second["confidence_rationale"])

    def test_confidence_is_serializable(self) -> None:
        service = ScriptAgentService(generator=_StructuredGenerator(_strong_script()))

        result = service.generate(_input(full=True))
        encoded = json.dumps(result.to_dict(), sort_keys=True)

        self.assertIn("script_confidence_calibration_v2_6", encoded)

    def test_confidence_does_not_emit_prediction_or_publishability_fields(self) -> None:
        service = ScriptAgentService(generator=_StructuredGenerator(_strong_script()))

        result = service.generate(_input(full=True))
        encoded = json.dumps(result.confidence_rationale).lower()

        self.assertNotIn("expected_performance", encoded)
        self.assertNotIn("prediction", encoded)
        self.assertNotIn("publishable", encoded)

    def test_calibrator_direct_use_is_deterministic(self) -> None:
        result = ScriptAgentService(generator=_StructuredGenerator(_strong_script())).generate(_input(full=True))
        calibrator = ScriptConfidenceCalibrator()

        first = calibrator.calibrate(
            context_governance=result.context_governance,
            quality_rubric=result.quality_rubric,
            hook_analysis=result.hook_analysis,
            setup_analysis=result.setup_analysis,
            payoff_analysis=result.payoff_analysis,
            diversity_analysis=result.diversity_analysis,
            provider_fallback_trace=result.provider_fallback_trace,
        ).to_dict()
        second = calibrator.calibrate(
            context_governance=result.context_governance,
            quality_rubric=result.quality_rubric,
            hook_analysis=result.hook_analysis,
            setup_analysis=result.setup_analysis,
            payoff_analysis=result.payoff_analysis,
            diversity_analysis=result.diversity_analysis,
            provider_fallback_trace=result.provider_fallback_trace,
        ).to_dict()

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
