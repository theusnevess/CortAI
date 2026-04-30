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
    telemetry_sources: list[dict[str, Any]] = field(default_factory=list)
    metric_window_summary: dict[str, Any] = field(default_factory=dict)
    qc_history_summary: dict[str, Any] = field(default_factory=dict)
    failure_history_summary: dict[str, Any] = field(default_factory=dict)
    format_repetition_summary: dict[str, Any] = field(default_factory=dict)
    telemetry_freshness: dict[str, Any] = field(default_factory=dict)

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
    input_summary: dict[str, Any] = field(default_factory=dict)
    decision_trace: dict[str, Any] = field(default_factory=dict)
    telemetry_summary: dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0
    risk_components: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    confidence_level: str = "low"
    confidence_components: dict[str, Any] = field(default_factory=dict)
    confidence_rationale: dict[str, Any] = field(default_factory=dict)
    temporal_health: dict[str, Any] = field(default_factory=dict)
    degraded_input_decision: dict[str, Any] = field(default_factory=dict)
    constraint_rationale: list[dict[str, Any]] = field(default_factory=list)
    health_trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.to_dict(),
            "fallback": self.fallback.to_dict(),
            "input_summary": dict(self.input_summary),
            "decision_trace": dict(self.decision_trace),
            "telemetry_summary": dict(self.telemetry_summary),
            "risk_score": float(self.risk_score),
            "risk_components": dict(self.risk_components),
            "confidence": float(self.confidence),
            "confidence_level": self.confidence_level,
            "confidence_components": dict(self.confidence_components),
            "confidence_rationale": dict(self.confidence_rationale),
            "temporal_health": dict(self.temporal_health),
            "degraded_input_decision": dict(self.degraded_input_decision),
            "constraint_rationale": [dict(item) for item in self.constraint_rationale],
            "health_trace": dict(self.health_trace),
        }
