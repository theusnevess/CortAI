from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.creative.agents.account_health.models import (
    AccountHealthDecision,
    AccountHealthInput,
    AccountHealthResult,
    AccountHealthStatus,
)
from app.creative.agents.account_health.confidence_calibrator import AccountHealthConfidenceCalibrator
from app.creative.agents.account_health.constraint_rationale import AccountHealthConstraintRationaleBuilder
from app.creative.agents.account_health.degraded_input_policy import AccountHealthDegradedInputPolicy
from app.creative.agents.account_health.health_trace import AccountHealthTraceBuilder
from app.creative.agents.account_health.risk_components import AccountHealthRiskComponentScorer
from app.creative.agents.account_health.temporal_health import AccountHealthTemporalAnalyzer
from app.creative.agents.account_health.telemetry_enrichment import AccountHealthTelemetryEnricher
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode


@dataclass
class AccountHealthAgentService:
    telemetry_enricher: AccountHealthTelemetryEnricher = field(default_factory=AccountHealthTelemetryEnricher)
    risk_component_scorer: AccountHealthRiskComponentScorer = field(default_factory=AccountHealthRiskComponentScorer)
    temporal_analyzer: AccountHealthTemporalAnalyzer = field(default_factory=AccountHealthTemporalAnalyzer)
    confidence_calibrator: AccountHealthConfidenceCalibrator = field(default_factory=AccountHealthConfidenceCalibrator)
    degraded_input_policy: AccountHealthDegradedInputPolicy = field(default_factory=AccountHealthDegradedInputPolicy)
    constraint_rationale_builder: AccountHealthConstraintRationaleBuilder = field(
        default_factory=AccountHealthConstraintRationaleBuilder
    )
    health_trace_builder: AccountHealthTraceBuilder = field(default_factory=AccountHealthTraceBuilder)

    def evaluate(self, data: AccountHealthInput) -> AccountHealthResult:
        try:
            return self._evaluate(data)
        except Exception:  # noqa: BLE001
            return self._fallback_result(data=data, reason="ACCOUNT_HEALTH_EVALUATION_EXCEPTION")

    def _evaluate(self, data: AccountHealthInput) -> AccountHealthResult:
        if data.recent_publish_count < 0:
            return self._fallback_result(data=data, reason="ACCOUNT_HEALTH_COLD_START")

        reasons: list[str] = []
        constraints: dict[str, object] = {}
        status = AccountHealthStatus.SAFE
        triggered_conditions: list[str] = []
        telemetry_summary = self.telemetry_enricher.enrich(data).to_dict()
        risk_summary = self.risk_component_scorer.score(data, telemetry_summary).to_dict()
        temporal_result = self.temporal_analyzer.analyze(
            data=data,
            telemetry_summary=telemetry_summary,
            risk_summary=risk_summary,
        ).to_dict()
        input_summary = self._build_input_summary(data, telemetry_summary=telemetry_summary)
        threshold_evaluations = self._build_threshold_evaluations(data)

        if data.recent_views_drop_ratio >= 0.75 or data.recent_low_performance_streak >= 4:
            status = AccountHealthStatus.HOLD
            if data.recent_views_drop_ratio >= 0.75:
                reasons.append("RECENT_VIEWS_DROP")
                triggered_conditions.append("recent_views_drop_ratio>=0.75")
            if data.recent_low_performance_streak >= 4:
                reasons.append("LOW_PERFORMANCE_STREAK")
                triggered_conditions.append("recent_low_performance_streak>=4")
            constraints["block_generation"] = True
        elif (
            data.recent_views_drop_ratio >= 0.40
            or data.recent_format_repetition_ratio >= 0.65
            or data.recent_low_performance_streak >= 2
        ):
            status = AccountHealthStatus.CAUTION
            if data.recent_views_drop_ratio >= 0.40:
                reasons.append("RECENT_VIEWS_DROP")
                triggered_conditions.append("recent_views_drop_ratio>=0.40")
            if data.recent_format_repetition_ratio >= 0.65:
                reasons.append("FORMAT_REPETITION_HIGH")
                triggered_conditions.append("recent_format_repetition_ratio>=0.65")
            if data.recent_low_performance_streak >= 2:
                reasons.append("LOW_PERFORMANCE_STREAK")
                triggered_conditions.append("recent_low_performance_streak>=2")
            constraints.update(
                {
                    "reduce_hook_aggressiveness": True,
                    "max_daily_posts": 1,
                }
            )

        if status is AccountHealthStatus.SAFE:
            reasons.append("HEALTHY_BASELINE")
        confidence_result = self.confidence_calibrator.calibrate(
            decision_status=status.value,
            telemetry_summary=telemetry_summary,
            risk_summary=risk_summary,
            temporal_health=temporal_result,
        ).to_dict()
        degraded_decision = self.degraded_input_policy.evaluate(
            original_decision=status.value,
            telemetry_summary=telemetry_summary,
            risk_summary=risk_summary,
            confidence_result=confidence_result,
            temporal_health=temporal_result,
            fallback_used=False,
        ).to_dict()
        status, reasons, constraints, triggered_conditions = self._apply_degraded_input_decision(
            status=status.value,
            reasons=reasons,
            constraints=constraints,
            triggered_conditions=triggered_conditions,
            degraded_decision=degraded_decision,
        )
        constraint_rationale = self.constraint_rationale_builder.build(
            recommended_constraints=constraints,
            final_decision=status,
            reasons=reasons,
            risk_summary=risk_summary,
            confidence_result=confidence_result,
            temporal_health=temporal_result,
            degraded_input_decision=degraded_decision,
            telemetry_summary=telemetry_summary,
            fallback_used=False,
        )
        health_trace = self.health_trace_builder.build(
            final_decision=status,
            reasons=reasons,
            recommended_constraints=constraints,
            triggered_conditions=triggered_conditions,
            threshold_evaluations=threshold_evaluations,
            telemetry_summary=telemetry_summary,
            risk_summary=risk_summary,
            confidence_result=confidence_result,
            temporal_health=temporal_result,
            degraded_input_decision=degraded_decision,
            constraint_rationale=constraint_rationale,
            fallback_used=False,
            fallback_reason="",
        )

        return AccountHealthResult(
            decision=AccountHealthDecision(
                status=status,
                reasons=reasons,
                recommended_constraints=constraints,
            ),
            fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
            input_summary=input_summary,
            decision_trace=self._build_decision_trace(
                data=data,
                status=status,
                reasons=reasons,
                constraints=constraints,
                triggered_conditions=triggered_conditions,
                threshold_evaluations=threshold_evaluations,
                fallback_used=False,
                fallback_reason="",
                telemetry_summary=telemetry_summary,
                risk_summary=risk_summary,
                temporal_result=temporal_result,
                confidence_result=confidence_result,
                degraded_decision=degraded_decision,
                constraint_rationale=constraint_rationale,
                health_trace=health_trace,
            ),
            telemetry_summary=telemetry_summary,
            risk_score=float(risk_summary.get("overall_risk_score") or 0.0),
            risk_components=risk_summary,
            confidence=float(confidence_result.get("confidence") or 0.0),
            confidence_level=str(confidence_result.get("level") or "low"),
            confidence_components=dict(confidence_result.get("components") or {}),
            confidence_rationale=dict(confidence_result.get("rationale") or {}),
            temporal_health=temporal_result,
            degraded_input_decision=degraded_decision,
            constraint_rationale=constraint_rationale,
            health_trace=health_trace,
        )

    def _fallback_result(self, *, data: AccountHealthInput | None = None, reason: str) -> AccountHealthResult:
        telemetry_summary = self.telemetry_enricher.enrich(data).to_dict()
        risk_summary = self.risk_component_scorer.score(data, telemetry_summary).to_dict()
        temporal_result = self.temporal_analyzer.analyze(
            data=data,
            telemetry_summary=telemetry_summary,
            risk_summary=risk_summary,
        ).to_dict()
        confidence_result = self.confidence_calibrator.calibrate(
            decision_status=AccountHealthStatus.SAFE.value,
            telemetry_summary=telemetry_summary,
            risk_summary=risk_summary,
            temporal_health=temporal_result,
        ).to_dict()
        degraded_decision = self.degraded_input_policy.evaluate(
            original_decision=AccountHealthStatus.SAFE.value,
            telemetry_summary=telemetry_summary,
            risk_summary=risk_summary,
            confidence_result=confidence_result,
            temporal_health=temporal_result,
            fallback_used=True,
        ).to_dict()
        constraint_rationale = self.constraint_rationale_builder.build(
            recommended_constraints={},
            final_decision=AccountHealthStatus.SAFE.value,
            reasons=["fallback_default"],
            risk_summary=risk_summary,
            confidence_result=confidence_result,
            temporal_health=temporal_result,
            degraded_input_decision=degraded_decision,
            telemetry_summary=telemetry_summary,
            fallback_used=True,
        )
        health_trace = self.health_trace_builder.build(
            final_decision=AccountHealthStatus.SAFE.value,
            reasons=["fallback_default"],
            recommended_constraints={},
            triggered_conditions=["fallback_safe_default"],
            threshold_evaluations=self._build_threshold_evaluations(data),
            telemetry_summary=telemetry_summary,
            risk_summary=risk_summary,
            confidence_result=confidence_result,
            temporal_health=temporal_result,
            degraded_input_decision=degraded_decision,
            constraint_rationale=constraint_rationale,
            fallback_used=True,
            fallback_reason=reason,
        )
        input_summary = self._build_input_summary(data, telemetry_summary=telemetry_summary)
        return AccountHealthResult(
            decision=AccountHealthDecision(
                status=AccountHealthStatus.SAFE.value,
                reasons=["fallback_default"],
                recommended_constraints={},
            ),
            fallback=FallbackDecision(
                used=True,
                mode=FallbackMode.SAFE_DEFAULT.value,
                reason=reason,
            ),
            input_summary=input_summary,
            decision_trace=self._build_decision_trace(
                data=data,
                status=AccountHealthStatus.SAFE.value,
                reasons=["fallback_default"],
                constraints={},
                triggered_conditions=["fallback_safe_default"],
                threshold_evaluations=self._build_threshold_evaluations(data),
                fallback_used=True,
                fallback_reason=reason,
                telemetry_summary=telemetry_summary,
                risk_summary=risk_summary,
                temporal_result=temporal_result,
                confidence_result=confidence_result,
                degraded_decision=degraded_decision,
                constraint_rationale=constraint_rationale,
                health_trace=health_trace,
            ),
            telemetry_summary=telemetry_summary,
            risk_score=float(risk_summary.get("overall_risk_score") or 0.0),
            risk_components=risk_summary,
            confidence=float(confidence_result.get("confidence") or 0.0),
            confidence_level=str(confidence_result.get("level") or "low"),
            confidence_components=dict(confidence_result.get("components") or {}),
            confidence_rationale=dict(confidence_result.get("rationale") or {}),
            temporal_health=temporal_result,
            degraded_input_decision=degraded_decision,
            constraint_rationale=constraint_rationale,
            health_trace=health_trace,
        )

    def _apply_degraded_input_decision(
        self,
        *,
        status: str,
        reasons: list[str],
        constraints: dict[str, object],
        triggered_conditions: list[str],
        degraded_decision: dict[str, Any],
    ) -> tuple[str, list[str], dict[str, object], list[str]]:
        final_status = str(degraded_decision.get("final_decision") or status)
        action = str(degraded_decision.get("action") or "no_change")
        updated_reasons = [reason for reason in reasons if not (reason == "HEALTHY_BASELINE" and final_status != "SAFE")]
        updated_constraints = dict(constraints)
        updated_triggers = list(triggered_conditions)

        if final_status == "CAUTION" and status == "SAFE":
            if "DEGRADED_INPUT_CAUTION" not in updated_reasons:
                updated_reasons.append("DEGRADED_INPUT_CAUTION")
            updated_constraints["degraded_input_caution"] = True
            updated_constraints["require_monitoring"] = True
            updated_triggers.append("degraded_input_policy:upgrade_to_caution")
        elif final_status == "HOLD" and status != "HOLD":
            if "SEVERE_DEGRADED_INPUT_WITH_HIGH_RISK" not in updated_reasons:
                updated_reasons.append("SEVERE_DEGRADED_INPUT_WITH_HIGH_RISK")
            updated_constraints["block_generation"] = True
            updated_triggers.append("degraded_input_policy:upgrade_to_hold")
        elif action != "no_change":
            updated_triggers.append(f"degraded_input_policy:{action}")

        return final_status, updated_reasons, updated_constraints, updated_triggers

    def _build_input_summary(
        self,
        data: AccountHealthInput | None,
        *,
        telemetry_summary: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if data is None:
            return {}
        telemetry_summary = telemetry_summary or self.telemetry_enricher.enrich(data).to_dict()
        return {
            "account_id": data.account_id,
            "recent_publish_count": int(data.recent_publish_count),
            "recent_format_repetition_ratio": float(data.recent_format_repetition_ratio),
            "recent_views_drop_ratio": float(data.recent_views_drop_ratio),
            "recent_low_performance_streak": int(data.recent_low_performance_streak),
            "telemetry_available_signals": list(telemetry_summary.get("available_signals") or []),
            "telemetry_missing_signals": list(telemetry_summary.get("missing_signals") or []),
            "telemetry_degraded_input_mode": bool(telemetry_summary.get("degraded_input_mode")),
        }

    def _build_threshold_evaluations(self, data: AccountHealthInput | None) -> dict[str, Any]:
        if data is None:
            return {}
        return {
            "fallback_on_negative_publish_count": bool(data.recent_publish_count < 0),
            "hold_on_views_drop": bool(data.recent_views_drop_ratio >= 0.75),
            "hold_on_low_performance_streak": bool(data.recent_low_performance_streak >= 4),
            "caution_on_views_drop": bool(data.recent_views_drop_ratio >= 0.40),
            "caution_on_format_repetition": bool(data.recent_format_repetition_ratio >= 0.65),
            "caution_on_low_performance_streak": bool(data.recent_low_performance_streak >= 2),
        }

    def _build_decision_trace(
        self,
        *,
        data: AccountHealthInput | None,
        status: str,
        reasons: list[str],
        constraints: dict[str, object],
        triggered_conditions: list[str],
        threshold_evaluations: dict[str, Any],
        fallback_used: bool,
        fallback_reason: str,
        telemetry_summary: dict[str, Any],
        risk_summary: dict[str, Any],
        temporal_result: dict[str, Any],
        confidence_result: dict[str, Any],
        degraded_decision: dict[str, Any],
        constraint_rationale: list[dict[str, Any]],
        health_trace: dict[str, Any],
    ) -> dict[str, Any]:
        changed = str(degraded_decision.get("original_decision") or status) != str(
            degraded_decision.get("final_decision") or status
        )
        return {
            "input_summary": self._build_input_summary(data, telemetry_summary=telemetry_summary),
            "telemetry_enrichment": {
                "lineage_summary": dict(telemetry_summary.get("lineage_summary") or {}),
                "freshness_summary": dict(telemetry_summary.get("freshness_summary") or {}),
                "source_status_distribution": dict(telemetry_summary.get("source_status_distribution") or {}),
                "available_signals": list(telemetry_summary.get("available_signals") or []),
                "missing_signals": list(telemetry_summary.get("missing_signals") or []),
                "degraded_input_mode": bool(telemetry_summary.get("degraded_input_mode")),
                "degradation_reasons": list(telemetry_summary.get("degradation_reasons") or []),
            },
            "risk_components": dict(risk_summary.get("components") or {}),
            "overall_risk": {
                "score": float(risk_summary.get("overall_risk_score") or 0.0),
                "level": str(risk_summary.get("overall_risk_level") or "low"),
                "dominant_components": list(risk_summary.get("dominant_components") or []),
                "missing_component_inputs": list(risk_summary.get("missing_component_inputs") or []),
                "degraded_component_inputs": list(risk_summary.get("degraded_component_inputs") or []),
                "weights": dict(risk_summary.get("weights") or {}),
            },
            "temporal_health": {
                "classification": str(temporal_result.get("classification") or "insufficient_evidence"),
                "confidence_impact": str(temporal_result.get("confidence_impact") or "negative"),
                "risk_direction": str(temporal_result.get("risk_direction") or "unknown"),
                "window_summary": dict(temporal_result.get("window_summary") or {}),
                "signals_used": list(temporal_result.get("signals_used") or []),
                "reason_codes": list(temporal_result.get("reason_codes") or []),
                "rationale": str(temporal_result.get("rationale") or ""),
            },
            "confidence_calibration": {
                "confidence": float(confidence_result.get("confidence") or 0.0),
                "level": str(confidence_result.get("level") or "low"),
                "components": dict(confidence_result.get("components") or {}),
                "rationale": dict(confidence_result.get("rationale") or {}),
            },
            "degraded_input_policy": {
                "degraded_input_detected": bool(degraded_decision.get("degraded_input_detected")),
                "severity": str(degraded_decision.get("severity") or "none"),
                "action": str(degraded_decision.get("action") or "no_change"),
                "original_decision": str(degraded_decision.get("original_decision") or status),
                "final_decision": str(degraded_decision.get("final_decision") or status),
                "reason_codes": list(degraded_decision.get("reason_codes") or []),
                "affected_sources": list(degraded_decision.get("affected_sources") or []),
                "rationale": str(degraded_decision.get("rationale") or ""),
            },
            "decision_adjustment": {
                "changed": changed,
                "from": str(degraded_decision.get("original_decision") or status),
                "to": str(degraded_decision.get("final_decision") or status),
                "reason": "" if not changed else str(degraded_decision.get("action") or ""),
            },
            "constraint_rationale": [dict(item) for item in constraint_rationale],
            "constraint_rationale_summary": {
                "constraints_emitted": bool(constraints),
                "constraint_count": len(constraints),
                "rationale_count": len(constraint_rationale),
                "coverage_complete": len(constraints) == len(constraint_rationale),
            },
            "health_trace": dict(health_trace),
            "thresholds": {
                "hold_views_drop_ratio": 0.75,
                "hold_low_performance_streak": 4,
                "caution_views_drop_ratio": 0.40,
                "caution_format_repetition_ratio": 0.65,
                "caution_low_performance_streak": 2,
            },
            "threshold_evaluations": dict(threshold_evaluations),
            "triggered_conditions": list(triggered_conditions),
            "reasons_emitted": list(reasons),
            "constraints_emitted": dict(constraints),
            "final_status": status,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
        }
