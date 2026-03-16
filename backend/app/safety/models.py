from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class AccountMode(str, Enum):
    NORMAL = "NORMAL"
    SLOW_MODE = "SLOW_MODE"
    COOLDOWN = "COOLDOWN"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SafetyDecisionType(str, Enum):
    ALLOW = "ALLOW"
    DELAY = "DELAY"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class AccountSafetyState:
    account_id: str
    mode: AccountMode
    cooldown_until: str | None
    last_publish_at: str | None
    posts_last_hour: int
    posts_last_day: int
    risk_level: RiskLevel
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["mode"] = self.mode.value
        payload["risk_level"] = self.risk_level.value
        return payload


@dataclass(frozen=True)
class SafetyDecision:
    decision: SafetyDecisionType
    reason_code: str
    next_allowed_time: str | None
    cooldown_applied: str | None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["decision"] = self.decision.value
        return payload


@dataclass(frozen=True)
class RiskSignal:
    account_id: str
    risk_type: str
    severity: str
    ts: str
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
