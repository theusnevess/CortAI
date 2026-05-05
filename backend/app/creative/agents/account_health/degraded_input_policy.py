from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AccountHealthDegradedInputDecision:
    degraded_input_detected: bool
    severity: str
    action: str
    reason_codes: list[str]
    rationale: str
    affected_sources: list[str]
    original_decision: str
    final_decision: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AccountHealthDegradedInputPolicy:
    """Applies bounded fail-safer behavior for degraded Account Health inputs."""

    def evaluate(
        self,
        *,
        original_decision: str,
        telemetry_summary: dict[str, Any] | None,
        risk_summary: dict[str, Any] | None,
        confidence_result: dict[str, Any] | None,
        temporal_health: dict[str, Any] | None,
        fallback_used: bool = False,
    ) -> AccountHealthDegradedInputDecision:
        original = str(original_decision or "SAFE").upper()
        telemetry_summary = dict(telemetry_summary or {})
        risk_summary = dict(risk_summary or {})
        confidence_result = dict(confidence_result or {})
        temporal_health = dict(temporal_health or {})

        affected_sources = self._affected_sources(telemetry_summary)
        distribution = self._distribution(telemetry_summary)
        confidence = self._safe_float(confidence_result.get("confidence"))
        confidence_level = str(confidence_result.get("level") or "low")
        overall_risk_score = self._safe_float(risk_summary.get("overall_risk_score"))
        overall_risk_level = str(risk_summary.get("overall_risk_level") or "low").lower()
        fallback_component = dict((risk_summary.get("components") or {}).get("fallback_contamination_risk") or {})
        fallback_high = (
            str(fallback_component.get("level") or "").lower() == "high"
            or self._safe_float(fallback_component.get("score")) >= 0.67
        )
        temporal_classification = str(temporal_health.get("classification") or "insufficient_evidence")
        degraded_detected = bool(affected_sources) or bool(telemetry_summary.get("degraded_input_mode"))
        reason_codes = self._reason_codes(
            distribution=distribution,
            confidence_level=confidence_level,
            temporal_classification=temporal_classification,
            overall_risk_level=overall_risk_level,
            fallback_high=fallback_high,
            fallback_used=fallback_used,
        )

        severity = self._severity(
            degraded_detected=degraded_detected,
            distribution=distribution,
            confidence=confidence,
            confidence_level=confidence_level,
            overall_risk_score=overall_risk_score,
            overall_risk_level=overall_risk_level,
            temporal_classification=temporal_classification,
            fallback_high=fallback_high,
            fallback_used=fallback_used,
        )
        action, final_decision = self._action(
            original_decision=original,
            severity=severity,
            overall_risk_level=overall_risk_level,
            fallback_high=fallback_high,
            fallback_used=fallback_used,
        )

        return AccountHealthDegradedInputDecision(
            degraded_input_detected=degraded_detected,
            severity=severity,
            action=action,
            reason_codes=reason_codes,
            rationale=self._rationale(
                severity=severity,
                action=action,
                original_decision=original,
                final_decision=final_decision,
                confidence=confidence,
                overall_risk_level=overall_risk_level,
                fallback_high=fallback_high,
                temporal_classification=temporal_classification,
                fallback_used=fallback_used,
            ),
            affected_sources=affected_sources,
            original_decision=original,
            final_decision=final_decision,
        )

    def _severity(
        self,
        *,
        degraded_detected: bool,
        distribution: dict[str, int],
        confidence: float,
        confidence_level: str,
        overall_risk_score: float,
        overall_risk_level: str,
        temporal_classification: str,
        fallback_high: bool,
        fallback_used: bool,
    ) -> str:
        if fallback_used:
            return "moderate"
        if not degraded_detected and confidence_level in {"medium", "high"} and overall_risk_level in {"low", "medium"}:
            return "none"

        total_sources = max(1, sum(distribution.values()))
        non_real = distribution["ABSENT"] + distribution["STALE"] + distribution["DEGRADED"]
        stale_or_degraded = distribution["STALE"] + distribution["DEGRADED"]
        non_real_ratio = non_real / total_sources
        stale_degraded_ratio = stale_or_degraded / total_sources
        severe_temporal = temporal_classification in {"volatile", "insufficient_evidence"}
        high_risk = overall_risk_level == "high" or overall_risk_score >= 0.67

        if (
            (confidence_level == "low" or (fallback_high and confidence <= 0.50))
            and severe_temporal
            and (high_risk or fallback_high)
            and (stale_degraded_ratio >= 0.50 or distribution["DEGRADED"] >= 2 or fallback_high)
        ):
            return "severe"

        if (
            stale_or_degraded > 0
            or (non_real_ratio >= 0.60 and confidence_level in {"low", "medium"} and overall_risk_score >= 0.45)
            or (severe_temporal and confidence_level == "low" and distribution["ABSENT"] >= 4 and overall_risk_score >= 0.45)
        ):
            return "moderate"

        if degraded_detected:
            return "minor"
        return "none"

    def _action(
        self,
        *,
        original_decision: str,
        severity: str,
        overall_risk_level: str,
        fallback_high: bool,
        fallback_used: bool,
    ) -> tuple[str, str]:
        if fallback_used:
            return "no_change", original_decision
        if original_decision == "HOLD":
            return "no_change", "HOLD"

        high_risk_or_fallback = overall_risk_level == "high" or fallback_high
        if original_decision == "CAUTION":
            if severity == "severe" and high_risk_or_fallback:
                return "upgrade_to_hold", "HOLD"
            return "no_change", "CAUTION"

        if original_decision == "SAFE":
            if severity == "severe" and high_risk_or_fallback:
                return "upgrade_to_hold", "HOLD"
            if severity == "moderate":
                return "upgrade_to_caution", "CAUTION"
            return "no_change", "SAFE"

        return "no_change", original_decision

    def _affected_sources(self, telemetry_summary: dict[str, Any]) -> list[str]:
        affected: list[str] = []
        for source in list(telemetry_summary.get("source_summaries") or []):
            if not isinstance(source, dict):
                continue
            status = str(source.get("source_status") or "ABSENT").upper()
            if status != "REAL":
                affected.append(f"{source.get('source_name') or 'unknown'}:{status}")
        return sorted(affected)

    def _reason_codes(
        self,
        *,
        distribution: dict[str, int],
        confidence_level: str,
        temporal_classification: str,
        overall_risk_level: str,
        fallback_high: bool,
        fallback_used: bool,
    ) -> list[str]:
        reasons: list[str] = []
        if distribution["ABSENT"] > 0:
            reasons.append("ABSENT_TELEMETRY_PRESENT")
        if distribution["STALE"] > 0:
            reasons.append("STALE_TELEMETRY_PRESENT")
        if distribution["DEGRADED"] > 0:
            reasons.append("DEGRADED_TELEMETRY_PRESENT")
        if confidence_level == "low":
            reasons.append("LOW_CONFIDENCE_FROM_DEGRADED_INPUT")
        if temporal_classification in {"volatile", "insufficient_evidence"}:
            reasons.append(f"TEMPORAL_{temporal_classification.upper()}")
        if overall_risk_level == "high":
            reasons.append("HIGH_OVERALL_RISK")
        if fallback_high:
            reasons.append("FALLBACK_CONTAMINATION_RISK_HIGH")
        if fallback_used:
            reasons.append("FALLBACK_SAFE_DEFAULT_PRESERVED")
        return sorted(set(reasons))

    def _rationale(
        self,
        *,
        severity: str,
        action: str,
        original_decision: str,
        final_decision: str,
        confidence: float,
        overall_risk_level: str,
        fallback_high: bool,
        temporal_classification: str,
        fallback_used: bool,
    ) -> str:
        if fallback_used:
            return (
                "Fallback safe-default semantics were preserved while degraded input remained explicit in trace."
            )
        return (
            f"Degraded input severity={severity}; action={action}; decision {original_decision}->{final_decision}; "
            f"confidence={round(confidence, 4)}; risk_level={overall_risk_level}; "
            f"fallback_high={fallback_high}; temporal={temporal_classification}."
        )

    def _distribution(self, telemetry_summary: dict[str, Any]) -> dict[str, int]:
        raw = dict(telemetry_summary.get("source_status_distribution") or {})
        return {
            "REAL": self._safe_int(raw.get("REAL")),
            "ABSENT": self._safe_int(raw.get("ABSENT")),
            "STALE": self._safe_int(raw.get("STALE")),
            "DEGRADED": self._safe_int(raw.get("DEGRADED")),
        }

    def _safe_int(self, value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _safe_float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
