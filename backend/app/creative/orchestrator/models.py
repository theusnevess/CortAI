from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.creative.contracts.creative_pack import CreativePack
from app.creative.agents.video_qc.models import VideoQcResult


@dataclass(frozen=True)
class CreativePipelineExecution:
    creative_pack: CreativePack
    pipeline_output: dict[str, object]
    video_qc: VideoQcResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "creative_pack": self.creative_pack.to_dict(),
            "pipeline_output": self.pipeline_output,
            "video_qc": self.video_qc.to_dict(),
        }
