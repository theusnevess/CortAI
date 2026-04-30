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
from app.creative.agents.script.models import ScriptAgentInput
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.script.trace_auditability import ScriptTraceBuilder
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import (
    ExperimentPlan,
    LearningInsights,
    ScriptPlan,
    StrategyProfile,
    TrendProfile,
)


class _StructuredGenerator:
    def __init__(
        self,
        script_plan: ScriptPlan,
        *,
        fallback: FallbackDecision | None = None,
        provider_attempt_trace: tuple[str, ...] = (),
    ) -> None:
        self.script_plan = script_plan
        self.fallback = fallback or FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason="")
        self.provider_attempt_trace = provider_attempt_trace

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
            fallback=self.fallback,
            provider_attempt_trace=self.provider_attempt_trace,
        )


class _FailingGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        raise ScriptGenerationError("forced_provider_failure")


def _input(full: bool = True, degraded_trend: bool = False) -> ScriptAgentInput:
    if not full:
        return ScriptAgentInput(account_id="acc_1", niche="horror", topic="archive door timestamp")
    trend = TrendProfile(
        niche="horror",
        dominant_hooks=["archive warning"],
        trend_source="safe_default" if degraded_trend else "manual_curation",
        confidence_scores={"overall": 0.2 if degraded_trend else 0.84},
        sample_size=0 if degraded_trend else 10,
    )
    return ScriptAgentInput(
        account_id="acc_1",
        niche="horror",
        topic="archive door timestamp",
        account_health_status="SAFE",
        strategy_profile=StrategyProfile(goal="retention", hook_aggressiveness="high"),
        trend_profile=trend,
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


class ScriptTraceAuditabilityTests(unittest.TestCase):
    def test_script_trace_exists_in_result_and_payload(self) -> None:
        result = ScriptAgentService(generator=_StructuredGenerator(_strong_script())).generate(_input())

        self.assertIn("script_trace", result.to_dict())
        self.assertIn("audit_summary", result.script_trace)
        self.assertEqual(result.script_trace["trace_version"], "script_trace_auditability_v2_6")

    def test_script_trace_exists_in_decision_trace(self) -> None:
        result = ScriptAgentService(generator=_StructuredGenerator(_strong_script())).generate(_input())

        self.assertIn("script_trace", result.decision_trace)
        self.assertEqual(result.script_trace, result.decision_trace["script_trace"])

    def test_all_required_sections_are_present(self) -> None:
        result = ScriptAgentService(generator=_StructuredGenerator(_strong_script())).generate(_input())

        self.assertEqual(
            set(result.script_trace).issuperset(
                {
                    "context_governance",
                    "quality_rubric",
                    "hook_analysis",
                    "setup_analysis",
                    "payoff_analysis",
                    "diversity_analysis",
                    "provider_fallback_trace",
                    "confidence_calibration",
                    "final_script_rationale",
                    "missing_or_degraded_inputs",
                    "audit_summary",
                }
            ),
            True,
        )
        self.assertTrue(result.script_trace["audit_summary"]["required_sections_present"])

    def test_final_script_rationale_reconstructs_provider_success_path(self) -> None:
        result = ScriptAgentService(generator=_StructuredGenerator(_strong_script())).generate(_input())

        rationale = result.script_trace["final_script_rationale"]
        self.assertTrue(rationale["script_emitted"])
        self.assertEqual(rationale["provider_used"], "groq")
        self.assertFalse(rationale["fallback_used"])
        self.assertEqual(rationale["confidence_level"], result.confidence_level)
        self.assertIn("ScriptPlan was emitted", rationale["rationale"][0])

    def test_fallback_script_is_reconstructible_and_fallback_visible(self) -> None:
        result = ScriptAgentService(generator=_FailingGenerator()).generate(_input(full=False))

        rationale = result.script_trace["final_script_rationale"]
        self.assertTrue(rationale["fallback_used"])
        self.assertEqual(rationale["fallback_type"], "contextual_safe_default")
        self.assertTrue(result.script_trace["audit_summary"]["fallback_visible"])
        self.assertTrue(result.script_trace["audit_summary"]["reconstructible"])

    def test_missing_or_degraded_inputs_include_missing_context(self) -> None:
        result = ScriptAgentService(generator=_StructuredGenerator(_strong_script())).generate(_input(full=False))

        items = result.script_trace["missing_or_degraded_inputs"]

        self.assertIn("missing_context", {item["kind"] for item in items})
        self.assertTrue(any(item["identifier"] == "strategy_context" for item in items))

    def test_missing_or_degraded_inputs_include_degraded_context(self) -> None:
        result = ScriptAgentService(generator=_StructuredGenerator(_strong_script())).generate(
            _input(full=True, degraded_trend=True)
        )

        items = result.script_trace["missing_or_degraded_inputs"]

        self.assertIn("degraded_context", {item["kind"] for item in items})
        self.assertTrue(any(item["identifier"] == "trend_context" for item in items))

    def test_missing_or_degraded_inputs_include_provider_failure_and_fallback(self) -> None:
        result = ScriptAgentService(generator=_FailingGenerator()).generate(_input(full=False))

        kinds = {item["kind"] for item in result.script_trace["missing_or_degraded_inputs"]}

        self.assertIn("provider_failure", kinds)
        self.assertIn("fallback", kinds)

    def test_missing_or_degraded_inputs_include_generic_and_cliche_signals(self) -> None:
        result = ScriptAgentService(generator=_StructuredGenerator(_weak_script())).generate(_input())

        kinds = {item["kind"] for item in result.script_trace["missing_or_degraded_inputs"]}

        self.assertIn("generic_hook", kinds)
        self.assertIn("generic_payoff", kinds)
        self.assertIn("high_cliche_risk", kinds)
        self.assertIn("high_repetition_risk", kinds)

    def test_audit_summary_reconstructible_false_when_required_section_missing(self) -> None:
        result = ScriptAgentService(generator=_StructuredGenerator(_strong_script())).generate(_input())
        builder = ScriptTraceBuilder()

        trace = builder.build(
            script_plan=result.script_plan,
            fallback=result.fallback,
            context_governance=result.context_governance,
            quality_rubric={},
            hook_analysis=result.hook_analysis,
            setup_analysis=result.setup_analysis,
            payoff_analysis=result.payoff_analysis,
            diversity_analysis=result.diversity_analysis,
            provider_fallback_trace=result.provider_fallback_trace,
            confidence_calibration={
                "confidence": result.confidence,
                "confidence_level": result.confidence_level,
                "confidence_components": result.confidence_components,
                "confidence_rationale": result.confidence_rationale,
                "confidence_meaning": "trust_in_script_construction",
            },
        ).to_dict()

        self.assertFalse(trace["audit_summary"]["reconstructible"])
        self.assertIn("MISSING_SECTION:quality_rubric", trace["audit_summary"]["silent_failure_indicators"])

    def test_script_trace_is_deterministic(self) -> None:
        service = ScriptAgentService(generator=_StructuredGenerator(_strong_script()))

        first = service.generate(_input()).script_trace
        second = service.generate(_input()).script_trace

        self.assertEqual(first, second)

    def test_script_output_is_not_changed_by_trace(self) -> None:
        result = ScriptAgentService(generator=_StructuredGenerator(_strong_script())).generate(_input())

        self.assertEqual(result.script_plan.hook, "THE ARCHIVE DOOR LOGGED A LOCKED WARNING AT MIDNIGHT")
        self.assertEqual(
            result.script_plan.setup,
            "AFTER THE ARCHIVE WARNING APPEARED, THE SIGNATURE MOVED TOWARD THE ROOM",
        )
        self.assertEqual(result.script_plan.payoff, "THE FINAL SIGNATURE CAME FROM INSIDE THE LOCKED ARCHIVE ROOM")

    def test_decision_trace_remains_backward_compatible(self) -> None:
        result = ScriptAgentService(generator=_StructuredGenerator(_strong_script())).generate(_input())

        for key in {
            "context_governance",
            "quality_rubric",
            "hook_analysis",
            "setup_analysis",
            "payoff_analysis",
            "diversity_analysis",
            "provider_fallback_trace",
            "confidence_calibration",
        }:
            self.assertIn(key, result.decision_trace)
        self.assertTrue(result.script_trace["audit_summary"]["decision_trace_backward_compatible"])

    def test_script_trace_is_serializable(self) -> None:
        result = ScriptAgentService(generator=_StructuredGenerator(_strong_script())).generate(_input())

        encoded = json.dumps(result.to_dict(), sort_keys=True)

        self.assertIn("script_trace_auditability_v2_6", encoded)


if __name__ == "__main__":
    unittest.main()
