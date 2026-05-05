from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SCRIPT_CONFIDENCE_CALIBRATION_VERSION = "script_confidence_calibration_v2_6"


@dataclass(frozen=True)
class ScriptConfidenceCalibrationResult:
    confidence: float
    confidence_level: str
    confidence_components: dict[str, float]
    confidence_rationale: dict[str, Any]
    confidence_meaning: str = "trust_in_script_construction"
    calibration_version: str = SCRIPT_CONFIDENCE_CALIBRATION_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "confidence": self.confidence,
            "confidence_level": self.confidence_level,
            "confidence_components": dict(self.confidence_components),
            "confidence_rationale": dict(self.confidence_rationale),
            "confidence_meaning": self.confidence_meaning,
            "calibration_version": self.calibration_version,
        }


class ScriptConfidenceCalibrator:
    """Calibrates trust in script construction without predicting performance."""

    WEIGHTS: dict[str, float] = {
        "context_completeness": 0.15,
        "provider_reliability": 0.18,
        "structure_integrity": 0.20,
        "rubric_strength": 0.18,
        "fallback_penalty": 0.10,
        "genericity_penalty": 0.10,
        "upstream_alignment": 0.09,
    }

    def calibrate(
        self,
        *,
        context_governance: dict[str, Any],
        quality_rubric: dict[str, Any],
        hook_analysis: dict[str, Any],
        setup_analysis: dict[str, Any],
        payoff_analysis: dict[str, Any],
        diversity_analysis: dict[str, Any],
        provider_fallback_trace: dict[str, Any],
    ) -> ScriptConfidenceCalibrationResult:
        components = {
            "context_completeness": self._context_completeness(context_governance),
            "provider_reliability": self._provider_reliability(provider_fallback_trace),
            "structure_integrity": self._structure_integrity(
                hook_analysis=hook_analysis,
                setup_analysis=setup_analysis,
                payoff_analysis=payoff_analysis,
            ),
            "rubric_strength": self._rubric_strength(quality_rubric),
            "fallback_penalty": self._fallback_penalty(provider_fallback_trace),
            "genericity_penalty": self._genericity_penalty(
                hook_analysis=hook_analysis,
                payoff_analysis=payoff_analysis,
                diversity_analysis=diversity_analysis,
            ),
            "upstream_alignment": self._upstream_alignment(quality_rubric, context_governance),
        }
        confidence = 0.0
        for key, value in components.items():
            confidence += value * self.WEIGHTS[key]
        confidence = round(min(max(confidence, 0.0), 1.0), 4)
        return ScriptConfidenceCalibrationResult(
            confidence=confidence,
            confidence_level=self._level(confidence),
            confidence_components=components,
            confidence_rationale=self._rationale(
                confidence=confidence,
                confidence_level=self._level(confidence),
                components=components,
                context_governance=context_governance,
                quality_rubric=quality_rubric,
                hook_analysis=hook_analysis,
                setup_analysis=setup_analysis,
                payoff_analysis=payoff_analysis,
                diversity_analysis=diversity_analysis,
                provider_fallback_trace=provider_fallback_trace,
            ),
        )

    def _context_completeness(self, context_governance: dict[str, Any]) -> float:
        signals = dict(context_governance.get("context_signals") or {})
        if not signals:
            return 0.0
        used = len(context_governance.get("used_context") or [])
        missing = len(context_governance.get("missing_context") or [])
        degraded = len(context_governance.get("degraded_context") or [])
        total = max(used + missing, len(signals), 1)
        score = used / total
        score -= 0.08 * degraded
        if not context_governance.get("policy_respected", False):
            score -= 0.25
        return self._clamp(score)

    def _provider_reliability(self, provider_fallback_trace: dict[str, Any]) -> float:
        if provider_fallback_trace.get("provider_success") is True:
            failure_count = len(provider_fallback_trace.get("provider_failures") or [])
            return self._clamp(0.95 - min(failure_count * 0.12, 0.36))
        if provider_fallback_trace.get("contextual_fallback_used") is True:
            return 0.42
        if provider_fallback_trace.get("fallback_used") is True:
            return 0.25
        return 0.35

    def _structure_integrity(
        self,
        *,
        hook_analysis: dict[str, Any],
        setup_analysis: dict[str, Any],
        payoff_analysis: dict[str, Any],
    ) -> float:
        hook = self._level_score(str(hook_analysis.get("strength_level") or "low"))
        setup = self._level_score(str(setup_analysis.get("progression_level") or "low"))
        payoff = self._level_score(str(payoff_analysis.get("memorability_level") or "low"))
        if not hook_analysis.get("hook_present", False):
            hook = 0.0
        if not setup_analysis.get("setup_present", False):
            setup = 0.0
        if not payoff_analysis.get("payoff_present", False):
            payoff = 0.0
        return round((hook + setup + payoff) / 3.0, 4)

    def _rubric_strength(self, quality_rubric: dict[str, Any]) -> float:
        return self._clamp(self._as_float(quality_rubric.get("overall_score")))

    def _fallback_penalty(self, provider_fallback_trace: dict[str, Any]) -> float:
        if provider_fallback_trace.get("fallback_used") is True:
            if provider_fallback_trace.get("contextual_fallback_used") is True:
                return 0.45
            return 0.2
        return 1.0

    def _genericity_penalty(
        self,
        *,
        hook_analysis: dict[str, Any],
        payoff_analysis: dict[str, Any],
        diversity_analysis: dict[str, Any],
    ) -> float:
        penalty = 1.0
        if hook_analysis.get("generic_hook_detected"):
            penalty -= 0.3
        if payoff_analysis.get("generic_payoff_detected"):
            penalty -= 0.25
        if payoff_analysis.get("vague_motivational_detected"):
            penalty -= 0.25
        if diversity_analysis.get("generic_phrase_detected"):
            penalty -= 0.2
        if diversity_analysis.get("generic_cta_detected"):
            penalty -= 0.15
        if str(diversity_analysis.get("repetition_risk_level") or "") == "high":
            penalty -= 0.15
        return self._clamp(penalty)

    def _upstream_alignment(self, quality_rubric: dict[str, Any], context_governance: dict[str, Any]) -> float:
        components = dict(quality_rubric.get("components") or {})
        trend = dict(components.get("trend_alignment") or {})
        strategy = dict(components.get("strategy_alignment") or {})
        trend_score = self._as_float(trend.get("score"))
        strategy_score = self._as_float(strategy.get("score"))
        used = set(context_governance.get("used_context") or [])
        values = []
        if "trend_context" in used:
            values.append(trend_score)
        if "strategy_context" in used:
            values.append(strategy_score)
        if not values:
            return 0.5
        return self._clamp(sum(values) / len(values))

    def _rationale(
        self,
        *,
        confidence: float,
        confidence_level: str,
        components: dict[str, float],
        context_governance: dict[str, Any],
        quality_rubric: dict[str, Any],
        hook_analysis: dict[str, Any],
        setup_analysis: dict[str, Any],
        payoff_analysis: dict[str, Any],
        diversity_analysis: dict[str, Any],
        provider_fallback_trace: dict[str, Any],
    ) -> dict[str, Any]:
        penalties: list[str] = []
        if provider_fallback_trace.get("fallback_used"):
            penalties.append("SCRIPT_FALLBACK_USED")
        if context_governance.get("degraded_context"):
            penalties.append("DEGRADED_CONTEXT_PRESENT")
        if not context_governance.get("policy_respected", True):
            penalties.append("CONTEXT_POLICY_NOT_RESPECTED")
        if hook_analysis.get("generic_hook_detected"):
            penalties.append("GENERIC_HOOK_PRESENT")
        if payoff_analysis.get("generic_payoff_detected"):
            penalties.append("GENERIC_PAYOFF_PRESENT")
        if payoff_analysis.get("vague_motivational_detected"):
            penalties.append("VAGUE_MOTIVATIONAL_PAYOFF_PRESENT")
        if str(diversity_analysis.get("cliche_risk_level") or "") == "high":
            penalties.append("HIGH_CLICHE_RISK")
        if str(diversity_analysis.get("repetition_risk_level") or "") == "high":
            penalties.append("HIGH_REPETITION_RISK")
        return {
            "confidence_meaning": "trust_in_script_construction",
            "confidence": confidence,
            "confidence_level": confidence_level,
            "weights": dict(self.WEIGHTS),
            "penalties": penalties,
            "used_context_count": len(context_governance.get("used_context") or []),
            "missing_context_count": len(context_governance.get("missing_context") or []),
            "degraded_context_count": len(context_governance.get("degraded_context") or []),
            "provider_success": bool(provider_fallback_trace.get("provider_success")),
            "fallback_used": bool(provider_fallback_trace.get("fallback_used")),
            "rubric_overall_score": self._as_float(quality_rubric.get("overall_score")),
            "hook_strength_level": str(hook_analysis.get("strength_level") or ""),
            "setup_progression_level": str(setup_analysis.get("progression_level") or ""),
            "payoff_memorability_level": str(payoff_analysis.get("memorability_level") or ""),
            "cliche_risk_level": str(diversity_analysis.get("cliche_risk_level") or ""),
            "repetition_risk_level": str(diversity_analysis.get("repetition_risk_level") or ""),
            "component_summary": dict(components),
            "boundary_statement": "Script confidence measures construction trust only; it is not performance scoring or QC publication authority.",
        }

    def _level(self, confidence: float) -> str:
        if confidence < 0.35:
            return "low"
        if confidence < 0.7:
            return "medium"
        return "high"

    def _level_score(self, level: str) -> float:
        if level == "high":
            return 1.0
        if level == "medium":
            return 0.62
        return 0.2

    def _as_float(self, value: Any) -> float:
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def _clamp(self, value: float) -> float:
        return round(min(max(value, 0.0), 1.0), 4)
