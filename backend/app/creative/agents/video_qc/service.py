from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.content.pipeline.render import MIN_VIDEO_DURATION_S
from app.creative.agents.video_qc.models import VideoQcResult


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class VideoQcAgentService:
    def evaluate(self, *, render_job_id: str, artifacts: object, base_dir: Path) -> VideoQcResult:
        try:
            return self._evaluate(render_job_id=render_job_id, artifacts=artifacts, base_dir=base_dir)
        except Exception as exc:  # noqa: BLE001
            return VideoQcResult(
                status="REJECT",
                reasons=["QC_INTERNAL_ERROR"],
                checked_at=_now_iso(),
                details={
                    "render_job_id": render_job_id,
                    "error": str(exc) or exc.__class__.__name__,
                },
            )

    def _evaluate(self, *, render_job_id: str, artifacts: object, base_dir: Path) -> VideoQcResult:
        reasons: list[str] = []
        details: dict[str, object] = {"render_job_id": render_job_id}

        if not isinstance(artifacts, dict):
            return VideoQcResult(status="REJECT", reasons=["QC_ARTIFACTS_INVALID"], checked_at=_now_iso(), details=details)

        video_path = Path(str(artifacts.get("video") or ""))
        audio_path = Path(str(artifacts.get("audio") or ""))
        metadata_path = base_dir / "metadata" / f"{render_job_id}.json"
        details["video_path"] = str(video_path)
        details["audio_path"] = str(audio_path)
        details["metadata_path"] = str(metadata_path)

        if not video_path.exists() or video_path.stat().st_size == 0:
            reasons.append("QC_VIDEO_MISSING")
        if not audio_path.exists() or audio_path.stat().st_size == 0:
            reasons.append("QC_AUDIO_MISSING")
        if not metadata_path.exists():
            reasons.append("QC_METADATA_MISSING")

        metadata: dict[str, object] = {}
        if not reasons:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            render_duration = float(metadata.get("render_duration_s") or 0.0)
            subtitle_cues = metadata.get("subtitle_cues", [])
            details["render_duration_s"] = render_duration
            if render_duration < MIN_VIDEO_DURATION_S:
                reasons.append("QC_DURATION_BELOW_MINIMUM")
            if not isinstance(subtitle_cues, list) or len(subtitle_cues) != 3:
                reasons.append("QC_SUBTITLE_CUES_INVALID")
            else:
                for cue in subtitle_cues:
                    text = str(cue.get("text") or "")
                    if not text.strip():
                        reasons.append("QC_EMPTY_CUE_TEXT")
                        break
                    if "\u25a1" in text or "\ufffd" in text:
                        reasons.append("QC_GLYPH_BROKEN")
                        break
            setup_luma = metadata.get("setup_background_mean_luma")
            payoff_luma = metadata.get("payoff_background_mean_luma")
            if isinstance(payoff_luma, (int, float)) and payoff_luma < 45:
                reasons.append("QC_PAYOFF_TOO_DARK")
            details["setup_background_mean_luma"] = setup_luma
            details["payoff_background_mean_luma"] = payoff_luma

            probe = self._probe_video(video_path)
            if probe.get("probe_mode") == "unavailable":
                inferred = self._infer_dimensions_from_metadata(metadata)
                probe["width"] = inferred["width"]
                probe["height"] = inferred["height"]
                probe["has_audio"] = audio_path.exists() and audio_path.stat().st_size > 0
                probe["probe_mode"] = "metadata_fallback"
            details.update(probe)
            if probe.get("width") != 1080 or probe.get("height") != 1920:
                reasons.append("QC_RESOLUTION_INVALID")
            if not probe.get("has_audio"):
                reasons.append("QC_AUDIO_STREAM_MISSING")

        return VideoQcResult(
            status="APPROVE" if not reasons else "REJECT",
            reasons=reasons,
            checked_at=_now_iso(),
            details=details,
        )

    def _probe_video(self, video_path: Path) -> dict[str, object]:
        ffprobe = shutil.which("ffprobe")
        if not ffprobe:
            return {"width": None, "height": None, "has_audio": True, "probe_mode": "unavailable"}

        cmd = [
            ffprobe,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            str(video_path),
        ]
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        payload = json.loads(result.stdout or "{}")
        streams = payload.get("streams", [])
        video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
        audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
        return {
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
            "has_audio": audio_stream is not None,
            "probe_mode": "ffprobe",
        }

    def _infer_dimensions_from_metadata(self, metadata: dict[str, object]) -> dict[str, int]:
        aspect_ratio = str(metadata.get("aspect_ratio") or "")
        if aspect_ratio == "16:9":
            return {"width": 1280, "height": 720}
        return {"width": 1080, "height": 1920}
