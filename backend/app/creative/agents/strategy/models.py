from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import StrategyProfile


@dataclass(frozen=True)
class StrategyInput:
    account_id: str
    account_goal: str
    recent_metrics_summary: dict[str, Any] = field(default_factory=dict)
    health_status: str = "SAFE"
    recommended_constraints: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StrategyResult:
    strategy_profile: StrategyProfile
    fallback: FallbackDecision

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_profile": self.strategy_profile.to_dict(),
            "fallback": self.fallback.to_dict(),
        }
