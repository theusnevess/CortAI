from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ConfidenceCalibration:
    confidence: float
    confidence_components: dict[str, float]
    confidence_rationale: dict[str, Any]
    evidence_origin_mix: dict[str, float] = field(default_factory=dict)
    controlled_validation_dominance: bool = False
    real_runtime_support: str = "none"
    bootstrap_bias_risk: str = "high"
    policy_strength: str = "weak"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LearningConfidenceCalibrator:
    """Calibrates Learning confidence from evidence quality, not desired policy.

    The calibrator is deliberately conservative. Controlled validation and small
    clean samples can prove code paths, but they do not prove production maturity.
    """

    def calibrate_insight_confidence(
        self,
        *,
        sample_size: int,
        clean_sample_size: int,
        contamination_rate: float,
        recency_weight: float,
        signal_consistency: float,
        signal_strength: float,
        evidence_source_mix: dict[str, float] | None = None,
        evidence_variety: int = 0,
        cluster_distribution: dict[str, int] | None = None,
        temporal_pattern_type: str = "unknown",
        contamination_summary: dict[str, Any] | None = None,
    ) -> ConfidenceCalibration:
        return self._calibrate(
            sample_size=sample_size,
            clean_sample_size=clean_sample_size,
            contamination_rate=contamination_rate,
            recency_weight=recency_weight,
            signal_consistency=signal_consistency,
            signal_strength=signal_strength,
            evidence_source_mix=evidence_source_mix or {},
            evidence_variety=evidence_variety,
            cluster_distribution=cluster_distribution or {},
            temporal_pattern_type=temporal_pattern_type,
            contamination_summary=contamination_summary or {},
            policy_mode=False,
        )

    def calibrate_policy_confidence(
        self,
        *,
        sample_size: int,
        clean_sample_size: int,
        contamination_rate: float,
        recency_weight: float,
        signal_consistency: float,
        signal_strength: float,
        evidence_source_mix: dict[str, float] | None = None,
        evidence_variety: int = 0,
        cluster_distribution: dict[str, int] | None = None,
        temporal_pattern_type: str = "unknown",
        contamination_summary: dict[str, Any] | None = None,
    ) -> ConfidenceCalibration:
        return self._calibrate(
            sample_size=sample_size,
            clean_sample_size=clean_sample_size,
            contamination_rate=contamination_rate,
            recency_weight=recency_weight,
            signal_consistency=signal_consistency,
            signal_strength=signal_strength,
            evidence_source_mix=evidence_source_mix or {},
            evidence_variety=evidence_variety,
            cluster_distribution=cluster_distribution or {},
            temporal_pattern_type=temporal_pattern_type,
            contamination_summary=contamination_summary or {},
            policy_mode=True,
        )

    def summarize_confidence(self, calibrations: list[ConfidenceCalibration]) -> dict[str, Any]:
        if not calibrations:
            return {
                "confidence": 0.0,
                "policy_strength": "weak",
                "bootstrap_bias_risk": "high",
                "calibration_count": 0,
            }
        confidence_values = [item.confidence for item in calibrations]
        return {
            "confidence": round(sum(confidence_values) / len(confidence_values), 4),
            "minimum_confidence": round(min(confidence_values), 4),
            "maximum_confidence": round(max(confidence_values), 4),
            "policy_strength": self.policy_strength_from_confidence(min(confidence_values)),
            "bootstrap_bias_risk": self._max_risk([item.bootstrap_bias_risk for item in calibrations]),
            "calibration_count": len(calibrations),
        }

    def calculate_bootstrap_bias_risk(
        self,
        *,
        sample_size: int,
        clean_sample_size: int,
        evidence_source_mix: dict[str, float] | None = None,
        evidence_variety: int = 0,
        cluster_distribution: dict[str, int] | None = None,
        recency_weight: float = 0.0,
    ) -> str:
        source_mix = self._normalize_source_mix(evidence_source_mix or {})
        controlled_ratio = source_mix.get("controlled_validation", 0.0)
        cluster_dominance = self._cluster_dominance(cluster_distribution or {})

        if (
            sample_size < 5
            or clean_sample_size < 3
            or controlled_ratio >= 0.7
            or (evidence_variety <= 1 and sample_size < 10)
            or (cluster_dominance >= 0.9 and sample_size < 10)
            or (recency_weight > 0.85 and sample_size < 10)
        ):
            return "high"
        if (
            sample_size < 10
            or clean_sample_size < 7
            or controlled_ratio >= 0.45
            or evidence_variety <= 2
            or (cluster_dominance >= 0.85 and sample_size < 20)
        ):
            return "medium"
        return "low"

    def policy_strength_from_confidence(self, confidence: float) -> str:
        confidence = self._clamp(confidence)
        if confidence < 0.35:
            return "weak"
        if confidence < 0.70:
            return "medium"
        return "strong"

    def _calibrate(
        self,
        *,
        sample_size: int,
        clean_sample_size: int,
        contamination_rate: float,
        recency_weight: float,
        signal_consistency: float,
        signal_strength: float,
        evidence_source_mix: dict[str, float],
        evidence_variety: int,
        cluster_distribution: dict[str, int],
        temporal_pattern_type: str,
        contamination_summary: dict[str, Any],
        policy_mode: bool,
    ) -> ConfidenceCalibration:
        sample_size = max(0, int(sample_size))
        clean_sample_size = max(0, min(int(clean_sample_size), sample_size))
        contamination_rate = self._clamp(contamination_rate)
        recency_weight = self._clamp(recency_weight)
        signal_consistency = self._clamp(signal_consistency)
        signal_strength = self._clamp(signal_strength)
        source_mix = self._normalize_source_mix(evidence_source_mix)
        contamination_profile = self._normalize_contamination_summary(contamination_summary)

        bootstrap_bias_risk = self.calculate_bootstrap_bias_risk(
            sample_size=sample_size,
            clean_sample_size=clean_sample_size,
            evidence_source_mix=source_mix,
            evidence_variety=evidence_variety,
            cluster_distribution=cluster_distribution,
            recency_weight=recency_weight,
        )
        controlled_ratio = source_mix.get("controlled_validation", 0.0)
        controlled_validation_dominance = controlled_ratio >= 0.55
        real_runtime_ratio = self._real_runtime_ratio(source_mix)
        real_runtime_support = self._real_runtime_support(real_runtime_ratio, clean_sample_size)

        components = {
            "sample_size": round(min(clean_sample_size / 20.0, 1.0), 4),
            "cleanliness": round(max(0.0, 1.0 - contamination_rate), 4),
            "recency": recency_weight,
            "consistency": signal_consistency,
            "signal_strength": signal_strength,
            "bootstrap_bias_penalty": self._bootstrap_penalty(bootstrap_bias_risk),
            "controlled_validation_penalty": 0.25 if controlled_validation_dominance else (0.12 if controlled_ratio >= 0.35 else 0.0),
            "temporal_reliability_modifier": self._temporal_modifier(temporal_pattern_type),
            "contamination_noise_penalty": contamination_profile["confidence_penalty"],
        }
        real_support_component = {"none": 0.0, "limited": 0.35, "moderate": 0.7, "strong": 1.0}[real_runtime_support]
        raw_confidence = (
            components["sample_size"] * 0.22
            + components["cleanliness"] * 0.18
            + components["recency"] * 0.12
            + components["consistency"] * 0.2
            + components["signal_strength"] * 0.2
            + real_support_component * 0.08
        )
        confidence = (
            raw_confidence
            - components["bootstrap_bias_penalty"]
            - components["controlled_validation_penalty"]
            - components["contamination_noise_penalty"]
            + components["temporal_reliability_modifier"]
        )
        if policy_mode:
            confidence -= 0.05

        confidence = min(confidence, self._confidence_cap(
            sample_size=sample_size,
            clean_sample_size=clean_sample_size,
            contamination_rate=contamination_rate,
            signal_consistency=signal_consistency,
            signal_strength=signal_strength,
            controlled_validation_dominance=controlled_validation_dominance,
            bootstrap_bias_risk=bootstrap_bias_risk,
            temporal_pattern_type=temporal_pattern_type,
            contamination_profile=contamination_profile,
            policy_mode=policy_mode,
        ))
        confidence = round(self._clamp(confidence), 4)

        rationale = {
            "sample_size": sample_size,
            "clean_sample_size": clean_sample_size,
            "contamination_rate": contamination_rate,
            "dominant_evidence_source": self._dominant_source(source_mix),
            "bootstrap_bias_risk": bootstrap_bias_risk,
            "evidence_variety": int(evidence_variety),
            "cluster_dominance": self._cluster_dominance(cluster_distribution),
            "controlled_validation_dominance": controlled_validation_dominance,
            "real_runtime_support": real_runtime_support,
            "temporal_pattern_type": temporal_pattern_type,
            "dominant_problem": contamination_profile["dominant_problem"],
            "policy_safe": contamination_profile["policy_safe"],
            "noise_rate": contamination_profile["noise_rate"],
            "weak_signal_rate": contamination_profile["weak_signal_rate"],
            "insufficient_rate": contamination_profile["insufficient_rate"],
            "policy_mode": policy_mode,
        }
        return ConfidenceCalibration(
            confidence=confidence,
            confidence_components=components,
            confidence_rationale=rationale,
            evidence_origin_mix=source_mix,
            controlled_validation_dominance=controlled_validation_dominance,
            real_runtime_support=real_runtime_support,
            bootstrap_bias_risk=bootstrap_bias_risk,
            policy_strength=self.policy_strength_from_confidence(confidence),
        )

    def _confidence_cap(
        self,
        *,
        sample_size: int,
        clean_sample_size: int,
        contamination_rate: float,
        signal_consistency: float,
        signal_strength: float,
        controlled_validation_dominance: bool,
        bootstrap_bias_risk: str,
        temporal_pattern_type: str,
        contamination_profile: dict[str, Any],
        policy_mode: bool,
    ) -> float:
        cap = 0.92
        if sample_size < 5:
            cap = min(cap, 0.34)
        if clean_sample_size < 3:
            cap = min(cap, 0.3)
        if contamination_rate > 0.4:
            cap = min(cap, 0.34)
        if signal_consistency < 0.45 or signal_strength < 0.25:
            cap = min(cap, 0.32)
        if controlled_validation_dominance:
            cap = min(cap, 0.55)
        if bootstrap_bias_risk == "high":
            cap = min(cap, 0.42)
        elif bootstrap_bias_risk == "medium":
            cap = min(cap, 0.68)
        if temporal_pattern_type == "recent_spike":
            cap = min(cap, 0.34)
        elif temporal_pattern_type == "volatile":
            cap = min(cap, 0.34)
        elif temporal_pattern_type == "stale_signal":
            cap = min(cap, 0.34)
        if not bool(contamination_profile.get("policy_safe")):
            cap = min(cap, 0.34)
        if self._clamp(contamination_profile.get("noise_rate", 0.0)) > 0.35:
            cap = min(cap, 0.34)
        if self._clamp(contamination_profile.get("insufficient_rate", 0.0)) > 0.45:
            cap = min(cap, 0.3)
        if str(contamination_profile.get("dominant_problem") or "") in {"noise", "insufficient", "contamination"}:
            cap = min(cap, 0.34)
        if policy_mode:
            cap = min(cap, 0.85)
        return cap

    def _temporal_modifier(self, temporal_pattern_type: str) -> float:
        if temporal_pattern_type == "durable_pattern":
            return 0.05
        if temporal_pattern_type == "recent_spike":
            return -0.18
        if temporal_pattern_type == "volatile":
            return -0.25
        if temporal_pattern_type == "stale_signal":
            return -0.22
        return 0.0

    def _normalize_source_mix(self, evidence_source_mix: dict[str, float]) -> dict[str, float]:
        allowed = {
            "qc_derived",
            "runtime_history",
            "real_runtime",
            "controlled_validation",
            "post_publish_metrics",
            "other_bounded",
        }
        numeric = {
            key: max(0.0, float(value))
            for key, value in evidence_source_mix.items()
            if key in allowed and isinstance(value, (int, float))
        }
        total = sum(numeric.values())
        if total <= 0:
            return {
                "qc_derived": 0.0,
                "runtime_history": 0.0,
                "real_runtime": 0.0,
                "controlled_validation": 0.0,
                "post_publish_metrics": 0.0,
                "other_bounded": 0.0,
            }
        normalized = {key: round(value / total, 4) for key, value in numeric.items()}
        for key in allowed:
            normalized.setdefault(key, 0.0)
        return dict(sorted(normalized.items()))

    def _normalize_contamination_summary(self, contamination_summary: dict[str, Any]) -> dict[str, Any]:
        summary = contamination_summary if isinstance(contamination_summary, dict) else {}
        return {
            "contamination_rate": self._clamp(summary.get("contamination_rate", 0.0)),
            "weak_signal_rate": self._clamp(summary.get("weak_signal_rate", 0.0)),
            "noise_rate": self._clamp(summary.get("noise_rate", 0.0)),
            "insufficient_rate": self._clamp(summary.get("insufficient_rate", 0.0)),
            "dominant_problem": str(summary.get("dominant_problem") or "none"),
            "policy_safe": bool(summary.get("policy_safe", True)),
            "confidence_penalty": self._clamp(summary.get("confidence_penalty", 0.0)),
        }

    def _real_runtime_ratio(self, source_mix: dict[str, float]) -> float:
        return self._clamp(
            source_mix.get("real_runtime", 0.0)
            + source_mix.get("qc_derived", 0.0)
            + source_mix.get("runtime_history", 0.0)
            + source_mix.get("post_publish_metrics", 0.0)
        )

    def _real_runtime_support(self, real_runtime_ratio: float, clean_sample_size: int) -> str:
        if real_runtime_ratio <= 0.0 or clean_sample_size <= 0:
            return "none"
        if clean_sample_size < 5 or real_runtime_ratio < 0.35:
            return "limited"
        if clean_sample_size < 15 or real_runtime_ratio < 0.75:
            return "moderate"
        return "strong"

    def _cluster_dominance(self, cluster_distribution: dict[str, int]) -> float:
        counts = [max(0, int(value)) for value in cluster_distribution.values() if isinstance(value, int)]
        total = sum(counts)
        if total <= 0:
            return 0.0
        return round(max(counts) / total, 4)

    def _bootstrap_penalty(self, risk: str) -> float:
        if risk == "high":
            return 0.38
        if risk == "medium":
            return 0.18
        return 0.0

    def _dominant_source(self, source_mix: dict[str, float]) -> str:
        if not source_mix:
            return "none"
        source, value = max(source_mix.items(), key=lambda item: (item[1], item[0]))
        return source if value > 0 else "none"

    def _max_risk(self, risks: list[str]) -> str:
        if "high" in risks:
            return "high"
        if "medium" in risks:
            return "medium"
        return "low"

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, round(float(value), 4)))
