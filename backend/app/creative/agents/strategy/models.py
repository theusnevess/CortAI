from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.agents.novelty.models import NoveltyPressureProfile
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import LearningPolicy, PatternFindingSummary, StrategyProfile, TrendProfile


@dataclass(frozen=True)
class StrategyInput:
    account_id: str
    account_goal: str
    recent_metrics_summary: dict[str, Any] = field(default_factory=dict)
    health_status: str = "SAFE"
    recommended_constraints: dict[str, Any] = field(default_factory=dict)
    trend_profile: TrendProfile | None = None
    novelty_pressure_profile: NoveltyPressureProfile | None = None
    learning_policy: LearningPolicy | None = None
    pattern_findings_summary: tuple[PatternFindingSummary, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.trend_profile is not None:
            payload["trend_profile"] = self.trend_profile.to_dict()
        if self.novelty_pressure_profile is not None:
            payload["novelty_pressure_profile"] = self.novelty_pressure_profile.to_dict()
        if self.learning_policy is not None:
            payload["learning_policy"] = self.learning_policy.to_dict()
        payload["pattern_findings_summary"] = [item.to_dict() for item in self.pattern_findings_summary]
        return payload


@dataclass(frozen=True)
class StrategyResult:
    strategy_profile: StrategyProfile
    fallback: FallbackDecision
    decision_trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_profile": self.strategy_profile.to_dict(),
            "fallback": self.fallback.to_dict(),
            "decision_trace": dict(self.decision_trace),
        }
