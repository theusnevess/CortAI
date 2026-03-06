from __future__ import annotations

from datetime import datetime, timezone

from app.integrations.base_client import ProviderInvalidPayloadError
from app.integrations.models import NormalizedPublishRecord, NormalizedVideoMetrics


class TikTokNormalizedAdapter:
    """Converte payload bruto do TikTok para contratos internos do CortAI."""

    def normalize_video_metrics(
        self,
        *,
        raw_payload: dict,
        account_id: str,
        captured_window_id: str,
    ) -> NormalizedVideoMetrics:
        provider_payload = raw_payload.get("payload")
        if not isinstance(provider_payload, dict):
            raise ProviderInvalidPayloadError("PROVIDER_INVALID_PAYLOAD")

        external_video_id = provider_payload.get("external_video_id")
        captured_at = provider_payload.get("captured_at")
        views = provider_payload.get("views")
        if not isinstance(external_video_id, str) or not external_video_id:
            raise ProviderInvalidPayloadError("PROVIDER_INVALID_PAYLOAD")
        if not isinstance(captured_at, str) or not captured_at:
            raise ProviderInvalidPayloadError("PROVIDER_INVALID_PAYLOAD")
        if not isinstance(views, int) or views < 0:
            raise ProviderInvalidPayloadError("PROVIDER_INVALID_PAYLOAD")

        return NormalizedVideoMetrics(
            record={
                "video_id": str(provider_payload.get("video_id") or external_video_id),
                "account_id": account_id,
                "captured_at": captured_at,
                "captured_window_id": captured_window_id,
                "source_kind": "PLATFORM_ANALYTICS",
                "views": views,
                "retention_3s": provider_payload.get("retention_3s"),
                "completion_rate": provider_payload.get("completion_rate"),
                "likes": provider_payload.get("likes"),
                "follows": provider_payload.get("follows"),
                "rpm": provider_payload.get("rpm"),
                "ingested_at": _utc_now(),
                "provider": "tiktok",
                "external_video_id": external_video_id,
            }
        )

    def normalize_publish_record(
        self,
        *,
        raw_payload: dict,
        account_id: str,
    ) -> NormalizedPublishRecord:
        provider_payload = raw_payload.get("payload")
        if not isinstance(provider_payload, dict):
            raise ProviderInvalidPayloadError("PROVIDER_INVALID_PAYLOAD")

        required = ("external_post_id", "job_id", "video_id", "published_at", "status")
        for field in required:
            value = provider_payload.get(field)
            if not isinstance(value, str) or not value:
                raise ProviderInvalidPayloadError("PROVIDER_INVALID_PAYLOAD")

        return NormalizedPublishRecord(
            record={
                "publish_id": provider_payload["external_post_id"],
                "account_id": account_id,
                "job_id": provider_payload["job_id"],
                "video_id": provider_payload["video_id"],
                "platform": "tiktok",
                "publish_mode": str(provider_payload.get("publish_mode") or "replay"),
                "status": provider_payload["status"],
                "published_at": provider_payload["published_at"],
                "created_at": _utc_now(),
                "metadata": {
                    "provider": "tiktok",
                    "request_id": raw_payload.get("request_id"),
                },
            }
        )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
