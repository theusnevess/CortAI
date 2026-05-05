from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class DecisionStatus(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    HOLD = "HOLD"
    ALLOW = "ALLOW"
    DELAY = "DELAY"
    BLOCK = "BLOCK"


class FallbackMode(str, Enum):
    NONE = "NONE"
    SAFE_DEFAULT = "SAFE_DEFAULT"
    LOCAL_DEFAULT = "LOCAL_DEFAULT"
    CONTROLLED_REJECT = "CONTROLLED_REJECT"


class FailureSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class AgentDecision:
    status: str
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AgentFailure:
    code: str
    message: str
    severity: str
    retryable: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FallbackDecision:
    used: bool
    mode: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
