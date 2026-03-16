from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


WORDS_PER_SECOND = 2.5
SAMPLE_RATE = 16000
SAMPLE_WIDTH = 2
CHANNELS = 1
MIN_DURATION_S = 3.0
DEFAULT_TTS_MODE = "auto"
DEFAULT_OPENAI_MODEL = "tts-1-hd"
DEFAULT_OPENAI_VOICE = "nova"
DEFAULT_PIPER_MODEL = "tools/piper/voices/en_US-lessac-high.onnx"
DEFAULT_EDGE_VOICE = "en-US-GuyNeural"
DEFAULT_PYTTSX3_VOICE_HINT = "en-US"
DEFAULT_BLOCK_PAUSE_MS = 650


class TtsTransientError(RuntimeError):
    """Falha transitoria elegivel para retry em TTS."""


@dataclass(frozen=True)
class TtsResponse:
    audio_path: str
    duration_s: float | None = None
    segment_durations: list[float] | None = None


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
    """TTS local com modos configuraveis e fallback deterministico."""

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

        mode = os.getenv("CORTAI_TTS_MODE", DEFAULT_TTS_MODE).lower()
        if mode in {"piper", "auto"}:
            piper_result = self._try_piper_tts(
                script_text=script_text,
                voice_profile=voice_profile,
                language=language,
                render_job_id=render_job_id,
                strict=(mode == "piper"),
            )
            if piper_result is not None:
                return piper_result

        if mode in {"openai", "auto"}:
            openai_result = self._try_openai_tts(
                script_text=script_text,
                voice_profile=voice_profile,
                language=language,
                render_job_id=render_job_id,
                strict=(mode == "openai"),
            )
            if openai_result is not None:
                return openai_result

        if mode in {"edge", "auto"}:
            edge_result = self._try_edge_tts(
                script_text=script_text,
                voice_profile=voice_profile,
                language=language,
                render_job_id=render_job_id,
                strict=(mode == "edge"),
            )
            if edge_result is not None:
                return edge_result

        if mode in {"pyttsx3", "auto"}:
            pyttsx3_result = self._try_pyttsx3(
                script_text=script_text,
                voice_profile=voice_profile,
                language=language,
                render_job_id=render_job_id,
                strict=(mode == "pyttsx3"),
            )
            if pyttsx3_result is not None:
                return pyttsx3_result

        return self._generate_silent_audio(script_text=script_text, render_job_id=render_job_id)

    def _try_piper_tts(
        self,
        *,
        script_text: str,
        voice_profile: str | None,
        language: str | None,
        render_job_id: str,
        strict: bool,
    ) -> TtsResponse | None:
        del language
        piper_cmd = shutil.which("piper")
        if not piper_cmd:
            piper_cmd = shutil.which("piper.exe")
        if not piper_cmd:
            if strict:
                raise TtsTransientError("PIPER_NOT_INSTALLED")
            return None

        model_path = Path(voice_profile or os.getenv("CORTAI_PIPER_MODEL", DEFAULT_PIPER_MODEL))
        config_path = Path(f"{model_path}.json")
        if not model_path.exists() or not config_path.exists():
            if strict:
                raise TtsTransientError("PIPER_MODEL_MISSING")
            return None

        target = self.base_dir / "audio" / f"{render_job_id}.wav"
        target.parent.mkdir(parents=True, exist_ok=True)
        sentence_silence = os.getenv("CORTAI_PIPER_SENTENCE_SILENCE", "0.08")
        length_scale = os.getenv("CORTAI_PIPER_LENGTH_SCALE", "0.94")
        noise_scale = os.getenv("CORTAI_PIPER_NOISE_SCALE", "0.45")
        noise_w_scale = os.getenv("CORTAI_PIPER_NOISE_W_SCALE", "0.75")
        cmd = [
            piper_cmd,
            "-m",
            str(model_path),
            "-c",
            str(config_path),
            "-f",
            str(target),
            "--sentence-silence",
            sentence_silence,
            "--length-scale",
            length_scale,
            "--noise-scale",
            noise_scale,
            "--noise-w-scale",
            noise_w_scale,
        ]
        try:
            segments = [item.strip() for item in script_text.split("\n\n") if item.strip()]
            if len(segments) > 1:
                pause_ms = int(float(os.getenv("CORTAI_TTS_BLOCK_PAUSE_MS", str(DEFAULT_BLOCK_PAUSE_MS))))
                segment_durations = self._render_piper_segments(
                    cmd=cmd,
                    segments=segments,
                    target=target,
                    pause_ms=pause_ms,
                )
                return TtsResponse(
                    audio_path=str(target),
                    duration_s=self._wave_duration(target),
                    segment_durations=segment_durations,
                )
            else:
                subprocess.run(
                    cmd,
                    input=script_text,
                    text=True,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            if not target.exists() or target.stat().st_size == 0:
                raise TtsTransientError("PIPER_OUTPUT_MISSING")
            return TtsResponse(audio_path=str(target), duration_s=self._wave_duration(target))
        except Exception as exc:  # noqa: BLE001
            if strict:
                raise TtsTransientError(f"PIPER_TTS_FAILED: {exc}") from exc
            return None

    def _try_openai_tts(
        self,
        *,
        script_text: str,
        voice_profile: str | None,
        language: str | None,
        render_job_id: str,
        strict: bool,
    ) -> TtsResponse | None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            if strict:
                raise TtsTransientError("OPENAI_API_KEY_MISSING")
            return None

        try:
            from openai import OpenAI
        except ImportError:
            if strict:
                raise TtsTransientError("OPENAI_CLIENT_NOT_INSTALLED")
            return None

        target = self.base_dir / "audio" / f"{render_job_id}.mp3"
        target.parent.mkdir(parents=True, exist_ok=True)
        model = os.getenv("CORTAI_OPENAI_TTS_MODEL", DEFAULT_OPENAI_MODEL)
        voice = voice_profile or os.getenv("CORTAI_TTS_VOICE") or self._default_openai_voice(language)
        speed_raw = os.getenv("CORTAI_OPENAI_TTS_SPEED", "1.0")
        try:
            speed = float(speed_raw)
        except ValueError:
            speed = 1.0

        try:
            client = OpenAI(api_key=api_key)
            response = client.audio.speech.create(
                model=model,
                voice=voice,
                input=script_text,
                response_format="mp3",
                speed=speed,
            )
            response.write_to_file(str(target))
            if not target.exists() or target.stat().st_size == 0:
                raise TtsTransientError("OPENAI_TTS_OUTPUT_MISSING")
            duration_s = self._probe_duration(target)
            return TtsResponse(audio_path=str(target), duration_s=duration_s)
        except Exception as exc:  # noqa: BLE001
            if strict:
                raise TtsTransientError(f"OPENAI_TTS_FAILED: {exc}") from exc
            return None

    def _try_pyttsx3(
        self,
        *,
        script_text: str,
        voice_profile: str | None,
        language: str | None,
        render_job_id: str,
        strict: bool,
    ) -> TtsResponse | None:
        try:
            import pyttsx3
        except ImportError:
            if strict:
                raise TtsTransientError("PYTTSX3_NOT_INSTALLED")
            return None

        target = self.base_dir / "audio" / f"{render_job_id}.wav"
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            engine = pyttsx3.init()
            selected_voice = self._select_pyttsx3_voice(
                engine=engine,
                requested_voice=voice_profile,
                language=language,
            )
            if selected_voice:
                engine.setProperty("voice", selected_voice)
            engine.setProperty("volume", 1.0)
            engine.setProperty("rate", 165)
            engine.save_to_file(script_text, str(target))
            engine.runAndWait()
            try:
                engine.stop()
            except Exception:
                pass
            if not target.exists() or target.stat().st_size == 0:
                raise TtsTransientError("PYTTSX3_OUTPUT_MISSING")
            return TtsResponse(audio_path=str(target), duration_s=self._wave_duration(target))
        except Exception as exc:  # noqa: BLE001
            if strict:
                raise TtsTransientError(str(exc)) from exc
            return None

    def _select_pyttsx3_voice(self, *, engine: object, requested_voice: str | None, language: str | None) -> str | None:
        voices = engine.getProperty("voices")
        if requested_voice:
            for voice in voices:
                haystacks = [str(getattr(voice, "id", "")), str(getattr(voice, "name", ""))]
                if any(requested_voice.lower() in item.lower() for item in haystacks):
                    return str(voice.id)
        preferred_language = language or DEFAULT_PYTTSX3_VOICE_HINT
        for voice in voices:
            languages = [str(item) for item in getattr(voice, "languages", [])]
            if any(preferred_language.lower() in item.lower() for item in languages):
                return str(voice.id)
        return str(voices[0].id) if voices else None

    def _try_edge_tts(
        self,
        *,
        script_text: str,
        voice_profile: str | None,
        language: str | None,
        render_job_id: str,
        strict: bool,
    ) -> TtsResponse | None:
        try:
            import edge_tts
        except ImportError:
            if strict:
                raise TtsTransientError("EDGE_TTS_NOT_INSTALLED")
            return None

        target = self.base_dir / "audio" / f"{render_job_id}.mp3"
        target.parent.mkdir(parents=True, exist_ok=True)
        voice = voice_profile or os.getenv("CORTAI_TTS_VOICE") or self._default_edge_voice(language)
        try:
            asyncio.run(edge_tts.Communicate(script_text, voice).save(str(target)))
            duration_s = self._probe_duration(target)
            return TtsResponse(audio_path=str(target), duration_s=duration_s)
        except Exception as exc:  # noqa: BLE001
            if strict:
                raise TtsTransientError(str(exc)) from exc
            return None

    def _generate_silent_audio(self, *, script_text: str, render_job_id: str) -> TtsResponse:
        target = self.base_dir / "audio" / f"{render_job_id}.wav"
        target.parent.mkdir(parents=True, exist_ok=True)
        duration_s = self._estimate_duration(script_text)
        frame_count = int(duration_s * SAMPLE_RATE)
        silence_frame = b"\x00" * SAMPLE_WIDTH
        with wave.open(str(target), "wb") as writer:
            writer.setnchannels(CHANNELS)
            writer.setsampwidth(SAMPLE_WIDTH)
            writer.setframerate(SAMPLE_RATE)
            writer.writeframes(silence_frame * frame_count)
        return TtsResponse(audio_path=str(target), duration_s=duration_s)

    def _render_piper_segments(
        self,
        *,
        cmd: list[str],
        segments: list[str],
        target: Path,
        pause_ms: int,
    ) -> list[float]:
        rendered_paths: list[Path] = []
        segment_lengths: list[float] = []
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            for index, segment in enumerate(segments, start=1):
                segment_path = temp_root / f"segment_{index}.wav"
                segment_cmd = list(cmd)
                out_index = segment_cmd.index("-f") + 1
                segment_cmd[out_index] = str(segment_path)
                subprocess.run(
                    segment_cmd,
                    input=segment,
                    text=True,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                if not segment_path.exists() or segment_path.stat().st_size == 0:
                    raise TtsTransientError(f"PIPER_SEGMENT_OUTPUT_MISSING:{index}")
                rendered_paths.append(segment_path)
                segment_lengths.append(self._wave_duration(segment_path))
            self._merge_wav_segments(rendered_paths=rendered_paths, target=target, pause_ms=pause_ms)
        pause_s = max(0.0, pause_ms / 1000.0)
        return [
            round(length + (pause_s if index != len(segment_lengths) - 1 else 0.0), 2)
            for index, length in enumerate(segment_lengths)
        ]

    def _merge_wav_segments(self, *, rendered_paths: list[Path], target: Path, pause_ms: int) -> None:
        if not rendered_paths:
            raise TtsTransientError("PIPER_SEGMENTS_EMPTY")
        target.parent.mkdir(parents=True, exist_ok=True)

        with wave.open(str(rendered_paths[0]), "rb") as first:
            params = first.getparams()
            pause_frames = int(params.framerate * max(0, pause_ms) / 1000)
            silence = b"\x00" * pause_frames * params.sampwidth * params.nchannels

        with wave.open(str(target), "wb") as writer:
            writer.setparams(params)
            for index, path in enumerate(rendered_paths):
                with wave.open(str(path), "rb") as reader:
                    writer.writeframes(reader.readframes(reader.getnframes()))
                if index != len(rendered_paths) - 1 and pause_frames > 0:
                    writer.writeframes(silence)

    def _estimate_duration(self, script_text: str) -> float:
        words = max(1, len(script_text.split()))
        estimated = round(words / WORDS_PER_SECOND, 2)
        return max(MIN_DURATION_S, estimated)

    def _default_edge_voice(self, language: str | None) -> str:
        if language and language.lower().startswith("pt"):
            return "pt-BR-AntonioNeural"
        return DEFAULT_EDGE_VOICE

    def _default_openai_voice(self, language: str | None) -> str:
        _ = language
        return DEFAULT_OPENAI_VOICE

    def _wave_duration(self, audio_path: Path) -> float:
        with wave.open(str(audio_path), "rb") as reader:
            frame_rate = reader.getframerate() or 1
            frame_count = reader.getnframes()
            return round(frame_count / frame_rate, 2)

    def _probe_duration(self, audio_path: Path) -> float:
        ffprobe_path = shutil.which("ffprobe")
        if ffprobe_path:
            return self._run_ffprobe([ffprobe_path], str(audio_path))

        repo_root = Path(__file__).resolve().parents[4]
        try:
            audio_rel = audio_path.resolve().relative_to(repo_root)
        except ValueError as exc:
            raise TtsTransientError("TTS_DURATION_PROBE_FAILED") from exc

        docker_path = shutil.which("docker")
        if not docker_path:
            raise TtsTransientError("TTS_DURATION_PROBE_FAILED")

        workspace = repo_root.resolve().as_posix()
        container_audio = str(PurePosixPath("/workspace").joinpath(*audio_rel.parts))
        return self._run_ffprobe(
            [
                docker_path,
                "run",
                "--rm",
                "--entrypoint",
                "ffprobe",
                "-v",
                f"{workspace}:/workspace",
                "-w",
                "/workspace",
                os.getenv("CORTAI_FFMPEG_IMAGE", "cortai10-api"),
            ],
            container_audio,
        )

    def _run_ffprobe(self, command: list[str], audio_path: str) -> float:
        cmd = [
            *command,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ]
        try:
            output = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return round(float(output.stdout.strip()), 2)
        except Exception as exc:  # noqa: BLE001
            raise TtsTransientError("TTS_DURATION_PROBE_FAILED") from exc
