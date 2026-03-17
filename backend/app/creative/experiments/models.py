from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import ExperimentPlan, LearningInsights


@dataclass(frozen=True)
class ExperimentCapabilityInput:
    account_id: str
    niche: str
    topic: str
    publish_slot: str
    learning_insights: LearningInsights
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
    fallback: FallbackDecision

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_plan": self.experiment_plan.to_dict(),
            "fallback": self.fallback.to_dict(),
        }
