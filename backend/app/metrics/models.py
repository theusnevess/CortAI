from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class VideoMetricsRecord:
    metrics_id: str
    publish_id: str
    account_id: str
    video_id: str
    views: int
    likes: int
    comments: int
    shares: int
    watch_time_total: float
    avg_watch_time: float
    completion_rate: float
    view_3s_rate: float
    view_5s_rate: float
    collected_at: str
    collected_at_bucket: str
    age_hours: float
    provider: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
