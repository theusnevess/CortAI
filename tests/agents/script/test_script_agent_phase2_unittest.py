from __future__ import annotations

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
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import ExperimentPlan, LearningInsights, ScriptPlan, StrategyProfile, TrendProfile


class _FailingGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        raise ScriptGenerationError("boom")


class _CapturingGenerator:
    def __init__(self) -> None:
        self.last_request = None

    def generate_structured(self, request):  # noqa: ANN001
        self.last_request = request
        return ScriptGenerationResponse(
            script_plan=ScriptPlan(
                hook="Someone wrote on the mirror tonight.",
                setup="The warning named the night guard directly.",
                payoff="The door locked after the second knock.",
                generation_mode="groq_structured",
            ),
            payload=StructuredScriptPayload(
                hook="Someone wrote on the mirror tonight.",
                setup="The warning named the night guard directly.",
                payoff="The door locked after the second knock.",
                narrative_mode="official_warning",
            ),
            provider_used="groq",
            model_used="llama-3.3-70b-versatile",
            prompt_used="prompt",
            raw_output='{"hook":"x"}',
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )


class ScriptAgentPhase2Tests(unittest.TestCase):
    def test_generates_contextual_script_plan_with_structured_provider_output(self) -> None:
        generator = _CapturingGenerator()
        service = ScriptAgentService(generator=generator)

        result = service.generate(
            ScriptAgentInput(
                account_id="acc_1",
                niche="horror",
                topic="mirror warning",
                account_health_status="SAFE",
                strategy_profile=StrategyProfile(goal="retention", content_mode="standard", hook_aggressiveness="high"),
                trend_profile=TrendProfile(niche="horror", dominant_hooks=["official_warning"], pacing="fast_first_3s"),
                learning_insights=LearningInsights(recommended_hook_type="official_warning", recommendations=["avoid_cliche"]),
                experiment_plan=ExperimentPlan(experiment_id="exp_1", variant_id="B", variant_type="narrative_mode", variant_params={"narrative_mode": "official_warning"}, fallback_used=False),
            )
        )

        self.assertEqual(result.script_plan.hook, "SOMEONE WROTE ON THE MIRROR TONIGHT")
        self.assertEqual(result.script_plan.setup, "THE WARNING NAMED THE NIGHT GUARD DIRECTLY")
        self.assertEqual(result.script_plan.payoff, "THE DOOR LOCKED AFTER THE SECOND KNOCK")
        self.assertEqual(result.script_plan.generation_mode, "groq_structured")
        self.assertFalse(result.fallback.used)
        self.assertIsNotNone(generator.last_request)
        self.assertEqual(generator.last_request.context.strategy_profile.hook_aggressiveness, "high")
        self.assertEqual(generator.last_request.context.trend_profile.dominant_hooks[0], "official_warning")
        self.assertEqual(generator.last_request.context.learning_insights.recommended_hook_type, "official_warning")
        self.assertEqual(generator.last_request.context.experiment_plan.variant_params["narrative_mode"], "official_warning")

    def test_falls_back_to_contextual_default_when_generation_fails(self) -> None:
        service = ScriptAgentService(generator=_FailingGenerator())

        result = service.generate(
            ScriptAgentInput(
                account_id="acc_1",
                niche="true_crime",
                topic="sealed evidence room",
                experiment_plan=ExperimentPlan(variant_params={"narrative_mode": "official_warning"}),
            )
        )

        self.assertTrue(result.fallback.used)
        self.assertEqual(result.fallback.reason, "script_generation_contextual_fallback")
        self.assertEqual(result.script_plan.generation_mode, "fallback_contextual")
        self.assertIn("LOCKED EVIDENCE ROOM", result.script_plan.hook)
        self.assertTrue(result.script_plan.setup)
        self.assertTrue(result.script_plan.payoff)


if __name__ == "__main__":
    unittest.main()
