from __future__ import annotations

import wave
from dataclasses import dataclass
from pathlib import Path


class TtsTransientError(RuntimeError):
    """Falha transitória elegível para retry em TTS."""


@dataclass(frozen=True)
class TtsResponse:
    audio_path: str
    duration_s: float | None = None


class TtsAdapter:
    def generate_audio(
        self,
        *,
        script_text: str,
        voice_profile: str | None,
        language: str | None,
        render_job_id: str,
        attempt_count: int,
    ) -> TtsResponse:
        raise NotImplementedError


class StubTtsAdapter(TtsAdapter):
    """Stub local que gera um WAV silencioso e determinístico."""

    def __init__(self, *, base_dir: Path = Path("OUT/content")) -> None:
        self.base_dir = base_dir

    def generate_audio(
        self,
        *,
        script_text: str,
        voice_profile: str | None,
        language: str | None,
        render_job_id: str,
        attempt_count: int,
    ) -> TtsResponse:
        if not script_text.strip():
            raise ValueError("TTS_INVALID_SCRIPT")
        target = self.base_dir / "audio" / f"{render_job_id}.wav"
        target.parent.mkdir(parents=True, exist_ok=True)
        duration_s = max(1.0, round(len(script_text.split()) * 0.35, 2))
        with wave.open(str(target), "w") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(16000)
            writer.writeframes(b"\x00\x00" * 16000)
        return TtsResponse(audio_path=str(target), duration_s=duration_s)
