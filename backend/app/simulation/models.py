from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SimulatedPublishRecord:
    simulation_run_id: str
    simulated_publish_id: str
    account_id: str
    creative_pack_id: str | None
    experiment_id: str | None
    variant: str | None
    published_at: str
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SimulatedVideoMetrics:
    simulation_run_id: str
    simulated_publish_id: str
    views: int
    watch_time_total: float
    avg_watch_time: float
    completion_rate: float
    view_3s_rate: float | None
    collected_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SimulatedExperimentResult:
    simulation_run_id: str
    experiment_id: str
    variant: str
    simulated_publish_id: str
    supporting_metric: str
    score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SimulationRunSummary:
    simulation_run_id: str
    generated_at: str
    total_accounts: int
    total_simulated_publishes: int
    total_metrics: int
    total_experiment_results: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

