from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.creative.contracts.creative_pack import TrendProfile


@dataclass(frozen=True)
class TrendConfidenceComponent:
    name: str
    value: float
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class TrendConfidenceCalibration:
    confidence: float
    confidence_level: str
    components: dict[str, float]
    penalties: tuple[str, ...] = ()
    rationale: tuple[str, ...] = ()
    confidence_meaning: str = "trust_in_trend_context"

    def to_dict(self) -> dict[str, Any]:
        return {
            "confidence": self.confidence,
            "confidence_level": self.confidence_level,
            "components": dict(self.components),
            "penalties": list(self.penalties),
            "rationale": list(self.rationale),
            "confidence_meaning": self.confidence_meaning,
        }


@dataclass
class TrendConfidenceCalibrator:
    component_weights: dict[str, float] = field(
        default_factory=lambda: {
            "source_governance_quality": 0.30,
            "provenance_completeness": 0.25,
            "freshness_validity": 0.25,
            "evidence_density": 0.20,
        }
    )
    penalty_weights: dict[str, float] = field(
        default_factory=lambda: {
            "fallback_penalty": 0.35,
            "source_rejection_penalty": 0.25,
        }
    )

    def calibrate(
        self,
        *,
        trend_profile: TrendProfile,
        source_governance: dict[str, Any] | None,
        provenance: dict[str, Any] | None,
        freshness: dict[str, Any] | None,
        validity: dict[str, Any] | None,
        fallback_used: bool,
        fallback_reason: str,
    ) -> TrendConfidenceCalibration:
        governance = dict(source_governance or {})
        provenance_payload = dict(provenance or {})
        freshness_payload = dict(freshness or {})
        validity_payload = dict(validity or {})

        components = {
            "source_governance_quality": self._source_governance_quality(governance=governance),
            "provenance_completeness": self._provenance_completeness(provenance=provenance_payload),
            "freshness_validity": self._freshness_validity(freshness=freshness_payload, validity=validity_payload),
            "evidence_density": self._evidence_density(trend_profile=trend_profile),
            "fallback_penalty": self._fallback_penalty(
                trend_profile=trend_profile,
                fallback_used=fallback_used,
                fallback_reason=fallback_reason,
            ),
            "source_rejection_penalty": self._source_rejection_penalty(governance=governance),
        }
        positive_score = sum(
            components[name] * weight for name, weight in self.component_weights.items()
        )
        penalty_score = sum(
            components[name] * weight for name, weight in self.penalty_weights.items()
        )
        raw_confidence = self._clamp(positive_score - penalty_score)
        penalties = self._penalties(
            trend_profile=trend_profile,
            governance=governance,
            provenance=provenance_payload,
            freshness=freshness_payload,
            validity=validity_payload,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            components=components,
        )
        confidence = self._apply_caps(
            confidence=raw_confidence,
            trend_profile=trend_profile,
            governance=governance,
            provenance=provenance_payload,
            freshness=freshness_payload,
            validity=validity_payload,
            fallback_used=fallback_used,
        )
        return TrendConfidenceCalibration(
            confidence=round(confidence, 4),
            confidence_level=self._level(confidence),
            components={name: round(value, 4) for name, value in components.items()},
            penalties=tuple(penalties),
            rationale=tuple(
                self._rationale(
                    confidence=confidence,
                    components=components,
                    penalties=penalties,
                    validity=validity_payload,
                )
            ),
        )

    def _source_governance_quality(self, *, governance: dict[str, Any]) -> float:
        accepted = list(governance.get("accepted_sources") or [])
        rejected = list(governance.get("rejected_sources") or [])
        selected_source_class = str(governance.get("selected_source_class") or "")
        if not accepted:
            return 0.1
        if selected_source_class == "safe_default":
            return 0.2
        base = {
            "approved_external_reference": 0.95,
            "manual_curation": 0.85,
            "current_store": 0.75,
            "validated_cache": 0.65,
            "history_snapshot": 0.60,
            "internal_runtime_metrics": 0.60,
        }.get(selected_source_class, 0.55)
        if len(accepted) > 1:
            base += 0.05
        if not bool(governance.get("policy_respected", True)):
            base -= 0.35
        base -= min(len(rejected), 3) * 0.08
        return self._clamp(base)

    def _provenance_completeness(self, *, provenance: dict[str, Any]) -> float:
        field_provenance = dict(provenance.get("field_provenance") or {})
        if not field_provenance:
            return 0.2
        if provenance.get("fallback_fields"):
            return 0.25
        if bool(provenance.get("provenance_complete", False)):
            weak_fields = list(provenance.get("weakly_supported_fields") or [])
            return self._clamp(0.9 - min(len(weak_fields), 4) * 0.05)
        total_fields = max(len(field_provenance), 1)
        unknown_ratio = len(list(provenance.get("unknown_source_fields") or [])) / total_fields
        weak_ratio = len(list(provenance.get("weakly_supported_fields") or [])) / total_fields
        return self._clamp(0.65 - (unknown_ratio * 0.45) - (weak_ratio * 0.15))

    def _freshness_validity(self, *, freshness: dict[str, Any], validity: dict[str, Any]) -> float:
        status = str(validity.get("validity_status") or "")
        base = {
            "valid": 0.95,
            "weak": 0.65,
            "degraded": 0.35,
            "invalid": 0.10,
        }.get(status, 0.25)
        missing_count = int(freshness.get("missing_timestamp_count") or 0)
        stale_count = int(freshness.get("stale_sources_count") or 0)
        expired_count = int(freshness.get("expired_sources_count") or 0)
        base -= min(missing_count, 3) * 0.06
        base -= min(stale_count, 3) * 0.08
        base -= min(expired_count, 3) * 0.12
        return self._clamp(base)

    def _evidence_density(self, *, trend_profile: TrendProfile) -> float:
        if trend_profile.trend_source == "safe_default":
            return 0.1
        evidence_count = len(trend_profile.evidence)
        sample_size = int(trend_profile.sample_size or 0)
        if sample_size >= 20 and evidence_count >= 2:
            return 1.0
        if sample_size >= 10 and evidence_count >= 1:
            return 0.8
        if sample_size >= 3 and evidence_count >= 1:
            return 0.55
        if evidence_count >= 1:
            return 0.35
        return 0.1

    def _fallback_penalty(
        self,
        *,
        trend_profile: TrendProfile,
        fallback_used: bool,
        fallback_reason: str,
    ) -> float:
        if trend_profile.trend_source == "safe_default":
            return 0.85
        if not fallback_used:
            return 0.0
        if fallback_reason == "TREND_CACHE_FALLBACK":
            return 0.25
        if fallback_reason == "TREND_HISTORY_FALLBACK":
            return 0.30
        return 0.55

    def _source_rejection_penalty(self, *, governance: dict[str, Any]) -> float:
        accepted_count = len(list(governance.get("accepted_sources") or []))
        rejected_count = len(list(governance.get("rejected_sources") or []))
        total = accepted_count + rejected_count
        if total == 0:
            return 0.2
        penalty = min(rejected_count / total, 1.0) * 0.55
        if not bool(governance.get("policy_respected", True)):
            penalty = max(penalty, 0.50)
        return self._clamp(penalty)

    def _penalties(
        self,
        *,
        trend_profile: TrendProfile,
        governance: dict[str, Any],
        provenance: dict[str, Any],
        freshness: dict[str, Any],
        validity: dict[str, Any],
        fallback_used: bool,
        fallback_reason: str,
        components: dict[str, float],
    ) -> list[str]:
        penalties: list[str] = []
        if fallback_used:
            penalties.append("FALLBACK_USED")
        if trend_profile.trend_source == "safe_default":
            penalties.append("SAFE_DEFAULT_CONTEXT")
        if fallback_reason:
            penalties.append(f"FALLBACK_REASON_{fallback_reason}")
        if not bool(governance.get("policy_respected", True)):
            penalties.append("POLICY_NOT_RESPECTED")
        if list(governance.get("rejected_sources") or []):
            penalties.append("SOURCE_REJECTION_PRESENT")
        if not bool(provenance.get("provenance_complete", False)):
            penalties.append("PROVENANCE_INCOMPLETE")
        if freshness.get("missing_timestamp_count"):
            penalties.append("MISSING_TIMESTAMP_PRESENT")
        if freshness.get("stale_sources_count"):
            penalties.append("STALE_SOURCE_PRESENT")
        if freshness.get("expired_sources_count"):
            penalties.append("EXPIRED_SOURCE_PRESENT")
        if str(validity.get("validity_status") or "") in {"degraded", "invalid"}:
            penalties.append(f"VALIDITY_{str(validity.get('validity_status')).upper()}")
        if components.get("evidence_density", 0.0) < 0.55:
            penalties.append("LOW_EVIDENCE_DENSITY")
        return penalties

    def _apply_caps(
        self,
        *,
        confidence: float,
        trend_profile: TrendProfile,
        governance: dict[str, Any],
        provenance: dict[str, Any],
        freshness: dict[str, Any],
        validity: dict[str, Any],
        fallback_used: bool,
    ) -> float:
        capped = confidence
        if trend_profile.trend_source == "safe_default":
            capped = min(capped, 0.30)
        if fallback_used:
            capped = min(capped, 0.69)
        if not bool(provenance.get("provenance_complete", False)):
            capped = min(capped, 0.69)
        if list(governance.get("rejected_sources") or []):
            capped = min(capped, 0.69)
        if freshness.get("missing_timestamp_count"):
            capped = min(capped, 0.64)
        if freshness.get("stale_sources_count"):
            capped = min(capped, 0.64)
        if freshness.get("expired_sources_count"):
            capped = min(capped, 0.49)
        validity_status = str(validity.get("validity_status") or "")
        if validity_status == "degraded":
            capped = min(capped, 0.55)
        if validity_status == "invalid":
            capped = min(capped, 0.34)
        return self._clamp(capped)

    def _rationale(
        self,
        *,
        confidence: float,
        components: dict[str, float],
        penalties: list[str],
        validity: dict[str, Any],
    ) -> list[str]:
        rationale = [
            "Confidence measures trust in the emitted Trend context, not trend strength or expected performance.",
            (
                "Positive evidence combines source governance, provenance completeness, freshness/validity, "
                "and evidence density."
            ),
        ]
        if penalties:
            rationale.append(f"Applied penalties: {', '.join(penalties)}.")
        rationale.append(
            f"Final calibrated confidence {round(confidence, 4)} reflects validity_status={validity.get('validity_status')}."
        )
        rationale.append(f"Component snapshot: { {name: round(value, 4) for name, value in components.items()} }.")
        return rationale

    def _level(self, confidence: float) -> str:
        if confidence < 0.35:
            return "low"
        if confidence < 0.70:
            return "medium"
        return "high"

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, float(value)))
