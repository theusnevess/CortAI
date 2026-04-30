from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import AssetPlan


ASSET_FALLBACK_HONESTY_VERSION = "asset_fallback_honesty_v2_6"


@dataclass(frozen=True)
class AssetSegmentFallbackHonesty:
    segment: str
    fallback_used: bool
    fallback_mode: str
    fallback_reason: str
    selected_asset_path: str
    safe_default_used: bool
    semantic_match_strength: str
    visual_evidence_strength: str
    evidence_status: str
    reason_codes: list[str]
    rationale: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AssetFallbackHonesty:
    honesty_version: str
    global_fallback_used: bool
    global_fallback_mode: str
    global_fallback_reason: str
    segment_fallbacks: dict[str, AssetSegmentFallbackHonesty]
    fallback_segments: list[str]
    safe_default_segments: list[str]
    weak_evidence_segments: list[str]
    fallback_evidence_is_strong: bool
    boundary_statement: str
    fallback_trace: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["segment_fallbacks"] = {
            name: segment.to_dict()
            for name, segment in self.segment_fallbacks.items()
        }
        return payload


@dataclass(frozen=True)
class AssetFallbackHonestyEvaluator:
    """Explains fallback state without changing fallback selection."""

    def evaluate(
        self,
        *,
        asset_selection: AssetPlan,
        fallback: FallbackDecision,
        segment_fallback_trace: dict[str, dict[str, Any]] | None = None,
        visual_alignment: dict[str, Any] | None = None,
        visual_truthfulness: dict[str, Any] | None = None,
    ) -> AssetFallbackHonesty:
        trace = segment_fallback_trace or {}
        alignment_by_segment = dict((visual_alignment or {}).get("segment_alignments") or {})
        truthfulness_by_segment = dict((visual_truthfulness or {}).get("segment_truthfulness") or {})
        segment_fallbacks = {
            segment_name: self._segment_fallback(
                segment_name=segment_name,
                selected_path=self._selected_path(asset_selection=asset_selection, segment_name=segment_name),
                fallback=fallback,
                trace=dict(trace.get(segment_name) or {}),
                alignment=dict(alignment_by_segment.get(segment_name) or {}),
                truthfulness=dict(truthfulness_by_segment.get(segment_name) or {}),
            )
            for segment_name in ("hook", "setup", "payoff")
        }
        fallback_segments = [
            name
            for name, segment in segment_fallbacks.items()
            if segment.fallback_used
        ]
        safe_default_segments = [
            name
            for name, segment in segment_fallbacks.items()
            if segment.safe_default_used
        ]
        weak_evidence_segments = [
            name
            for name, segment in segment_fallbacks.items()
            if segment.visual_evidence_strength == "weak"
        ]

        return AssetFallbackHonesty(
            honesty_version=ASSET_FALLBACK_HONESTY_VERSION,
            global_fallback_used=fallback.used,
            global_fallback_mode=fallback.mode,
            global_fallback_reason=fallback.reason,
            segment_fallbacks=segment_fallbacks,
            fallback_segments=fallback_segments,
            safe_default_segments=safe_default_segments,
            weak_evidence_segments=weak_evidence_segments,
            fallback_evidence_is_strong=False,
            boundary_statement="Asset fallback honesty is audit-only; fallback selection, ranking, and providers are unchanged.",
            fallback_trace={
                "segment_fallback_trace_available": bool(trace),
                "safe_default_is_semantic_match": False,
                "fallback_marked_as_weak_visual_evidence": bool(fallback_segments or safe_default_segments),
                "selection_ranking_unchanged": True,
                "fallback_behavior_unchanged": True,
                "external_provider_added": False,
            },
        )

    def _segment_fallback(
        self,
        *,
        segment_name: str,
        selected_path: str,
        fallback: FallbackDecision,
        trace: dict[str, Any],
        alignment: dict[str, Any],
        truthfulness: dict[str, Any],
    ) -> AssetSegmentFallbackHonesty:
        primary_selector_returned_asset = bool(trace.get("primary_selector_returned_asset", bool(selected_path)))
        safe_fallback_used = bool(trace.get("safe_fallback_used", False))
        global_safe_default = bool(fallback.used and fallback.mode == "SAFE_DEFAULT")
        missing_path = not bool(selected_path)
        fallback_used = safe_fallback_used or global_safe_default or (fallback.used and missing_path)
        fallback_mode = self._fallback_mode(
            fallback=fallback,
            safe_fallback_used=safe_fallback_used,
            global_safe_default=global_safe_default,
        )
        fallback_reason = self._fallback_reason(
            fallback=fallback,
            safe_fallback_used=safe_fallback_used,
            missing_path=missing_path,
        )
        semantic_match_strength = self._semantic_match_strength(
            fallback_used=fallback_used,
            alignment=alignment,
            truthfulness=truthfulness,
        )
        visual_evidence_strength = self._visual_evidence_strength(
            fallback_used=fallback_used,
            truthfulness=truthfulness,
        )
        reason_codes = self._reason_codes(
            fallback_used=fallback_used,
            safe_default_used=global_safe_default or missing_path,
            safe_fallback_used=safe_fallback_used,
            primary_selector_returned_asset=primary_selector_returned_asset,
            visual_evidence_strength=visual_evidence_strength,
        )

        return AssetSegmentFallbackHonesty(
            segment=segment_name,
            fallback_used=fallback_used,
            fallback_mode=fallback_mode,
            fallback_reason=fallback_reason,
            selected_asset_path=selected_path,
            safe_default_used=global_safe_default or (fallback.used and missing_path),
            semantic_match_strength=semantic_match_strength,
            visual_evidence_strength=visual_evidence_strength,
            evidence_status="fallback_weak" if fallback_used else "selected_metadata_observed",
            reason_codes=reason_codes,
            rationale=self._rationale(
                segment_name=segment_name,
                fallback_used=fallback_used,
                fallback_mode=fallback_mode,
                fallback_reason=fallback_reason,
                visual_evidence_strength=visual_evidence_strength,
            ),
            metadata={
                "primary_selector_returned_asset": primary_selector_returned_asset,
                "safe_fallback_used": safe_fallback_used,
                "alignment_level": alignment.get("alignment_level", ""),
                "truthfulness_risk_level": truthfulness.get("risk_level", ""),
                "truthfulness_status": truthfulness.get("truthfulness_status", ""),
            },
        )

    def _fallback_mode(
        self,
        *,
        fallback: FallbackDecision,
        safe_fallback_used: bool,
        global_safe_default: bool,
    ) -> str:
        if global_safe_default:
            return "safe_default"
        if safe_fallback_used:
            return "local_safe_fallback"
        if fallback.used:
            return fallback.mode or "reported_fallback"
        return "none"

    def _fallback_reason(
        self,
        *,
        fallback: FallbackDecision,
        safe_fallback_used: bool,
        missing_path: bool,
    ) -> str:
        if fallback.reason:
            return fallback.reason
        if safe_fallback_used:
            return "SEGMENT_SAFE_FALLBACK_USED"
        if missing_path:
            return "SEGMENT_ASSET_PATH_MISSING"
        return ""

    def _semantic_match_strength(
        self,
        *,
        fallback_used: bool,
        alignment: dict[str, Any],
        truthfulness: dict[str, Any],
    ) -> str:
        if fallback_used:
            return "weak"
        risk_level = str(truthfulness.get("risk_level") or "")
        alignment_level = str(alignment.get("alignment_level") or "")
        if risk_level == "low" and alignment_level == "high":
            return "strong"
        if risk_level in {"low", "medium"} and alignment_level in {"medium", "high"}:
            return "partial"
        if alignment_level == "unknown":
            return "unknown"
        return "weak"

    def _visual_evidence_strength(self, *, fallback_used: bool, truthfulness: dict[str, Any]) -> str:
        if fallback_used:
            return "weak"
        risk_level = str(truthfulness.get("risk_level") or "")
        if risk_level == "low":
            return "strong"
        if risk_level == "medium":
            return "partial"
        if risk_level == "high":
            return "weak"
        return "unknown"

    def _reason_codes(
        self,
        *,
        fallback_used: bool,
        safe_default_used: bool,
        safe_fallback_used: bool,
        primary_selector_returned_asset: bool,
        visual_evidence_strength: str,
    ) -> list[str]:
        codes: list[str] = []
        if fallback_used:
            codes.append("ASSET_FALLBACK_USED")
        if safe_default_used:
            codes.append("SAFE_DEFAULT_VISUAL_EVIDENCE_WEAK")
        if safe_fallback_used:
            codes.append("SEGMENT_SAFE_FALLBACK_USED")
        if not primary_selector_returned_asset:
            codes.append("PRIMARY_SELECTOR_DID_NOT_RETURN_ASSET")
        if not fallback_used:
            codes.append("ASSET_FALLBACK_NOT_USED")
        if visual_evidence_strength == "weak":
            codes.append("VISUAL_EVIDENCE_WEAK")
        return codes

    def _rationale(
        self,
        *,
        segment_name: str,
        fallback_used: bool,
        fallback_mode: str,
        fallback_reason: str,
        visual_evidence_strength: str,
    ) -> list[str]:
        if fallback_used:
            return [
                f"{segment_name} used fallback mode '{fallback_mode}'.",
                f"Fallback reason: {fallback_reason or 'not reported'}.",
                "Fallback is treated as weak visual evidence, not as a strong semantic match.",
            ]
        return [
            f"{segment_name} did not report fallback usage.",
            f"Visual evidence strength is {visual_evidence_strength}.",
        ]

    def _selected_path(self, *, asset_selection: AssetPlan, segment_name: str) -> str:
        if segment_name == "hook":
            return asset_selection.hook_asset
        if segment_name == "setup":
            return asset_selection.setup_asset
        if segment_name == "payoff":
            return asset_selection.payoff_asset
        return ""
