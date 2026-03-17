from __future__ import annotations

from dataclasses import dataclass

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
            return self._fallback_result()

    def _evaluate(self, data: AccountHealthInput) -> AccountHealthResult:
        if data.recent_publish_count < 0:
            return self._fallback_result()

        reasons: list[str] = []
        constraints: dict[str, object] = {}
        status = AccountHealthStatus.SAFE

        if data.recent_views_drop_ratio >= 0.75 or data.recent_low_performance_streak >= 4:
            status = AccountHealthStatus.HOLD
            reasons.append("RECENT_VIEWS_DROP")
            constraints["block_generation"] = True
        elif (
            data.recent_views_drop_ratio >= 0.40
            or data.recent_format_repetition_ratio >= 0.65
            or data.recent_low_performance_streak >= 2
        ):
            status = AccountHealthStatus.CAUTION
            if data.recent_views_drop_ratio >= 0.40:
                reasons.append("RECENT_VIEWS_DROP")
            if data.recent_format_repetition_ratio >= 0.65:
                reasons.append("FORMAT_REPETITION_HIGH")
            if data.recent_low_performance_streak >= 2:
                reasons.append("LOW_PERFORMANCE_STREAK")
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
        )

    def _fallback_result(self) -> AccountHealthResult:
        return AccountHealthResult(
            decision=AccountHealthDecision(
                status=AccountHealthStatus.SAFE.value,
                reasons=["fallback_default"],
                recommended_constraints={},
            ),
            fallback=FallbackDecision(
                used=True,
                mode=FallbackMode.SAFE_DEFAULT.value,
                reason="ACCOUNT_HEALTH_COLD_START",
            ),
        )
