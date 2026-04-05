from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import LearningInsights, LearningPolicy, PatternFindingSummary


@dataclass(frozen=True)
class LearningAgentInput:
    account_id: str
    publish_records_path: Path | None = None
    video_metrics_path: Path | None = None
    analysis_dir: Path | None = None
    qc_events_path: Path | None = None
    execution_history_dir: Path | None = None
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
    learning_policy: LearningPolicy
    pattern_findings_summary: tuple[PatternFindingSummary, ...]
    fallback: FallbackDecision

    def to_dict(self) -> dict[str, Any]:
        return {
            "learning_insights": self.learning_insights.to_dict(),
            "learning_policy": self.learning_policy.to_dict(),
            "pattern_findings_summary": [item.to_dict() for item in self.pattern_findings_summary],
            "fallback": self.fallback.to_dict(),
        }
