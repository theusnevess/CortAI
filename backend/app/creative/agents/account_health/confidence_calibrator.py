from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AccountHealthConfidenceResult:
    confidence: float
    level: str
    components: dict[str, float]
    rationale: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AccountHealthConfidenceCalibrator:
    """Calibrates trust in the Account Health decision, not account health itself."""

    def calibrate(
        self,
        *,
        decision_status: str,
        telemetry_summary: dict[str, Any] | None,
        risk_summary: dict[str, Any] | None,
        temporal_health: dict[str, Any] | None = None,
    ) -> AccountHealthConfidenceResult:
        telemetry_summary = dict(telemetry_summary or {})
        risk_summary = dict(risk_summary or {})
        temporal_health = dict(temporal_health or {})
        distribution = self._distribution(telemetry_summary)
        freshness = dict(telemetry_summary.get("freshness_summary") or {})
        available_signals = list(telemetry_summary.get("available_signals") or [])
        missing_signals = list(telemetry_summary.get("missing_signals") or [])
        components_payload = dict(risk_summary.get("components") or {})

        telemetry_richness = self._telemetry_richness(
            available_signal_count=len(available_signals),
            missing_signal_count=len(missing_signals),
            real_source_count=distribution["REAL"],
            total_source_count=sum(distribution.values()),
        )
        freshness_score = self._freshness_score(freshness=freshness, total_source_count=sum(distribution.values()))
        source_quality = self._source_quality(distribution)
        risk_consistency = self._risk_consistency(
            decision_status=decision_status,
            overall_risk_level=str(risk_summary.get("overall_risk_level") or "low"),
            overall_risk_score=self._safe_float(risk_summary.get("overall_risk_score")),
        )
        degraded_input_penalty = self._degraded_input_penalty(
            telemetry_summary=telemetry_summary,
            distribution=distribution,
            components=components_payload,
        )
        missing_signal_penalty = self._missing_signal_penalty(
            missing_signal_count=len(missing_signals),
            distribution=distribution,
            components=components_payload,
        )

        base = (
            telemetry_richness * 0.30
            + freshness_score * 0.20
            + source_quality * 0.20
            + risk_consistency * 0.30
        )
        confidence = base
        confidence *= 1.0 - (0.35 * degraded_input_penalty)
        confidence *= 1.0 - (0.30 * missing_signal_penalty)
        confidence = self._apply_temporal_adjustment(confidence=confidence, temporal_health=temporal_health)
        confidence = self._apply_conservative_caps(
            confidence=confidence,
            risk_consistency=risk_consistency,
            missing_signal_count=len(missing_signals),
            distribution=distribution,
            risk_summary=risk_summary,
            temporal_health=temporal_health,
        )
        confidence = round(self._clamp(confidence), 4)

        dominant_reason_codes = self._dominant_reason_codes(
            distribution=distribution,
            missing_signal_count=len(missing_signals),
            degraded_input_mode=bool(telemetry_summary.get("degraded_input_mode")),
            risk_consistency=risk_consistency,
            risk_summary=risk_summary,
        )

        return AccountHealthConfidenceResult(
            confidence=confidence,
            level=self._level(confidence),
            components={
                "telemetry_richness": round(telemetry_richness, 4),
                "freshness": round(freshness_score, 4),
                "source_quality": round(source_quality, 4),
                "risk_consistency": round(risk_consistency, 4),
                "degraded_input_penalty": round(degraded_input_penalty, 4),
                "missing_signal_penalty": round(missing_signal_penalty, 4),
            },
            rationale={
                "available_signal_count": len(available_signals),
                "missing_signal_count": len(missing_signals),
                "real_source_count": distribution["REAL"],
                "stale_source_count": distribution["STALE"],
                "degraded_source_count": distribution["DEGRADED"],
                "absent_source_count": distribution["ABSENT"],
                "degraded_input_mode": bool(telemetry_summary.get("degraded_input_mode")),
                "decision_status": str(decision_status or ""),
                "overall_risk_score": self._safe_float(risk_summary.get("overall_risk_score")),
                "overall_risk_level": str(risk_summary.get("overall_risk_level") or "low"),
                "dominant_reason_codes": dominant_reason_codes,
                "temporal_health": {
                    "classification": str(temporal_health.get("classification") or "not_provided"),
                    "confidence_impact": str(temporal_health.get("confidence_impact") or "neutral"),
                    "reason_codes": list(temporal_health.get("reason_codes") or []),
                },
            },
        )

    def _telemetry_richness(
        self,
        *,
        available_signal_count: int,
        missing_signal_count: int,
        real_source_count: int,
        total_source_count: int,
    ) -> float:
        signal_total = available_signal_count + missing_signal_count
        signal_ratio = 0.0 if signal_total <= 0 else available_signal_count / signal_total
        source_ratio = 0.0 if total_source_count <= 0 else real_source_count / total_source_count
        return self._clamp((signal_ratio * 0.45) + (source_ratio * 0.55))

    def _freshness_score(self, *, freshness: dict[str, Any], total_source_count: int) -> float:
        if total_source_count <= 0:
            return 0.0
        fresh = self._safe_int(freshness.get("fresh_source_count"))
        stale = self._safe_int(freshness.get("stale_source_count"))
        unknown = self._safe_int(freshness.get("unknown_freshness_source_count"))
        absent = self._safe_int(freshness.get("absent_freshness_source_count"))
        weighted = fresh + (unknown * 0.45) + (stale * 0.20) + (absent * 0.0)
        return self._clamp(weighted / total_source_count)

    def _source_quality(self, distribution: dict[str, int]) -> float:
        total = sum(distribution.values())
        if total <= 0:
            return 0.0
        weighted = (
            distribution["REAL"]
            + (distribution["STALE"] * 0.45)
            + (distribution["DEGRADED"] * 0.25)
            + (distribution["ABSENT"] * 0.0)
        )
        return self._clamp(weighted / total)

    def _risk_consistency(self, *, decision_status: str, overall_risk_level: str, overall_risk_score: float) -> float:
        status = str(decision_status or "").upper()
        risk_level = str(overall_risk_level or "low").lower()
        if status == "SAFE":
            if risk_level == "low":
                return 1.0
            if risk_level == "medium":
                return 0.45
            return 0.10
        if status == "CAUTION":
            if risk_level == "medium":
                return 1.0
            if risk_level == "high":
                return 0.70
            return 0.60
        if status == "HOLD":
            if risk_level == "high":
                return 1.0
            if risk_level == "medium":
                return 0.65
            return 0.20 if overall_risk_score < 0.34 else 0.45
        return 0.0

    def _degraded_input_penalty(
        self,
        *,
        telemetry_summary: dict[str, Any],
        distribution: dict[str, int],
        components: dict[str, Any],
    ) -> float:
        total = max(1, sum(distribution.values()))
        degraded_ratio = (distribution["DEGRADED"] + distribution["STALE"]) / total
        component_count = max(1, len(components))
        degraded_components = sum(
            1
            for component in components.values()
            if isinstance(component, dict) and str(component.get("evidence_status") or "") in {"STALE", "DEGRADED"}
        )
        fallback_component = dict(components.get("fallback_contamination_risk") or {})
        fallback_penalty = 0.25 if str(fallback_component.get("evidence_status") or "") != "REAL" else 0.0
        if bool(telemetry_summary.get("degraded_input_mode")):
            fallback_penalty = max(fallback_penalty, 0.25)
        return self._clamp((degraded_ratio * 0.45) + ((degraded_components / component_count) * 0.35) + fallback_penalty)

    def _missing_signal_penalty(
        self,
        *,
        missing_signal_count: int,
        distribution: dict[str, int],
        components: dict[str, Any],
    ) -> float:
        source_total = max(1, sum(distribution.values()))
        absent_source_ratio = distribution["ABSENT"] / source_total
        component_count = max(1, len(components))
        absent_components = sum(
            1
            for component in components.values()
            if isinstance(component, dict) and str(component.get("evidence_status") or "") == "ABSENT"
        )
        missing_signal_factor = min(missing_signal_count / 5.0, 1.0)
        return self._clamp(
            (missing_signal_factor * 0.35)
            + (absent_source_ratio * 0.35)
            + ((absent_components / component_count) * 0.30)
        )

    def _dominant_reason_codes(
        self,
        *,
        distribution: dict[str, int],
        missing_signal_count: int,
        degraded_input_mode: bool,
        risk_consistency: float,
        risk_summary: dict[str, Any],
    ) -> list[str]:
        reasons: list[str] = []
        if missing_signal_count > 0 or distribution["ABSENT"] > 0:
            reasons.append("MISSING_TELEMETRY_PENALTY")
        if distribution["STALE"] > 0:
            reasons.append("STALE_TELEMETRY_PENALTY")
        if distribution["DEGRADED"] > 0 or degraded_input_mode:
            reasons.append("DEGRADED_INPUT_PENALTY")
        if risk_consistency < 0.70:
            reasons.append("DECISION_RISK_INCONSISTENCY")
        if risk_summary.get("missing_component_inputs"):
            reasons.append("ABSENT_RISK_COMPONENT_EVIDENCE")
        if risk_summary.get("degraded_component_inputs"):
            reasons.append("DEGRADED_RISK_COMPONENT_EVIDENCE")
        return sorted(set(reasons))

    def _apply_conservative_caps(
        self,
        *,
        confidence: float,
        risk_consistency: float,
        missing_signal_count: int,
        distribution: dict[str, int],
        risk_summary: dict[str, Any],
        temporal_health: dict[str, Any],
    ) -> float:
        capped = confidence
        if risk_consistency < 0.35:
            capped = min(capped, 0.69)
        elif risk_consistency < 0.70:
            capped = min(capped, 0.74)
        if missing_signal_count > 0 or distribution["ABSENT"] > 0 or risk_summary.get("missing_component_inputs"):
            capped = min(capped, 0.69)
        if str(temporal_health.get("classification") or "") in {"volatile", "insufficient_evidence"}:
            capped = min(capped, 0.69)
        return capped

    def _apply_temporal_adjustment(self, *, confidence: float, temporal_health: dict[str, Any]) -> float:
        classification = str(temporal_health.get("classification") or "not_provided")
        impact = str(temporal_health.get("confidence_impact") or "neutral")
        adjusted = confidence
        if classification in {"volatile", "insufficient_evidence"} or impact == "negative":
            adjusted *= 0.90
        elif classification in {"stable", "recovering"} and impact == "positive":
            adjusted = min(1.0, adjusted + 0.03)
        return adjusted

    def _distribution(self, telemetry_summary: dict[str, Any]) -> dict[str, int]:
        raw = dict(telemetry_summary.get("source_status_distribution") or {})
        return {
            "REAL": self._safe_int(raw.get("REAL")),
            "ABSENT": self._safe_int(raw.get("ABSENT")),
            "STALE": self._safe_int(raw.get("STALE")),
            "DEGRADED": self._safe_int(raw.get("DEGRADED")),
        }

    def _level(self, confidence: float) -> str:
        if confidence >= 0.70:
            return "high"
        if confidence >= 0.35:
            return "medium"
        return "low"

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

    def _clamp(self, value: float) -> float:
        return min(max(float(value), 0.0), 1.0)
