from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class HookPerformance:
    hook_performance_id: str
    account_id: str
    publish_id: str
    creative_pack_id: str
    hook_key: str
    hook_type: str
    views: int
    completion_rate: float
    watch_3s_rate: float
    experiment_variant: str | None
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StructurePerformance:
    structure_performance_id: str
    account_id: str
    publish_id: str
    creative_pack_id: str
    structure_key: str
    views: int
    completion_rate: float
    experiment_variant: str | None
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DurationAnalysis:
    duration_analysis_id: str
    account_id: str
    publish_id: str
    creative_pack_id: str
    duration_s: int
    duration_bucket: str
    completion_rate: float
    dropoff_point: float
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PatternPerformance:
    pattern_performance_id: str
    account_id: str
    publish_id: str
    creative_pack_id: str
    pattern_key: str
    views: int
    completion_rate: float
    experiment_variant: str | None
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
