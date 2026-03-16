from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class PilotMetricsSummary:
    generated_at: str
    total_accounts: int
    total_videos: int
    total_views: int
    avg_watch_time: float | None
    avg_completion_rate: float | None
    avg_3s_view_rate: float | None
    top_account_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExperimentWinnerItem:
    experiment_id: str
    winner_variant: str | None
    confidence_level: str | None
    supporting_metric: str
    notes: str | None = None


@dataclass(frozen=True)
class ExperimentWinners:
    generated_at: str
    experiments: list[ExperimentWinnerItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "experiments": [asdict(item) for item in self.experiments],
        }


@dataclass(frozen=True)
class HookPerformanceItem:
    hook_id: str | None
    hook_type: str | None
    video_count: int
    avg_completion_rate: float | None
    avg_watch_time: float | None
    performance_rank: int


@dataclass(frozen=True)
class HookPerformanceSummary:
    generated_at: str
    hooks: list[HookPerformanceItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "hooks": [asdict(item) for item in self.hooks],
        }


@dataclass(frozen=True)
class AccountHealthItem:
    account_id: str
    risk_level: str
    cooldown_active: bool
    last_publish_at: str | None
    pacing_delays_count: int
    recent_risk_events_count: int
    health_status: str


@dataclass(frozen=True)
class AccountHealthSummary:
    generated_at: str
    accounts: list[AccountHealthItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "accounts": [asdict(item) for item in self.accounts],
        }
