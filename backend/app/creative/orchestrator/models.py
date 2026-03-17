from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.creative.agents.learning.models import LearningAgentResult
from app.creative.agents.asset_selection.models import AssetSelectionResult
from app.creative.agents.account_health.models import AccountHealthResult
from app.creative.agents.strategy.models import StrategyResult
from app.creative.agents.trend_analysis.models import TrendAnalysisResult
from app.creative.experiments.models import ExperimentCapabilityResult
from app.creative.contracts.creative_pack import CreativePack
from app.creative.agents.video_qc.models import VideoQcResult


@dataclass(frozen=True)
class CreativePipelineExecution:
    creative_pack: CreativePack | None
    pipeline_output: dict[str, object]
    video_qc: VideoQcResult | None
    account_health: AccountHealthResult | None = None
    trend_analysis: TrendAnalysisResult | None = None
    learning: LearningAgentResult | None = None
    strategy: StrategyResult | None = None
    experiment: ExperimentCapabilityResult | None = None
    asset_selection: AssetSelectionResult | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "pipeline_output": self.pipeline_output,
        }
        payload["creative_pack"] = None if self.creative_pack is None else self.creative_pack.to_dict()
        payload["video_qc"] = None if self.video_qc is None else self.video_qc.to_dict()
        payload["account_health"] = None if self.account_health is None else self.account_health.to_dict()
        payload["trend_analysis"] = None if self.trend_analysis is None else self.trend_analysis.to_dict()
        payload["learning"] = None if self.learning is None else self.learning.to_dict()
        payload["strategy"] = None if self.strategy is None else self.strategy.to_dict()
        payload["experiment"] = None if self.experiment is None else self.experiment.to_dict()
        payload["asset_selection"] = None if self.asset_selection is None else self.asset_selection.to_dict()
        return payload
