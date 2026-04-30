from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


RISK_COMPONENT_WEIGHTS = {
    "publish_frequency_risk": 0.20,
    "performance_drop_risk": 0.25,
    "repetition_risk": 0.20,
    "low_quality_streak_risk": 0.25,
    "fallback_contamination_risk": 0.10,
}


@dataclass(frozen=True)
class RiskComponent:
    name: str
    score: float
    level: str
    reason_code: str
    input_value: Any
    thresholds: dict[str, Any]
    evidence_status: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RiskComponentSummary:
    overall_risk_score: float
    overall_risk_level: str
    components: dict[str, dict[str, Any]]
    dominant_components: list[str]
    missing_component_inputs: list[str]
    degraded_component_inputs: list[str]
    weights: dict[str, float] = field(default_factory=lambda: dict(RISK_COMPONENT_WEIGHTS))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AccountHealthRiskComponentScorer:
    """Deterministic risk explanation layer for Account Health posture."""

    def score(self, data: Any | None, telemetry_summary: dict[str, Any] | None) -> RiskComponentSummary:
        telemetry_summary = dict(telemetry_summary or {})
        components = {
            "publish_frequency_risk": self._publish_frequency_risk(data, telemetry_summary),
            "performance_drop_risk": self._performance_drop_risk(data, telemetry_summary),
            "repetition_risk": self._repetition_risk(data, telemetry_summary),
            "low_quality_streak_risk": self._low_quality_streak_risk(data, telemetry_summary),
            "fallback_contamination_risk": self._fallback_contamination_risk(telemetry_summary),
        }
        component_payloads = {name: component.to_dict() for name, component in components.items()}
        overall = self._weighted_score(components)
        return RiskComponentSummary(
            overall_risk_score=overall,
            overall_risk_level=self._level(overall),
            components=component_payloads,
            dominant_components=self._dominant_components(components),
            missing_component_inputs=sorted(
                name for name, component in components.items() if component.evidence_status == "ABSENT"
            ),
            degraded_component_inputs=sorted(
                name for name, component in components.items() if component.evidence_status in {"STALE", "DEGRADED"}
            ),
        )

    def _publish_frequency_risk(self, data: Any | None, telemetry_summary: dict[str, Any]) -> RiskComponent:
        value = max(0, self._safe_int(getattr(data, "recent_publish_count", None)))
        thresholds = {"low_max": 3, "medium_min": 4, "high_min": 8}
        evidence_status = self._evidence_status(telemetry_summary, ("publish_history",))
        if value >= thresholds["high_min"]:
            base_score = 0.85
            reason_code = "PUBLISH_FREQUENCY_EXCESSIVE"
        elif value >= thresholds["medium_min"]:
            base_score = 0.50
            reason_code = "PUBLISH_FREQUENCY_ELEVATED"
        else:
            base_score = 0.10
            reason_code = "PUBLISH_FREQUENCY_LOW"
        score = self._apply_evidence_floor(base_score, evidence_status)
        return self._component(
            name="publish_frequency_risk",
            score=score,
            reason_code=reason_code if evidence_status == "REAL" else f"{reason_code}_{evidence_status}",
            input_value=value,
            thresholds=thresholds,
            evidence_status=evidence_status,
            rationale=self._rationale(
                metric="recent_publish_count",
                value=value,
                reason_code=reason_code,
                evidence_status=evidence_status,
            ),
        )

    def _performance_drop_risk(self, data: Any | None, telemetry_summary: dict[str, Any]) -> RiskComponent:
        value = self._clamp(self._safe_float(getattr(data, "recent_views_drop_ratio", None)))
        thresholds = {"low_below": 0.40, "medium_min": 0.40, "high_min": 0.75}
        evidence_status = self._evidence_status(telemetry_summary, ("metric_window",))
        if value >= thresholds["high_min"]:
            base_score = self._linear(value, start=0.75, end=1.0, start_score=0.67, end_score=1.0)
            reason_code = "PERFORMANCE_DROP_SEVERE"
        elif value >= thresholds["medium_min"]:
            base_score = self._linear(value, start=0.40, end=0.75, start_score=0.34, end_score=0.66)
            reason_code = "PERFORMANCE_DROP_MODERATE"
        else:
            base_score = self._linear(value, start=0.0, end=0.40, start_score=0.0, end_score=0.33)
            reason_code = "PERFORMANCE_DROP_LOW"
        score = self._apply_evidence_floor(base_score, evidence_status)
        return self._component(
            name="performance_drop_risk",
            score=score,
            reason_code=reason_code if evidence_status == "REAL" else f"{reason_code}_{evidence_status}",
            input_value=value,
            thresholds=thresholds,
            evidence_status=evidence_status,
            rationale=self._rationale(
                metric="recent_views_drop_ratio",
                value=value,
                reason_code=reason_code,
                evidence_status=evidence_status,
            ),
        )

    def _repetition_risk(self, data: Any | None, telemetry_summary: dict[str, Any]) -> RiskComponent:
        value = self._clamp(self._safe_float(getattr(data, "recent_format_repetition_ratio", None)))
        thresholds = {"low_below": 0.50, "medium_min": 0.50, "high_min": 0.80}
        evidence_status = self._evidence_status(telemetry_summary, ("format_repetition",))
        if value >= thresholds["high_min"]:
            base_score = self._linear(value, start=0.80, end=1.0, start_score=0.67, end_score=1.0)
            reason_code = "FORMAT_REPETITION_EXCESSIVE"
        elif value >= thresholds["medium_min"]:
            base_score = self._linear(value, start=0.50, end=0.80, start_score=0.34, end_score=0.66)
            reason_code = "FORMAT_REPETITION_MODERATE"
        else:
            base_score = self._linear(value, start=0.0, end=0.50, start_score=0.0, end_score=0.33)
            reason_code = "FORMAT_REPETITION_LOW"
        score = self._apply_evidence_floor(base_score, evidence_status)
        return self._component(
            name="repetition_risk",
            score=score,
            reason_code=reason_code if evidence_status == "REAL" else f"{reason_code}_{evidence_status}",
            input_value=value,
            thresholds=thresholds,
            evidence_status=evidence_status,
            rationale=self._rationale(
                metric="recent_format_repetition_ratio",
                value=value,
                reason_code=reason_code,
                evidence_status=evidence_status,
            ),
        )

    def _low_quality_streak_risk(self, data: Any | None, telemetry_summary: dict[str, Any]) -> RiskComponent:
        value = max(0, self._safe_int(getattr(data, "recent_low_performance_streak", None)))
        thresholds = {"low_max": 1, "medium_min": 2, "high_min": 4}
        evidence_status = self._evidence_status(telemetry_summary, ("qc_history",))
        if value >= thresholds["high_min"]:
            base_score = 0.85
            reason_code = "LOW_QUALITY_STREAK_SEVERE"
        elif value >= thresholds["medium_min"]:
            base_score = 0.50
            reason_code = "LOW_QUALITY_STREAK_MODERATE"
        else:
            base_score = 0.10 if value == 0 else 0.25
            reason_code = "LOW_QUALITY_STREAK_LOW"
        score = self._apply_evidence_floor(base_score, evidence_status)
        return self._component(
            name="low_quality_streak_risk",
            score=score,
            reason_code=reason_code if evidence_status == "REAL" else f"{reason_code}_{evidence_status}",
            input_value=value,
            thresholds=thresholds,
            evidence_status=evidence_status,
            rationale=self._rationale(
                metric="recent_low_performance_streak",
                value=value,
                reason_code=reason_code,
                evidence_status=evidence_status,
            ),
        )

    def _fallback_contamination_risk(self, telemetry_summary: dict[str, Any]) -> RiskComponent:
        distribution = dict(telemetry_summary.get("source_status_distribution") or {})
        evidence_status = self._evidence_status(telemetry_summary, ("failure_history",))
        degraded_input_mode = bool(telemetry_summary.get("degraded_input_mode"))
        degraded_count = self._safe_int(distribution.get("DEGRADED")) + self._safe_int(distribution.get("STALE"))
        real_count = self._safe_int(distribution.get("REAL"))
        absent_count = self._safe_int(distribution.get("ABSENT"))
        input_value = {
            "degraded_input_mode": degraded_input_mode,
            "source_status_distribution": {
                "REAL": real_count,
                "ABSENT": absent_count,
                "STALE": self._safe_int(distribution.get("STALE")),
                "DEGRADED": self._safe_int(distribution.get("DEGRADED")),
            },
        }
        thresholds = {
            "medium_when_degraded_input": True,
            "high_when_degraded_sources_dominate": True,
            "absent_failure_history_floor": 0.34,
        }
        if degraded_count > 0 and degraded_count >= max(1, real_count):
            base_score = 0.85
            reason_code = "FALLBACK_OR_DEGRADED_TELEMETRY_DOMINANT"
        elif degraded_input_mode:
            base_score = 0.50
            reason_code = "FALLBACK_OR_DEGRADED_TELEMETRY_PRESENT"
        else:
            base_score = 0.10
            reason_code = "FALLBACK_CONTAMINATION_LOW"
        score = self._apply_evidence_floor(base_score, evidence_status)
        if evidence_status == "ABSENT":
            reason_code = "FALLBACK_HISTORY_ABSENT"
        return self._component(
            name="fallback_contamination_risk",
            score=score,
            reason_code=reason_code if evidence_status == "REAL" else f"{reason_code}_{evidence_status}",
            input_value=input_value,
            thresholds=thresholds,
            evidence_status=evidence_status,
            rationale=(
                f"{reason_code}: failure/fallback telemetry evidence is {evidence_status}; "
                f"degraded_input_mode={degraded_input_mode}; degraded_or_stale_sources={degraded_count}."
            ),
        )

    def _component(
        self,
        *,
        name: str,
        score: float,
        reason_code: str,
        input_value: Any,
        thresholds: dict[str, Any],
        evidence_status: str,
        rationale: str,
    ) -> RiskComponent:
        bounded_score = round(self._clamp(score), 4)
        return RiskComponent(
            name=name,
            score=bounded_score,
            level=self._level(bounded_score),
            reason_code=reason_code,
            input_value=input_value,
            thresholds=thresholds,
            evidence_status=evidence_status,
            rationale=rationale,
        )

    def _evidence_status(self, telemetry_summary: dict[str, Any], source_names: tuple[str, ...]) -> str:
        sources = {
            str(source.get("source_name") or ""): str(source.get("source_status") or "ABSENT").upper()
            for source in list(telemetry_summary.get("source_summaries") or [])
            if isinstance(source, dict)
        }
        statuses = [sources[name] for name in source_names if name in sources]
        if not statuses:
            return "ABSENT"
        if "DEGRADED" in statuses:
            return "DEGRADED"
        if "STALE" in statuses:
            return "STALE"
        if "REAL" in statuses:
            return "REAL"
        return "ABSENT"

    def _apply_evidence_floor(self, base_score: float, evidence_status: str) -> float:
        if evidence_status == "ABSENT":
            return max(base_score, 0.34)
        if evidence_status == "STALE":
            return max(base_score, 0.40)
        if evidence_status == "DEGRADED":
            return max(base_score, 0.50)
        return base_score

    def _weighted_score(self, components: dict[str, RiskComponent]) -> float:
        total = 0.0
        total_weight = 0.0
        for name, component in components.items():
            weight = RISK_COMPONENT_WEIGHTS[name]
            total += component.score * weight
            total_weight += weight
        if total_weight <= 0:
            return 0.0
        return round(self._clamp(total / total_weight), 4)

    def _dominant_components(self, components: dict[str, RiskComponent]) -> list[str]:
        if not components:
            return []
        high = sorted(name for name, component in components.items() if component.level == "high")
        if high:
            return high
        max_score = max(component.score for component in components.values())
        if max_score < 0.34:
            return []
        return sorted(name for name, component in components.items() if component.score == max_score)

    def _level(self, score: float) -> str:
        if score >= 0.67:
            return "high"
        if score >= 0.34:
            return "medium"
        return "low"

    def _rationale(self, *, metric: str, value: Any, reason_code: str, evidence_status: str) -> str:
        evidence_clause = {
            "REAL": "real telemetry supports this component.",
            "ABSENT": "component-specific telemetry is absent, so risk is not allowed to collapse to healthy.",
            "STALE": "component-specific telemetry is stale, so risk is floored conservatively.",
            "DEGRADED": "component-specific telemetry is degraded, so risk is floored conservatively.",
        }.get(evidence_status, "component-specific telemetry is not fully reliable.")
        return f"{reason_code}: {metric}={value}. {evidence_clause}"

    def _linear(self, value: float, *, start: float, end: float, start_score: float, end_score: float) -> float:
        if end <= start:
            return start_score
        bounded_value = min(max(value, start), end)
        ratio = (bounded_value - start) / (end - start)
        return start_score + ratio * (end_score - start_score)

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
