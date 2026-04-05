from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import ExperimentAssignment, ExperimentPlan, LearningInsights


@dataclass(frozen=True)
class ExperimentCapabilityInput:
    account_id: str
    niche: str
    topic: str
    publish_slot: str
    learning_insights: LearningInsights
    account_health_status: str = "SAFE"
    novelty_pressure_level: str = "low"
    recent_hold_or_reject_rate: float = 0.0
    recent_avg_overall_score: float = 0.0
    config_path: Path | None = None
    output_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["learning_insights"] = self.learning_insights.to_dict()
        for key, value in list(payload.items()):
            if isinstance(value, Path):
                payload[key] = str(value)
        return payload


@dataclass(frozen=True)
class ExperimentCapabilityResult:
    experiment_plan: ExperimentPlan
    experiment_assignment: ExperimentAssignment | None
    fallback: FallbackDecision
    experiment_result: dict[str, Any] | None = None
    decision_trace: dict[str, Any] = field(default_factory=dict)
    experiment_trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "experiment_plan": self.experiment_plan.to_dict(),
            "fallback": self.fallback.to_dict(),
        }
        if self.experiment_assignment is not None:
            payload["experiment_assignment"] = self.experiment_assignment.to_dict()
        if self.experiment_result is not None:
            payload["experiment_result"] = dict(self.experiment_result)
        if self.decision_trace:
            payload["decision_trace"] = dict(self.decision_trace)
        if self.experiment_trace:
            payload["experiment_trace"] = dict(self.experiment_trace)
        return payload
