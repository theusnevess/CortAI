from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


_TEMPORAL_SOURCES = {
    "metric_window": "metric_window_summary",
    "qc_history": "qc_history_summary",
    "failure_history": "failure_history_summary",
    "format_repetition": "format_repetition_summary",
}

_HIGH_IS_RISK_KEYS = (
    "risk_score",
    "views_drop_ratio",
    "recent_views_drop_ratio",
    "drop_ratio",
    "hold_or_reject_rate",
    "reject_rate",
    "failure_rate",
    "failed_run_rate",
    "fallback_rate",
    "degraded_rate",
    "repetition_ratio",
    "format_repetition_ratio",
    "low_quality_streak",
    "low_performance_streak",
)

_LOW_IS_RISK_KEYS = (
    "approve_rate",
    "avg_overall_score",
    "overall_score",
    "quality_score",
)


@dataclass(frozen=True)
class AccountHealthTemporalResult:
    classification: str
    confidence_impact: str
    risk_direction: str
    window_summary: dict[str, Any]
    signals_used: list[str]
    reason_codes: list[str]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AccountHealthTemporalAnalyzer:
    """Classifies observed posture movement without forecasting."""

    meaningful_delta = 0.12
    strong_delta = 0.20

    def analyze(
        self,
        *,
        data: Any | None,
        telemetry_summary: dict[str, Any] | None,
        risk_summary: dict[str, Any] | None = None,
    ) -> AccountHealthTemporalResult:
        _ = risk_summary
        if data is None:
            return self._insufficient(reason_codes=["ACCOUNT_HEALTH_INPUT_MISSING"])

        telemetry_summary = dict(telemetry_summary or {})
        source_status = self._source_status_map(telemetry_summary)
        signal_movements: dict[str, dict[str, Any]] = {}
        blocked_sources: list[str] = []

        for source_name, attr_name in _TEMPORAL_SOURCES.items():
            payload = dict(getattr(data, attr_name, {}) or {})
            status = source_status.get(source_name, "ABSENT")
            if status != "REAL":
                if payload or status in {"STALE", "DEGRADED"}:
                    blocked_sources.append(f"{source_name}:{status}")
                continue
            movement = self._movement_for_source(source_name=source_name, payload=payload)
            if movement is not None:
                signal_movements[source_name] = movement

        if len(signal_movements) < 2:
            reason_codes = ["TEMPORAL_HISTORY_INSUFFICIENT"]
            if blocked_sources:
                reason_codes.append("TEMPORAL_EVIDENCE_NOT_REAL")
            if not signal_movements:
                reason_codes.append("NO_USABLE_TEMPORAL_WINDOWS")
            return self._result(
                classification="insufficient_evidence",
                confidence_impact="negative",
                risk_direction="unknown",
                signal_movements=signal_movements,
                reason_codes=reason_codes,
                rationale=(
                    "Temporal health could not be classified because fewer than two real sources "
                    "provided usable recent and previous windows."
                ),
            )

        directions = [item["direction"] for item in signal_movements.values()]
        has_up = "up" in directions
        has_down = "down" in directions
        has_flat = "flat" in directions
        max_abs_delta = max(abs(float(item["delta"])) for item in signal_movements.values())

        if has_up and has_down:
            return self._result(
                classification="volatile",
                confidence_impact="negative",
                risk_direction="mixed",
                signal_movements=signal_movements,
                reason_codes=["TEMPORAL_SIGNAL_CONFLICT"],
                rationale="Temporal sources moved in conflicting directions across recent and previous windows.",
            )

        if has_up and max_abs_delta >= self.strong_delta:
            return self._result(
                classification="degrading",
                confidence_impact="neutral",
                risk_direction="up",
                signal_movements=signal_movements,
                reason_codes=["RECENT_RISK_INCREASE"],
                rationale="Recent windows show meaningfully higher posture risk than previous windows.",
            )

        if has_down and max_abs_delta >= self.strong_delta:
            return self._result(
                classification="recovering",
                confidence_impact="positive",
                risk_direction="down",
                signal_movements=signal_movements,
                reason_codes=["RECENT_RISK_DECREASE"],
                rationale="Recent windows show meaningfully lower posture risk than previous windows.",
            )

        if has_up and not has_down:
            return self._result(
                classification="degrading",
                confidence_impact="neutral",
                risk_direction="up",
                signal_movements=signal_movements,
                reason_codes=["RECENT_RISK_INCREASE"],
                rationale="Recent windows show higher posture risk than previous windows.",
            )

        if has_down and not has_up:
            return self._result(
                classification="recovering",
                confidence_impact="positive",
                risk_direction="down",
                signal_movements=signal_movements,
                reason_codes=["RECENT_RISK_DECREASE"],
                rationale="Recent windows show lower posture risk than previous windows.",
            )

        if has_flat:
            return self._result(
                classification="stable",
                confidence_impact="positive",
                risk_direction="flat",
                signal_movements=signal_movements,
                reason_codes=["TEMPORAL_RISK_FLAT"],
                rationale="Recent and previous windows are aligned within the bounded temporal delta.",
            )

        return self._insufficient(reason_codes=["TEMPORAL_DIRECTION_UNKNOWN"])

    def _movement_for_source(self, *, source_name: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        windows = self._window_pair(payload)
        if windows is None:
            return None
        previous_window, recent_window = windows
        previous_risk = self._risk_value(previous_window)
        recent_risk = self._risk_value(recent_window)
        if previous_risk is None or recent_risk is None:
            return None
        delta = round(recent_risk - previous_risk, 4)
        if delta >= self.meaningful_delta:
            direction = "up"
        elif delta <= -self.meaningful_delta:
            direction = "down"
        else:
            direction = "flat"
        return {
            "source": source_name,
            "previous_risk": round(previous_risk, 4),
            "recent_risk": round(recent_risk, 4),
            "delta": delta,
            "direction": direction,
        }

    def _window_pair(self, payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]] | None:
        previous_window = payload.get("previous_window") or payload.get("previous")
        recent_window = payload.get("recent_window") or payload.get("recent")
        if isinstance(previous_window, dict) and isinstance(recent_window, dict):
            return dict(previous_window), dict(recent_window)

        windows = payload.get("windows")
        if isinstance(windows, list) and len(windows) >= 2:
            previous_candidate = windows[-2]
            recent_candidate = windows[-1]
            if isinstance(previous_candidate, dict) and isinstance(recent_candidate, dict):
                return dict(previous_candidate), dict(recent_candidate)
        return None

    def _risk_value(self, window: dict[str, Any]) -> float | None:
        for key in _HIGH_IS_RISK_KEYS:
            if key in window:
                return self._normalize_risk_value(key=key, value=window.get(key))
        for key in _LOW_IS_RISK_KEYS:
            if key in window:
                return 1.0 - self._clamp(self._safe_float(window.get(key)))
        return None

    def _normalize_risk_value(self, *, key: str, value: Any) -> float:
        raw = self._safe_float(value)
        if key in {"low_quality_streak", "low_performance_streak"}:
            return self._clamp(raw / 4.0)
        return self._clamp(raw)

    def _result(
        self,
        *,
        classification: str,
        confidence_impact: str,
        risk_direction: str,
        signal_movements: dict[str, dict[str, Any]],
        reason_codes: list[str],
        rationale: str,
    ) -> AccountHealthTemporalResult:
        recent_window = {
            name: {
                "risk": item["recent_risk"],
                "direction": item["direction"],
            }
            for name, item in sorted(signal_movements.items())
        }
        previous_window = {
            name: {
                "risk": item["previous_risk"],
                "direction": item["direction"],
            }
            for name, item in sorted(signal_movements.items())
        }
        return AccountHealthTemporalResult(
            classification=classification,
            confidence_impact=confidence_impact,
            risk_direction=risk_direction,
            window_summary={
                "recent_window": recent_window,
                "previous_window": previous_window,
                "available_windows": 2 if signal_movements else 0,
                "signal_movements": {name: dict(item) for name, item in sorted(signal_movements.items())},
            },
            signals_used=sorted(signal_movements),
            reason_codes=sorted(set(reason_codes)),
            rationale=rationale,
        )

    def _insufficient(self, *, reason_codes: list[str]) -> AccountHealthTemporalResult:
        return self._result(
            classification="insufficient_evidence",
            confidence_impact="negative",
            risk_direction="unknown",
            signal_movements={},
            reason_codes=reason_codes,
            rationale="Temporal health cannot be classified from the available evidence.",
        )

    def _source_status_map(self, telemetry_summary: dict[str, Any]) -> dict[str, str]:
        return {
            str(source.get("source_name") or ""): str(source.get("source_status") or "ABSENT").upper()
            for source in list(telemetry_summary.get("source_summaries") or [])
            if isinstance(source, dict)
        }

    def _safe_float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _clamp(self, value: float) -> float:
        return min(max(float(value), 0.0), 1.0)
