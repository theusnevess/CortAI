from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


QC_TRACE_VERSION = "qc_trace_auditability_v2_6"

REQUIRED_QC_TRACE_SECTIONS = [
    "input_governance",
    "evidence_scoring",
    "confidence_calibration",
    "decision_semantics",
    "final_qc_decision_rationale",
    "missing_or_degraded_inputs",
    "audit_summary",
]


@dataclass(frozen=True)
class VideoQcTraceAuditSummary:
    reconstructible: bool
    sections_present: list[str]
    missing_sections: list[str]
    required_sections_present: bool
    silent_failure_indicators: list[str]
    decision_trace_consistent: bool
    confidence_consistent: bool
    input_coverage_complete: bool
    boundary_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VideoQcTrace:
    trace_version: str
    input_governance: dict[str, Any]
    evidence_scoring: dict[str, Any]
    confidence_calibration: dict[str, Any]
    decision_semantics: dict[str, Any]
    final_qc_decision_rationale: dict[str, Any]
    missing_or_degraded_inputs: dict[str, Any]
    evidence_summary: dict[str, Any]
    audit_summary: VideoQcTraceAuditSummary

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["audit_summary"] = self.audit_summary.to_dict()
        return payload


@dataclass(frozen=True)
class VideoQcTraceBuilder:
    """Consolidates existing QC audit sections without recalculating QC behavior."""

    def build(
        self,
        *,
        status: str,
        publishable: bool,
        reasons: list[str],
        qc_input_governance: dict[str, Any],
        qc_evidence_scoring: dict[str, Any],
        confidence_calibration: dict[str, Any],
        decision_semantics: dict[str, Any],
        details: dict[str, Any],
    ) -> dict[str, Any]:
        final_rationale = self._final_qc_decision_rationale(
            status=status,
            publishable=publishable,
            reasons=reasons,
            qc_evidence_scoring=qc_evidence_scoring,
            confidence_calibration=confidence_calibration,
            decision_semantics=decision_semantics,
        )
        missing_or_degraded = self._missing_or_degraded_inputs(
            qc_input_governance=qc_input_governance,
            qc_evidence_scoring=qc_evidence_scoring,
            confidence_calibration=confidence_calibration,
            details=details,
        )
        evidence_summary = self._evidence_summary(
            qc_input_governance=qc_input_governance,
            qc_evidence_scoring=qc_evidence_scoring,
            confidence_calibration=confidence_calibration,
            decision_semantics=decision_semantics,
            details=details,
        )
        sections = {
            "input_governance": qc_input_governance,
            "evidence_scoring": qc_evidence_scoring,
            "confidence_calibration": confidence_calibration,
            "decision_semantics": decision_semantics,
            "final_qc_decision_rationale": final_rationale,
            "missing_or_degraded_inputs": missing_or_degraded,
            "audit_summary": {"pending_build": True},
        }
        audit_summary = self._audit_summary(
            sections=sections,
            status=status,
            publishable=publishable,
            qc_input_governance=qc_input_governance,
            confidence_calibration=confidence_calibration,
            decision_semantics=decision_semantics,
        )
        trace = VideoQcTrace(
            trace_version=QC_TRACE_VERSION,
            input_governance=qc_input_governance,
            evidence_scoring=qc_evidence_scoring,
            confidence_calibration=confidence_calibration,
            decision_semantics=decision_semantics,
            final_qc_decision_rationale=final_rationale,
            missing_or_degraded_inputs=missing_or_degraded,
            evidence_summary=evidence_summary,
            audit_summary=audit_summary,
        )
        return trace.to_dict()

    def _final_qc_decision_rationale(
        self,
        *,
        status: str,
        publishable: bool,
        reasons: list[str],
        qc_evidence_scoring: dict[str, Any],
        confidence_calibration: dict[str, Any],
        decision_semantics: dict[str, Any],
    ) -> dict[str, Any]:
        blockers = list(decision_semantics.get("blockers", []))
        warnings = list(decision_semantics.get("warnings", []))
        monitorable = list(decision_semantics.get("monitorable", []))
        dominant_failure_type = self._dominant_failure_type(qc_evidence_scoring)
        confidence = confidence_calibration.get("confidence")
        confidence_level = confidence_calibration.get("confidence_level")
        severity_level = decision_semantics.get("severity_level")
        if status == "APPROVE":
            summary = "APPROVE because no blockers or warnings were emitted and publishable is true under existing QC semantics."
        elif status == "HOLD":
            summary = "HOLD because warning-level soft failures were emitted without blocker failures."
        elif blockers:
            summary = "REJECT because blocker failures were emitted by existing QC logic."
        else:
            summary = "REJECT because existing QC logic did not meet approve or hold semantics."
        return {
            "decision": status,
            "publishable": publishable,
            "dominant_failure_type": dominant_failure_type,
            "blocker_count": len(blockers),
            "warning_count": len(warnings),
            "monitorable_count": len(monitorable),
            "reason_codes": list(reasons),
            "confidence": confidence,
            "confidence_level": confidence_level,
            "severity_level": severity_level,
            "decision_rule_applied": decision_semantics.get("decision_rule_applied"),
            "summary": summary,
        }

    def _missing_or_degraded_inputs(
        self,
        *,
        qc_input_governance: dict[str, Any],
        qc_evidence_scoring: dict[str, Any],
        confidence_calibration: dict[str, Any],
        details: dict[str, Any],
    ) -> dict[str, Any]:
        probe_mode = str(details.get("probe_mode") or qc_input_governance.get("environment_summary", {}).get("media_probe_mode") or "unavailable")
        limitations = []
        missing_inputs = list(qc_input_governance.get("missing_inputs", []))
        degraded_inputs = list(qc_input_governance.get("degraded_inputs", []))
        ignored_inputs = list(qc_input_governance.get("ignored_inputs", []))
        if missing_inputs:
            limitations.append("QC_MISSING_INPUTS_VISIBLE")
        if degraded_inputs:
            limitations.append("QC_DEGRADED_INPUTS_VISIBLE")
        if ignored_inputs:
            limitations.append("QC_IGNORED_INPUTS_VISIBLE")
        if probe_mode == "metadata_fallback":
            limitations.append("QC_METADATA_FALLBACK_USED")
        if qc_evidence_scoring.get("failure_categories", {}).get("environment_limitations"):
            limitations.append("QC_ENVIRONMENT_LIMITATIONS_VISIBLE")
        for penalty in confidence_calibration.get("confidence_rationale", {}).get("penalties", []):
            reason_code = penalty.get("reason_code")
            if reason_code:
                limitations.append(str(reason_code))
        return {
            "missing_inputs": missing_inputs,
            "degraded_inputs": degraded_inputs,
            "ignored_inputs": ignored_inputs,
            "metadata_fallback_used": probe_mode == "metadata_fallback",
            "probe_mode": probe_mode,
            "limitations_detected": list(dict.fromkeys(limitations)),
        }

    def _evidence_summary(
        self,
        *,
        qc_input_governance: dict[str, Any],
        qc_evidence_scoring: dict[str, Any],
        confidence_calibration: dict[str, Any],
        decision_semantics: dict[str, Any],
        details: dict[str, Any],
    ) -> dict[str, Any]:
        failure_categories = qc_evidence_scoring.get("failure_categories", {})
        return {
            "available_inputs": list(qc_input_governance.get("available_inputs", [])),
            "used_inputs": list(qc_input_governance.get("used_inputs", [])),
            "technical_failures": list(failure_categories.get("technical_failures", [])),
            "perceptual_failures": list(failure_categories.get("perceptual_failures", [])),
            "product_failures": list(failure_categories.get("product_failures", [])),
            "environment_limitations": list(failure_categories.get("environment_limitations", [])),
            "confidence": confidence_calibration.get("confidence"),
            "confidence_level": confidence_calibration.get("confidence_level"),
            "severity_level": decision_semantics.get("severity_level"),
            "probe_mode": details.get("probe_mode"),
        }

    def _audit_summary(
        self,
        *,
        sections: dict[str, Any],
        status: str,
        publishable: bool,
        qc_input_governance: dict[str, Any],
        confidence_calibration: dict[str, Any],
        decision_semantics: dict[str, Any],
    ) -> VideoQcTraceAuditSummary:
        sections_present = [
            section
            for section in REQUIRED_QC_TRACE_SECTIONS
            if section in sections and sections.get(section) not in ({}, None)
        ]
        missing_sections = [
            section
            for section in REQUIRED_QC_TRACE_SECTIONS
            if section not in sections or sections.get(section) in ({}, None)
        ]
        decision_trace_consistent = (
            decision_semantics.get("status") == status
            and decision_semantics.get("publishable") == publishable
            and bool(decision_semantics.get("decision_rule_applied"))
            and decision_semantics.get("decision_consistency") is True
        )
        confidence_consistent = (
            isinstance(confidence_calibration.get("confidence"), (int, float))
            and confidence_calibration.get("confidence_level") in {"low", "medium", "high"}
            and confidence_calibration.get("confidence_rationale", {}).get("confidence_meaning") == "trust_in_qc_decision"
        )
        input_coverage_complete = self._input_coverage_complete(qc_input_governance)
        indicators = []
        for section in missing_sections:
            indicators.append(f"QC_TRACE_REQUIRED_SECTION_MISSING:{section}")
        if not decision_trace_consistent:
            indicators.append("QC_TRACE_DECISION_INCONSISTENT")
        if not confidence_consistent:
            indicators.append("QC_TRACE_CONFIDENCE_INCONSISTENT")
        if not input_coverage_complete:
            indicators.append("QC_TRACE_INPUT_USED_NOT_DECLARED")
        required_sections_present = not missing_sections
        reconstructible = (
            required_sections_present
            and decision_trace_consistent
            and confidence_consistent
            and input_coverage_complete
            and not indicators
        )
        return VideoQcTraceAuditSummary(
            reconstructible=reconstructible,
            sections_present=sections_present,
            missing_sections=missing_sections,
            required_sections_present=required_sections_present,
            silent_failure_indicators=indicators,
            decision_trace_consistent=decision_trace_consistent,
            confidence_consistent=confidence_consistent,
            input_coverage_complete=input_coverage_complete,
        )

    def _dominant_failure_type(self, qc_evidence_scoring: dict[str, Any]) -> str:
        categories = qc_evidence_scoring.get("failure_categories", {})
        for category, key in [
            ("technical", "technical_failures"),
            ("perceptual", "perceptual_failures"),
            ("product", "product_failures"),
            ("environment", "environment_limitations"),
            ("unknown", "unknown_failures"),
        ]:
            if categories.get(key):
                return category
        return "none"

    def _input_coverage_complete(self, qc_input_governance: dict[str, Any]) -> bool:
        signal_keys = {
            str(signal.get("input_key"))
            for signal in qc_input_governance.get("input_signals", [])
            if isinstance(signal, dict)
        }
        declared_inputs = set(qc_input_governance.get("available_inputs", []))
        declared_inputs.update(qc_input_governance.get("missing_inputs", []))
        declared_inputs.update(qc_input_governance.get("degraded_inputs", []))
        declared_inputs.update(qc_input_governance.get("ignored_inputs", []))
        declared_inputs.update(qc_input_governance.get("used_inputs", []))
        if not signal_keys:
            return False
        return declared_inputs.issubset(signal_keys)
