from __future__ import annotations

from app.integrations.base_client import BasePlatformClient


class TikTokPlatformClient(BasePlatformClient):
    """Cliente de integração v1.0 para borda TikTok."""

    def __init__(self, **kwargs) -> None:
        super().__init__(provider_name="tiktok", **kwargs)

    def fetch_video_metrics(self, *, external_video_id: str, captured_window_id: str) -> dict:
        result = self.execute(
            "video_metrics",
            {
                "external_video_id": external_video_id,
                "captured_window_id": captured_window_id,
            },
        )
        return result.to_dict()

    def fetch_publish_record(self, *, external_post_id: str) -> dict:
        result = self.execute(
            "publish_record",
            {"external_post_id": external_post_id},
        )
        return result.to_dict()
