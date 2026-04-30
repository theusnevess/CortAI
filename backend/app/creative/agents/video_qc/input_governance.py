from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import shutil
from typing import Any

from app.creative.agents.video_qc.models import VideoQcInput


QC_INPUT_GOVERNANCE_VERSION = "qc_input_governance_v2_6"


QC_INPUT_PRIORITY = [
    "render_job_id",
    "video_artifact",
    "audio_artifact",
    "metadata_artifact",
    "script_text",
    "tts_trace",
    "visual_trace",
    "edit_trace",
    "media_probe_capability",
    "metadata_fallback_probe",
]


@dataclass(frozen=True)
class VideoQcInputSignal:
    input_key: str
    available: bool
    used: bool
    status: str
    priority_rank: int | None
    reason_code: str
    rationale: str
    evidence_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VideoQcInputGovernance:
    governance_version: str
    policy_respected: bool
    available_inputs: list[str]
    used_inputs: list[str]
    missing_inputs: list[str]
    degraded_inputs: list[str]
    ignored_inputs: list[str]
    environment_dependent_inputs: list[str]
    input_priority: list[str]
    input_signals: list[VideoQcInputSignal]
    artifact_summary: dict[str, Any]
    environment_summary: dict[str, Any]
    boundary_statement: str
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["input_signals"] = [signal.to_dict() for signal in self.input_signals]
        return payload


