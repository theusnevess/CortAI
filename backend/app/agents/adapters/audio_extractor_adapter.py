# backend/app/agents/adapters/audio_extractor_adapter.py

import subprocess
import uuid
from pathlib import Path

from app.services.storage import MinioService


class AudioExtractorAdapter:
    def process(self, state: dict, payload: dict | None = None) -> dict:
        payload = payload or state.get("_action", {}).get("payload", {})
        raw_video_minio_path = payload.get("raw_video_minio_path")
        if not isinstance(raw_video_minio_path, str) or not raw_video_minio_path:
            raise ValueError("MissingField: payload.raw_video_minio_path")

        audio_format = payload.get("audio_format", "wav")
        if audio_format not in ("wav", "mp3"):
            raise ValueError("InvalidField: payload.audio_format")

        object_name = raw_video_minio_path
        if "/" in raw_video_minio_path:
            bucket = raw_video_minio_path.split("/", 1)[0]
            prefix = f"{bucket}/"
            if raw_video_minio_path.startswith(prefix):
                object_name = raw_video_minio_path[len(prefix):]

        ext = Path(raw_video_minio_path).suffix or ".mp4"
        video_local_path = Path("/tmp") / f"cortai_{uuid.uuid4()}{ext}"
        audio_local_path = Path("/tmp") / f"cortai_{uuid.uuid4()}.{audio_format}"

        MinioService().download_file(object_name, str(video_local_path))

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_local_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(audio_local_path),
        ]
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if proc.returncode != 0:
            msg = (proc.stderr or proc.stdout or "").strip()
            raise OSError(f"FFmpegFailed: {msg}")

        state["audio_local_path"] = str(audio_local_path)
        state.setdefault("artifacts", {})
        state["artifacts"]["audio_ready"] = True
        state["artifacts"]["audio_local_path"] = state["audio_local_path"]
        return state
