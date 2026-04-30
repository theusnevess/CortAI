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
from app.creative.agents.script.provider_fallback_trace import ScriptProviderFallbackTracer
from app.creative.agents.script.service import ScriptAgentService
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import ScriptPlan


def _input() -> ScriptAgentInput:
    return ScriptAgentInput(
        account_id="acc_1",
        niche="horror",
        topic="archive door timestamp",
        account_health_status="SAFE",
    )


def _plan(mode: str = "groq_structured") -> ScriptPlan:
    return ScriptPlan(
        hook="The archive door logged a sealed warning",
        setup="A second timestamp appeared before the guard arrived",
        payoff="The final signature came from inside the locked room",
        generation_mode=mode,
    )


def _response(
    *,
    provider_used: str = "groq",
    model_used: str = "test-model",
    fallback: FallbackDecision | None = None,
    provider_attempt_trace: tuple[str, ...] = (),
    generation_mode: str = "groq_structured",
) -> ScriptGenerationResponse:
    plan = _plan(generation_mode)
    return ScriptGenerationResponse(
        script_plan=plan,
        payload=StructuredScriptPayload(
            hook=plan.hook,
            setup=plan.setup,
            payoff=plan.payoff,
            narrative_mode="official_warning",
        ),
        provider_used=provider_used,
        model_used=model_used,
        prompt_used="prompt",
        raw_output="{}",
        fallback=fallback or FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
        provider_attempt_trace=provider_attempt_trace,
    )


class _ResponseGenerator:
    def __init__(self, response: ScriptGenerationResponse) -> None:
        self.response = response

    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        return self.response


class _FailingGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        raise ScriptGenerationError("forced_provider_failure")


class ScriptProviderFallbackHonestyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tracer = ScriptProviderFallbackTracer()

    def test_provider_success_trace_exposes_provider_and_attempt_path(self) -> None:
        trace = self.tracer.from_generation(
            _response(
                provider_used="groq",
                model_used="llama-test",
                provider_attempt_trace=("ollama[1/1]:OLLAMA_GENERATION_FAILED",),
            ),
            _plan(),
        ).to_dict()

        self.assertEqual(trace["provider_used"], "groq")
        self.assertEqual(trace["model_used"], "llama-test")
        self.assertEqual(trace["provider_path"], ["ollama", "groq"])
        self.assertTrue(trace["provider_success"])
        self.assertFalse(trace["fallback_used"])
        self.assertEqual(trace["fallback_type"], "none")

    def test_generation_fallback_is_explicit_and_not_provider_success(self) -> None:
        trace = self.tracer.from_generation(
            _response(
                provider_used="fallback",
                model_used="deterministic",
                fallback=FallbackDecision(
                    used=True,
                    mode=FallbackMode.SAFE_DEFAULT.value,
                    reason="script_generation_contextual_fallback",
                ),
                provider_attempt_trace=("groq[1/2]:GROQ_API_KEY_MISSING", "ollama[1/1]:OLLAMA_GENERATION_FAILED"),
                generation_mode="fallback_contextual",
            ),
            _plan("fallback_contextual"),
        ).to_dict()

        self.assertFalse(trace["provider_success"])
        self.assertTrue(trace["fallback_used"])
        self.assertTrue(trace["safe_default_used"])
        self.assertTrue(trace["contextual_fallback_used"])
        self.assertEqual(trace["fallback_type"], "contextual_safe_default")
        self.assertEqual(len(trace["provider_failures"]), 2)

    def test_script_agent_exception_fallback_is_explicit(self) -> None:
        service = ScriptAgentService(generator=_FailingGenerator())

        result = service.generate(_input())

        trace = result.provider_fallback_trace
        self.assertTrue(result.fallback.used)
        self.assertFalse(trace["provider_success"])
        self.assertTrue(trace["fallback_used"])
        self.assertEqual(trace["provider_used"], "fallback")
        self.assertEqual(trace["provider_path"], ["script_agent_exception_fallback"])
        self.assertIn("forced_provider_failure", trace["provider_failures"][0])
        self.assertEqual(trace["fallback_type"], "contextual_safe_default")

    def test_repair_status_is_honest_when_not_reported(self) -> None:
        trace = self.tracer.from_generation(_response(), _plan()).to_dict()

        self.assertIsNone(trace["repair_applied"])
        self.assertEqual(trace["repair_status"], "not_reported_by_generator")

    def test_service_attaches_provider_fallback_trace_without_changing_script_output(self) -> None:
        service = ScriptAgentService(generator=_ResponseGenerator(_response(provider_used="ollama", model_used="qwen")))

        result = service.generate(_input())

        self.assertEqual(result.script_plan.hook, "THE ARCHIVE DOOR LOGGED A SEALED WARNING")
        self.assertIn("provider_fallback_trace", result.to_dict())
        self.assertIn("provider_fallback_trace", result.decision_trace)
        self.assertEqual(result.provider_fallback_trace["provider_used"], "ollama")
        self.assertFalse(result.provider_fallback_trace["fallback_used"])

    def test_provider_fallback_trace_is_deterministic(self) -> None:
        response = _response(provider_attempt_trace=("groq[1/2]:GROQ_EMPTY_RESPONSE",))

        first = self.tracer.from_generation(response, _plan()).to_dict()
        second = self.tracer.from_generation(response, _plan()).to_dict()

        self.assertEqual(first, second)

    def test_provider_fallback_trace_is_serializable(self) -> None:
        trace = self.tracer.from_generation(_response(), _plan()).to_dict()

        encoded = json.dumps(trace, sort_keys=True)

        self.assertIn("script_provider_fallback_trace_v2_6", encoded)

    def test_provider_fallback_trace_does_not_add_provider_or_order_policy(self) -> None:
        trace = self.tracer.from_generation(
            _response(provider_attempt_trace=("groq[1/2]:GROQ_EMPTY_RESPONSE",)),
            _plan(),
        ).to_dict()
        encoded = json.dumps(trace).lower()

        self.assertNotIn("provider_added", encoded)
        self.assertNotIn("provider_order_changed", encoded)
        self.assertNotIn("strategy", encoded)


if __name__ == "__main__":
    unittest.main()
