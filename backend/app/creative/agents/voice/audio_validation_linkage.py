from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.creative.contracts.creative_pack import VoicePlan


VOICE_AUDIO_VALIDATION_LINKAGE_VERSION = "voice_audio_validation_linkage_v2_6"


@dataclass(frozen=True)
class VoiceAudioValidationLinkageResult:
    linkage_version: str
    audio_trace_available: bool
    provider_execution_verified: bool
    duration_available: bool
    segment_durations_available: bool
    provider_requested: str
    provider_executed: str | None
    voice_id_requested: str
    voice_id_executed: str | None
    fallback_used: bool | None
    fallback_reason: str | None
    audio_duration_s: float | None
    segment_durations: list[float]
    audio_artifact_path: str | None
    audio_artifact_status: str
    validation_status: str
    missing_evidence: list[str] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)
    boundary_statement: str = "Voice links audio validation evidence only when supplied; it does not synthesize or inspect audio files."

    def to_dict(self) -> dict[str, Any]:
        return {
            "linkage_version": self.linkage_version,
            "audio_trace_available": self.audio_trace_available,
            "provider_execution_verified": self.provider_execution_verified,
            "duration_available": self.duration_available,
            "segment_durations_available": self.segment_durations_available,
            "provider_requested": self.provider_requested,
            "provider_executed": self.provider_executed,
            "voice_id_requested": self.voice_id_requested,
            "voice_id_executed": self.voice_id_executed,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
            "audio_duration_s": self.audio_duration_s,
            "segment_durations": list(self.segment_durations),
            "audio_artifact_path": self.audio_artifact_path,
            "audio_artifact_status": self.audio_artifact_status,
            "validation_status": self.validation_status,
            "missing_evidence": list(self.missing_evidence),
            "reason_codes": list(self.reason_codes),
            "rationale": list(self.rationale),
            "boundary_statement": self.boundary_statement,
        }


