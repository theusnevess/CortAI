from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.content.script_gen.models import ScriptGenerationResponse
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import ScriptPlan


SCRIPT_PROVIDER_FALLBACK_TRACE_VERSION = "script_provider_fallback_trace_v2_6"


@dataclass(frozen=True)
class ScriptProviderFallbackTrace:
    provider_path: list[str]
    provider_used: str
    model_used: str
    provider_success: bool
    provider_failures: list[str]
    repair_applied: bool | None
    repair_status: str
    fallback_used: bool
    fallback_mode: str | None
    fallback_reason: str | None
    fallback_type: str
    contextual_fallback_used: bool
    safe_default_used: bool
    generation_mode: str
    trace_version: str = SCRIPT_PROVIDER_FALLBACK_TRACE_VERSION
    rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_path": list(self.provider_path),
            "provider_used": self.provider_used,
            "model_used": self.model_used,
            "provider_success": self.provider_success,
            "provider_failures": list(self.provider_failures),
            "repair_applied": self.repair_applied,
            "repair_status": self.repair_status,
            "fallback_used": self.fallback_used,
            "fallback_mode": self.fallback_mode,
            "fallback_reason": self.fallback_reason,
            "fallback_type": self.fallback_type,
            "contextual_fallback_used": self.contextual_fallback_used,
            "safe_default_used": self.safe_default_used,
            "generation_mode": self.generation_mode,
            "trace_version": self.trace_version,
            "rationale": list(self.rationale),
        }


class ScriptProviderFallbackTracer:
    """Builds provider/fallback honesty trace without changing provider order or generation."""

    def from_generation(self, generation: ScriptGenerationResponse, script_plan: ScriptPlan) -> ScriptProviderFallbackTrace:
        fallback = generation.fallback
        provider_failures = list(generation.provider_attempt_trace)
        provider_used = str(generation.provider_used or "")
        provider_path = self._provider_path(provider_failures=provider_failures, provider_used=provider_used)
        fallback_used = bool(fallback.used)
        generation_mode = str(script_plan.generation_mode or generation.script_plan.generation_mode or "")
        fallback_type = self._fallback_type(
            fallback=fallback,
            generation_mode=generation_mode,
            provider_used=provider_used,
        )
        provider_success = not fallback_used and provider_used not in {"", "fallback"}
        rationale = [
            "Provider trace reflects metadata returned by the script generation service.",
            "Provider order is not modified by this trace.",
        ]
        if provider_failures:
            rationale.append("Provider failures are visible in provider_attempt_trace.")
        if fallback_used:
            rationale.append("Fallback is explicit and is not treated as provider success.")
        if provider_success:
            rationale.append("Provider generation succeeded without Script Agent fallback.")

        return ScriptProviderFallbackTrace(
            provider_path=provider_path,
            provider_used=provider_used,
            model_used=str(generation.model_used or ""),
            provider_success=provider_success,
            provider_failures=provider_failures,
            repair_applied=None,
            repair_status="not_reported_by_generator",
            fallback_used=fallback_used,
            fallback_mode=None if not fallback.mode else str(fallback.mode),
            fallback_reason=None if not fallback.reason else str(fallback.reason),
            fallback_type=fallback_type,
            contextual_fallback_used=fallback_type == "contextual_safe_default",
            safe_default_used=str(fallback.mode or "") == FallbackMode.SAFE_DEFAULT.value,
            generation_mode=generation_mode,
            rationale=rationale,
        )

    def from_exception(self, *, exc: ScriptGenerationErrorLike, fallback: FallbackDecision, script_plan: ScriptPlan) -> ScriptProviderFallbackTrace:
        failure = str(exc)
        generation_mode = str(script_plan.generation_mode or "")
        fallback_type = self._fallback_type(
            fallback=fallback,
            generation_mode=generation_mode,
            provider_used="fallback",
        )
        return ScriptProviderFallbackTrace(
            provider_path=["script_agent_exception_fallback"],
            provider_used="fallback",
            model_used="deterministic",
            provider_success=False,
            provider_failures=[failure] if failure else ["SCRIPT_GENERATION_ERROR"],
            repair_applied=None,
            repair_status="not_reported_by_generator",
            fallback_used=True,
            fallback_mode=str(fallback.mode or ""),
            fallback_reason=str(fallback.reason or ""),
            fallback_type=fallback_type,
            contextual_fallback_used=fallback_type == "contextual_safe_default",
            safe_default_used=str(fallback.mode or "") == FallbackMode.SAFE_DEFAULT.value,
            generation_mode=generation_mode,
            rationale=[
                "Script Agent caught ScriptGenerationError and used deterministic contextual fallback.",
                "Fallback is explicit and is not treated as provider success.",
                "Provider repair status is not reported by the current generator contract.",
            ],
        )

    def _provider_path(self, *, provider_failures: list[str], provider_used: str) -> list[str]:
        path: list[str] = []
        for failure in provider_failures:
            provider = str(failure).split("[", 1)[0].strip()
            if provider and provider not in path:
                path.append(provider)
        if provider_used and provider_used not in path:
            path.append(provider_used)
        return path

    def _fallback_type(self, *, fallback: FallbackDecision, generation_mode: str, provider_used: str) -> str:
        if not fallback.used:
            return "none"
        if generation_mode == "fallback_contextual":
            if str(fallback.mode or "") == FallbackMode.SAFE_DEFAULT.value:
                return "contextual_safe_default"
            return "contextual_fallback"
        if provider_used == "fallback":
            return "safe_default"
        return "fallback"


ScriptGenerationErrorLike = BaseException
