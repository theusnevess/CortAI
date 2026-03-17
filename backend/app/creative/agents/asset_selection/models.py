from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import AssetPlan as AssetSelection, StrategyProfile, TrendProfile


@dataclass(frozen=True)
class AssetSelectionInput:
    niche: str
    topic: str
    strategy_profile: StrategyProfile
    trend_profile: TrendProfile

    def to_dict(self) -> dict[str, Any]:
        return {
            "niche": self.niche,
            "topic": self.topic,
            "strategy_profile": self.strategy_profile.to_dict(),
            "trend_profile": self.trend_profile.to_dict(),
        }


@dataclass(frozen=True)
class AssetSelectionResult:
    asset_selection: AssetSelection
    fallback: FallbackDecision

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_selection": self.asset_selection.to_dict(),
            "fallback": self.fallback.to_dict(),
        }
