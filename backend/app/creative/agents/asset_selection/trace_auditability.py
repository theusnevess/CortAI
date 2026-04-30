from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import AssetPlan


ASSET_TRACE_VERSION = "asset_trace_auditability_v2_6"


REQUIRED_TRACE_SECTIONS = [
    "asset_context_governance",
    "catalog_governance",
    "segment_visual_intent",
    "visual_alignment",
    "visual_truthfulness",
    "asset_fallback_honesty",
    "asset_diversity",
    "confidence_calibration",
    "final_asset_plan_rationale",
    "missing_or_degraded_inputs",
    "audit_summary",
]


@dataclass(frozen=True)
class AssetTraceBuilder:
    """Consolidates existing Asset Selection audit sections without recalculation."""

    def build(
        self,
        *,
        asset_selection: AssetPlan,
        fallback: FallbackDecision,
        asset_context_governance: dict[str, Any],
        asset_source_governance: dict[str, Any],
        segment_visual_intent: dict[str, Any],
        visual_alignment: dict[str, Any],
        visual_truthfulness: dict[str, Any],
        asset_fallback_honesty: dict[str, Any],
        asset_diversity: dict[str, Any],
        confidence: float,
        confidence_level: str,
        confidence_components: dict[str, float],
        confidence_rationale: dict[str, Any],
    ) -> dict[str, Any]:
        confidence_calibration = {
            "confidence": confidence,
            "confidence_level": confidence_level,
            "confidence_components": dict(confidence_components),
            "confidence_rationale": dict(confidence_rationale),
        }
        final_rationale = self._final_asset_plan_rationale(
            asset_selection=asset_selection,
            fallback=fallback,
            visual_alignment=visual_alignment,
            visual_truthfulness=visual_truthfulness,
            asset_fallback_honesty=asset_fallback_honesty,
            asset_diversity=asset_diversity,
            confidence=confidence,
            confidence_level=confidence_level,
            confidence_rationale=confidence_rationale,
        )
        missing_or_degraded = self._missing_or_degraded_inputs(
            asset_context_governance=asset_context_governance,
            asset_source_governance=asset_source_governance,
            segment_visual_intent=segment_visual_intent,
            visual_alignment=visual_alignment,
            visual_truthfulness=visual_truthfulness,
            asset_fallback_honesty=asset_fallback_honesty,
            asset_diversity=asset_diversity,
            confidence_rationale=confidence_rationale,
        )
        trace_without_summary = {
            "trace_version": ASSET_TRACE_VERSION,
            "asset_context_governance": dict(asset_context_governance),
            "catalog_governance": dict(asset_source_governance),
            "segment_visual_intent": dict(segment_visual_intent),
            "visual_alignment": dict(visual_alignment),
            "visual_truthfulness": dict(visual_truthfulness),
            "asset_fallback_honesty": dict(asset_fallback_honesty),
            "asset_diversity": dict(asset_diversity),
            "confidence_calibration": confidence_calibration,
            "final_asset_plan_rationale": final_rationale,
            "missing_or_degraded_inputs": missing_or_degraded,
        }
        audit_summary = self._audit_summary(
            trace=trace_without_summary,
            fallback=fallback,
            confidence_rationale=confidence_rationale,
            visual_alignment=visual_alignment,
        )
        return {
            **trace_without_summary,
            "audit_summary": audit_summary,
        }

    def _final_asset_plan_rationale(
        self,
        *,
        asset_selection: AssetPlan,
        fallback: FallbackDecision,
        visual_alignment: dict[str, Any],
        visual_truthfulness: dict[str, Any],
        asset_fallback_honesty: dict[str, Any],
        asset_diversity: dict[str, Any],
        confidence: float,
        confidence_level: str,
        confidence_rationale: dict[str, Any],
    ) -> dict[str, Any]:
        selected_paths = [asset_selection.hook_asset, asset_selection.setup_asset, asset_selection.payoff_asset]
        assets_emitted = all(bool(str(path or "").strip()) for path in selected_paths)
        selection_mode = "fallback_safe_default" if fallback.used else "catalog_match"
        alignment_level = str(visual_alignment.get("overall_alignment_level") or "unknown")
        truthfulness_level = str(visual_truthfulness.get("overall_risk_level") or "unknown")
        diversity_risk = self._diversity_risk(asset_diversity)
        dominant_reason_codes = self._dominant_reason_codes(
            fallback=fallback,
            visual_alignment=visual_alignment,
            visual_truthfulness=visual_truthfulness,
            asset_fallback_honesty=asset_fallback_honesty,
            asset_diversity=asset_diversity,
            confidence_rationale=confidence_rationale,
        )
        rationale = [
            f"Asset plan emitted with selection mode {selection_mode}.",
            f"Confidence is {confidence} ({confidence_level}).",
            f"Overall alignment is {alignment_level}.",
            f"Visual truthfulness risk is {truthfulness_level}.",
            f"Diversity risk is {diversity_risk}.",
        ]
        if fallback.used:
            rationale.append("Fallback is visible and treated as weak visual evidence.")
        if visual_alignment.get("mismatched_segments"):
            rationale.append("Visual semantic mismatches are explicitly exposed.")
        if asset_diversity.get("repeated_asset_detected") or asset_diversity.get("repeated_category_detected"):
            rationale.append("Asset/category repetition is explicitly exposed.")

        return {
            "assets_emitted": assets_emitted,
            "selection_mode": selection_mode,
            "fallback_used": fallback.used,
            "confidence": confidence,
            "confidence_level": confidence_level,
            "alignment_level": alignment_level,
            "truthfulness_level": truthfulness_level,
            "diversity_risk": diversity_risk,
            "dominant_reason_codes": dominant_reason_codes,
            "boundary_statement": "Asset Selection explains visual choice; QC retains final authority.",
            "rationale": rationale,
        }

    def _missing_or_degraded_inputs(
        self,
        *,
        asset_context_governance: dict[str, Any],
        asset_source_governance: dict[str, Any],
        segment_visual_intent: dict[str, Any],
        visual_alignment: dict[str, Any],
        visual_truthfulness: dict[str, Any],
        asset_fallback_honesty: dict[str, Any],
        asset_diversity: dict[str, Any],
        confidence_rationale: dict[str, Any],
    ) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        for context_key in sorted(asset_context_governance.get("missing_context") or []):
            items.append(self._item("missing_context", context_key, "context_governance", "Context is missing from Asset Selection input."))
        for context_key in sorted(asset_context_governance.get("degraded_context") or []):
            items.append(self._item("degraded_context", context_key, "context_governance", "Context is present but degraded or fallback-derived."))

        for limitation in sorted(asset_source_governance.get("coverage_limitations") or []):
            if limitation == "NO_CATALOG_SOURCE_LIMITATIONS_DETECTED":
                continue
            items.append(self._item("catalog_coverage_limitation", limitation, "catalog_governance", "Catalog/source governance reported a coverage limitation."))
        for source in asset_source_governance.get("selected_sources") or []:
            if source.get("governance_status") not in {"accepted", ""}:
                identifier = str(source.get("path") or source.get("segment") or "selected_source")
                items.append(self._item("selected_source_issue", identifier, "catalog_governance", str(source.get("rationale") or "Selected source is not fully accepted.")))

        for segment in sorted(segment_visual_intent.get("missing_segments") or []):
            items.append(self._item("missing_segment_intent", segment, "segment_visual_intent", "Segment visual intent is missing."))
        for segment in sorted(segment_visual_intent.get("degraded_segments") or []):
            items.append(self._item("degraded_segment_intent", segment, "segment_visual_intent", "Segment visual intent is degraded."))

        for segment in sorted(visual_alignment.get("mismatched_segments") or []):
            items.append(self._item("visual_mismatch", segment, "visual_alignment", "Selected asset metadata does not fully match requested visual intent."))
        for segment in sorted(visual_alignment.get("missing_metadata_segments") or []):
            items.append(self._item("missing_asset_metadata", segment, "visual_alignment", "Selected asset metadata is missing or unobservable."))

        for segment in sorted(visual_truthfulness.get("high_risk_segments") or []):
            items.append(self._item("truthfulness_high_risk", segment, "visual_truthfulness", "Visual truthfulness risk is high."))
        for segment in sorted(visual_truthfulness.get("unsupported_claim_segments") or []):
            items.append(self._item("unsupported_visual_claim", segment, "visual_truthfulness", "Visual claim is not supported by catalog metadata."))
        for segment in sorted(visual_truthfulness.get("generic_or_fallback_segments") or []):
            items.append(self._item("generic_or_fallback_visual_risk", segment, "visual_truthfulness", "Asset is generic or fallback-derived and should not be treated as strong visual evidence."))

        for segment in sorted(asset_fallback_honesty.get("fallback_segments") or []):
            items.append(self._item("fallback_used", segment, "asset_fallback_honesty", "Fallback usage is explicitly reported."))
        for segment in sorted(asset_fallback_honesty.get("safe_default_segments") or []):
            items.append(self._item("safe_default_used", segment, "asset_fallback_honesty", "Safe default is weak visual evidence, not a strong semantic match."))

        if asset_diversity.get("repeated_asset_detected"):
            for path in sorted(asset_diversity.get("repeated_asset_paths") or []):
                items.append(self._item("repeated_asset", path, "asset_diversity", "Same asset path is reused across segments."))
        if asset_diversity.get("repeated_category_detected"):
            for category in sorted(asset_diversity.get("repeated_categories") or []):
                items.append(self._item("repeated_category", category, "asset_diversity", "Same visual category repeats across segments."))
        if str(asset_diversity.get("visual_progression_level") or "") in {"none", "weak"}:
            items.append(self._item("weak_visual_progression", str(asset_diversity.get("visual_progression_level") or "unknown"), "asset_diversity", "Visual progression is weak or unavailable."))

        for penalty in sorted(confidence_rationale.get("penalties") or []):
            items.append(self._item("confidence_penalty", penalty, "confidence_calibration", "Confidence calibration applied this penalty."))
        return items

    def _audit_summary(
        self,
        *,
        trace: dict[str, Any],
        fallback: FallbackDecision,
        confidence_rationale: dict[str, Any],
        visual_alignment: dict[str, Any],
    ) -> dict[str, Any]:
        missing_sections = [
            section
            for section in REQUIRED_TRACE_SECTIONS
            if section != "audit_summary" and section not in trace
        ]
        silent_failure_indicators: list[str] = []
        for section in missing_sections:
            silent_failure_indicators.append(f"MISSING_TRACE_SECTION:{section}")
        fallback_visible = bool(trace.get("asset_fallback_honesty"))
        if fallback.used and not fallback_visible:
            silent_failure_indicators.append("FALLBACK_USED_BUT_NOT_VISIBLE")
        confidence_explained = bool(confidence_rationale.get("confidence_meaning")) and bool(trace.get("confidence_calibration", {}).get("confidence_components"))
        if not confidence_explained:
            silent_failure_indicators.append("CONFIDENCE_NOT_EXPLAINED")
        if visual_alignment.get("mismatched_segments") and not any(
            item.get("kind") == "visual_mismatch"
            for item in trace.get("missing_or_degraded_inputs", [])
        ):
            silent_failure_indicators.append("VISUAL_MISMATCH_NOT_EXPOSED")
        required_sections_present = not missing_sections
        reconstructible = required_sections_present and fallback_visible and confidence_explained and not silent_failure_indicators
        return {
            "reconstructible": reconstructible,
            "required_sections_present": required_sections_present,
            "fallback_visible": fallback_visible,
            "confidence_explained": confidence_explained,
            "silent_failure_indicators": silent_failure_indicators,
            "trace_version": ASSET_TRACE_VERSION,
        }

    def _dominant_reason_codes(
        self,
        *,
        fallback: FallbackDecision,
        visual_alignment: dict[str, Any],
        visual_truthfulness: dict[str, Any],
        asset_fallback_honesty: dict[str, Any],
        asset_diversity: dict[str, Any],
        confidence_rationale: dict[str, Any],
    ) -> list[str]:
        codes: list[str] = []
        if fallback.used:
            codes.append(fallback.reason or "ASSET_FALLBACK_USED")
        if visual_alignment.get("mismatched_segments"):
            codes.append("VISUAL_SEMANTIC_MISMATCH")
        if visual_truthfulness.get("high_risk_segments"):
            codes.append("VISUAL_TRUTHFULNESS_HIGH_RISK")
        if asset_fallback_honesty.get("safe_default_segments"):
            codes.append("SAFE_DEFAULT_VISUAL_EVIDENCE_WEAK")
        if asset_diversity.get("repeated_asset_detected"):
            codes.append("REPEATED_ASSET_PATH_DETECTED")
        if asset_diversity.get("repeated_category_detected"):
            codes.append("REPEATED_VISUAL_CATEGORY_DETECTED")
        codes.extend(str(item) for item in confidence_rationale.get("penalties") or [])
        return self._dedupe(codes)

    def _diversity_risk(self, asset_diversity: dict[str, Any]) -> str:
        if asset_diversity.get("repeated_asset_detected"):
            return "high"
        progression = str(asset_diversity.get("visual_progression_level") or "")
        if progression in {"none", "weak"}:
            return "high"
        if asset_diversity.get("repeated_category_detected") or progression == "moderate":
            return "medium"
        return "low"

    def _item(self, kind: str, identifier: str, impact: str, rationale: str) -> dict[str, str]:
        return {
            "kind": kind,
            "identifier": str(identifier),
            "impact": impact,
            "rationale": rationale,
        }

    def _dedupe(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for value in values:
            if not value or value in seen:
                continue
            seen.add(value)
            deduped.append(value)
        return deduped
