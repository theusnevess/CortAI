from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class RenderJobStatus(str, Enum):
    """Estados canonicos do job de conteudo."""

    PENDING = "PENDING"
    TTS_RUNNING = "TTS_RUNNING"
    TTS_DONE = "TTS_DONE"
    RENDER_RUNNING = "RENDER_RUNNING"
    RENDER_DONE = "RENDER_DONE"
    READY = "READY"
    FAILED = "FAILED"
    NOOP = "NOOP"


@dataclass(frozen=True)
class ExecutionEnvelope:
    job_id: str
    account_id: str
    creative_pack_id: str
    publish_slot: str
    experiment_variant: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PublishManifest:
    publish_id: str
    account_id: str
    video_path: str
    caption: str
    hashtags: list[str]
    scheduled_time: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RenderJob:
    """Job deterministico do pipeline de conteudo."""

    render_job_id: str
    creative_pack_id: str
    account_id: str
    status: RenderJobStatus
    attempt_count: int
    created_at: str
    updated_at: str
    audio_path: str | None = None
    video_path: str | None = None
    error_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


@dataclass(frozen=True)
class PipelineResult:
    """Resultado explicito do pipeline sem side effects de publicacao."""

    status: str
    publish_manifest: PublishManifest | None = None
    artifacts: dict[str, str] = field(default_factory=dict)
    events_emitted: list[str] = field(default_factory=list)
    error_code: str | None = None
    render_job_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.publish_manifest is not None:
            payload["publish_manifest"] = self.publish_manifest.to_dict()
        return payload
