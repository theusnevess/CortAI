from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import TrendEvidenceReference, TrendProfile


@dataclass(frozen=True)
class TrendAnalysisInput:
    niche: str
    account_id: str = ""
    region: str = "US"
    allow_cached: bool = True
    force_refresh: bool = False
    current_time: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrendAnalysisResult:
    trend_profile: TrendProfile
    fallback: FallbackDecision
    validation_summary: dict[str, Any]
    collector_trace: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "trend_profile": self.trend_profile.to_dict(),
            "fallback": self.fallback.to_dict(),
            "validation_summary": dict(self.validation_summary),
            "collector_trace": dict(self.collector_trace),
        }


@dataclass(frozen=True)
class TrendSourceRecord:
    source: str
    niche: str
    region: str = "US"
    collected_at: str = ""
    sample_size: int = 0
    dominant_hooks: list[str] = field(default_factory=list)
    avg_duration: str = ""
    pacing: str = ""
    visual_style: str = ""
    text_style: str = ""
    evidence: list[TrendEvidenceReference] = field(default_factory=list)
    source_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence"] = [item.to_dict() for item in self.evidence]
        return payload


@dataclass(frozen=True)
class TrendCollectorResult:
    source_record: TrendSourceRecord | None
    used_stub: bool
    trace: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_record": None if self.source_record is None else self.source_record.to_dict(),
            "used_stub": self.used_stub,
            "trace": dict(self.trace),
        }