@dataclass(frozen=True)
class VideoQcInputGovernanceEvaluator:
    """Trace-only governance for QC inputs and artifact observability."""

    def evaluate(
        self,
        *,
        qc_input: VideoQcInput,
        probe: dict[str, Any] | None = None,
        metadata_loaded: bool = False,
        hard_failures: list[str] | None = None,
    ) -> VideoQcInputGovernance:
        probe_payload = dict(probe or {})
        failures = list(hard_failures or [])
        signals = [
            self._render_job_signal(qc_input.render_job_id),
            self._artifact_signal(
                input_key="video_artifact",
                path=qc_input.video_path,
                reason_prefix="VIDEO_ARTIFACT",
            ),
            self._artifact_signal(
                input_key="audio_artifact",
                path=qc_input.audio_path,
                reason_prefix="AUDIO_ARTIFACT",
            ),
            self._metadata_signal(path=qc_input.metadata_path, metadata_loaded=metadata_loaded),
            self._text_signal(input_key="script_text", value=qc_input.script_text),
            self._trace_signal(input_key="tts_trace", payload=qc_input.tts_trace, used_when_present=True),
            self._trace_signal(input_key="visual_trace", payload=qc_input.visual_trace, used_when_present=False),
            self._trace_signal(input_key="edit_trace", payload=qc_input.edit_trace, used_when_present=True),
            self._media_probe_signal(probe_payload),
            self._metadata_fallback_signal(probe_payload, metadata_loaded=metadata_loaded),
        ]
        available_inputs = [
            signal.input_key
            for signal in signals
            if signal.available
        ]
        used_inputs = [
            signal.input_key
            for signal in signals
            if signal.used
        ]
        missing_inputs = [
            signal.input_key
            for signal in signals
            if signal.status == "missing"
        ]
        degraded_inputs = [
            signal.input_key
            for signal in signals
            if signal.status in {"degraded", "environment_dependent"}
        ]
        ignored_inputs = [
            signal.input_key
            for signal in signals
            if signal.status == "ignored"
        ]
        environment_dependent_inputs = [
            signal.input_key
            for signal in signals
            if signal.status == "environment_dependent"
        ]
        required_inputs = {"render_job_id", "video_artifact", "audio_artifact", "metadata_artifact"}
        policy_respected = not any(
            signal.input_key in required_inputs and signal.status in {"missing", "degraded"}
            for signal in signals
        )
        rationale = [
            "QC input governance is trace-only and does not change QC status, product signals, thresholds, or publishability.",
            "Required final artifacts are video, audio, metadata, and render job id.",
        ]
        if failures:
            rationale.append("Hard failures remain owned by existing QC decision logic and are only mirrored here as evidence.")
        if environment_dependent_inputs:
            rationale.append("Environment-dependent media probing was exposed instead of being treated as full probe evidence.")
        if missing_inputs:
            rationale.append("Missing inputs are explicit and not fabricated.")

        return VideoQcInputGovernance(
            governance_version=QC_INPUT_GOVERNANCE_VERSION,
            policy_respected=policy_respected,
            available_inputs=available_inputs,
            used_inputs=used_inputs,
            missing_inputs=missing_inputs,
            degraded_inputs=degraded_inputs,
            ignored_inputs=ignored_inputs,
            environment_dependent_inputs=environment_dependent_inputs,
            input_priority=list(QC_INPUT_PRIORITY),
            input_signals=signals,
            artifact_summary=self._artifact_summary(qc_input=qc_input, metadata_loaded=metadata_loaded),
            environment_summary=self._environment_summary(probe_payload),
            boundary_statement="Video QC evaluates final artifacts only; it does not repair or publish.",
            rationale=rationale,
        )

    def _rank(self, input_key: str) -> int | None:
        if input_key not in QC_INPUT_PRIORITY:
            return None
        return QC_INPUT_PRIORITY.index(input_key) + 1

    def _render_job_signal(self, render_job_id: str) -> VideoQcInputSignal:
        available = bool(str(render_job_id or "").strip())
        return VideoQcInputSignal(
            input_key="render_job_id",
            available=available,
            used=available,
            status="available" if available else "missing",
            priority_rank=self._rank("render_job_id"),
            reason_code="RENDER_JOB_ID_AVAILABLE" if available else "RENDER_JOB_ID_MISSING",
            rationale=(
                "Render job id is available for QC artifact correlation."
                if available
                else "Render job id is missing."
            ),
            evidence_summary={"render_job_id_present": available},
        )

    def _artifact_signal(self, *, input_key: str, path: str, reason_prefix: str) -> VideoQcInputSignal:
        path_value = str(path or "").strip()
        if not path_value:
            return VideoQcInputSignal(
                input_key=input_key,
                available=False,
                used=False,
                status="missing",
                priority_rank=self._rank(input_key),
                reason_code=f"{reason_prefix}_PATH_MISSING",
                rationale=f"{input_key} path is missing.",
                evidence_summary={"path": "", "exists": False, "size_bytes": 0},
            )
        artifact_path = Path(path_value)
        exists = artifact_path.exists()
        size_bytes = self._size_bytes(artifact_path) if exists else 0
        if not exists:
            status = "missing"
            reason_code = f"{reason_prefix}_FILE_MISSING"
            rationale = f"{input_key} path was provided but the file does not exist."
            available = False
            used = False
        elif size_bytes <= 0:
            status = "degraded"
            reason_code = f"{reason_prefix}_FILE_EMPTY"
            rationale = f"{input_key} file exists but is empty."
            available = True
            used = True
        else:
            status = "available"
            reason_code = f"{reason_prefix}_AVAILABLE"
            rationale = f"{input_key} file exists and is non-empty."
            available = True
            used = True
        return VideoQcInputSignal(
            input_key=input_key,
            available=available,
            used=used,
            status=status,
            priority_rank=self._rank(input_key),
            reason_code=reason_code,
            rationale=rationale,
            evidence_summary={"path": path_value, "exists": exists, "size_bytes": size_bytes},
        )

    def _metadata_signal(self, *, path: str | None, metadata_loaded: bool) -> VideoQcInputSignal:
        path_value = str(path or "").strip()
        if not path_value:
            return VideoQcInputSignal(
                input_key="metadata_artifact",
                available=False,
                used=False,
                status="missing",
                priority_rank=self._rank("metadata_artifact"),
                reason_code="METADATA_PATH_MISSING",
                rationale="Metadata path is missing.",
                evidence_summary={"path": "", "exists": False, "metadata_loaded": False},
            )
        metadata_path = Path(path_value)
        exists = metadata_path.exists()
        size_bytes = self._size_bytes(metadata_path) if exists else 0
        if not exists:
            status = "missing"
            reason_code = "METADATA_FILE_MISSING"
            rationale = "Metadata path was provided but the file does not exist."
            available = False
            used = False
        elif size_bytes <= 0:
            status = "degraded"
            reason_code = "METADATA_FILE_EMPTY"
            rationale = "Metadata file exists but is empty."
            available = True
            used = False
        else:
            status = "available" if metadata_loaded else "degraded"
            reason_code = "METADATA_LOADED" if metadata_loaded else "METADATA_PRESENT_NOT_LOADED"
            rationale = (
                "Metadata artifact is present and was loaded by QC."
                if metadata_loaded
                else "Metadata artifact is present but was not loaded, likely because earlier hard failures prevented metadata evaluation."
            )
            available = True
            used = metadata_loaded
        return VideoQcInputSignal(
            input_key="metadata_artifact",
            available=available,
            used=used,
            status=status,
            priority_rank=self._rank("metadata_artifact"),
            reason_code=reason_code,
            rationale=rationale,
            evidence_summary={
                "path": path_value,
                "exists": exists,
                "size_bytes": size_bytes,
                "metadata_loaded": metadata_loaded,
            },
        )

    def _text_signal(self, *, input_key: str, value: str) -> VideoQcInputSignal:
        text = str(value or "").strip()
        available = bool(text)
        return VideoQcInputSignal(
            input_key=input_key,
            available=available,
            used=available,
            status="available" if available else "missing",
            priority_rank=self._rank(input_key),
            reason_code="SCRIPT_TEXT_AVAILABLE" if available else "SCRIPT_TEXT_MISSING_METADATA_CUES_USED_IF_AVAILABLE",
            rationale=(
                "Script text is available for QC product-signal scoring."
                if available
                else "Script text is missing; existing QC scoring can fall back to subtitle cue text when metadata is available."
            ),
            evidence_summary={"text_present": available, "word_count": len(text.split())},
        )

    def _trace_signal(self, *, input_key: str, payload: dict[str, Any], used_when_present: bool) -> VideoQcInputSignal:
        present = isinstance(payload, dict) and bool(payload)
        if not present:
            return VideoQcInputSignal(
                input_key=input_key,
                available=False,
                used=False,
                status="missing",
                priority_rank=self._rank(input_key),
                reason_code=f"{input_key.upper()}_MISSING",
                rationale=f"{input_key} is absent; QC must rely on artifacts and metadata for that layer.",
                evidence_summary={"present": False, "keys": []},
            )
        degraded = self._trace_degraded(input_key=input_key, payload=payload)
        if not used_when_present:
            return VideoQcInputSignal(
                input_key=input_key,
                available=True,
                used=False,
                status="ignored",
                priority_rank=self._rank(input_key),
                reason_code=f"{input_key.upper()}_PRESENT_NOT_USED_BY_CURRENT_QC",
                rationale=f"{input_key} is present but current QC logic does not consume it directly in this workstream.",
                evidence_summary={"present": True, "keys": sorted(payload.keys())},
            )
        return VideoQcInputSignal(
            input_key=input_key,
            available=True,
            used=True,
            status="degraded" if degraded else "available",
            priority_rank=self._rank(input_key),
            reason_code=f"{input_key.upper()}_DEGRADED" if degraded else f"{input_key.upper()}_AVAILABLE",
            rationale=(
                f"{input_key} is present but lacks expected detail."
                if degraded
                else f"{input_key} is available to current QC scoring."
            ),
            evidence_summary={"present": True, "keys": sorted(payload.keys())},
        )

    def _trace_degraded(self, *, input_key: str, payload: dict[str, Any]) -> bool:
        if input_key == "tts_trace":
            return "segment_durations" not in payload
        if input_key == "edit_trace":
            return not bool(payload)
        return False

    def _media_probe_signal(self, probe: dict[str, Any]) -> VideoQcInputSignal:
        probe_mode = str(probe.get("probe_mode") or "unavailable")
        ffprobe_available = shutil.which("ffprobe") is not None
        if probe_mode == "ffprobe":
            return VideoQcInputSignal(
                input_key="media_probe_capability",
                available=True,
                used=True,
                status="available",
                priority_rank=self._rank("media_probe_capability"),
                reason_code="FFPROBE_MEDIA_PROBE_USED",
                rationale="Full media probe was available and used.",
                evidence_summary={"probe_mode": probe_mode, "ffprobe_available": ffprobe_available},
            )
        if probe_mode == "metadata_fallback":
            return VideoQcInputSignal(
                input_key="media_probe_capability",
                available=ffprobe_available,
                used=False,
                status="environment_dependent",
                priority_rank=self._rank("media_probe_capability"),
                reason_code="MEDIA_PROBE_METADATA_FALLBACK_USED",
                rationale="Full media probe was unavailable or inconclusive; metadata fallback supplied dimensions/audio observability.",
                evidence_summary={"probe_mode": probe_mode, "ffprobe_available": ffprobe_available},
            )
        return VideoQcInputSignal(
            input_key="media_probe_capability",
            available=ffprobe_available,
            used=False,
            status="missing" if not ffprobe_available else "ignored",
            priority_rank=self._rank("media_probe_capability"),
            reason_code="MEDIA_PROBE_NOT_USED",
            rationale="Media probe was not used for this QC evaluation path.",
            evidence_summary={"probe_mode": probe_mode, "ffprobe_available": ffprobe_available},
        )

    def _metadata_fallback_signal(self, probe: dict[str, Any], *, metadata_loaded: bool) -> VideoQcInputSignal:
        probe_mode = str(probe.get("probe_mode") or "unavailable")
        if probe_mode == "metadata_fallback":
            return VideoQcInputSignal(
                input_key="metadata_fallback_probe",
                available=metadata_loaded,
                used=True,
                status="environment_dependent",
                priority_rank=self._rank("metadata_fallback_probe"),
                reason_code="METADATA_FALLBACK_PROBE_USED",
                rationale="Metadata fallback was used for media dimensions/audio observability.",
                evidence_summary={"probe_mode": probe_mode, "metadata_loaded": metadata_loaded},
            )
        return VideoQcInputSignal(
            input_key="metadata_fallback_probe",
            available=metadata_loaded,
            used=False,
            status="ignored" if metadata_loaded else "missing",
            priority_rank=self._rank("metadata_fallback_probe"),
            reason_code="METADATA_FALLBACK_PROBE_NOT_USED",
            rationale="Metadata fallback probe was not used.",
            evidence_summary={"probe_mode": probe_mode, "metadata_loaded": metadata_loaded},
        )

    def _artifact_summary(self, *, qc_input: VideoQcInput, metadata_loaded: bool) -> dict[str, Any]:
        return {
            "render_job_id_present": bool(str(qc_input.render_job_id or "").strip()),
            "video": self._path_summary(qc_input.video_path),
            "audio": self._path_summary(qc_input.audio_path),
            "metadata": self._path_summary(qc_input.metadata_path or ""),
            "metadata_loaded": metadata_loaded,
            "script_text_present": bool(str(qc_input.script_text or "").strip()),
            "tts_trace_present": bool(qc_input.tts_trace),
            "visual_trace_present": bool(qc_input.visual_trace),
            "edit_trace_present": bool(qc_input.edit_trace),
        }

    def _environment_summary(self, probe: dict[str, Any]) -> dict[str, Any]:
        probe_mode = str(probe.get("probe_mode") or "unavailable")
        return {
            "ffprobe_available": shutil.which("ffprobe") is not None,
            "media_probe_mode": probe_mode,
            "metadata_fallback_used": probe_mode == "metadata_fallback",
            "full_media_probe_used": probe_mode == "ffprobe",
            "probe_width": probe.get("width"),
            "probe_height": probe.get("height"),
            "probe_has_audio": probe.get("has_audio"),
        }

    def _path_summary(self, path: str) -> dict[str, Any]:
        path_value = str(path or "").strip()
        if not path_value:
            return {"path": "", "exists": False, "size_bytes": 0}
        value = Path(path_value)
        exists = value.exists()
        return {
            "path": path_value,
            "exists": exists,
            "size_bytes": self._size_bytes(value) if exists else 0,
        }

    def _size_bytes(self, path: Path) -> int:
        try:
            return int(path.stat().st_size)
        except OSError:
            return 0
