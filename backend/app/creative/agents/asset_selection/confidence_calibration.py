from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


ASSET_CONFIDENCE_MEANING = "trust_in_asset_selection"


@dataclass(frozen=True)
class AssetConfidenceCalibration:
    confidence: float
    confidence_level: str
    confidence_components: dict[str, float]
    confidence_rationale: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AssetConfidenceCalibrator:
    """Calibrates trust in the selected asset plan, not visual performance."""

    def calibrate(
        self,
        *,
        asset_context_governance: dict[str, Any],
        asset_source_governance: dict[str, Any],
        segment_visual_intent: dict[str, Any],
        visual_alignment: dict[str, Any],
        visual_truthfulness: dict[str, Any],
        asset_fallback_honesty: dict[str, Any],
        asset_diversity: dict[str, Any],
    ) -> AssetConfidenceCalibration:
        components = {
            "context_completeness": self._context_completeness(asset_context_governance),
            "catalog_governance": self._catalog_governance(asset_source_governance),
            "semantic_alignment": self._semantic_alignment(visual_alignment),
            "visual_truthfulness": self._visual_truthfulness(visual_truthfulness),
            "fallback_penalty": self._fallback_penalty(asset_fallback_honesty),
            "diversity_penalty": self._diversity_penalty(asset_diversity),
        }
        base = (
            components["context_completeness"] * 0.16
            + components["catalog_governance"] * 0.18
            + components["semantic_alignment"] * 0.24
            + components["visual_truthfulness"] * 0.24
            + (1.0 - components["fallback_penalty"]) * 0.10
            + (1.0 - components["diversity_penalty"]) * 0.08
        )
        penalties = self._penalties(
            asset_context_governance=asset_context_governance,
            asset_source_governance=asset_source_governance,
            segment_visual_intent=segment_visual_intent,
            visual_alignment=visual_alignment,
            visual_truthfulness=visual_truthfulness,
            asset_fallback_honesty=asset_fallback_honesty,
            asset_diversity=asset_diversity,
        )
        confidence = base
        caps = self._caps(
            visual_alignment=visual_alignment,
            visual_truthfulness=visual_truthfulness,
            asset_fallback_honesty=asset_fallback_honesty,
            asset_diversity=asset_diversity,
        )
        for cap in caps:
            confidence = min(confidence, cap["cap"])
        confidence = round(max(0.0, min(1.0, confidence)), 4)

        return AssetConfidenceCalibration(
            confidence=confidence,
            confidence_level=self._level(confidence),
            confidence_components={key: round(value, 4) for key, value in components.items()},
            confidence_rationale={
                "confidence_meaning": ASSET_CONFIDENCE_MEANING,
                "penalties": penalties,
                "caps": caps,
                "boundary_statement": "Asset confidence is not performance prediction.",
                "rationale": [
                    "Confidence measures trust in the emitted asset selection and its metadata support.",
                    "It does not measure expected content performance, visual beauty, QC status, or publishability.",
                ],
            },
        )

    def _context_completeness(self, payload: dict[str, Any]) -> float:
        priority = list(payload.get("context_priority") or [])
        if not priority:
            return 0.5
        available = set(payload.get("available_context") or [])
        degraded = set(payload.get("degraded_context") or [])
        missing = set(payload.get("missing_context") or [])
        ignored = set(payload.get("ignored_context") or [])
        expected = [item for item in priority if item not in ignored]
        if not expected:
            return 0.5
        score = sum(1.0 for item in expected if item in available) / len(expected)
        score -= 0.12 * len(degraded)
        score -= 0.08 * len(missing)
        return self._bounded(score)

    def _catalog_governance(self, payload: dict[str, Any]) -> float:
        if not payload.get("catalog_available", False):
            return 0.2
        selected = list(payload.get("selected_sources") or [])
        if not selected:
            return 0.35
        accepted = sum(1 for item in selected if item.get("governance_status") == "accepted")
        score = accepted / len(selected)
        if not payload.get("policy_respected", False):
            score = min(score, 0.55)
        if payload.get("fallback_sources"):
            score = min(score, 0.65)
        return self._bounded(score)

    def _semantic_alignment(self, payload: dict[str, Any]) -> float:
        score = self._float(payload.get("overall_alignment_score"), 0.0)
        if not payload.get("alignment_complete", False):
            score = min(score, 0.65)
        if payload.get("missing_metadata_segments"):
            score = min(score, 0.45)
        if payload.get("mismatched_segments"):
            score = min(score, 0.55)
        return self._bounded(score)

    def _visual_truthfulness(self, payload: dict[str, Any]) -> float:
        risk = str(payload.get("overall_risk_level") or "high")
        base = {
            "low": 0.9,
            "medium": 0.62,
            "high": 0.35,
        }.get(risk, 0.35)
        high_risk_count = len(payload.get("high_risk_segments") or [])
        unsupported_count = len(payload.get("unsupported_claim_segments") or [])
        score = base - (0.08 * high_risk_count) - (0.05 * unsupported_count)
        return self._bounded(score)

    def _fallback_penalty(self, payload: dict[str, Any]) -> float:
        fallback_count = len(payload.get("fallback_segments") or [])
        safe_default_count = len(payload.get("safe_default_segments") or [])
        weak_count = len(payload.get("weak_evidence_segments") or [])
        if payload.get("global_fallback_used", False):
            return 0.55 + min(0.25, safe_default_count * 0.08)
        if fallback_count:
            return 0.35 + min(0.20, fallback_count * 0.06)
        if weak_count:
            return min(0.25, weak_count * 0.05)
        return 0.0

    def _diversity_penalty(self, payload: dict[str, Any]) -> float:
        penalty = 0.0
        if payload.get("repeated_asset_detected", False):
            penalty += 0.40
        if payload.get("repeated_category_detected", False):
            penalty += 0.18
        progression = str(payload.get("visual_progression_level") or "none")
        if progression == "none":
            penalty += 0.35
        elif progression == "weak":
            penalty += 0.25
        elif progression == "moderate":
            penalty += 0.08
        return self._bounded(penalty)

    def _penalties(
        self,
        *,
        asset_context_governance: dict[str, Any],
        asset_source_governance: dict[str, Any],
        segment_visual_intent: dict[str, Any],
        visual_alignment: dict[str, Any],
        visual_truthfulness: dict[str, Any],
        asset_fallback_honesty: dict[str, Any],
        asset_diversity: dict[str, Any],
    ) -> list[str]:
        penalties: list[str] = []
        if asset_context_governance.get("missing_context"):
            penalties.append("MISSING_CONTEXT_REDUCES_CONFIDENCE")
        if asset_context_governance.get("degraded_context"):
            penalties.append("DEGRADED_CONTEXT_REDUCES_CONFIDENCE")
        if not asset_source_governance.get("policy_respected", True):
            penalties.append("SOURCE_GOVERNANCE_POLICY_NOT_RESPECTED")
        if not segment_visual_intent.get("intent_complete", True):
            penalties.append("INCOMPLETE_SEGMENT_VISUAL_INTENT")
        if visual_alignment.get("mismatched_segments"):
            penalties.append("VISUAL_SEMANTIC_MISMATCH_REDUCES_CONFIDENCE")
        if visual_alignment.get("missing_metadata_segments"):
            penalties.append("MISSING_ASSET_METADATA_REDUCES_CONFIDENCE")
        if visual_truthfulness.get("high_risk_segments"):
            penalties.append("VISUAL_TRUTHFULNESS_HIGH_RISK_REDUCES_CONFIDENCE")
        if visual_truthfulness.get("generic_or_fallback_segments"):
            penalties.append("GENERIC_OR_FALLBACK_VISUAL_RISK_REDUCES_CONFIDENCE")
        if asset_fallback_honesty.get("global_fallback_used") or asset_fallback_honesty.get("fallback_segments"):
            penalties.append("FALLBACK_REDUCES_CONFIDENCE")
        if asset_fallback_honesty.get("safe_default_segments"):
            penalties.append("SAFE_DEFAULT_PREVENTS_HIGH_CONFIDENCE")
        if asset_diversity.get("repeated_asset_detected"):
            penalties.append("REPEATED_ASSET_REDUCES_CONFIDENCE")
        if asset_diversity.get("repeated_category_detected"):
            penalties.append("REPEATED_CATEGORY_REDUCES_CONFIDENCE")
        return penalties

    def _caps(
        self,
        *,
        visual_alignment: dict[str, Any],
        visual_truthfulness: dict[str, Any],
        asset_fallback_honesty: dict[str, Any],
        asset_diversity: dict[str, Any],
    ) -> list[dict[str, Any]]:
        caps: list[dict[str, Any]] = []
        if asset_fallback_honesty.get("global_fallback_used") or asset_fallback_honesty.get("fallback_segments"):
            caps.append({"cap": 0.65, "reason": "FALLBACK_USED_CAP"})
        if asset_fallback_honesty.get("safe_default_segments"):
            caps.append({"cap": 0.55, "reason": "SAFE_DEFAULT_CAP"})
        high_mismatch = [
            segment
            for segment, alignment in dict(visual_alignment.get("segment_alignments") or {}).items()
            if alignment.get("mismatch_level") == "high"
        ]
        if high_mismatch:
            caps.append({"cap": 0.55, "reason": "HIGH_MISMATCH_CAP", "segments": high_mismatch})
        generic_segments = [
            segment
            for segment, truthfulness in dict(visual_truthfulness.get("segment_truthfulness") or {}).items()
            if truthfulness.get("generic_asset_risk")
        ]
        if generic_segments:
            caps.append({"cap": 0.60, "reason": "GENERIC_ASSET_RISK_CAP", "segments": generic_segments})
        if asset_diversity.get("repeated_asset_detected"):
            caps.append({"cap": 0.62, "reason": "REPEATED_ASSET_CAP"})
        return caps

    def _level(self, confidence: float) -> str:
        if confidence >= 0.75:
            return "high"
        if confidence >= 0.45:
            return "medium"
        return "low"

    def _float(self, value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _bounded(self, value: float) -> float:
        return max(0.0, min(1.0, value))
