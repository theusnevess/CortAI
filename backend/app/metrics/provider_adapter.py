from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class MetricsProviderTimeout(RuntimeError):
    pass


class MetricsProviderRateLimit(RuntimeError):
    pass


class MetricsProviderUnavailable(RuntimeError):
    pass


class MetricsProviderClient(Protocol):
    def fetch_video_metrics(self, *, publish_id: str, video_id: str, account_id: str) -> dict:
        ...


@dataclass
class StubMetricsProviderAdapter:
    default_views: int = 1000

    def fetch_video_metrics(self, *, publish_id: str, video_id: str, account_id: str) -> dict:
        del publish_id
        del video_id
        del account_id
        return {
            "views": self.default_views,
            "likes": 50,
            "comments": 7,
            "shares": 3,
            "watch_time_total": 18000.0,
            "avg_watch_time": 18.0,
            "completion_rate": 0.42,
            "view_3s_rate": 0.71,
            "view_5s_rate": 0.54,
        }
