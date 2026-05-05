from __future__ import annotations

from dataclasses import dataclass

from app.creative.contracts.creative_pack import (
    ScriptPlan,
    StrategyProfile,
    VoiceDeliveryProfile,
    VoiceSegmentPlan,
)


@dataclass(frozen=True)
class VoiceInterpretation:
    style: str
    delivery_profile: VoiceDeliveryProfile
    segments: dict[str, VoiceSegmentPlan]


@dataclass(frozen=True)
class VoiceInterpreter:
    """Deterministic v1 voice director based on narrative roles."""

    def interpret(
        self,
        *,
        niche: str,
        script_plan: ScriptPlan,
        strategy_profile: StrategyProfile | None = None,
    ) -> VoiceInterpretation:
        style = self._resolve_style(niche=niche, strategy_profile=strategy_profile)
        overall_rate = self._resolve_overall_rate(niche=niche, strategy_profile=strategy_profile)
        intensity = self._resolve_overall_intensity(niche=niche)
        segments = {
            "hook": VoiceSegmentPlan(rate=round(overall_rate * 0.96, 2), emphasis="high", pause_after_ms=320),
            "setup": VoiceSegmentPlan(rate=round(overall_rate, 2), emphasis="medium", pause_after_ms=180),
            "payoff": VoiceSegmentPlan(rate=round(overall_rate * 0.93, 2), emphasis="high", pause_before_ms=420),
        }
        if not script_plan.hook.strip():
            segments["hook"] = VoiceSegmentPlan(rate=round(overall_rate, 2), emphasis="medium", pause_after_ms=180)
        if not script_plan.payoff.strip():
            segments["payoff"] = VoiceSegmentPlan(rate=round(overall_rate, 2), emphasis="medium", pause_before_ms=180)
        return VoiceInterpretation(
            style=style,
            delivery_profile=VoiceDeliveryProfile(
                overall_mode=style,
                overall_rate=round(overall_rate, 2),
                overall_intensity=intensity,
            ),
            segments=segments,
        )

    def _resolve_style(self, *, niche: str, strategy_profile: StrategyProfile | None) -> str:
        normalized_niche = (niche or "").strip().lower()
        if normalized_niche == "horror":
            return "ominous_minimal"
        if normalized_niche == "true_crime":
            return "investigative"
        if normalized_niche == "facts":
            return "neutral_archive"
        if strategy_profile is not None and strategy_profile.content_mode == "conservative":
            return "measured_dark"
        return "dark_calm"

    def _resolve_overall_rate(self, *, niche: str, strategy_profile: StrategyProfile | None) -> float:
        if strategy_profile is not None and strategy_profile.target_duration_range.startswith("8-10"):
            return 0.98
        normalized_niche = (niche or "").strip().lower()
        if normalized_niche in {"horror", "true_crime"}:
            return 0.97
        if normalized_niche == "facts":
            return 1.0
        return 0.99

    def _resolve_overall_intensity(self, *, niche: str) -> str:
        normalized_niche = (niche or "").strip().lower()
        if normalized_niche in {"horror", "true_crime"}:
            return "high"
        return "medium"
