from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.creative.agents.strategy.models import StrategyInput, StrategyResult
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import StrategyProfile, TrendProfile


@dataclass
class StrategyAgentService:
    def generate(self, data: StrategyInput) -> StrategyResult:
        try:
            return self._generate(data)
        except Exception:  # noqa: BLE001
            return StrategyResult(
                strategy_profile=self._default_strategy(),
                fallback=FallbackDecision(
                    used=True,
                    mode=FallbackMode.SAFE_DEFAULT.value,
                    reason="STRATEGY_COLD_START",
                ),
                decision_trace={"fallback_reason": "STRATEGY_COLD_START"},
            )

    def _generate(self, data: StrategyInput) -> StrategyResult:
        account_goal = (data.account_goal or "").strip().lower()
        health_status = (data.health_status or "SAFE").strip().upper()
        if health_status not in {"SAFE", "CAUTION", "HOLD"}:
            return StrategyResult(
                strategy_profile=self._default_strategy(),
                fallback=FallbackDecision(
                    used=True,
                    mode=FallbackMode.SAFE_DEFAULT.value,
                    reason="STRATEGY_COLD_START",
                ),
                decision_trace={"fallback_reason": "STRATEGY_COLD_START", "invalid_health_status": health_status},
            )

        goal = account_goal or "retention"
        profile = self._base_profile(goal=goal, health_status=health_status)
        trace: dict[str, Any] = {
            "health_status": health_status,
            "base_profile": profile.to_dict(),
            "goal_applied": goal,
            "constraint_adjustments": [],
            "metric_adjustments": [],
            "trend_adjustments": [],
            "learning_adjustments": [],
            "novelty_adjustments": [],
        }
        profile = self._apply_constraints(
            profile=profile,
            constraints=data.recommended_constraints,
            trace=trace["constraint_adjustments"],
        )
        profile = self._apply_recent_metrics(
            profile=profile,
            metrics=data.recent_metrics_summary,
            health_status=health_status,
            trace=trace["metric_adjustments"],
        )
        profile = self._apply_trend_profile(
            profile=profile,
            trend_profile=data.trend_profile,
            health_status=health_status,
            trace=trace["trend_adjustments"],
        )
        profile = self._apply_learning_policy(
            profile=profile,
            learning_policy=data.learning_policy,
            pattern_findings_summary=data.pattern_findings_summary,
            health_status=health_status,
            trace=trace["learning_adjustments"],
        )
        profile = self._apply_novelty_pressure(
            profile=profile,
            novelty_pressure_profile=data.novelty_pressure_profile,
            health_status=health_status,
            trace=trace["novelty_adjustments"],
        )
        profile = self._reapply_constraint_caps(
            profile=profile,
            constraints=data.recommended_constraints,
            trace=trace["constraint_adjustments"],
        )
        profile = self._clamp_profile(profile)
        trace["final_profile"] = profile.to_dict()
        trace["signals_seen"] = {
            "metrics_keys": sorted(str(key) for key in (data.recent_metrics_summary or {}).keys()),
            "constraint_keys": sorted(str(key) for key in (data.recommended_constraints or {}).keys()),
            "trend_present": data.trend_profile is not None,
            "learning_policy_present": data.learning_policy is not None,
            "pattern_findings_count": len(data.pattern_findings_summary or ()),
            "novelty_present": data.novelty_pressure_profile is not None,
        }

        return StrategyResult(
            strategy_profile=profile,
            fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
            decision_trace=trace,
        )

    def _default_strategy(self) -> StrategyProfile:
        return StrategyProfile(
            goal="retention",
            content_mode="standard",
            hook_aggressiveness="medium",
            target_duration_range="8-12s",
            variation_policy="low",
            novelty_hints={},
        )

    def _base_profile(self, *, goal: str, health_status: str) -> StrategyProfile:
        if health_status == "CAUTION":
            return StrategyProfile(
                goal=goal,
                content_mode="conservative",
                hook_aggressiveness="medium",
                target_duration_range="8-12s",
                variation_policy="low",
                novelty_hints={},
            )
        if health_status == "HOLD":
            return StrategyProfile(
                goal=goal,
                content_mode="paused",
                hook_aggressiveness="low",
                target_duration_range="8-12s",
                variation_policy="none",
                novelty_hints={},
            )
        return StrategyProfile(
            goal=goal,
            content_mode="standard",
            hook_aggressiveness="medium",
            target_duration_range="8-12s",
            variation_policy="low",
            novelty_hints={},
        )

    def _apply_constraints(
        self,
        *,
        profile: StrategyProfile,
        constraints: dict[str, Any],
        trace: list[dict[str, str]],
    ) -> StrategyProfile:
        if not constraints:
            return profile
        next_profile = profile
        if bool(constraints.get("reduce_hook_aggressiveness")) or bool(constraints.get("reduce_aggressiveness")):
            next_profile = self._copy_profile(
                next_profile,
                content_mode="conservative" if next_profile.content_mode != "paused" else next_profile.content_mode,
                hook_aggressiveness=self._step_level(next_profile.hook_aggressiveness, direction=-1),
            )
            trace.append({"rule": "reduce_hook_aggressiveness", "effect": "hook_downshift"})
        if bool(constraints.get("prefer_shorter_duration")) or int(constraints.get("max_daily_posts", 0) or 0) == 1:
            next_profile = self._copy_profile(next_profile, target_duration_range="8-10s")
            trace.append({"rule": "prefer_shorter_duration", "effect": "duration_8_10s"})
        if bool(constraints.get("low_variation_only")):
            next_profile = self._copy_profile(
                next_profile,
                variation_policy="low" if next_profile.variation_policy != "none" else "none",
            )
            trace.append({"rule": "low_variation_only", "effect": "variation_capped_low"})
        return next_profile

    def _apply_recent_metrics(
        self,
        *,
        profile: StrategyProfile,
        metrics: dict[str, Any],
        health_status: str,
        trace: list[dict[str, str]],
    ) -> StrategyProfile:
        if not metrics:
            return profile
        next_profile = profile
        avg_completion = self._as_float(metrics.get("avg_completion_rate"))
        avg_views = self._as_float(metrics.get("avg_views"))
        publish_count = self._as_float(metrics.get("publish_count"))
        metrics_count = self._as_float(metrics.get("metrics_count"))

        if health_status != "HOLD" and metrics_count > 0 and avg_completion > 0 and avg_completion < 0.38:
            next_profile = self._copy_profile(
                next_profile,
                hook_aggressiveness=self._step_level(next_profile.hook_aggressiveness, direction=1),
            )
            trace.append({"rule": "weak_retention", "effect": "hook_upshift"})

        if health_status == "SAFE" and publish_count >= 5:
            next_profile = self._copy_profile(
                next_profile,
                variation_policy=self._step_variation(next_profile.variation_policy, direction=1),
            )
            trace.append({"rule": "format_saturation_hint", "effect": "variation_upshift"})

        if metrics_count >= 3 and avg_views > 0 and avg_views < 120:
            next_profile = self._copy_profile(
                next_profile,
                content_mode="conservative" if next_profile.content_mode != "paused" else next_profile.content_mode,
            )
            trace.append({"rule": "weak_quality_consistency_proxy", "effect": "content_mode_conservative"})
        return next_profile

    def _apply_trend_profile(
        self,
        *,
        profile: StrategyProfile,
        trend_profile: TrendProfile | None,
        health_status: str,
        trace: list[dict[str, str]],
    ) -> StrategyProfile:
        if trend_profile is None:
            return profile
        next_profile = profile
        pacing = (trend_profile.pacing or "").strip().lower()
        hooks = [str(item).strip().lower() for item in trend_profile.dominant_hooks]

        if health_status != "HOLD" and pacing == "fast_first_3s":
            next_profile = self._copy_profile(
                next_profile,
                hook_aggressiveness=self._step_level(next_profile.hook_aggressiveness, direction=1),
            )
            trace.append({"rule": "trend_fast_first_3s", "effect": "hook_upshift"})

        if health_status == "SAFE" and any(item in {"shock_statement", "story_opening"} for item in hooks):
            next_profile = self._copy_profile(
                next_profile,
                hook_aggressiveness=self._step_level(next_profile.hook_aggressiveness, direction=1),
            )
            trace.append({"rule": "trend_hook_family", "effect": "hook_upshift"})
        return next_profile

    def _apply_novelty_pressure(
        self,
        *,
        profile: StrategyProfile,
        novelty_pressure_profile,
        health_status: str,
        trace: list[dict[str, object]],
    ) -> StrategyProfile:
        if novelty_pressure_profile is None or health_status == "HOLD":
            return profile
        next_profile = profile
        recommended_variation = str(novelty_pressure_profile.recommended_variation_policy or "low")
        if recommended_variation == "medium" and next_profile.variation_policy == "low":
            next_profile = self._copy_profile(next_profile, variation_policy="medium")
            trace.append({
                "rule": "novelty_pressure",
                "effect": "variation_upshift",
                "pressure_level": novelty_pressure_profile.pressure_level,
            })

        novelty_hints = dict(next_profile.novelty_hints)
        if novelty_pressure_profile.blocked_payoff_structures:
            novelty_hints["blocked_payoff_structures"] = list(novelty_pressure_profile.blocked_payoff_structures)
        if novelty_pressure_profile.blocked_visual_payoff_categories:
            novelty_hints["blocked_visual_payoff_categories"] = list(novelty_pressure_profile.blocked_visual_payoff_categories)
        if novelty_pressure_profile.preferred_alternative_payoff_families:
            novelty_hints["preferred_alternative_payoff_families"] = list(novelty_pressure_profile.preferred_alternative_payoff_families)
        novelty_hints["novelty_pressure_level"] = novelty_pressure_profile.pressure_level
        novelty_hints["novelty_budget"] = novelty_pressure_profile.novelty_budget
        if novelty_hints != next_profile.novelty_hints:
            next_profile = self._copy_profile(next_profile, novelty_hints=novelty_hints)
            trace.append({
                "rule": "novelty_hints_attached",
                "blocked_payoff_structures": list(novelty_hints.get("blocked_payoff_structures", [])),
                "blocked_visual_payoff_categories": list(novelty_hints.get("blocked_visual_payoff_categories", [])),
            })
        return next_profile

    def _apply_learning_policy(
        self,
        *,
        profile: StrategyProfile,
        learning_policy,
        pattern_findings_summary,
        health_status: str,
        trace: list[dict[str, object]],
    ) -> StrategyProfile:
        if learning_policy is None or health_status == "HOLD":
            return profile
        next_profile = profile

        duration_signal = getattr(learning_policy, "duration_bias", None)
        duration_value = str(getattr(duration_signal, "value", "") or "")
        duration_confidence = self._as_float(getattr(duration_signal, "confidence", 0.0))
        if duration_value in {"8-10s", "8-12s", "10-14s"} and duration_confidence >= 0.55:
            if duration_value != next_profile.target_duration_range:
                next_profile = self._copy_profile(next_profile, target_duration_range=duration_value)
                trace.append({"rule": "learning_duration_bias", "effect": duration_value, "confidence": duration_confidence})

        risk_signal = getattr(learning_policy, "risk_adjustment_hint", None)
        risk_value = str(getattr(risk_signal, "value", "") or "")
        risk_confidence = self._as_float(getattr(risk_signal, "confidence", 0.0))
        if risk_value == "conservative_if_low_score_cluster" and risk_confidence >= 0.6:
            if next_profile.content_mode != "paused":
                next_profile = self._copy_profile(next_profile, content_mode="conservative")
                trace.append({"rule": "learning_risk_adjustment", "effect": "content_mode_conservative", "confidence": risk_confidence})

        hook_signal = getattr(learning_policy, "hook_type_bias", None)
        hook_value = str(getattr(hook_signal, "value", "") or "").strip().lower()
        hook_confidence = self._as_float(getattr(hook_signal, "confidence", 0.0))
        if hook_confidence >= 0.6 and hook_value in {"story_opening", "shock_statement"}:
            upshifted = self._step_level(next_profile.hook_aggressiveness, direction=1)
            if upshifted != next_profile.hook_aggressiveness:
                next_profile = self._copy_profile(next_profile, hook_aggressiveness=upshifted)
                trace.append({"rule": "learning_hook_bias", "effect": "hook_upshift", "hook_type": hook_value, "confidence": hook_confidence})

        variation_signal = getattr(learning_policy, "variation_tolerance_hint", None)
        variation_value = str(getattr(variation_signal, "value", "") or "").strip().lower()
        variation_confidence = self._as_float(getattr(variation_signal, "confidence", 0.0))
        if variation_value == "medium" and variation_confidence >= 0.75 and next_profile.variation_policy == "low":
            next_profile = self._copy_profile(next_profile, variation_policy="medium")
            trace.append({"rule": "learning_variation_tolerance", "effect": "variation_upshift", "confidence": variation_confidence})
        elif variation_value == "low" and variation_confidence >= 0.6 and next_profile.variation_policy == "medium":
            next_profile = self._copy_profile(next_profile, variation_policy="low")
            trace.append({"rule": "learning_variation_tolerance", "effect": "variation_downshift", "confidence": variation_confidence})

        payoff_signal = getattr(learning_policy, "payoff_specificity_bias", None)
        payoff_value = str(getattr(payoff_signal, "value", "") or "").strip().lower()
        payoff_confidence = self._as_float(getattr(payoff_signal, "confidence", 0.0))
        if payoff_value:
            novelty_hints = dict(next_profile.novelty_hints)
            novelty_hints["payoff_specificity_bias"] = payoff_value
            if pattern_findings_summary:
                novelty_hints["learning_pattern_count"] = len(pattern_findings_summary)
            if novelty_hints != next_profile.novelty_hints:
                next_profile = self._copy_profile(next_profile, novelty_hints=novelty_hints)
                trace.append({"rule": "learning_payoff_specificity_hint", "effect": payoff_value, "confidence": payoff_confidence})
        return next_profile

    def _clamp_profile(self, profile: StrategyProfile) -> StrategyProfile:
        hook = profile.hook_aggressiveness if profile.hook_aggressiveness in {"low", "medium", "high"} else "medium"
        duration = profile.target_duration_range if profile.target_duration_range in {"8-10s", "8-12s", "10-14s"} else "8-12s"
        variation = profile.variation_policy if profile.variation_policy in {"none", "low", "medium"} else "low"
        mode = profile.content_mode if profile.content_mode in {"paused", "conservative", "standard"} else "standard"
        return StrategyProfile(
            goal=profile.goal or "retention",
            content_mode=mode,
            hook_aggressiveness=hook,
            target_duration_range=duration,
            variation_policy=variation,
            novelty_hints=dict(profile.novelty_hints),
        )

    def _reapply_constraint_caps(
        self,
        *,
        profile: StrategyProfile,
        constraints: dict[str, Any],
        trace: list[dict[str, str]],
    ) -> StrategyProfile:
        if not constraints:
            return profile
        next_profile = profile
        if bool(constraints.get("reduce_hook_aggressiveness")) or bool(constraints.get("reduce_aggressiveness")):
            capped = self._step_level(next_profile.hook_aggressiveness, direction=-1)
            if capped != next_profile.hook_aggressiveness:
                next_profile = self._copy_profile(
                    next_profile,
                    content_mode="conservative" if next_profile.content_mode != "paused" else next_profile.content_mode,
                    hook_aggressiveness=capped,
                )
                trace.append({"rule": "constraint_cap_reapplied", "effect": "hook_capped"})
        if bool(constraints.get("low_variation_only")) and next_profile.variation_policy == "medium":
            next_profile = self._copy_profile(next_profile, variation_policy="low")
            trace.append({"rule": "constraint_cap_reapplied", "effect": "variation_capped_low"})
        return next_profile

    def _copy_profile(
        self,
        profile: StrategyProfile,
        *,
        goal: str | None = None,
        content_mode: str | None = None,
        hook_aggressiveness: str | None = None,
        target_duration_range: str | None = None,
        variation_policy: str | None = None,
        novelty_hints: dict[str, Any] | None = None,
    ) -> StrategyProfile:
        return StrategyProfile(
            goal=profile.goal if goal is None else goal,
            content_mode=profile.content_mode if content_mode is None else content_mode,
            hook_aggressiveness=profile.hook_aggressiveness if hook_aggressiveness is None else hook_aggressiveness,
            target_duration_range=profile.target_duration_range if target_duration_range is None else target_duration_range,
            variation_policy=profile.variation_policy if variation_policy is None else variation_policy,
            novelty_hints=dict(profile.novelty_hints if novelty_hints is None else novelty_hints),
        )

    def _step_level(self, value: str, *, direction: int) -> str:
        order = ("low", "medium", "high")
        try:
            index = order.index(value)
        except ValueError:
            index = 1
        return order[max(0, min(len(order) - 1, index + direction))]

    def _step_variation(self, value: str, *, direction: int) -> str:
        order = ("none", "low", "medium")
        try:
            index = order.index(value)
        except ValueError:
            index = 1
        return order[max(0, min(len(order) - 1, index + direction))]

    def _as_float(self, value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value or "").strip())
        except Exception:  # noqa: BLE001
            return 0.0
