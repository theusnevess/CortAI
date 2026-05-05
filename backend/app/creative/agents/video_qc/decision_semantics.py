from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.agents.video_qc.confidence_evidence import (
    PERCEPTUAL_FAILURE_CODES,
    PRODUCT_FAILURE_CODES,
    TECHNICAL_FAILURE_CODES,
)


QC_DECISION_SEMANTICS_VERSION = "qc_decision_semantics_v2_6"


CRITICAL_REASON_CODES = {
    "QC_INTERNAL_ERROR",
    "QC_VIDEO_MISSING",
    "QC_AUDIO_MISSING",
    "QC_METADATA_MISSING",
    "QC_AUDIO_STREAM_MISSING",
}

HIGH_REASON_CODES = {
    "QC_RENDER_JOB_ID_MISSING",
    "QC_DURATION_BELOW_MINIMUM",
    "QC_SUBTITLE_CUES_INVALID",
    "QC_EMPTY_CUE_TEXT",
    "QC_GLYPH_BROKEN",
    "QC_PAYOFF_TOO_DARK",
    "QC_RESOLUTION_INVALID",
    "QC_HOOK_QUALITY_FAIL",
    "QC_PAYOFF_QUALITY_FAIL",
    "QC_PUBLISHABILITY_FAIL",
    "QC_OVERALL_SCORE_FAIL",
}

MEDIUM_REASON_CODES = {
    "QC_HOOK_QUALITY_BORDERLINE",
    "QC_PAYOFF_QUALITY_BORDERLINE",
    "QC_PUBLISHABILITY_HOLD",
    "QC_OVERALL_SCORE_BORDERLINE",
}


@dataclass(frozen=True)
class VideoQcReasonSemantics:
    reason_code: str
    source_list: str
    category: str
    severity: str
    disposition: str
    decision_impact: str
    evidence_summary: dict[str, Any] = field(default_factory=dict)
    rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VideoQcDecisionSemantics:
    semantics_version: str
    status: str
    publishable: bool
    severity_level: str
    decision_rule_applied: str
    hard_failures: list[str]
    soft_failures: list[str]
    product_vetoes: list[str]
    blockers: list[str]
    warnings: list[str]
    monitorable: list[str]
    reason_semantics: list[VideoQcReasonSemantics]
    publishability_rationale: dict[str, Any]
    decision_consistency: bool
    boundary_statement: str
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["reason_semantics"] = [item.to_dict() for item in self.reason_semantics]
        return payload


