from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.agents.script.models import ScriptAgentInput


SCRIPT_CONTEXT_POLICY_VERSION = "script_context_governance_v2_6"


@dataclass(frozen=True)
class ScriptContextSignal:
    context_key: str
    available: bool
    used: bool
    ignored: bool
    missing: bool
    degraded: bool
    priority_rank: int
    role: str
    authority_level: str
    reason_code: str
    evidence_summary: dict[str, Any] = field(default_factory=dict)
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScriptContextGovernanceResult:
    policy_version: str
    policy_respected: bool
    available_context: list[str]
    used_context: list[str]
    ignored_context: list[str]
    missing_context: list[str]
    degraded_context: list[str]
    context_priority: list[dict[str, Any]]
    context_signals: dict[str, dict[str, Any]]
    boundary_statement: str
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_version": self.policy_version,
            "policy_respected": self.policy_respected,
            "available_context": list(self.available_context),
            "used_context": list(self.used_context),
            "ignored_context": list(self.ignored_context),
            "missing_context": list(self.missing_context),
            "degraded_context": list(self.degraded_context),
            "context_priority": [dict(item) for item in self.context_priority],
            "context_signals": {key: dict(value) for key, value in self.context_signals.items()},
            "boundary_statement": self.boundary_statement,
            "rationale": list(self.rationale),
        }


