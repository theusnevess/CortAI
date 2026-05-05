from __future__ import annotations

from dataclasses import dataclass
from typing import Any


_REQUIRED_HEALTH_TRACE_SECTIONS = (
    "telemetry_lineage",
    "risk_assessment",
    "confidence_calibration",
    "temporal_health",
    "degraded_input_policy",
    "constraint_rationale",
    "final_decision_rationale",
    "downgraded_or_missing_inputs",
    "audit_summary",
)


@dataclass(frozen=True)
class AccountHealthTraceBuilder:
    """Consolidates existing Account Health artifacts into an audit trace."""

    def build(
        self,
        *,
        final_decision: str,
        reasons: list[str] | None,
        recommended_constraints: dict[str, Any] | None,
        triggered_conditions: list[str] | None,
        threshold_evaluations: dict[str, Any] | None,
        telemetry_summary: dict[str, Any] | None,
        risk_summary: dict[str, Any] | None,
        confidence_result: dict[str, Any] | None,
        temporal_health: dict[str, Any] | None,
        degraded_input_decision: dict[str, Any] | None,
        constraint_rationale: list[dict[str, Any]] | None,
        fallback_used: bool,
        fallback_reason: str,
    ) -> dict[str, Any]:
        telemetry_summary = dict(telemetry_summary or {})
        risk_summary = dict(risk_summary or {})
        confidence_result = dict(confidence_result or {})
        temporal_health = dict(temporal_health or {})
        degraded_input_decision = dict(degraded_input_decision or {})
        constraints = dict(recommended_constraints or {})
        constraint_rationale = [dict(item) for item in list(constraint_rationale or [])]

        health_trace = {
            "telemetry_lineage": self._telemetry_lineage(telemetry_summary),
            "risk_assessment": self._risk_assessment(risk_summary),
            "confidence_calibration": self._confidence_calibration(confidence_result),
            "temporal_health": self._temporal_health(temporal_health),
            "degraded_input_policy": self._degraded_input_policy(degraded_input_decision),
            "constraint_rationale": constraint_rationale,
            "final_decision_rationale": self._final_decision_rationale(
                final_decision=final_decision,
                reasons=list(reasons or []),
                triggered_conditions=list(triggered_conditions or []),
                threshold_evaluations=dict(threshold_evaluations or {}),
                risk_summary=risk_summary,
                confidence_result=confidence_result,
                temporal_health=temporal_health,
                degraded_input_decision=degraded_input_decision,
                fallback_used=fallback_used,
                fallback_reason=fallback_reason,
            ),
            "downgraded_or_missing_inputs": self._downgraded_or_missing_inputs(
                telemetry_summary=telemetry_summary,
                risk_summary=risk_summary,
            ),
        }
        health_trace["audit_summary"] = self._audit_summary(
            health_trace=health_trace,
            constraints=constraints,
            constraint_rationale=constraint_rationale,
        )
        return health_trace

    def _telemetry_lineage(self, telemetry_summary: dict[str, Any]) -> dict[str, Any]:
        return {
            "lineage_summary": dict(telemetry_summary.get("lineage_summary") or {}),
            "freshness_summary": dict(telemetry_summary.get("freshness_summary") or {}),
            "source_status_distribution": dict(telemetry_summary.get("source_status_distribution") or {}),
            "available_signals": list(telemetry_summary.get("available_signals") or []),
            "missing_signals": list(telemetry_summary.get("missing_signals") or []),
            "degraded_input_mode": bool(telemetry_summary.get("degraded_input_mode")),
            "degradation_reasons": list(telemetry_summary.get("degradation_reasons") or []),
        }

    def _risk_assessment(self, risk_summary: dict[str, Any]) -> dict[str, Any]:
        return {
            "risk_score": self._safe_float(risk_summary.get("overall_risk_score")),
            "overall_risk_level": str(risk_summary.get("overall_risk_level") or "low"),
            "dominant_components": list(risk_summary.get("dominant_components") or []),
            "risk_components": dict(risk_summary.get("components") or {}),
            "missing_component_inputs": list(risk_summary.get("missing_component_inputs") or []),
            "degraded_component_inputs": list(risk_summary.get("degraded_component_inputs") or []),
            "weights": dict(risk_summary.get("weights") or {}),
        }

    def _confidence_calibration(self, confidence_result: dict[str, Any]) -> dict[str, Any]:
        rationale = dict(confidence_result.get("rationale") or {})
        components = dict(confidence_result.get("components") or {})
        penalty_components = {
            key: value
            for key, value in sorted(components.items())
            if str(key).endswith("_penalty") or "penalty" in str(key)
        }
        return {
            "confidence": self._safe_float(confidence_result.get("confidence")),
            "confidence_level": str(confidence_result.get("level") or "low"),
            "confidence_components": components,
            "confidence_rationale": rationale,
            "penalty_components": penalty_components,
            "dominant_reason_codes": list(rationale.get("dominant_reason_codes") or []),
        }

    def _temporal_health(self, temporal_health: dict[str, Any]) -> dict[str, Any]:
        return {
            "classification": str(temporal_health.get("classification") or "insufficient_evidence"),
            "confidence_impact": str(temporal_health.get("confidence_impact") or "negative"),
            "risk_direction": str(temporal_health.get("risk_direction") or "unknown"),
            "signals_used": list(temporal_health.get("signals_used") or []),
            "reason_codes": list(temporal_health.get("reason_codes") or []),
            "rationale": str(temporal_health.get("rationale") or ""),
            "window_summary": dict(temporal_health.get("window_summary") or {}),
        }

    def _degraded_input_policy(self, degraded_input_decision: dict[str, Any]) -> dict[str, Any]:
        return {
            "degraded_input_detected": bool(degraded_input_decision.get("degraded_input_detected")),
            "severity": str(degraded_input_decision.get("severity") or "none"),
            "action": str(degraded_input_decision.get("action") or "no_change"),
            "original_decision": str(degraded_input_decision.get("original_decision") or ""),
            "final_decision": str(degraded_input_decision.get("final_decision") or ""),
            "reason_codes": list(degraded_input_decision.get("reason_codes") or []),
            "affected_sources": list(degraded_input_decision.get("affected_sources") or []),
            "rationale": str(degraded_input_decision.get("rationale") or ""),
        }

    def _final_decision_rationale(
        self,
        *,
        final_decision: str,
        reasons: list[str],
        triggered_conditions: list[str],
        threshold_evaluations: dict[str, Any],
        risk_summary: dict[str, Any],
        confidence_result: dict[str, Any],
        temporal_health: dict[str, Any],
        degraded_input_decision: dict[str, Any],
        fallback_used: bool,
        fallback_reason: str,
    ) -> dict[str, Any]:
        base_decision = str(degraded_input_decision.get("original_decision") or final_decision or "SAFE")
        final_status = str(final_decision or degraded_input_decision.get("final_decision") or base_decision)
        decision_adjusted = base_decision != final_status
        degraded_action = str(degraded_input_decision.get("action") or "no_change")
        dominant_reason_codes = sorted(
            set(
                list(reasons)
                + list(degraded_input_decision.get("reason_codes") or [])
                + list(temporal_health.get("reason_codes") or [])
                + list(dict(confidence_result.get("rationale") or {}).get("dominant_reason_codes") or [])
            )
        )
        if fallback_used and fallback_reason:
            dominant_reason_codes.append(fallback_reason)
            dominant_reason_codes = sorted(set(dominant_reason_codes))
        return {
            "base_decision": base_decision,
            "final_decision": final_status,
            "decision_adjusted": decision_adjusted,
            "adjustment_reason": degraded_action if decision_adjusted else "",
            "dominant_reason_codes": dominant_reason_codes,
            "triggered_conditions": list(triggered_conditions),
            "threshold_evaluations": dict(threshold_evaluations),
            "dominant_risk_components": list(risk_summary.get("dominant_components") or []),
            "confidence_level": str(confidence_result.get("level") or "low"),
            "degraded_input_severity": str(degraded_input_decision.get("severity") or "none"),
            "temporal_classification": str(temporal_health.get("classification") or "insufficient_evidence"),
            "hold_authority_invoked": final_status == "HOLD",
            "fallback_used": bool(fallback_used),
            "fallback_reason": str(fallback_reason or ""),
        }

    def _downgraded_or_missing_inputs(
        self,
        *,
        telemetry_summary: dict[str, Any],
        risk_summary: dict[str, Any],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for source in list(telemetry_summary.get("source_summaries") or []):
            if not isinstance(source, dict):
                continue
            status = str(source.get("source_status") or "ABSENT").upper()
            if status not in {"ABSENT", "STALE", "DEGRADED"}:
                continue
            signal = str(source.get("source_name") or "unknown")
            reason_codes = list(source.get("reason_codes") or [])
            items.append(
                {
                    "signal": signal,
                    "status": status,
                    "impact": self._telemetry_impact(signal=signal, status=status),
                    "rationale": self._source_rationale(signal=signal, status=status, reason_codes=reason_codes),
                }
            )

        for name, component in sorted(dict(risk_summary.get("components") or {}).items()):
            if not isinstance(component, dict):
                continue
            status = str(component.get("evidence_status") or "REAL").upper()
            if status not in {"ABSENT", "STALE", "DEGRADED"}:
                continue
            items.append(
                {
                    "signal": str(name),
                    "status": status,
                    "impact": "risk_component",
                    "rationale": str(component.get("rationale") or f"{name} evidence_status={status}."),
                }
            )

        return sorted(items, key=lambda item: (str(item["signal"]), str(item["status"]), str(item["impact"])))

    def _telemetry_impact(self, *, signal: str, status: str) -> str:
        if status == "ABSENT":
            return "confidence"
        if signal in {"metric_window", "qc_history", "failure_history", "format_repetition"}:
            return "temporal_health"
        if status == "DEGRADED":
            return "degraded_input_policy"
        return "confidence"

    def _source_rationale(self, *, signal: str, status: str, reason_codes: list[Any]) -> str:
        reason_text = ",".join(sorted(str(reason) for reason in reason_codes)) or "no_source_reason_code"
        return f"{signal} telemetry is {status}; reason_codes={reason_text}."

    def _audit_summary(
        self,
        *,
        health_trace: dict[str, Any],
        constraints: dict[str, Any],
        constraint_rationale: list[dict[str, Any]],
    ) -> dict[str, Any]:
        missing_sections = [
            section
            for section in _REQUIRED_HEALTH_TRACE_SECTIONS
            if section != "audit_summary" and section not in health_trace
        ]
        rationale_keys = [str(item.get("constraint_key") or "") for item in constraint_rationale]
        constraint_keys = [str(key) for key in constraints]
        coverage_complete = sorted(rationale_keys) == sorted(constraint_keys) and len(rationale_keys) == len(
            set(rationale_keys)
        )
        indicators: list[str] = []
        if missing_sections:
            indicators.append("HEALTH_TRACE_REQUIRED_SECTION_MISSING")
        if not coverage_complete:
            indicators.append("CONSTRAINT_RATIONALE_COVERAGE_INCOMPLETE")
        return {
            "reconstructible": not indicators,
            "required_sections_present": not missing_sections,
            "decision_trace_backward_compatible": True,
            "constraint_coverage_complete": coverage_complete,
            "silent_failure_indicators": indicators,
        }

    def _safe_float(self, value: Any) -> float:
        try:
            return round(float(value), 4)
        except (TypeError, ValueError):
            return 0.0
