from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.contracts.creative_pack import LearningStrategyPressure, PatternFindingSummary
from app.learning.contamination_guard import LearningContaminationGuard
from app.learning.confidence_calibrator import ConfidenceCalibration


@dataclass(frozen=True)
class LearningEvidenceReference:
    source_type: str
    source_id: str
    timestamp: str = ""
    clean: bool = False
    classification: str = "INSUFFICIENT"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LearningLineageSummary:
    total_evidence_count: int
    clean_evidence_count: int
    contaminated_evidence_count: int
    weak_signal_count: int
    insufficient_count: int
    noisy_count: int
    dominant_source_type: str
    controlled_validation_dominance: bool
    real_runtime_support: str
    evidence_references: list[LearningEvidenceReference] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence_references"] = [item.to_dict() for item in self.evidence_references]
        return payload


class LearningTraceBuilder:
    """Builds an audit-grade trace surface for the bounded Learning subsystem."""

    def __init__(self) -> None:
        self._guard = LearningContaminationGuard()

    def build_learning_trace(
        self,
        *,
        evidence_items: list[dict[str, Any]],
        qc_analysis: dict[str, Any],
        confidence_calibration: ConfidenceCalibration,
        confidence_inputs: dict[str, Any],
        confidence_summary: dict[str, Any],
        temporal_analysis: dict[str, Any],
        contamination_summary: dict[str, Any],
        strategy_pressure: LearningStrategyPressure,
        pattern_findings: list[PatternFindingSummary],
    ) -> dict[str, Any]:
        lineage_summary = self.build_lineage_summary(
            evidence_items=evidence_items,
            confidence_calibration=confidence_calibration,
        )
        confidence_trace = self._confidence_trace(
            calibration=confidence_calibration,
            confidence_inputs=confidence_inputs,
            confidence_summary=confidence_summary,
        )
        contamination_trace = self._contamination_trace(contamination_summary)
        temporal_trace = self._temporal_trace(temporal_analysis)
        pressure_trace = self._strategy_pressure_trace(strategy_pressure)
        safety_summary = self._policy_safety_summary(
            confidence_calibration=confidence_calibration,
            temporal_analysis=temporal_analysis,
            contamination_summary=contamination_summary,
            strategy_pressure=strategy_pressure,
        )
        return {
            "lineage_summary": lineage_summary,
            "qc_analysis": self._qc_trace(qc_analysis),
            "confidence_calibration": confidence_trace,
            "temporal_analysis": temporal_trace,
            "contamination_analysis": contamination_trace,
            "strategy_pressure": pressure_trace,
            "policy_safety_summary": safety_summary,
            "pattern_rationale": self._pattern_rationale(
                pattern_findings=pattern_findings,
                temporal_analysis=temporal_analysis,
                contamination_summary=contamination_summary,
                confidence=confidence_calibration.confidence,
            ),
            "downgraded_evidence": self._downgraded_evidence(evidence_items),
        }

    def build_policy_trace(
        self,
        *,
        evidence_items: list[dict[str, Any]],
        confidence_calibration: ConfidenceCalibration,
        temporal_analysis: dict[str, Any],
        contamination_summary: dict[str, Any],
        strategy_pressure: LearningStrategyPressure,
        existing_policy_trace: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        base = dict(existing_policy_trace or {})
        lineage = self.build_lineage_summary(
            evidence_items=evidence_items,
            confidence_calibration=confidence_calibration,
        )
        base["lineage_summary"] = {
            "total_evidence_count": lineage["total_evidence_count"],
            "clean_evidence_count": lineage["clean_evidence_count"],
            "dominant_source_type": lineage["dominant_source_type"],
            "real_runtime_support": lineage["real_runtime_support"],
        }
        base["confidence_formation"] = {
            "final_confidence": confidence_calibration.confidence,
            "policy_strength": confidence_calibration.policy_strength,
            "bootstrap_bias_risk": confidence_calibration.bootstrap_bias_risk,
            "penalties_applied": self._penalties_applied(confidence_calibration, contamination_summary),
        }
        base["temporal_pattern_impact"] = {
            "pattern_type": str(temporal_analysis.get("pattern_type") or "unknown"),
            "staleness_detected": bool(temporal_analysis.get("staleness_detected", False)),
            "volatility_detected": bool(temporal_analysis.get("volatility_detected", False)),
        }
        base["contamination_impact"] = {
            "dominant_problem": str(contamination_summary.get("dominant_problem") or "none"),
            "policy_safe": bool(contamination_summary.get("policy_safe", False)),
            "confidence_penalty": self._as_float(contamination_summary.get("confidence_penalty")),
        }
        base["strategy_pressure_generation"] = self._strategy_pressure_trace(strategy_pressure)
        base["final_safety_classification"] = self._policy_safety_summary(
            confidence_calibration=confidence_calibration,
            temporal_analysis=temporal_analysis,
            contamination_summary=contamination_summary,
            strategy_pressure=strategy_pressure,
        )
        return base

    def build_lineage_summary(
        self,
        *,
        evidence_items: list[dict[str, Any]],
        confidence_calibration: ConfidenceCalibration,
    ) -> dict[str, Any]:
        references: list[LearningEvidenceReference] = []
        label_counts = {
            "CLEAN": 0,
            "CONTAMINATED": 0,
            "WEAK_SIGNAL": 0,
            "INSUFFICIENT": 0,
            "NOISY": 0,
        }
        source_counts: dict[str, int] = {}
        for index, item in enumerate(evidence_items):
            if not isinstance(item, dict):
                continue
            classification = self._guard.classify_evidence_item(item)
            label_counts[classification.label] = label_counts.get(classification.label, 0) + 1
            source_type = str(item.get("source_type") or item.get("source") or "other")
            source_counts[source_type] = source_counts.get(source_type, 0) + 1
            source_id = self._source_id(item=item, fallback_index=index)
            if source_id:
                references.append(
                    LearningEvidenceReference(
                        source_type=source_type,
                        source_id=source_id,
                        timestamp=str(item.get("timestamp") or ""),
                        clean=classification.label == "CLEAN",
                        classification=classification.label,
                    )
                )

        total = sum(label_counts.values())
        dominant_source = "none"
        if source_counts:
            dominant_source = max(sorted(source_counts), key=lambda key: source_counts[key])
        return LearningLineageSummary(
            total_evidence_count=total,
            clean_evidence_count=label_counts["CLEAN"],
            contaminated_evidence_count=label_counts["CONTAMINATED"],
            weak_signal_count=label_counts["WEAK_SIGNAL"],
            insufficient_count=label_counts["INSUFFICIENT"],
            noisy_count=label_counts["NOISY"],
            dominant_source_type=dominant_source,
            controlled_validation_dominance=confidence_calibration.controlled_validation_dominance,
            real_runtime_support=confidence_calibration.real_runtime_support,
            evidence_references=references[:25],
        ).to_dict()

    def _qc_trace(self, qc_analysis: dict[str, Any]) -> dict[str, Any]:
        return {
            "sample_size": int(qc_analysis.get("sample_size") or 0),
            "clean_sample_size": int(qc_analysis.get("clean_sample_size") or 0),
            "approve_rate": self._as_float(qc_analysis.get("approve_rate")),
            "hold_rate": self._as_float(qc_analysis.get("hold_rate")),
            "reject_rate": self._as_float(qc_analysis.get("reject_rate")),
            "top_patterns": list(qc_analysis.get("patterns") or [])[:5],
            "confidence_summary": dict(qc_analysis.get("confidence_summary") or {}),
            "contamination_rate": self._as_float(qc_analysis.get("contamination_rate")),
        }

    def _confidence_trace(
        self,
        *,
        calibration: ConfidenceCalibration,
        confidence_inputs: dict[str, Any],
        confidence_summary: dict[str, Any],
    ) -> dict[str, Any]:
        penalties = self._penalties_applied(calibration, calibration.confidence_rationale)
        components = dict(calibration.confidence_components)
        base_estimate = self._base_confidence_estimate(components, calibration.real_runtime_support)
        return {
            "sample_size": calibration.confidence_rationale.get("sample_size", 0),
            "clean_sample_size": calibration.confidence_rationale.get("clean_sample_size", 0),
            "contamination_rate": calibration.confidence_rationale.get("contamination_rate", 0.0),
            "signal_consistency": confidence_inputs.get("signal_consistency", 0.0),
            "signal_strength": confidence_inputs.get("signal_strength", 0.0),
            "bootstrap_bias_risk": calibration.bootstrap_bias_risk,
            "controlled_validation_dominance": calibration.controlled_validation_dominance,
            "temporal_pattern_type": confidence_inputs.get("temporal_pattern_type", "unknown"),
            "evidence_origin_mix": dict(calibration.evidence_origin_mix),
            "real_runtime_support": calibration.real_runtime_support,
            "base_confidence_estimate": base_estimate,
            "final_confidence": calibration.confidence,
            "policy_strength": calibration.policy_strength,
            "confidence_components": components,
            "confidence_summary": dict(confidence_summary),
            "penalties_applied": penalties,
            "rationale": self._confidence_rationale_text(calibration, penalties),
        }

    def _temporal_trace(self, temporal_analysis: dict[str, Any]) -> dict[str, Any]:
        pattern_type = str(temporal_analysis.get("pattern_type") or "volatile")
        return {
            "recent_weight": self._as_float(temporal_analysis.get("recent_weight")),
            "mid_term_weight": self._as_float(temporal_analysis.get("mid_term_weight")),
            "long_term_weight": self._as_float(temporal_analysis.get("long_term_weight")),
            "dominant_window": str(temporal_analysis.get("dominant_window") or "recent"),
            "pattern_type": pattern_type,
            "staleness_detected": bool(temporal_analysis.get("staleness_detected", False)),
            "volatility_detected": bool(temporal_analysis.get("volatility_detected", False)),
            "weighted_sample_size": self._as_float(temporal_analysis.get("weighted_sample_size")),
            "weighted_signal_strength": self._as_float(temporal_analysis.get("weighted_signal_strength")),
            "weighted_consistency": self._as_float(temporal_analysis.get("weighted_consistency")),
            "window_breakdown": dict(temporal_analysis.get("window_breakdown") or {}),
            "rationale": self._temporal_rationale_text(pattern_type),
        }

    def _contamination_trace(self, contamination_summary: dict[str, Any]) -> dict[str, Any]:
        return {
            "sample_size": int(contamination_summary.get("sample_size") or 0),
            "clean_sample_size": int(contamination_summary.get("clean_sample_size") or 0),
            "contamination_rate": self._as_float(contamination_summary.get("contamination_rate")),
            "noise_rate": self._as_float(contamination_summary.get("noise_rate")),
            "weak_signal_rate": self._as_float(contamination_summary.get("weak_signal_rate")),
            "insufficient_rate": self._as_float(contamination_summary.get("insufficient_rate")),
            "dominant_problem": str(contamination_summary.get("dominant_problem") or "none"),
            "policy_safe": bool(contamination_summary.get("policy_safe", False)),
            "confidence_penalty": self._as_float(contamination_summary.get("confidence_penalty")),
            "cluster_report": dict(contamination_summary.get("cluster_report") or {}),
            "rationale": self._contamination_rationale_text(contamination_summary),
        }

    def _strategy_pressure_trace(self, strategy_pressure: LearningStrategyPressure) -> dict[str, Any]:
        payload = strategy_pressure.to_dict()
        origin = payload.get("pressure_origin_summary") if isinstance(payload.get("pressure_origin_summary"), dict) else {}
        target_count = len(payload.get("pressure_targets") or [])
        pressure_mode = str(payload.get("pressure_mode") or "weak_bias")
        pressure_safe = bool(origin.get("policy_safe", False)) and target_count > 0
        payload["pressure_eligibility"] = {
            "eligible_for_strong_bias": pressure_mode == "strong_bias",
            "policy_safe": bool(origin.get("policy_safe", False)),
            "clean_sample_size": int(origin.get("clean_sample_size") or 0),
            "temporal_pattern_type": str(origin.get("temporal_pattern_type") or "unknown"),
            "confidence": self._as_float(origin.get("confidence")),
        }
        payload["target_generation_reason"] = (
            "targets_generated_from_bounded_policy_signals"
            if target_count
            else "targets_suppressed_due_to_insufficient_or_unsafe_evidence"
        )
        payload["target_suppression_reason"] = "" if target_count else self._target_suppression_reason(origin)
        payload["boundedness_reason"] = (
            "Learning emits policy pressure only; Strategy, Health constraints, Novelty, Experiment, and QC retain authority."
        )
        payload["safe_for_strategy_consideration"] = pressure_safe
        return payload

    def _policy_safety_summary(
        self,
        *,
        confidence_calibration: ConfidenceCalibration,
        temporal_analysis: dict[str, Any],
        contamination_summary: dict[str, Any],
        strategy_pressure: LearningStrategyPressure,
    ) -> dict[str, Any]:
        confidence = confidence_calibration.confidence
        reason_codes: list[str] = []
        warnings: list[str] = []
        blocking: list[str] = []
        confidence_level = "low"
        if confidence >= 0.7:
            confidence_level = "high"
        elif confidence >= 0.35:
            confidence_level = "medium"

        if confidence_calibration.bootstrap_bias_risk == "high":
            reason_codes.append("BOOTSTRAP_BIAS_HIGH")
            warnings.append("Evidence history is still too narrow for unconstrained pressure.")
        if confidence_calibration.controlled_validation_dominance:
            reason_codes.append("CONTROLLED_VALIDATION_DOMINANCE")
            warnings.append("Controlled validation dominates over runtime evidence.")
        if str(temporal_analysis.get("pattern_type") or "") in {"recent_spike", "volatile", "stale_signal"}:
            reason_codes.append(f"TEMPORAL_{str(temporal_analysis.get('pattern_type')).upper()}")
        if not bool(contamination_summary.get("policy_safe", False)):
            reason_codes.append("POLICY_NOT_SAFE_FROM_EVIDENCE_QUALITY")
            blocking.append("policy_safe_false")
        if int(contamination_summary.get("clean_sample_size") or 0) < 5:
            reason_codes.append("CLEAN_SAMPLE_TOO_SMALL")
            blocking.append("clean_sample_size_below_policy_threshold")

        pressure_mode = str(strategy_pressure.pressure_mode or "weak_bias")
        policy_safe = not blocking and confidence_level in {"medium", "high"}
        return {
            "policy_safe": policy_safe,
            "reason_codes": reason_codes,
            "confidence_level": confidence_level,
            "pressure_mode": pressure_mode,
            "blocking_issues": blocking,
            "warnings": warnings,
        }

    def _pattern_rationale(
        self,
        *,
        pattern_findings: list[PatternFindingSummary],
        temporal_analysis: dict[str, Any],
        contamination_summary: dict[str, Any],
        confidence: float,
    ) -> list[dict[str, Any]]:
        temporal_pattern = str(temporal_analysis.get("pattern_type") or "unknown")
        contamination_rate = self._as_float(contamination_summary.get("contamination_rate"))
        policy_safe = bool(contamination_summary.get("policy_safe", False))
        rationales: list[dict[str, Any]] = []
        for item in pattern_findings[:10]:
            safe_to_influence = (
                item.confidence >= 0.35
                and policy_safe
                and contamination_rate <= 0.4
                and temporal_pattern not in {"volatile", "stale_signal"}
            )
            rationales.append({
                "pattern_name": item.pattern_name,
                "evidence_count": item.evidence_count,
                "approve_rate": item.approve_rate,
                "hold_rate": item.hold_rate,
                "reject_rate": item.reject_rate,
                "confidence": item.confidence,
                "temporal_pattern_type": temporal_pattern,
                "contaminated_evidence_rate": item.contaminated_evidence_rate,
                "safe_to_influence_policy": safe_to_influence,
                "rationale": self._pattern_rationale_text(
                    item=item,
                    temporal_pattern=temporal_pattern,
                    contamination_rate=contamination_rate,
                    global_confidence=confidence,
                    policy_safe=policy_safe,
                ),
            })
        return rationales

    def _downgraded_evidence(self, evidence_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        downgraded: list[dict[str, Any]] = []
        for index, item in enumerate(evidence_items):
            if not isinstance(item, dict):
                continue
            classification = self._guard.classify_evidence_item(item)
            if classification.label == "CLEAN":
                continue
            downgraded.append({
                "source_id": self._source_id(item=item, fallback_index=index),
                "source_type": str(item.get("source_type") or item.get("source") or "other"),
                "timestamp": str(item.get("timestamp") or ""),
                "reason": classification.label.lower(),
                "reasons": list(classification.reasons),
                "confidence_penalty": classification.confidence_penalty,
            })
        return downgraded[:25]

    def _penalties_applied(
        self,
        calibration: ConfidenceCalibration,
        contamination_summary: dict[str, Any],
    ) -> list[str]:
        penalties: list[str] = []
        components = calibration.confidence_components
        if calibration.bootstrap_bias_risk == "high":
            penalties.append("bootstrap_bias_high")
        elif calibration.bootstrap_bias_risk == "medium":
            penalties.append("bootstrap_bias_medium")
        if calibration.controlled_validation_dominance:
            penalties.append("controlled_validation_dominance")
        if self._as_float(components.get("controlled_validation_penalty")) > 0:
            penalties.append("controlled_validation_penalty")
        if self._as_float(components.get("contamination_noise_penalty")) > 0:
            penalties.append("contamination_noise_penalty")
        temporal_modifier = self._as_float(components.get("temporal_reliability_modifier"))
        if temporal_modifier < 0:
            penalties.append("temporal_reliability_penalty")
        if self._as_float(contamination_summary.get("noise_rate")) > 0.0:
            penalties.append("noise_present")
        if self._as_float(contamination_summary.get("contamination_rate")) > 0.0:
            penalties.append("contamination_present")
        if int(calibration.confidence_rationale.get("clean_sample_size") or 0) < 5:
            penalties.append("insufficient_clean_sample")
        return penalties

    def _base_confidence_estimate(self, components: dict[str, Any], real_runtime_support: str) -> float:
        real_support_component = {"none": 0.0, "limited": 0.35, "moderate": 0.7, "strong": 1.0}.get(real_runtime_support, 0.0)
        value = (
            self._as_float(components.get("sample_size")) * 0.22
            + self._as_float(components.get("cleanliness")) * 0.18
            + self._as_float(components.get("recency")) * 0.12
            + self._as_float(components.get("consistency")) * 0.2
            + self._as_float(components.get("signal_strength")) * 0.2
            + real_support_component * 0.08
        )
        return round(max(0.0, min(1.0, value)), 4)

    def _confidence_rationale_text(self, calibration: ConfidenceCalibration, penalties: list[str]) -> str:
        if calibration.confidence < 0.35:
            level = "low"
        elif calibration.confidence < 0.7:
            level = "medium"
        else:
            level = "high"
        penalty_text = ", ".join(penalties) if penalties else "no major penalties"
        return (
            f"Confidence is {level} because clean_sample_size="
            f"{calibration.confidence_rationale.get('clean_sample_size', 0)}, "
            f"real_runtime_support={calibration.real_runtime_support}, "
            f"bootstrap_bias_risk={calibration.bootstrap_bias_risk}, penalties={penalty_text}."
        )

    def _temporal_rationale_text(self, pattern_type: str) -> str:
        if pattern_type == "durable_pattern":
            return "Temporal evidence is consistent across recent, mid-term, and long-term windows."
        if pattern_type == "recent_spike":
            return "Recent evidence is directionally stronger than available history, so pressure remains conservative."
        if pattern_type == "volatile":
            return "Recent and historical evidence conflict or lack stable direction, reducing confidence."
        if pattern_type == "stale_signal":
            return "Evidence is dominated by older windows or lacks recent support, reducing confidence."
        return "Temporal evidence did not form a stronger classified pattern."

    def _contamination_rationale_text(self, contamination_summary: dict[str, Any]) -> str:
        dominant = str(contamination_summary.get("dominant_problem") or "none")
        policy_safe = bool(contamination_summary.get("policy_safe", False))
        return (
            f"Evidence quality dominant_problem={dominant}, policy_safe={policy_safe}, "
            f"clean_sample_size={int(contamination_summary.get('clean_sample_size') or 0)}."
        )

    def _pattern_rationale_text(
        self,
        *,
        item: PatternFindingSummary,
        temporal_pattern: str,
        contamination_rate: float,
        global_confidence: float,
        policy_safe: bool,
    ) -> str:
        if item.contaminated_evidence_rate > 0.4 or contamination_rate > 0.4:
            return (
                f"Pattern {item.pattern_name} downgraded because contamination is elevated; "
                f"evidence_count={item.evidence_count}, approve_rate={item.approve_rate:.2f}."
            )
        if temporal_pattern in {"volatile", "stale_signal"}:
            return (
                f"Pattern {item.pattern_name} held cautiously due to temporal state '{temporal_pattern}'; "
                f"evidence_count={item.evidence_count}, confidence={item.confidence:.2f}."
            )
        if not policy_safe or global_confidence < 0.35:
            return (
                f"Pattern {item.pattern_name} remains weak because policy safety or confidence is insufficient; "
                f"evidence_count={item.evidence_count}, approve_rate={item.approve_rate:.2f}."
            )
        return (
            f"Pattern {item.pattern_name} supported by {item.evidence_count} items with approve_rate="
            f"{item.approve_rate:.2f} under temporal pattern '{temporal_pattern}'."
        )

    def _target_suppression_reason(self, origin: dict[str, Any]) -> str:
        if int(origin.get("clean_sample_size") or 0) < 3:
            return "clean_sample_size_below_minimum"
        if not bool(origin.get("policy_safe", False)):
            return "policy_not_safe_from_evidence_quality"
        dominant = str(origin.get("dominant_problem") or "none")
        if dominant in {"contamination", "noise", "insufficient"}:
            return f"dominant_problem_{dominant}"
        return "no_policy_targets_with_supported_confidence"

    def _source_id(self, *, item: dict[str, Any], fallback_index: int) -> str:
        for key in ("source_id", "source_path", "event_id", "publish_id", "metric_id"):
            value = str(item.get(key) or "").strip()
            if value:
                return value
        return f"evidence_item:{fallback_index}"

    def _as_float(self, value: Any) -> float:
        if isinstance(value, (int, float)):
            return round(max(0.0, min(1.0, float(value))), 4)
        try:
            return round(max(0.0, min(1.0, float(str(value or "").strip()))), 4)
        except Exception:  # noqa: BLE001
            return 0.0
