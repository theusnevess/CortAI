from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import (
    ExperimentPlan,
    LearningInsights,
    ScriptPlan,
    StrategyProfile,
    TrendProfile,
)


@dataclass(frozen=True)
class ScriptGenerationContext:
    account_id: str
    niche: str
    topic: str
    account_health_status: str = "SAFE"
    strategy_profile: StrategyProfile | None = None
    trend_profile: TrendProfile | None = None
    learning_insights: LearningInsights | None = None
    experiment_plan: ExperimentPlan | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.strategy_profile is not None:
            payload["strategy_profile"] = self.strategy_profile.to_dict()
        if self.trend_profile is not None:
            payload["trend_profile"] = self.trend_profile.to_dict()
        if self.learning_insights is not None:
            payload["learning_insights"] = self.learning_insights.to_dict()
        if self.experiment_plan is not None:
            payload["experiment_plan"] = self.experiment_plan.to_dict()
        return payload


@dataclass(frozen=True)
class ScriptGenerationRequest:
    context: ScriptGenerationContext
    preferred_provider: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "context": self.context.to_dict(),
            "preferred_provider": self.preferred_provider,
        }


@dataclass(frozen=True)
class StructuredScriptPayload:
    hook: str
    setup: str
    payoff: str
    narrative_mode: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScriptGenerationResponse:
    script_plan: ScriptPlan
    payload: StructuredScriptPayload
    provider_used: str
    model_used: str
    prompt_used: str
    raw_output: str
    fallback: FallbackDecision
    provider_attempt_trace: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "script_plan": self.script_plan.to_dict(),
            "payload": self.payload.to_dict(),
            "provider_used": self.provider_used,
            "model_used": self.model_used,
            "prompt_used": self.prompt_used,
            "raw_output": self.raw_output,
            "fallback": self.fallback.to_dict(),
            "provider_attempt_trace": list(self.provider_attempt_trace),
        }
