from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PublishWindowRecommendation:
    recommendation_id: str
    account_id: str
    generated_at: str
    best_publish_windows: list[str]
    source_publish_count: int
    source_metric_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PacingRecommendation:
    recommendation_id: str
    account_id: str
    generated_at: str
    recommended_min_interval_minutes: int
    recommended_max_posts_per_day: int
    recommended_max_posts_per_hour: int
    reason_codes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RiskProfile:
    profile_id: str
    account_id: str
    generated_at: str
    risk_level: str
    signal_counts: dict[str, int]
    latest_risk_ts: str | None
    reason_codes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AccountHealthSnapshot:
    snapshot_id: str
    account_id: str
    generated_at: str
    account_health: str
    avg_views: float
    avg_completion_rate: float
    publish_count: int
    risk_level: str
    reason_codes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PlatformIntelligenceBundle:
    publish_window: PublishWindowRecommendation
    pacing: PacingRecommendation
    risk_profile: RiskProfile
    account_health: AccountHealthSnapshot
    actions: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "publish_window": self.publish_window.to_dict(),
            "pacing": self.pacing.to_dict(),
            "risk_profile": self.risk_profile.to_dict(),
            "account_health": self.account_health.to_dict(),
            "actions": dict(self.actions),
        }
