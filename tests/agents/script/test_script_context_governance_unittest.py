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
from app.creative.agents.script.context_governance import ScriptContextGovernanceEvaluator
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
    def generate_structured(self, request):  # noqa: ANN001
        self.last_request = request
        return ScriptGenerationResponse(
            script_plan=ScriptPlan(
                hook="The archive door answered at midnight.",
                setup="A second log appeared before the power failed.",
                payoff="The entry was signed by tomorrow's guard.",
                generation_mode="test_structured",
            ),
            payload=StructuredScriptPayload(
                hook="The archive door answered at midnight.",
                setup="A second log appeared before the power failed.",
                payoff="The entry was signed by tomorrow's guard.",
                narrative_mode="official_warning",
            ),
            provider_used="test",
            model_used="test",
            prompt_used="prompt",
            raw_output="{}",
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )


class _FailingGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        raise ScriptGenerationError("forced")


def _full_input() -> ScriptAgentInput:
    return ScriptAgentInput(
        account_id="acc_1",
        niche="horror",
        topic="archive door",
        account_health_status="SAFE",
        strategy_profile=StrategyProfile(goal="retention", content_mode="standard", hook_aggressiveness="high"),
        trend_profile=TrendProfile(
            niche="horror",
            dominant_hooks=["official_warning"],
            trend_source="manual_curation",
            confidence_scores={"overall": 0.82},
            sample_size=12,
        ),
        learning_insights=LearningInsights(
            recommended_hook_type="official_warning",
            recommendations=["avoid_cliche"],
            confidence=0.74,
        ),
        experiment_plan=ExperimentPlan(
            experiment_id="exp_1",
            variant_id="B",
            variant_type="narrative_mode",
            variant_params={"narrative_mode": "official_warning"},
            fallback_used=False,
        ),
    )


class ScriptContextGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.evaluator = ScriptContextGovernanceEvaluator()

    def test_maps_available_used_context_with_priority(self) -> None:
        result = self.evaluator.evaluate(_full_input()).to_dict()

        self.assertEqual(
            result["available_context"],
            [
                "account_health_context",
                "strategy_context",
                "experiment_context",
                "trend_context",
                "learning_context",
                "topic_context",
                "niche_context",
            ],
        )
        self.assertEqual(result["used_context"], result["available_context"])
        self.assertEqual(result["ignored_context"], [])
        self.assertTrue(result["policy_respected"])
        self.assertEqual(result["context_priority"][0]["context_key"], "account_health_context")
        self.assertEqual(result["context_signals"]["strategy_context"]["authority_level"], "control")
        self.assertEqual(result["context_signals"]["trend_context"]["authority_level"], "advisory")

    def test_missing_optional_context_is_visible_without_policy_failure(self) -> None:
        result = self.evaluator.evaluate(
            ScriptAgentInput(account_id="acc_1", niche="horror", topic="archive door", account_health_status="SAFE")
        ).to_dict()

        self.assertTrue(result["policy_respected"])
        self.assertIn("strategy_context", result["missing_context"])
        self.assertIn("trend_context", result["missing_context"])
        self.assertIn("learning_context", result["missing_context"])
        self.assertIn("experiment_context", result["missing_context"])
        self.assertNotIn("topic_context", result["missing_context"])

    def test_missing_required_context_marks_policy_not_respected(self) -> None:
        result = self.evaluator.evaluate(
            ScriptAgentInput(account_id="acc_1", niche="", topic="", account_health_status="")
        ).to_dict()

        self.assertFalse(result["policy_respected"])
        self.assertIn("topic_context", result["missing_context"])
        self.assertIn("niche_context", result["missing_context"])
        self.assertIn("account_health_context", result["missing_context"])

    def test_degraded_context_is_visible(self) -> None:
        result = self.evaluator.evaluate(
            ScriptAgentInput(
                account_id="acc_1",
                niche="horror",
                topic="archive door",
                account_health_status="UNKNOWN",
                trend_profile=TrendProfile(trend_source="safe_default", sample_size=0),
                learning_insights=LearningInsights(
                    confidence=0.2,
                    contamination_summary={"contaminated_evidence_rate": 0.5},
                ),
                experiment_plan=ExperimentPlan(fallback_used=True),
            )
        ).to_dict()

        self.assertIn("account_health_context", result["degraded_context"])
        self.assertIn("trend_context", result["degraded_context"])
        self.assertIn("learning_context", result["degraded_context"])
        self.assertIn("experiment_context", result["degraded_context"])
        self.assertEqual(
            result["context_signals"]["trend_context"]["reason_code"],
            "SCRIPT_CONTEXT_AVAILABLE_DEGRADED",
        )

    def test_service_attaches_context_governance_and_preserves_script_output(self) -> None:
        service = ScriptAgentService(generator=_StructuredGenerator())

        result = service.generate(_full_input())

        self.assertEqual(result.script_plan.hook, "THE ARCHIVE DOOR ANSWERED AT MIDNIGHT")
        self.assertFalse(result.fallback.used)
        self.assertIn("context_governance", result.to_dict())
        self.assertIn("context_governance", result.decision_trace)
        self.assertEqual(
            result.context_governance["context_signals"]["strategy_context"]["authority_level"],
            "control",
        )

    def test_fallback_path_still_emits_context_governance(self) -> None:
        service = ScriptAgentService(generator=_FailingGenerator())

        result = service.generate(
            ScriptAgentInput(
                account_id="acc_1",
                niche="true_crime",
                topic="sealed evidence room",
                account_health_status="CAUTION",
            )
        )

        self.assertTrue(result.fallback.used)
        self.assertEqual(result.script_plan.generation_mode, "fallback_contextual")
        self.assertIn("context_governance", result.decision_trace)
        self.assertIn("strategy_context", result.context_governance["missing_context"])

    def test_current_path_does_not_mark_available_context_ignored(self) -> None:
        result = self.evaluator.evaluate(_full_input()).to_dict()

        self.assertEqual(result["ignored_context"], [])
        self.assertTrue(
            set(result["available_context"]).issubset(set(result["used_context"]))
        )

    def test_context_governance_is_deterministic(self) -> None:
        first = self.evaluator.evaluate(_full_input()).to_dict()
        second = self.evaluator.evaluate(_full_input()).to_dict()

        self.assertEqual(first, second)

    def test_context_governance_is_serializable(self) -> None:
        payload = self.evaluator.evaluate(_full_input()).to_dict()

        encoded = json.dumps(payload, sort_keys=True)

        self.assertIn("script_context_governance_v2_6", encoded)

    def test_boundary_statement_keeps_script_out_of_strategy_authority(self) -> None:
        result = self.evaluator.evaluate(_full_input()).to_dict()

        self.assertEqual(
            result["boundary_statement"],
            "Script consumes upstream context to construct narrative; Strategy remains the control layer.",
        )
        self.assertNotIn("publisher", result["boundary_statement"].lower())


if __name__ == "__main__":
    unittest.main()