class ScriptContextGovernanceEvaluator:
    """Audits Script context intake without changing generation behavior."""

    CONTEXT_PRIORITY: tuple[tuple[str, str, str], ...] = (
        ("account_health_context", "safety_constraint", "safety"),
        ("strategy_context", "creative_control", "control"),
        ("experiment_context", "assigned_variation", "bounded_experiment"),
        ("trend_context", "advisory_trend_context", "advisory"),
        ("learning_context", "bounded_historical_signal", "advisory"),
        ("topic_context", "base_generation_context", "base"),
        ("niche_context", "base_generation_context", "base"),
    )
    REQUIRED_CONTEXTS: frozenset[str] = frozenset(
        {"account_health_context", "topic_context", "niche_context"}
    )

    def evaluate(self, data: ScriptAgentInput) -> ScriptContextGovernanceResult:
        signals: dict[str, ScriptContextSignal] = {}
        rationale: list[str] = []

        for rank, (context_key, role, authority_level) in enumerate(self.CONTEXT_PRIORITY, start=1):
            signal = self._build_signal(
                data=data,
                context_key=context_key,
                role=role,
                authority_level=authority_level,
                priority_rank=rank,
            )
            signals[context_key] = signal

        available_context = [key for key, signal in signals.items() if signal.available]
        used_context = [key for key, signal in signals.items() if signal.used]
        ignored_context = [key for key, signal in signals.items() if signal.ignored]
        missing_context = [key for key, signal in signals.items() if signal.missing]
        degraded_context = [key for key, signal in signals.items() if signal.degraded]

        missing_required = [key for key in missing_context if key in self.REQUIRED_CONTEXTS]
        policy_respected = not missing_required
        if missing_required:
            rationale.append(
                "Required Script base context is missing: " + ", ".join(missing_required)
            )
        else:
            rationale.append("Required Script base context is present.")

        if degraded_context:
            rationale.append(
                "Degraded upstream context is visible and remains advisory unless governed elsewhere: "
                + ", ".join(degraded_context)
            )
        else:
            rationale.append("No degraded upstream context detected.")

        rationale.append("Strategy remains the creative control layer; Script only consumes context.")

        return ScriptContextGovernanceResult(
            policy_version=SCRIPT_CONTEXT_POLICY_VERSION,
            policy_respected=policy_respected,
            available_context=available_context,
            used_context=used_context,
            ignored_context=ignored_context,
            missing_context=missing_context,
            degraded_context=degraded_context,
            context_priority=self._priority_trace(),
            context_signals={key: signal.to_dict() for key, signal in signals.items()},
            boundary_statement="Script consumes upstream context to construct narrative; Strategy remains the control layer.",
            rationale=rationale,
        )

    def _priority_trace(self) -> list[dict[str, Any]]:
        return [
            {
                "rank": rank,
                "context_key": context_key,
                "role": role,
                "authority_level": authority_level,
            }
            for rank, (context_key, role, authority_level) in enumerate(self.CONTEXT_PRIORITY, start=1)
        ]

    def _build_signal(
        self,
        *,
        data: ScriptAgentInput,
        context_key: str,
        role: str,
        authority_level: str,
        priority_rank: int,
    ) -> ScriptContextSignal:
        evidence = self._evidence_for(data=data, context_key=context_key)
        available = bool(evidence.pop("_available", False))
        degraded_reason = str(evidence.pop("_degraded_reason", ""))
        missing = not available
        degraded = bool(degraded_reason)
        used = available
        ignored = False

        if missing:
            reason_code = (
                "SCRIPT_CONTEXT_MISSING_REQUIRED"
                if context_key in self.REQUIRED_CONTEXTS
                else "SCRIPT_CONTEXT_MISSING_OPTIONAL"
            )
            rationale = f"{context_key} was not available to Script."
        elif degraded:
            reason_code = "SCRIPT_CONTEXT_AVAILABLE_DEGRADED"
            rationale = f"{context_key} was available and used, but marked degraded: {degraded_reason}."
        else:
            reason_code = "SCRIPT_CONTEXT_AVAILABLE_USED"
            rationale = f"{context_key} was available and passed to script generation context."

        return ScriptContextSignal(
            context_key=context_key,
            available=available,
            used=used,
            ignored=ignored,
            missing=missing,
            degraded=degraded,
            priority_rank=priority_rank,
            role=role,
            authority_level=authority_level,
            reason_code=reason_code,
            evidence_summary=evidence,
            rationale=rationale,
        )

    def _evidence_for(self, *, data: ScriptAgentInput, context_key: str) -> dict[str, Any]:
        if context_key == "account_health_context":
            status = str(data.account_health_status or "").strip().upper()
            degraded_reason = "" if status in {"SAFE", "CAUTION", "HOLD"} else "unknown_account_health_status"
            return {
                "_available": bool(status),
                "_degraded_reason": degraded_reason,
                "status": status,
            }
        if context_key == "strategy_context":
            strategy = data.strategy_profile
            return {
                "_available": strategy is not None,
                "_degraded_reason": "",
                "goal": "" if strategy is None else strategy.goal,
                "content_mode": "" if strategy is None else strategy.content_mode,
                "hook_aggressiveness": "" if strategy is None else strategy.hook_aggressiveness,
                "target_duration_range": "" if strategy is None else strategy.target_duration_range,
            }
        if context_key == "experiment_context":
            experiment = data.experiment_plan
            fallback_used = False if experiment is None else bool(experiment.fallback_used)
            return {
                "_available": experiment is not None,
                "_degraded_reason": "experiment_fallback_used" if fallback_used else "",
                "experiment_id": "" if experiment is None else experiment.experiment_id,
                "variant_id": "" if experiment is None else experiment.variant_id,
                "variant_type": "" if experiment is None else experiment.variant_type,
                "fallback_used": fallback_used,
            }
        if context_key == "trend_context":
            trend = data.trend_profile
            confidence = self._trend_confidence(trend)
            source = "" if trend is None else str(trend.trend_source or "")
            degraded_reason = ""
            if trend is not None:
                source_lower = source.lower()
                if source_lower in {"safe_default", "fallback", "fallback_safe_default"}:
                    degraded_reason = "trend_fallback_source"
                elif trend.sample_size <= 0:
                    degraded_reason = "trend_zero_sample_size"
                elif 0.0 < confidence < 0.35:
                    degraded_reason = "trend_low_confidence"
            return {
                "_available": trend is not None,
                "_degraded_reason": degraded_reason,
                "trend_source": source,
                "dominant_hooks_count": 0 if trend is None else len(trend.dominant_hooks),
                "sample_size": 0 if trend is None else trend.sample_size,
                "overall_confidence": confidence,
            }
        if context_key == "learning_context":
            learning = data.learning_insights
            confidence = 0.0 if learning is None else float(learning.confidence or 0.0)
            degraded_reason = ""
            if learning is not None:
                contamination = dict(learning.contamination_summary or {})
                fallback_visible = bool((learning.learning_trace or {}).get("fallback_used"))
                if fallback_visible:
                    degraded_reason = "learning_fallback_visible"
                elif contamination and self._as_float(contamination.get("contaminated_evidence_rate")) > 0.0:
                    degraded_reason = "learning_contaminated_evidence_visible"
                elif 0.0 < confidence < 0.35:
                    degraded_reason = "learning_low_confidence"
            return {
                "_available": learning is not None,
                "_degraded_reason": degraded_reason,
                "recommended_hook_type": "" if learning is None else learning.recommended_hook_type,
                "recommendations_count": 0 if learning is None else len(learning.recommendations),
                "confidence": confidence,
            }
        if context_key == "topic_context":
            topic = str(data.topic or "").strip()
            return {
                "_available": bool(topic),
                "_degraded_reason": "",
                "present": bool(topic),
            }
        if context_key == "niche_context":
            niche = str(data.niche or "").strip()
            return {
                "_available": bool(niche),
                "_degraded_reason": "",
                "present": bool(niche),
            }
        return {"_available": False, "_degraded_reason": "unknown_context_key"}

    def _trend_confidence(self, trend: Any) -> float:
        if trend is None:
            return 0.0
        scores = getattr(trend, "confidence_scores", {}) or {}
        return self._as_float(scores.get("overall"))

    def _as_float(self, value: Any) -> float:
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0
