from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import LearningInsights


@dataclass(frozen=True)
class LearningAgentInput:
    account_id: str
    publish_records_path: Path | None = None
    video_metrics_path: Path | None = None
    analysis_dir: Path | None = None
    output_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key, value in list(payload.items()):
            if isinstance(value, Path):
                payload[key] = str(value)
        return payload


@dataclass(frozen=True)
class LearningAgentResult:
    learning_insights: LearningInsights
    fallback: FallbackDecision

    def to_dict(self) -> dict[str, Any]:
        return {
            "learning_insights": self.learning_insights.to_dict(),
            "fallback": self.fallback.to_dict(),
        }
