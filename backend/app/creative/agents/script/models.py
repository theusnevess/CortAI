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
class ScriptAgentInput:
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
class ScriptAgentResult:
    script_plan: ScriptPlan
    fallback: FallbackDecision
    context_governance: dict[str, Any] = field(default_factory=dict)
    quality_rubric: dict[str, Any] = field(default_factory=dict)
    hook_analysis: dict[str, Any] = field(default_factory=dict)
    setup_analysis: dict[str, Any] = field(default_factory=dict)
    payoff_analysis: dict[str, Any] = field(default_factory=dict)
    diversity_analysis: dict[str, Any] = field(default_factory=dict)
    provider_fallback_trace: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    confidence_level: str = "low"
    confidence_components: dict[str, float] = field(default_factory=dict)
    confidence_rationale: dict[str, Any] = field(default_factory=dict)
    script_trace: dict[str, Any] = field(default_factory=dict)
    decision_trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "script_plan": self.script_plan.to_dict(),
            "fallback": self.fallback.to_dict(),
            "context_governance": dict(self.context_governance),
            "quality_rubric": dict(self.quality_rubric),
            "hook_analysis": dict(self.hook_analysis),
            "setup_analysis": dict(self.setup_analysis),
            "payoff_analysis": dict(self.payoff_analysis),
            "diversity_analysis": dict(self.diversity_analysis),
            "provider_fallback_trace": dict(self.provider_fallback_trace),
            "confidence": self.confidence,
            "confidence_level": self.confidence_level,
            "confidence_components": dict(self.confidence_components),
            "confidence_rationale": dict(self.confidence_rationale),
            "script_trace": dict(self.script_trace),
            "decision_trace": dict(self.decision_trace),
        }
