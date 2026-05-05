from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


VOICE_CONFIDENCE_VERSION = "voice_confidence_calibration_v2_6"


@dataclass(frozen=True)
class VoiceConfidenceCalibrationResult:
    confidence_version: str
    confidence: float
    confidence_level: str
    confidence_components: dict[str, float]
    confidence_rationale: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "confidence_version": self.confidence_version,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level,
            "confidence_components": dict(self.confidence_components),
            "confidence_rationale": dict(self.confidence_rationale),
        }


class VoiceConfidenceCalibrator:
    """Calibrates trust in voice plan execution readiness, not audio performance."""

    def calibrate(
        self,
        *,
        voice_plan_governance: dict[str, Any],
        delivery_semantics: dict[str, Any],
        segment_timing: dict[str, Any],
        monotony_contrast_analysis: dict[str, Any],
        provider_fallback_honesty: dict[str, Any],
        audio_validation_linkage: dict[str, Any],
    ) -> VoiceConfidenceCalibrationResult:
        components = {
            "contract_completeness": self._contract_completeness(voice_plan_governance),
            "delivery_semantics": self._delivery_semantics(delivery_semantics),
            "timing_completeness": self._timing_completeness(segment_timing),
            "contrast_strength": self._contrast_strength(monotony_contrast_analysis),
            "provider_trace_quality": self._provider_trace_quality(provider_fallback_honesty),
            "audio_validation_support": self._audio_validation_support(audio_validation_linkage),
            "fallback_penalty": self._fallback_penalty(provider_fallback_honesty, audio_validation_linkage),
        }
        base = (
            components["contract_completeness"] * 0.18
            + components["delivery_semantics"] * 0.14
            + components["timing_completeness"] * 0.16
            + components["contrast_strength"] * 0.14
            + components["provider_trace_quality"] * 0.14
            + components["audio_validation_support"] * 0.18
        )
        confidence = self._clamp(base - components["fallback_penalty"])
        penalties = self._penalties(
            voice_plan_governance=voice_plan_governance,
            delivery_semantics=delivery_semantics,
            segment_timing=segment_timing,
            monotony_contrast_analysis=monotony_contrast_analysis,
            provider_fallback_honesty=provider_fallback_honesty,
            audio_validation_linkage=audio_validation_linkage,
            fallback_penalty=components["fallback_penalty"],
        )
        # Voice Agent has not observed TTS execution when trace is missing; do not allow high confidence.
        if not bool(audio_validation_linkage.get("audio_trace_available")):
            confidence = min(confidence, 0.68)
            if "AUDIO_TRACE_MISSING_CAP_APPLIED" not in penalties:
                penalties.append("AUDIO_TRACE_MISSING_CAP_APPLIED")
        if monotony_contrast_analysis.get("monotony_risk_level") == "high":
            confidence = min(confidence, 0.64)
            if "HIGH_MONOTONY_CAP_APPLIED" not in penalties:
                penalties.append("HIGH_MONOTONY_CAP_APPLIED")
        elif monotony_contrast_analysis.get("monotony_risk_level") == "medium":
            confidence = min(confidence, 0.78)
            if "MEDIUM_MONOTONY_CAP_APPLIED" not in penalties:
                penalties.append("MEDIUM_MONOTONY_CAP_APPLIED")
        confidence = round(confidence, 3)
        level = self._level(confidence)
        confidence_rationale = {
            "confidence_meaning": "trust_in_voice_plan_execution_readiness",
            "penalties": penalties,
            "boundary_statement": "Voice confidence is not performance prediction.",
            "evidence_summary": {
                "contract_complete": bool(voice_plan_governance.get("contract_complete")),
                "semantics_complete": bool(delivery_semantics.get("semantics_complete")),
                "timing_complete": bool(segment_timing.get("timing_complete")),
                "monotony_risk_level": str(monotony_contrast_analysis.get("monotony_risk_level") or "unknown"),
                "contrast_level": str(monotony_contrast_analysis.get("contrast_level") or "unknown"),
                "provider_order_preserved": bool(provider_fallback_honesty.get("provider_order_preserved")),
                "audio_trace_available": bool(audio_validation_linkage.get("audio_trace_available")),
                "provider_execution_verified": bool(audio_validation_linkage.get("provider_execution_verified")),
                "validation_status": str(audio_validation_linkage.get("validation_status") or "unknown"),
            },
            "rationale": self._rationale(components=components, confidence=confidence, level=level, penalties=penalties),
        }
        return VoiceConfidenceCalibrationResult(
            confidence_version=VOICE_CONFIDENCE_VERSION,
            confidence=confidence,
            confidence_level=level,
            confidence_components=components,
            confidence_rationale=confidence_rationale,
        )

    def _contract_completeness(self, governance: dict[str, Any]) -> float:
        if governance.get("contract_complete") and governance.get("policy_respected"):
            return 1.0
        missing_count = len(governance.get("missing_fields") or [])
        degraded_count = len(governance.get("degraded_fields") or [])
        return self._clamp(0.85 - (missing_count * 0.18) - (degraded_count * 0.12))

    def _delivery_semantics(self, semantics: dict[str, Any]) -> float:
        if semantics.get("semantics_complete"):
            return 1.0
        missing_count = len(semantics.get("missing_or_degraded_inputs") or [])
        supported_segments = sum(
            1
            for segment in (semantics.get("segment_semantics") or {}).values()
            if segment.get("mapping_supported")
        )
        base = supported_segments / 3.0
        return self._clamp(base - (missing_count * 0.08))

    def _timing_completeness(self, timing: dict[str, Any]) -> float:
        if timing.get("timing_complete"):
            return 1.0
        degraded_count = len(timing.get("missing_or_degraded_inputs") or [])
        valid_segments = sum(
            1
            for segment in (timing.get("segment_timing") or {}).values()
            if segment.get("timing_valid")
        )
        base = valid_segments / 3.0
        return self._clamp(base - (degraded_count * 0.06))

    def _contrast_strength(self, monotony: dict[str, Any]) -> float:
        monotony_level = str(monotony.get("monotony_risk_level") or "high")
        contrast_level = str(monotony.get("contrast_level") or "low")
        if monotony_level == "low" and contrast_level == "high":
            return 1.0
        if monotony_level == "medium" or contrast_level == "medium":
            return 0.62
        return 0.22

    def _provider_trace_quality(self, provider_honesty: dict[str, Any]) -> float:
        if provider_honesty.get("real_tts_execution_trace_present") and provider_honesty.get("tts_executed_provider"):
            return 1.0
        if provider_honesty.get("provider_order_preserved") and provider_honesty.get("honest"):
            return 0.62
        return 0.32

    def _audio_validation_support(self, audio_linkage: dict[str, Any]) -> float:
        status = str(audio_linkage.get("validation_status") or "missing_trace")
        if status == "linked":
            return 1.0
        if status == "partial":
            return 0.48
        return 0.12

    def _fallback_penalty(self, provider_honesty: dict[str, Any], audio_linkage: dict[str, Any]) -> float:
        penalty = 0.0
        if provider_honesty.get("fallback_allowed") and not provider_honesty.get("real_tts_execution_trace_present"):
            penalty += 0.05
        if provider_honesty.get("tts_fallback_used") is True:
            penalty += 0.14
        if audio_linkage.get("fallback_used") is True:
            penalty += 0.10
        return round(self._clamp(penalty), 3)

    def _penalties(
        self,
        *,
        voice_plan_governance: dict[str, Any],
        delivery_semantics: dict[str, Any],
        segment_timing: dict[str, Any],
        monotony_contrast_analysis: dict[str, Any],
        provider_fallback_honesty: dict[str, Any],
        audio_validation_linkage: dict[str, Any],
        fallback_penalty: float,
    ) -> list[str]:
        penalties: list[str] = []
        if not voice_plan_governance.get("contract_complete"):
            penalties.append("VOICE_PLAN_CONTRACT_INCOMPLETE")
        if not delivery_semantics.get("semantics_complete"):
            penalties.append("DELIVERY_SEMANTICS_INCOMPLETE")
        if not segment_timing.get("timing_complete"):
            penalties.append("SEGMENT_TIMING_INCOMPLETE")
        if monotony_contrast_analysis.get("monotony_risk_level") == "high":
            penalties.append("HIGH_MONOTONY_RISK")
        elif monotony_contrast_analysis.get("monotony_risk_level") == "medium":
            penalties.append("MEDIUM_MONOTONY_RISK")
        if not provider_fallback_honesty.get("real_tts_execution_trace_present"):
            penalties.append("TTS_EXECUTION_TRACE_MISSING")
        if not audio_validation_linkage.get("provider_execution_verified"):
            penalties.append("PROVIDER_EXECUTION_NOT_VERIFIED")
        if not audio_validation_linkage.get("duration_available"):
            penalties.append("AUDIO_DURATION_MISSING")
        if not audio_validation_linkage.get("segment_durations_available"):
            penalties.append("SEGMENT_DURATIONS_MISSING")
        if fallback_penalty > 0.0:
            penalties.append("FALLBACK_PENALTY_APPLIED")
        return self._unique(penalties)

    def _rationale(
        self,
        *,
        components: dict[str, float],
        confidence: float,
        level: str,
        penalties: list[str],
    ) -> list[str]:
        return [
            "Voice confidence measures trust in voice plan execution readiness, not audio quality or performance.",
            "Components used: " + ", ".join(f"{key}={value}" for key, value in components.items()),
            f"Final confidence is {confidence} ({level}).",
            "Penalties: " + (", ".join(penalties) if penalties else "none"),
        ]

    def _level(self, confidence: float) -> str:
        if confidence < 0.35:
            return "low"
        if confidence < 0.70:
            return "medium"
        return "high"

    def _clamp(self, value: float) -> float:
        return round(max(0.0, min(1.0, float(value))), 3)

    def _unique(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        output: list[str] = []
        for value in values:
            if not value or value in seen:
                continue
            seen.add(value)
            output.append(value)
        return output
