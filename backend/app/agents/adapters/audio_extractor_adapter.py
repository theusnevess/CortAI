from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path

from app.agents.collector.utils import parse_minio_path
from app.services.storage import MinioService

TMP_DIR = Path("/tmp/cortai/audio_extractor")
DEFAULT_AUDIO_BUCKET = os.getenv("MINIO_BUCKET_AUDIO", "audio-raw")


class AudioExtractorAdapter:
    """
    Normaliza a midia do pipeline em audio local e em MinIO.

    Contrato v0.1:
    - aceita exatamente um dos modos:
      - payload.raw_video_minio_path
      - payload.audio_minio_path
    - sempre retorna um state completo com os campos necessarios para os
      proximos steps do Maestro, mesmo sob `state.clear()`.
    """

    def process(self, state: dict, payload: dict | None = None) -> dict:
        payload = payload or state.get("_action", {}).get("payload", {})
        raw_video_minio_path = payload.get("raw_video_minio_path")
        audio_minio_path = payload.get("audio_minio_path")

        if bool(raw_video_minio_path) == bool(audio_minio_path):
            raise ValueError(
                "ContractViolation: audio_extractor requires exactly one of "
                "raw_video_minio_path or audio_minio_path"
            )

        job_id = state.get("job_id")
        input_ref = state.get("input_ref")
        artifacts = dict(state.get("artifacts") or {})
        TMP_DIR.mkdir(parents=True, exist_ok=True)

        if isinstance(raw_video_minio_path, str) and raw_video_minio_path:
            artifacts["raw_video_minio_path"] = raw_video_minio_path
            audio_local_path, audio_minio_path = self._extract_from_raw_video(raw_video_minio_path)
        elif isinstance(audio_minio_path, str) and audio_minio_path:
            audio_local_path = self._download_audio_to_tmp(audio_minio_path)
        else:
            raise ValueError("ContractViolation: invalid payload values for audio_extractor")

        artifacts["audio_ready"] = True
        artifacts["audio_local_path"] = audio_local_path
        artifacts["audio_minio_path"] = audio_minio_path

        out_state = {
            "job_id": job_id,
            "input_ref": input_ref,
            "source_type": "audio",
            "audio_local_path": audio_local_path,
            "audio_minio_path": audio_minio_path,
            "artifacts": artifacts,
        }
        if artifacts.get("raw_video_minio_path"):
            out_state["raw_video_minio_path"] = artifacts["raw_video_minio_path"]
        return out_state

    def _extract_from_raw_video(self, raw_video_minio_path: str) -> tuple[str, str]:
        local_video_path = self._download_to_tmp(raw_video_minio_path)
        audio_local_path = self._extract_wav(local_video_path)
        audio_minio_path = self._upload_audio(audio_local_path)
        return audio_local_path, audio_minio_path

    def _download_audio_to_tmp(self, audio_minio_path: str) -> str:
        return self._download_to_tmp(audio_minio_path, suffix=".wav")

    def _download_to_tmp(self, minio_path: str, suffix: str | None = None) -> str:
        parsed = parse_minio_path(minio_path)
        src_storage = MinioService()
        src_storage.bucket_name = parsed.bucket
        src_storage._ensure_bucket_exists()

        file_suffix = suffix or Path(parsed.key).suffix or ".bin"
        local_path = TMP_DIR / f"{uuid.uuid4()}{file_suffix}"
        src_storage.download_file(parsed.key, str(local_path))
        if not local_path.exists():
            raise RuntimeError("AudioExtractorError: download did not produce local file")
        return str(local_path)

    def _extract_wav(self, local_video_path: str) -> str:
        audio_local_path = TMP_DIR / f"{uuid.uuid4()}.wav"
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(local_video_path),
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(audio_local_path),
        ]
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if proc.returncode != 0:
            msg = (proc.stderr or proc.stdout or "").strip()
            raise OSError(f"FFmpegFailed: {msg[:500]}")
        if not audio_local_path.exists():
            raise RuntimeError("AudioExtractorError: ffmpeg did not produce wav")
        return str(audio_local_path)

    def _upload_audio(self, audio_local_path: str) -> str:
        storage = MinioService()
        storage.bucket_name = DEFAULT_AUDIO_BUCKET
        storage._ensure_bucket_exists()
        object_name = f"{uuid.uuid4()}.wav"
        return storage.upload_file(audio_local_path, object_name)
