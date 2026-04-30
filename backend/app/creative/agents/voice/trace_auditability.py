from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import VoicePlan


VOICE_TRACE_VERSION = "voice_trace_v2_6"

REQUIRED_VOICE_TRACE_SECTIONS: tuple[str, ...] = (
    "voice_plan_governance",
    "delivery_semantics",
    "segment_timing",
    "monotony_contrast_analysis",
    "provider_fallback_honesty",
    "audio_validation_linkage",
    "confidence_calibration",
    "final_voice_plan_rationale",
    "missing_or_degraded_inputs",
    "audit_summary",
)


@dataclass(frozen=True)
class VoiceTraceResult:
    voice_trace: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.voice_trace)


class VoiceTraceBuilder:
    """Consolidates Voice v2.6 audit sections without recalculating them."""

    def build(
        self,
        *,
        voice_plan: VoicePlan,
        fallback: FallbackDecision,
        voice_plan_governance: dict[str, Any],
        delivery_semantics: dict[str, Any],
        segment_timing: dict[str, Any],
        monotony_contrast_analysis: dict[str, Any],
        provider_fallback_honesty: dict[str, Any],
        audio_validation_linkage: dict[str, Any],
        confidence_calibration: dict[str, Any],
    ) -> VoiceTraceResult:
        final_rationale = self._final_voice_plan_rationale(
            voice_plan=voice_plan,
            fallback=fallback,
            voice_plan_governance=voice_plan_governance,
            delivery_semantics=delivery_semantics,
            segment_timing=segment_timing,
            monotony_contrast_analysis=monotony_contrast_analysis,
            provider_fallback_honesty=provider_fallback_honesty,
            audio_validation_linkage=audio_validation_linkage,
            confidence_calibration=confidence_calibration,
        )
        missing_or_degraded = self._missing_or_degraded_inputs(
            voice_plan_governance=voice_plan_governance,
            delivery_semantics=delivery_semantics,
            segment_timing=segment_timing,
            monotony_contrast_analysis=monotony_contrast_analysis,
            provider_fallback_honesty=provider_fallback_honesty,
            audio_validation_linkage=audio_validation_linkage,
            confidence_calibration=confidence_calibration,
        )
        trace_without_audit = {
            "trace_version": VOICE_TRACE_VERSION,
            "voice_plan_governance": dict(voice_plan_governance),
            "delivery_semantics": dict(delivery_semantics),
            "segment_timing": dict(segment_timing),
            "monotony_contrast_analysis": dict(monotony_contrast_analysis),
            "provider_fallback_honesty": dict(provider_fallback_honesty),
            "audio_validation_linkage": dict(audio_validation_linkage),
            "confidence_calibration": dict(confidence_calibration),
            "final_voice_plan_rationale": final_rationale,
            "missing_or_degraded_inputs": missing_or_degraded,
        }
        trace = dict(trace_without_audit)
        trace["audit_summary"] = self._audit_summary(trace_without_audit)
        return VoiceTraceResult(voice_trace=trace)

    def _final_voice_plan_rationale(
        self,
        *,
        voice_plan: VoicePlan,
        fallback: FallbackDecision,
        voice_plan_governance: dict[str, Any],
        delivery_semantics: dict[str, Any],
        segment_timing: dict[str, Any],
        monotony_contrast_analysis: dict[str, Any],
        provider_fallback_honesty: dict[str, Any],
        audio_validation_linkage: dict[str, Any],
        confidence_calibration: dict[str, Any],
    ) -> dict[str, Any]:
        provider_requested = str(voice_plan.provider or "")
        fallback_order = list(voice_plan.runtime_constraints.fallback_order or [])
        confidence_level = str(confidence_calibration.get("confidence_level") or "low")
        validation_status = str(audio_validation_linkage.get("validation_status") or "unknown")
        rationale = [
            "VoicePlan was emitted by the Voice Agent interpreter and not recalculated by trace consolidation.",
            f"Requested provider is {provider_requested}; fallback order is {fallback_order}.",
            f"Contract complete: {bool(voice_plan_governance.get('contract_complete'))}; semantics complete: {bool(delivery_semantics.get('semantics_complete'))}; timing complete: {bool(segment_timing.get('timing_complete'))}.",
            f"Monotony risk is {monotony_contrast_analysis.get('monotony_risk_level')}; contrast level is {monotony_contrast_analysis.get('contrast_level')}.",
            f"Audio validation status is {validation_status}; confidence level is {confidence_level}.",
        ]
        return {
            "voice_plan_emitted": True,
            "provider_requested": provider_requested,
            "voice_id_requested": str(voice_plan.voice_id or ""),
            "style_requested": str(voice_plan.style or ""),
            "fallback_order": fallback_order,
            "voice_agent_fallback_used": bool(fallback.used),
            "contract_complete": bool(voice_plan_governance.get("contract_complete")),
            "semantics_complete": bool(delivery_semantics.get("semantics_complete")),
            "timing_complete": bool(segment_timing.get("timing_complete")),
            "monotony_risk_level": str(monotony_contrast_analysis.get("monotony_risk_level") or "unknown"),
            "contrast_level": str(monotony_contrast_analysis.get("contrast_level") or "unknown"),
            "audio_validation_status": validation_status,
            "provider_execution_verified": bool(audio_validation_linkage.get("provider_execution_verified")),
            "confidence": float(confidence_calibration.get("confidence") or 0.0),
            "confidence_level": confidence_level,
            "boundary_statement": "Voice trace reconstructs the voice plan only; TTS Router remains execution authority.",
            "rationale": rationale,
        }

    def _missing_or_degraded_inputs(
        self,
        *,
        voice_plan_governance: dict[str, Any],
        delivery_semantics: dict[str, Any],
        segment_timing: dict[str, Any],
        monotony_contrast_analysis: dict[str, Any],
        provider_fallback_honesty: dict[str, Any],
        audio_validation_linkage: dict[str, Any],
        confidence_calibration: dict[str, Any],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for field_name in voice_plan_governance.get("missing_fields") or []:
            items.append(self._item("missing_field", field_name, "voice_plan_governance", "Required VoicePlan contract field is missing."))
        for field_name in voice_plan_governance.get("degraded_fields") or []:
            items.append(self._item("degraded_field", field_name, "voice_plan_governance", "VoicePlan contract field is present but degraded."))
        for field_name in delivery_semantics.get("missing_or_degraded_inputs") or []:
            items.append(self._item("semantic_input", field_name, "delivery_semantics", "Delivery semantic support is missing or degraded."))
        for field_name in segment_timing.get("missing_or_degraded_inputs") or []:
            items.append(self._item("timing_input", field_name, "segment_timing", "Segment timing evidence is missing or degraded."))
        for field_name in monotony_contrast_analysis.get("missing_or_degraded_inputs") or []:
            items.append(self._item("monotony_input", field_name, "monotony_contrast_analysis", "Monotony/contrast analysis input is missing or degraded."))
        if provider_fallback_honesty.get("real_tts_execution_trace_present") is False:
            items.append(self._item("missing_trace", "tts_execution_trace", "provider_fallback_honesty", "TTS execution trace is not available to Voice Agent."))
        for field_name in audio_validation_linkage.get("missing_evidence") or []:
            items.append(self._item("missing_audio_evidence", field_name, "audio_validation_linkage", "Audio validation evidence is unavailable or incomplete."))
        for penalty in (confidence_calibration.get("confidence_rationale") or {}).get("penalties") or []:
            items.append(self._item("confidence_penalty", penalty, "confidence_calibration", "Confidence calibration applied this penalty."))
        return self._unique_items(items)

    def _audit_summary(self, trace: dict[str, Any]) -> dict[str, Any]:
        missing_sections = [
            section
            for section in REQUIRED_VOICE_TRACE_SECTIONS
            if section != "audit_summary" and section not in trace
        ]
        section_empty = [
            section
            for section in REQUIRED_VOICE_TRACE_SECTIONS
            if section != "audit_summary" and section in trace and trace.get(section) in ({}, [], None)
        ]
        silent_failure_indicators = [f"MISSING_SECTION:{section}" for section in missing_sections]
        silent_failure_indicators.extend(f"EMPTY_SECTION:{section}" for section in section_empty)
        required_sections_present = not missing_sections and not section_empty
        fallback_visible = "provider_fallback_honesty" in trace and bool(
            trace.get("provider_fallback_honesty", {}).get("voice_agent_fallback") is not None
        )
        audio_trace_status_visible = "audio_validation_linkage" in trace and bool(
            trace.get("audio_validation_linkage", {}).get("validation_status")
        )
        confidence_visible = "confidence_calibration" in trace and "confidence" in trace.get("confidence_calibration", {})
        final_rationale_visible = bool(trace.get("final_voice_plan_rationale", {}).get("voice_plan_emitted"))
        reconstructible = (
            required_sections_present
            and fallback_visible
            and audio_trace_status_visible
            and confidence_visible
            and final_rationale_visible
        )
        return {
            "reconstructible": reconstructible,
            "required_sections_present": required_sections_present,
            "decision_trace_backward_compatible": True,
            "voice_plan_governance_present": "voice_plan_governance" in trace,
            "delivery_semantics_present": "delivery_semantics" in trace,
            "segment_timing_present": "segment_timing" in trace,
            "monotony_contrast_present": "monotony_contrast_analysis" in trace,
            "provider_fallback_honesty_present": "provider_fallback_honesty" in trace,
            "audio_validation_linkage_present": "audio_validation_linkage" in trace,
            "confidence_calibration_present": "confidence_calibration" in trace,
            "fallback_visible": fallback_visible,
            "audio_trace_status_visible": audio_trace_status_visible,
            "confidence_visible": confidence_visible,
            "silent_failure_indicators": silent_failure_indicators,
        }

    def _item(self, kind: str, identifier: str, source: str, rationale: str) -> dict[str, Any]:
        return {
            "kind": kind,
            "identifier": identifier,
            "source": source,
            "rationale": rationale,
        }

    def _unique_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[tuple[str, str, str]] = set()
        output: list[dict[str, Any]] = []
        for item in items:
            key = (str(item.get("kind")), str(item.get("identifier")), str(item.get("source")))
            if key in seen:
                continue
            seen.add(key)
            output.append(item)
        return output
