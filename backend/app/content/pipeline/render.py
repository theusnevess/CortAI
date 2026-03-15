from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class RenderTransientError(RuntimeError):
    """Falha transitória elegível para retry em render."""


@dataclass(frozen=True)
class RenderResponse:
    video_path: str


class RenderAdapter:
    def render_video(
        self,
        *,
        audio_path: str,
        render_job_id: str,
        template_id: str | None,
        aspect_ratio: str | None,
        attempt_count: int,
    ) -> RenderResponse:
        raise NotImplementedError


class StubRenderAdapter(RenderAdapter):
    """Stub local que gera vídeo placeholder e metadata do render."""

    def __init__(self, *, base_dir: Path = Path("OUT/content")) -> None:
        self.base_dir = base_dir

    def render_video(
        self,
        *,
        audio_path: str,
        render_job_id: str,
        template_id: str | None,
        aspect_ratio: str | None,
        attempt_count: int,
    ) -> RenderResponse:
        if not Path(audio_path).exists():
            raise ValueError("RENDER_AUDIO_MISSING")
        video_path = self.base_dir / "video" / f"{render_job_id}.mp4"
        metadata_path = self.base_dir / "metadata" / f"{render_job_id}.json"
        video_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        video_path.write_bytes(b"FAKE_MP4_PLACEHOLDER")
        metadata_path.write_text(
            json.dumps(
                {
                    "render_job_id": render_job_id,
                    "audio_path": audio_path,
                    "template_id": template_id,
                    "aspect_ratio": aspect_ratio,
                    "attempt_count": attempt_count,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return RenderResponse(video_path=str(video_path))
