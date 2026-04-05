from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.creative.agents.account_health.models import (
    AccountHealthDecision,
    AccountHealthInput,
    AccountHealthResult,
    AccountHealthStatus,
)
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode


@dataclass
class AccountHealthAgentService:
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
        input_summary = self._build_input_summary(data)
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

        return AccountHealthResult(
            decision=AccountHealthDecision(
                status=status.value,
                reasons=reasons,
                recommended_constraints=constraints,
            ),
            fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
            input_summary=input_summary,
            decision_trace=self._build_decision_trace(
                data=data,
                status=status.value,
                reasons=reasons,
                constraints=constraints,
                triggered_conditions=triggered_conditions,
                threshold_evaluations=threshold_evaluations,
                fallback_used=False,
                fallback_reason="",
            ),
        )

    def _fallback_result(self, *, data: AccountHealthInput | None = None, reason: str) -> AccountHealthResult:
        input_summary = self._build_input_summary(data)
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
            ),
        )

    def _build_input_summary(self, data: AccountHealthInput | None) -> dict[str, Any]:
        if data is None:
            return {}
        return {
            "account_id": data.account_id,
            "recent_publish_count": int(data.recent_publish_count),
            "recent_format_repetition_ratio": float(data.recent_format_repetition_ratio),
            "recent_views_drop_ratio": float(data.recent_views_drop_ratio),
            "recent_low_performance_streak": int(data.recent_low_performance_streak),
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
    ) -> dict[str, Any]:
        return {
            "input_summary": self._build_input_summary(data),
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
