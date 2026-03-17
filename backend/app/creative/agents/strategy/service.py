from __future__ import annotations

from dataclasses import dataclass

from app.creative.agents.strategy.models import StrategyInput, StrategyResult
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import StrategyProfile


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
            )

        if health_status == "CAUTION":
            profile = StrategyProfile(
                goal=account_goal or "retention",
                content_mode="conservative",
                hook_aggressiveness="medium",
                target_duration_range="8-12s",
                variation_policy="low",
            )
        elif health_status == "HOLD":
            profile = StrategyProfile(
                goal=account_goal or "retention",
                content_mode="paused",
                hook_aggressiveness="low",
                target_duration_range="8-12s",
                variation_policy="none",
            )
        else:
            profile = StrategyProfile(
                goal=account_goal or "retention",
                content_mode="standard",
                hook_aggressiveness="medium",
                target_duration_range="8-12s",
                variation_policy="low",
            )

        return StrategyResult(
            strategy_profile=profile,
            fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
        )

    def _default_strategy(self) -> StrategyProfile:
        return StrategyProfile(
            goal="retention",
            content_mode="standard",
            hook_aggressiveness="medium",
            target_duration_range="8-12s",
            variation_policy="low",
        )
