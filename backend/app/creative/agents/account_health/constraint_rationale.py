from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AccountHealthConstraintRationale:
    constraint_key: str
    value: Any
    interpretation_mode: str
    severity: str
    reason_code: str
    source: str
    linked_risk_components: list[str]
    evidence_summary: dict[str, Any]
    downstream_interpretation: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AccountHealthConstraintRationaleBuilder:
    """Builds audit rationale for existing Account Health constraints."""

    def build(
        self,
        *,
        recommended_constraints: dict[str, Any] | None,
        final_decision: str,
        reasons: list[str] | None,
        risk_summary: dict[str, Any] | None,
        confidence_result: dict[str, Any] | None,
        temporal_health: dict[str, Any] | None,
        degraded_input_decision: dict[str, Any] | None,
        telemetry_summary: dict[str, Any] | None,
        fallback_used: bool,
    ) -> list[dict[str, Any]]:
        constraints = dict(recommended_constraints or {})
        if not constraints:
            return []

        risk_summary = dict(risk_summary or {})
        confidence_result = dict(confidence_result or {})
        temporal_health = dict(temporal_health or {})
        degraded_input_decision = dict(degraded_input_decision or {})
        telemetry_summary = dict(telemetry_summary or {})
        final_status = str(final_decision or "SAFE").upper()

        rationale_entries = [
            self._build_one(
                constraint_key=key,
                value=constraints[key],
                final_decision=final_status,
                reasons=list(reasons or []),
                risk_summary=risk_summary,
                confidence_result=confidence_result,
                temporal_health=temporal_health,
                degraded_input_decision=degraded_input_decision,
                telemetry_summary=telemetry_summary,
                fallback_used=fallback_used,
            )
            for key in sorted(constraints)
        ]
        return [entry.to_dict() for entry in rationale_entries]

    def _build_one(
        self,
        *,
        constraint_key: str,
        value: Any,
        final_decision: str,
        reasons: list[str],
        risk_summary: dict[str, Any],
        confidence_result: dict[str, Any],
        temporal_health: dict[str, Any],
        degraded_input_decision: dict[str, Any],
        telemetry_summary: dict[str, Any],
        fallback_used: bool,
    ) -> AccountHealthConstraintRationale:
        linked_risks = self._linked_risk_components(constraint_key=constraint_key, risk_summary=risk_summary)
        interpretation_mode = self._interpretation_mode(
            constraint_key=constraint_key,
            final_decision=final_decision,
            degraded_input_decision=degraded_input_decision,
        )
        severity = self._severity(
            interpretation_mode=interpretation_mode,
            risk_level=str(risk_summary.get("overall_risk_level") or "low"),
            degraded_severity=str(degraded_input_decision.get("severity") or "none"),
        )
        source = self._source(
            constraint_key=constraint_key,
            linked_risks=linked_risks,
            degraded_input_decision=degraded_input_decision,
            confidence_result=confidence_result,
            temporal_health=temporal_health,
            fallback_used=fallback_used,
        )
        reason_code = self._reason_code(
            constraint_key=constraint_key,
            source=source,
            final_decision=final_decision,
        )
        evidence_summary = self._evidence_summary(
            risk_summary=risk_summary,
            confidence_result=confidence_result,
            temporal_health=temporal_health,
            degraded_input_decision=degraded_input_decision,
            telemetry_summary=telemetry_summary,
        )
        downstream_interpretation = self._downstream_interpretation(interpretation_mode=interpretation_mode)
        return AccountHealthConstraintRationale(
            constraint_key=constraint_key,
            value=value,
            interpretation_mode=interpretation_mode,
            severity=severity,
            reason_code=reason_code,
            source=source,
            linked_risk_components=linked_risks,
            evidence_summary=evidence_summary,
            downstream_interpretation=downstream_interpretation,
            rationale=self._rationale(
                constraint_key=constraint_key,
                final_decision=final_decision,
                interpretation_mode=interpretation_mode,
                source=source,
                linked_risks=linked_risks,
                reasons=reasons,
                evidence_summary=evidence_summary,
            ),
        )

    def _interpretation_mode(
        self,
        *,
        constraint_key: str,
        final_decision: str,
        degraded_input_decision: dict[str, Any],
    ) -> str:
        if constraint_key == "block_generation" or final_decision == "HOLD":
            return "blocking"
        degraded_severity = str(degraded_input_decision.get("severity") or "none")
        if final_decision == "CAUTION" or degraded_severity in {"moderate", "severe"}:
            return "cautionary"
        return "advisory"

    def _severity(self, *, interpretation_mode: str, risk_level: str, degraded_severity: str) -> str:
        if interpretation_mode == "blocking" or risk_level == "high" or degraded_severity == "severe":
            return "high"
        if interpretation_mode == "cautionary" or risk_level == "medium" or degraded_severity == "moderate":
            return "medium"
        return "low"

    def _source(
        self,
        *,
        constraint_key: str,
        linked_risks: list[str],
        degraded_input_decision: dict[str, Any],
        confidence_result: dict[str, Any],
        temporal_health: dict[str, Any],
        fallback_used: bool,
    ) -> str:
        if fallback_used:
            return "fallback"
        degraded_action = str(degraded_input_decision.get("action") or "no_change")
        if constraint_key in {"degraded_input_caution", "require_monitoring"} and degraded_action != "no_change":
            return "degraded_input_policy"
        if constraint_key == "block_generation":
            if degraded_action == "upgrade_to_hold":
                return "degraded_input_policy"
            return "base_decision"
        if linked_risks:
            return "risk_component"
        if str(confidence_result.get("level") or "") == "low":
            return "confidence_calibration"
        if str(temporal_health.get("classification") or "") in {"volatile", "insufficient_evidence"}:
            return "temporal_health"
        return "base_decision"

    def _reason_code(self, *, constraint_key: str, source: str, final_decision: str) -> str:
        if constraint_key == "block_generation" and source == "degraded_input_policy":
            return "SEVERE_DEGRADED_INPUT_WITH_HIGH_RISK"
        if constraint_key == "block_generation":
            return "ACCOUNT_HEALTH_HOLD_BLOCK_GENERATION"
        if constraint_key == "degraded_input_caution":
            return "DEGRADED_INPUT_CAUTION"
        if constraint_key == "require_monitoring":
            return "REQUIRE_MONITORING_FROM_DEGRADED_OR_LOW_CONFIDENCE_INPUT"
        if constraint_key == "reduce_hook_aggressiveness":
            return "ACCOUNT_HEALTH_CAUTION_REDUCE_HOOK_AGGRESSIVENESS"
        if constraint_key == "max_daily_posts":
            return "ACCOUNT_HEALTH_CAUTION_LIMIT_DAILY_POSTS"
        return f"ACCOUNT_HEALTH_{final_decision}_CONSTRAINT"

    def _linked_risk_components(self, *, constraint_key: str, risk_summary: dict[str, Any]) -> list[str]:
        components = dict(risk_summary.get("components") or {})
        dominant = set(str(item) for item in list(risk_summary.get("dominant_components") or []))
        key_map = {
            "reduce_hook_aggressiveness": {
                "performance_drop_risk",
                "repetition_risk",
                "low_quality_streak_risk",
            },
            "max_daily_posts": {
                "publish_frequency_risk",
                "performance_drop_risk",
                "low_quality_streak_risk",
            },
            "block_generation": {
                "performance_drop_risk",
                "low_quality_streak_risk",
                "fallback_contamination_risk",
            },
            "degraded_input_caution": {"fallback_contamination_risk"},
            "require_monitoring": {"fallback_contamination_risk"},
        }
        candidates = key_map.get(constraint_key, set(components))
        linked = []
        for name in candidates:
            component = dict(components.get(name) or {})
            if not component:
                continue
            score = self._safe_float(component.get("score"))
            level = str(component.get("level") or "")
            if name in dominant or level in {"medium", "high"} or score >= 0.34:
                linked.append(name)
        return sorted(set(linked))

    def _evidence_summary(
        self,
        *,
        risk_summary: dict[str, Any],
        confidence_result: dict[str, Any],
        temporal_health: dict[str, Any],
        degraded_input_decision: dict[str, Any],
        telemetry_summary: dict[str, Any],
    ) -> dict[str, Any]:
        summary: dict[str, Any] = {}
        if risk_summary:
            summary["risk_score"] = self._safe_float(risk_summary.get("overall_risk_score"))
            summary["risk_level"] = str(risk_summary.get("overall_risk_level") or "low")
            summary["dominant_risk_components"] = list(risk_summary.get("dominant_components") or [])
        if confidence_result:
            summary["confidence"] = self._safe_float(confidence_result.get("confidence"))
            summary["confidence_level"] = str(confidence_result.get("level") or "low")
        if temporal_health:
            summary["temporal_classification"] = str(
                temporal_health.get("classification") or "insufficient_evidence"
            )
        if degraded_input_decision:
            summary["degraded_input_severity"] = str(degraded_input_decision.get("severity") or "none")
            summary["degraded_input_action"] = str(degraded_input_decision.get("action") or "no_change")
        if telemetry_summary:
            summary["source_status_distribution"] = dict(
                telemetry_summary.get("source_status_distribution") or {}
            )
        return summary

    def _downstream_interpretation(self, *, interpretation_mode: str) -> str:
        if interpretation_mode == "blocking":
            return "Downstream generation must not proceed because Account Health returned HOLD."
        if interpretation_mode == "cautionary":
            return (
                "Downstream execution may continue, but Strategy should interpret this as a conservative "
                "health constraint."
            )
        return "Downstream agents may consider this signal, but it is not a hard restriction."

    def _rationale(
        self,
        *,
        constraint_key: str,
        final_decision: str,
        interpretation_mode: str,
        source: str,
        linked_risks: list[str],
        reasons: list[str],
        evidence_summary: dict[str, Any],
    ) -> str:
        risk_level = str(evidence_summary.get("risk_level") or "unknown")
        confidence_level = str(evidence_summary.get("confidence_level") or "unknown")
        temporal = str(evidence_summary.get("temporal_classification") or "unknown")
        degraded = str(evidence_summary.get("degraded_input_severity") or "unknown")
        reason_text = ",".join(sorted(str(reason) for reason in reasons)) or "none"
        linked_text = ",".join(linked_risks) or "none"
        return (
            f"{constraint_key} is {interpretation_mode} because final_decision={final_decision}; "
            f"source={source}; reasons={reason_text}; risk_level={risk_level}; "
            f"confidence_level={confidence_level}; temporal={temporal}; degraded_severity={degraded}; "
            f"linked_risk_components={linked_text}."
        )

    def _safe_float(self, value: Any) -> float:
        try:
            return round(float(value), 4)
        except (TypeError, ValueError):
            return 0.0
