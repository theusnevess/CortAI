from __future__ import annotations

import os
import shutil
import tempfile
import time
import wave
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import soundfile as sf

from app.content.pipeline.tts import TtsResponse, TtsTransientError

DEFAULT_KOKORO_MODEL_PATH = "OUT/audit/phase2_5b_kokoro/kokoro_assets/kokoro-v1.0.onnx"
DEFAULT_KOKORO_VOICES_PATH = "OUT/audit/phase2_5b_kokoro/kokoro_assets/voices-v1.0.bin"
DEFAULT_KOKORO_VOICE = "af_heart"
DEFAULT_KOKORO_LANG = "en-us"


@dataclass
class KokoroAdapter:
    base_dir: Path = Path("OUT/content")
    _runtime: object | None = field(default=None, init=False, repr=False)
    _runtime_key: tuple[str, str, str] | None = field(default=None, init=False, repr=False)

    def generate_audio(
        self,
        *,
        script_text: str,
        voice_profile: str | None,
        language: str | None,
        render_job_id: str,
        overall_rate: float | None = None,
        inter_segment_pause_ms: list[int] | None = None,
    ) -> TtsResponse:
        if not script_text.strip():
            raise TtsTransientError("KOKORO_INVALID_SCRIPT")

        runtime = self._get_runtime()
        target = self.base_dir / "audio" / f"{render_job_id}.wav"
        target.parent.mkdir(parents=True, exist_ok=True)
        voice = voice_profile or os.getenv("CORTAI_KOKORO_VOICE", DEFAULT_KOKORO_VOICE)
        lang = self._normalize_language(language)
        speed = float(overall_rate or os.getenv("CORTAI_KOKORO_SPEED", "1.0"))
        segments = [item.strip() for item in script_text.split("\n\n") if item.strip()]
        if not segments:
            raise TtsTransientError("KOKORO_SEGMENTS_EMPTY")

        pause_profile_ms = list(inter_segment_pause_ms or [])
        audio_parts: list[np.ndarray] = []
        segment_durations: list[float] = []
        sample_rate: int | None = None
        for index, segment in enumerate(segments):
            try:
                audio, sample_rate = runtime.create(segment, voice=voice, speed=speed, lang=lang)
            except Exception as exc:  # noqa: BLE001
                raise TtsTransientError(f"KOKORO_GENERATION_FAILED:{exc}") from exc
            audio_part = np.asarray(audio, dtype=np.float32)
            if audio_part.size == 0:
                raise TtsTransientError("KOKORO_OUTPUT_EMPTY")
            part_duration = round(float(audio_part.shape[0]) / float(sample_rate), 3)
            if index < len(segments) - 1:
                pause_ms = pause_profile_ms[index] if index < len(pause_profile_ms) else 0
                if pause_ms > 0:
                    silence = np.zeros(int(sample_rate * (pause_ms / 1000.0)), dtype=np.float32)
                    audio_part = np.concatenate([audio_part, silence])
                    part_duration = round(part_duration + (pause_ms / 1000.0), 3)
            audio_parts.append(audio_part)
            segment_durations.append(part_duration)
        final_audio = np.concatenate(audio_parts)
        sf.write(target, final_audio, sample_rate or 24000)
        if not target.exists() or target.stat().st_size == 0:
            raise TtsTransientError("KOKORO_OUTPUT_MISSING")
        return TtsResponse(
            audio_path=str(target),
            duration_s=self._wave_duration(target),
            segment_durations=segment_durations,
        )

    def available(self) -> bool:
        model_path, voices_path, _ = self._runtime_paths()
        if not model_path.exists() or not voices_path.exists():
            return False
        try:
            self._import_runtime()
        except TtsTransientError:
            return False
        return True

    def _get_runtime(self):
        model_path, voices_path, device = self._runtime_paths()
        runtime_key = (str(model_path), str(voices_path), device)
        if self._runtime is not None and self._runtime_key == runtime_key:
            return self._runtime
        Kokoro = self._import_runtime()
        original_provider = os.environ.get("ONNX_PROVIDER")
        if device == "cuda":
            os.environ["ONNX_PROVIDER"] = "CUDAExecutionProvider"
        elif device == "cpu":
            os.environ["ONNX_PROVIDER"] = "CPUExecutionProvider"
        try:
            started = time.perf_counter()
            runtime = Kokoro(str(model_path), str(voices_path))
            _ = round(time.perf_counter() - started, 3)
        except Exception as exc:  # noqa: BLE001
            raise TtsTransientError(f"KOKORO_INIT_FAILED:{exc}") from exc
        finally:
            if original_provider is None:
                os.environ.pop("ONNX_PROVIDER", None)
            else:
                os.environ["ONNX_PROVIDER"] = original_provider
        self._runtime = runtime
        self._runtime_key = runtime_key
        return runtime

    def _runtime_paths(self) -> tuple[Path, Path, str]:
        model_path = Path(os.getenv("CORTAI_KOKORO_MODEL_PATH", DEFAULT_KOKORO_MODEL_PATH))
        voices_path = Path(
            os.getenv(
                "CORTAI_KOKORO_VOICES_PATH",
                str(model_path.with_name("voices-v1.0.bin")) if model_path.name else DEFAULT_KOKORO_VOICES_PATH,
            )
        )
        device = os.getenv("CORTAI_KOKORO_DEVICE", "cpu").strip().lower() or "cpu"
        return model_path, voices_path, device

    def _normalize_language(self, language: str | None) -> str:
        normalized = (language or DEFAULT_KOKORO_LANG).strip().lower()
        if normalized in {"en", "en-us", "en_us"}:
            return "en-us"
        if normalized in {"pt", "pt-br", "pt_br"}:
            return "pt-br"
        return normalized

    def _import_runtime(self):
        try:
            from kokoro_onnx import Kokoro
        except ImportError as exc:
            raise TtsTransientError("KOKORO_RUNTIME_NOT_INSTALLED") from exc
        return Kokoro

    def _wave_duration(self, audio_path: Path) -> float:
        with wave.open(str(audio_path), "rb") as reader:
            frame_rate = reader.getframerate() or 1
            frame_count = reader.getnframes()
            return round(frame_count / frame_rate, 2)
