from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import TrendProfile


@dataclass(frozen=True)
class TrendAnalysisInput:
    niche: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrendAnalysisResult:
    trend_profile: TrendProfile
    fallback: FallbackDecision

    def to_dict(self) -> dict[str, Any]:
        return {
            "trend_profile": self.trend_profile.to_dict(),
            "fallback": self.fallback.to_dict(),
        }