@dataclass(frozen=True)
class VideoQcDecisionSemanticsEvaluator:
    """Explain existing QC status semantics without changing the status."""

    def evaluate(
        self,
        *,
        status: str,
        publishable: bool,
        hard_failures: list[str],
        soft_failures: list[str],
        product_vetoes: list[str],
        score_summary: dict[str, float],
        product_signals: dict[str, Any],
        qc_input_governance: dict[str, Any],
        qc_evidence_scoring: dict[str, Any],
        confidence_calibration: dict[str, Any],
        details: dict[str, Any],
    ) -> VideoQcDecisionSemantics:
        unique_hard = list(dict.fromkeys(hard_failures))
        unique_soft = list(dict.fromkeys(soft_failures))
        unique_vetoes = list(dict.fromkeys(product_vetoes))
        monitorable = self._monitorable_reason_codes(
            qc_input_governance=qc_input_governance,
            details=details,
            confidence_calibration=confidence_calibration,
        )
        reason_semantics = [
            *[
                self._reason_semantics(
                    reason_code=reason_code,
                    source_list="hard_failures",
                    score_summary=score_summary,
                    product_signals=product_signals,
                    details=details,
                )
                for reason_code in unique_hard
            ],
            *[
                self._reason_semantics(
                    reason_code=reason_code,
                    source_list="product_vetoes",
                    score_summary=score_summary,
                    product_signals=product_signals,
                    details=details,
                )
                for reason_code in unique_vetoes
            ],
            *[
                self._reason_semantics(
                    reason_code=reason_code,
                    source_list="soft_failures",
                    score_summary=score_summary,
                    product_signals=product_signals,
                    details=details,
                )
                for reason_code in unique_soft
            ],
            *[
                self._monitorable_semantics(
                    reason_code=reason_code,
                    qc_input_governance=qc_input_governance,
                    details=details,
                )
                for reason_code in monitorable
            ],
        ]
        blockers = [item.reason_code for item in reason_semantics if item.disposition == "blocker"]
        warnings = [item.reason_code for item in reason_semantics if item.disposition == "warning"]
        monitorable_codes = [item.reason_code for item in reason_semantics if item.disposition == "monitorable"]
        severity_level = self._overall_severity(status=status, reason_semantics=reason_semantics)
        decision_rule = self._decision_rule(
            status=status,
            hard_failures=unique_hard,
            product_vetoes=unique_vetoes,
            soft_failures=unique_soft,
        )
        consistency = self._decision_consistency(
            status=status,
            publishable=publishable,
            hard_failures=unique_hard,
            product_vetoes=unique_vetoes,
            soft_failures=unique_soft,
            product_signals=product_signals,
        )
        return VideoQcDecisionSemantics(
            semantics_version=QC_DECISION_SEMANTICS_VERSION,
            status=status,
            publishable=publishable,
            severity_level=severity_level,
            decision_rule_applied=decision_rule,
            hard_failures=unique_hard,
            soft_failures=unique_soft,
            product_vetoes=unique_vetoes,
            blockers=blockers,
            warnings=warnings,
            monitorable=monitorable_codes,
            reason_semantics=reason_semantics,
            publishability_rationale=self._publishability_rationale(
                status=status,
                publishable=publishable,
                product_signals=product_signals,
                blockers=blockers,
                warnings=warnings,
            ),
            decision_consistency=consistency,
            boundary_statement="QC decision semantics explain APPROVE/HOLD/REJECT only; they do not change thresholds or publishability.",
            rationale=self._rationale(
                status=status,
                severity_level=severity_level,
                decision_rule=decision_rule,
                consistency=consistency,
                qc_evidence_scoring=qc_evidence_scoring,
            ),
        )

    def _reason_semantics(
        self,
        *,
        reason_code: str,
        source_list: str,
        score_summary: dict[str, float],
        product_signals: dict[str, Any],
        details: dict[str, Any],
    ) -> VideoQcReasonSemantics:
        category = self._category(reason_code)
        severity = self._severity(reason_code=reason_code, source_list=source_list)
        disposition = "warning" if source_list == "soft_failures" else "blocker"
        decision_impact = "hold_path" if disposition == "warning" else "reject_path"
        return VideoQcReasonSemantics(
            reason_code=reason_code,
            source_list=source_list,
            category=category,
            severity=severity,
            disposition=disposition,
            decision_impact=decision_impact,
            evidence_summary=self._evidence_summary(reason_code=reason_code, score_summary=score_summary, product_signals=product_signals, details=details),
            rationale=[
                self._reason_rationale(
                    reason_code=reason_code,
                    category=category,
                    severity=severity,
                    disposition=disposition,
                )
            ],
        )

    def _monitorable_semantics(
        self,
        *,
        reason_code: str,
        qc_input_governance: dict[str, Any],
        details: dict[str, Any],
    ) -> VideoQcReasonSemantics:
        return VideoQcReasonSemantics(
            reason_code=reason_code,
            source_list="monitorable",
            category="environment" if "PROBE" in reason_code or "FALLBACK" in reason_code else "evidence_limitation",
            severity="low",
            disposition="monitorable",
            decision_impact="monitoring_only",
            evidence_summary={
                "probe_mode": details.get("probe_mode"),
                "missing_inputs": list(qc_input_governance.get("missing_inputs", [])),
                "environment_dependent_inputs": list(qc_input_governance.get("environment_dependent_inputs", [])),
            },
            rationale=["Monitorable evidence limitation is exposed for audit and does not alter the current QC decision."],
        )

    def _monitorable_reason_codes(
        self,
        *,
        qc_input_governance: dict[str, Any],
        details: dict[str, Any],
        confidence_calibration: dict[str, Any],
    ) -> list[str]:
        reason_codes: list[str] = []
        if details.get("probe_mode") == "metadata_fallback":
            reason_codes.append("QC_METADATA_FALLBACK_PROBE_MONITORABLE")
        missing_traces = [
            key
            for key in qc_input_governance.get("missing_inputs", [])
            if key in {"tts_trace", "visual_trace", "edit_trace"}
        ]
        if missing_traces:
            reason_codes.append("QC_OPTIONAL_UPSTREAM_TRACE_MISSING_MONITORABLE")
        if confidence_calibration.get("confidence_level") == "low":
            reason_codes.append("QC_LOW_CONFIDENCE_MONITORABLE")
        return list(dict.fromkeys(reason_codes))

    def _category(self, reason_code: str) -> str:
        if reason_code in TECHNICAL_FAILURE_CODES:
            return "technical"
        if reason_code in PERCEPTUAL_FAILURE_CODES:
            return "perceptual"
        if reason_code in PRODUCT_FAILURE_CODES:
            return "product"
        if "PROBE" in reason_code or "FALLBACK" in reason_code:
            return "environment"
        return "unknown"

    def _severity(self, *, reason_code: str, source_list: str) -> str:
        if reason_code in CRITICAL_REASON_CODES:
            return "critical"
        if reason_code in HIGH_REASON_CODES:
            return "high"
        if reason_code in MEDIUM_REASON_CODES:
            return "medium"
        if source_list == "soft_failures":
            return "medium"
        if source_list in {"hard_failures", "product_vetoes"}:
            return "high"
        return "low"

    def _overall_severity(self, *, status: str, reason_semantics: list[VideoQcReasonSemantics]) -> str:
        severity_order = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
        if not reason_semantics:
            return "none"
        max_severity = max((item.severity for item in reason_semantics), key=lambda value: severity_order.get(value, 0))
        if status == "APPROVE":
            return "none" if severity_order.get(max_severity, 0) <= 1 else max_severity
        return max_severity

    def _decision_rule(self, *, status: str, hard_failures: list[str], product_vetoes: list[str], soft_failures: list[str]) -> str:
        if status == "APPROVE":
            return "APPROVE_NO_FAILURES_AND_PUBLISHABLE_SIGNAL"
        if status == "HOLD":
            return "HOLD_SOFT_FAILURES_WITHOUT_BLOCKERS"
        if hard_failures:
            return "REJECT_HARD_FAILURE_BLOCKER"
        if product_vetoes:
            return "REJECT_PRODUCT_VETO_BLOCKER"
        return "UNCLASSIFIED_DECISION_RULE"

    def _decision_consistency(
        self,
        *,
        status: str,
        publishable: bool,
        hard_failures: list[str],
        product_vetoes: list[str],
        soft_failures: list[str],
        product_signals: dict[str, Any],
    ) -> bool:
        if status == "APPROVE":
            return not hard_failures and not product_vetoes and not soft_failures and publishable and bool(product_signals.get("publishable"))
        if status == "HOLD":
            return not hard_failures and not product_vetoes and bool(soft_failures) and not publishable
        if status == "REJECT":
            return bool(hard_failures or product_vetoes) and not publishable
        return False

    def _publishability_rationale(
        self,
        *,
        status: str,
        publishable: bool,
        product_signals: dict[str, Any],
        blockers: list[str],
        warnings: list[str],
    ) -> dict[str, Any]:
        if publishable:
            rationale = "Publishable is true only because QC status is APPROVE and existing product publishability signal is true."
        elif blockers:
            rationale = "Publishable is false because blockers require REJECT under existing QC semantics."
        elif warnings:
            rationale = "Publishable is false because HOLD is a non-publishable review state under existing QC semantics."
        else:
            rationale = "Publishable is false because the existing QC decision did not meet APPROVE semantics."
        return {
            "publishable": publishable,
            "status": status,
            "product_publishable_signal": product_signals.get("publishable"),
            "blockers_present": bool(blockers),
            "warnings_present": bool(warnings),
            "rationale": rationale,
        }

    def _evidence_summary(
        self,
        *,
        reason_code: str,
        score_summary: dict[str, float],
        product_signals: dict[str, Any],
        details: dict[str, Any],
    ) -> dict[str, Any]:
        summary: dict[str, Any] = {"probe_mode": details.get("probe_mode")}
        if reason_code.startswith("QC_HOOK"):
            summary["hook_quality"] = product_signals.get("hook_quality")
        if reason_code.startswith("QC_PAYOFF"):
            summary["payoff_quality"] = product_signals.get("payoff_quality")
            summary["payoff_background_mean_luma"] = details.get("payoff_background_mean_luma")
        if reason_code.startswith("QC_PUBLISHABILITY"):
            summary["publishability_signal"] = product_signals.get("publishability_signal")
        if reason_code.startswith("QC_OVERALL"):
            summary["overall_score"] = score_summary.get("overall_score")
        if reason_code == "QC_RESOLUTION_INVALID":
            summary["width"] = details.get("width")
            summary["height"] = details.get("height")
        if reason_code == "QC_DURATION_BELOW_MINIMUM":
            summary["render_duration_s"] = details.get("render_duration_s")
        return {key: value for key, value in summary.items() if value is not None}

    def _reason_rationale(self, *, reason_code: str, category: str, severity: str, disposition: str) -> str:
        return (
            f"{reason_code} is classified as {category} evidence with {severity} severity "
            f"and {disposition} disposition under existing QC semantics."
        )

    def _rationale(
        self,
        *,
        status: str,
        severity_level: str,
        decision_rule: str,
        consistency: bool,
        qc_evidence_scoring: dict[str, Any],
    ) -> list[str]:
        rationale = [
            f"{status} was explained using existing hard failures, product vetoes, soft failures, and publishability.",
            f"Severity is {severity_level} based on emitted reason codes; no thresholds were changed.",
            f"Decision rule applied: {decision_rule}.",
        ]
        if not consistency:
            rationale.append("Decision consistency check failed; this is trace-visible but does not mutate the emitted decision.")
        if qc_evidence_scoring:
            rationale.append("Evidence scoring is linked for audit, not for decision recalculation.")
        return rationale
