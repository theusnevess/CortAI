from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.content.pipeline.models import ExecutionEnvelope, PublishManifest


class PublishTransientError(RuntimeError):
    """Falha transitoria elegivel para retry em criacao de manifest."""


@dataclass(frozen=True)
class PublishResponse:
    manifest: PublishManifest


class PublishAdapter:
    def create_manifest(
        self,
        *,
        envelope: ExecutionEnvelope,
        video_path: str,
        caption: str,
        hashtags: list[str],
        attempt_count: int,
    ) -> PublishResponse:
        raise NotImplementedError


class StubPublishAdapter(PublishAdapter):
    """Cria um publish manifest deterministico sem persistir publish_record."""

    def create_manifest(
        self,
        *,
        envelope: ExecutionEnvelope,
        video_path: str,
        caption: str,
        hashtags: list[str],
        attempt_count: int,
    ) -> PublishResponse:
        _ = attempt_count
        if not Path(video_path).exists():
            raise ValueError("PUBLISH_VIDEO_MISSING")
        manifest = PublishManifest(
            publish_id=f"pub_{envelope.job_id}",
            account_id=envelope.account_id,
            video_path=video_path,
            caption=caption,
            hashtags=list(hashtags),
            scheduled_time=envelope.publish_slot,
        )
        return PublishResponse(manifest=manifest)