class VoiceAudioValidationLinker:
    """Links provided TTS/audio trace evidence without reading audio artifacts."""

    def link(
        self,
        *,
        voice_plan: VoicePlan,
        tts_trace: Any | None = None,
        audio_artifact: Any | None = None,
    ) -> VoiceAudioValidationLinkageResult:
        trace = self._trace_dict(tts_trace)
        artifact = self._artifact_dict(audio_artifact)
        audio_trace_available = bool(trace)
        provider_requested = str(voice_plan.provider or "").strip().lower()
        voice_id_requested = str(voice_plan.voice_id or "").strip()
        provider_executed = self._trace_value(trace, "provider_executed")
        voice_id_executed = self._trace_value(trace, "voice_id_executed")
        fallback_used = self._trace_bool(trace, "fallback_used")
        fallback_reason = self._trace_value(trace, "fallback_reason")
        audio_duration_s = self._trace_float(trace, "audio_duration_s")
        segment_durations = self._trace_float_list(trace, "segment_durations")
        audio_artifact_path = self._artifact_path(artifact)

        provider_execution_verified = bool(
            audio_trace_available
            and provider_executed
            and str(trace.get("provider_requested") or "").strip().lower() == provider_requested
        )
        duration_available = audio_duration_s is not None and audio_duration_s > 0.0
        segment_durations_available = bool(segment_durations) and all(value > 0.0 for value in segment_durations)
        missing_evidence = self._missing_evidence(
            audio_trace_available=audio_trace_available,
            provider_execution_verified=provider_execution_verified,
            duration_available=duration_available,
            segment_durations_available=segment_durations_available,
            audio_artifact_path=audio_artifact_path,
        )
        audio_artifact_status = "provided_not_inspected" if audio_artifact_path else "not_provided"
        validation_status = self._validation_status(
            audio_trace_available=audio_trace_available,
            provider_execution_verified=provider_execution_verified,
            duration_available=duration_available,
            segment_durations_available=segment_durations_available,
        )
        reason_codes = self._reason_codes(
            audio_trace_available=audio_trace_available,
            provider_execution_verified=provider_execution_verified,
            duration_available=duration_available,
            segment_durations_available=segment_durations_available,
            audio_artifact_path=audio_artifact_path,
        )
        rationale = self._rationale(
            audio_trace_available=audio_trace_available,
            provider_execution_verified=provider_execution_verified,
            duration_available=duration_available,
            segment_durations_available=segment_durations_available,
            audio_artifact_status=audio_artifact_status,
            reason_codes=reason_codes,
        )
        return VoiceAudioValidationLinkageResult(
            linkage_version=VOICE_AUDIO_VALIDATION_LINKAGE_VERSION,
            audio_trace_available=audio_trace_available,
            provider_execution_verified=provider_execution_verified,
            duration_available=duration_available,
            segment_durations_available=segment_durations_available,
            provider_requested=provider_requested,
            provider_executed=provider_executed,
            voice_id_requested=voice_id_requested,
            voice_id_executed=voice_id_executed,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            audio_duration_s=audio_duration_s,
            segment_durations=segment_durations,
            audio_artifact_path=audio_artifact_path,
            audio_artifact_status=audio_artifact_status,
            validation_status=validation_status,
            missing_evidence=missing_evidence,
            reason_codes=reason_codes,
            rationale=rationale,
        )

    def _trace_dict(self, trace: Any | None) -> dict[str, Any]:
        if trace is None:
            return {}
        if isinstance(trace, dict):
            return dict(trace)
        if hasattr(trace, "to_dict"):
            value = trace.to_dict()
            return dict(value) if isinstance(value, dict) else {}
        if hasattr(trace, "__dict__"):
            return dict(vars(trace))
        return {}

    def _artifact_dict(self, artifact: Any | None) -> dict[str, Any]:
        if artifact is None:
            return {}
        if isinstance(artifact, dict):
            return dict(artifact)
        if isinstance(artifact, str):
            return {"path": artifact}
        if hasattr(artifact, "to_dict"):
            value = artifact.to_dict()
            return dict(value) if isinstance(value, dict) else {}
        if hasattr(artifact, "__dict__"):
            return dict(vars(artifact))
        return {}

    def _trace_value(self, trace: dict[str, Any], key: str) -> str | None:
        value = trace.get(key)
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    def _trace_bool(self, trace: dict[str, Any], key: str) -> bool | None:
        if key not in trace:
            return None
        return bool(trace.get(key))

    def _trace_float(self, trace: dict[str, Any], key: str) -> float | None:
        if key not in trace:
            return None
        try:
            value = float(trace.get(key))
        except (TypeError, ValueError):
            return None
        return round(value, 3) if value > 0.0 else None

    def _trace_float_list(self, trace: dict[str, Any], key: str) -> list[float]:
        values = trace.get(key) or []
        if not isinstance(values, list):
            return []
        output: list[float] = []
        for value in values:
            try:
                parsed = float(value)
            except (TypeError, ValueError):
                return []
            output.append(round(parsed, 3))
        return output

    def _artifact_path(self, artifact: dict[str, Any]) -> str | None:
        for key in ("audio_path", "path", "audio"):
            value = artifact.get(key)
            if value:
                normalized = str(value).strip()
                if normalized:
                    return normalized
        return None

    def _missing_evidence(
        self,
        *,
        audio_trace_available: bool,
        provider_execution_verified: bool,
        duration_available: bool,
        segment_durations_available: bool,
        audio_artifact_path: str | None,
    ) -> list[str]:
        missing: list[str] = []
        if not audio_trace_available:
            missing.append("tts_trace")
        if not provider_execution_verified:
            missing.append("provider_execution_verification")
        if not duration_available:
            missing.append("audio_duration_s")
        if not segment_durations_available:
            missing.append("segment_durations")
        if not audio_artifact_path:
            missing.append("audio_artifact_path")
        return missing

    def _validation_status(
        self,
        *,
        audio_trace_available: bool,
        provider_execution_verified: bool,
        duration_available: bool,
        segment_durations_available: bool,
    ) -> str:
        if provider_execution_verified and duration_available and segment_durations_available:
            return "linked"
        if audio_trace_available:
            return "partial"
        return "missing_trace"

    def _reason_codes(
        self,
        *,
        audio_trace_available: bool,
        provider_execution_verified: bool,
        duration_available: bool,
        segment_durations_available: bool,
        audio_artifact_path: str | None,
    ) -> list[str]:
        codes: list[str] = []
        codes.append("AUDIO_TRACE_AVAILABLE" if audio_trace_available else "AUDIO_TRACE_MISSING")
        codes.append("PROVIDER_EXECUTION_VERIFIED" if provider_execution_verified else "PROVIDER_EXECUTION_NOT_VERIFIED")
        codes.append("AUDIO_DURATION_AVAILABLE" if duration_available else "AUDIO_DURATION_MISSING")
        codes.append(
            "SEGMENT_DURATIONS_AVAILABLE"
            if segment_durations_available
            else "SEGMENT_DURATIONS_MISSING"
        )
        codes.append("AUDIO_ARTIFACT_PATH_PROVIDED_NOT_INSPECTED" if audio_artifact_path else "AUDIO_ARTIFACT_PATH_MISSING")
        return codes

    def _rationale(
        self,
        *,
        audio_trace_available: bool,
        provider_execution_verified: bool,
        duration_available: bool,
        segment_durations_available: bool,
        audio_artifact_status: str,
        reason_codes: list[str],
    ) -> list[str]:
        return [
            "Audio validation linkage consumes provided TTS trace only; it does not synthesize audio or inspect files.",
            f"Audio trace available: {audio_trace_available}; provider execution verified: {provider_execution_verified}.",
            f"Duration available: {duration_available}; segment durations available: {segment_durations_available}.",
            f"Audio artifact status: {audio_artifact_status}.",
            "Reason codes: " + ", ".join(reason_codes),
        ]
