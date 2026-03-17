from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision


class AccountHealthStatus(str, Enum):
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    HOLD = "HOLD"


@dataclass(frozen=True)
class AccountHealthInput:
    account_id: str
    recent_publish_count: int = 0
    recent_format_repetition_ratio: float = 0.0
    recent_views_drop_ratio: float = 0.0
    recent_low_performance_streak: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AccountHealthDecision:
    status: str
    reasons: list[str] = field(default_factory=list)
    recommended_constraints: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AccountHealthResult:
    decision: AccountHealthDecision
    fallback: FallbackDecision

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.to_dict(),
            "fallback": self.fallback.to_dict(),
        }
