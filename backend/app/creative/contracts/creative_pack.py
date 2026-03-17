from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class StrategyProfile:
    goal: str = "retention"
    content_mode: str = "standard"
    hook_aggressiveness: str = "medium"
    target_duration_range: str = "8-12s"
    variation_policy: str = "low"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrendProfile:
    niche: str = "default"
    dominant_hooks: list[str] = field(default_factory=list)
    avg_duration: str = "8-12"
    pacing: str = "baseline"
    visual_style: str = "phase1_baseline"
    text_style: str = "caption_focus"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScriptPlan:
    hook: str
    setup: str
    payoff: str
    generation_mode: str = "contextual"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def narration_text(self) -> str:
        blocks = []
        for value in (self.hook, self.setup, self.payoff):
            text = str(value or "").strip()
            if not text:
                continue
            if text.endswith(("?", "!", ".")):
                blocks.append(text)
            else:
                blocks.append(f"{text}.")
        return "\n\n".join(blocks)


@dataclass(frozen=True)
class VoicePlan:
    provider: str
    voice_id: str
    style: str
    fallback_used: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AssetPlan:
    hook_asset: str = ""
    setup_asset: str = ""
    payoff_asset: str = ""
    visual_style: str = "phase1_baseline"
    motion_profile: str = "phase1_baseline"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LearningInsights:
    recommended_hook_type: str = "question"
    target_duration_range: str = "8-12s"
    preferred_visual_style: str = "phase1_baseline"
    preferred_voice_style: str = "phase1_baseline"
    saturation_signal: str = "baseline"
    recommendations: list[str] = field(default_factory=list)
    signal_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExperimentPlan:
    experiment_id: str = "exp_default"
    variant_id: str = "A"
    variant_type: str = "baseline"
    variant_params: dict[str, Any] = field(default_factory=dict)
    fallback_used: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExperimentAssignment:
    experiment_id: str
    variant_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CreativePack:
    creative_pack_id: str
    account_id: str
    niche: str
    topic: str
    strategy_profile: StrategyProfile
    trend_profile: TrendProfile
    script_plan: ScriptPlan
    voice_plan: VoicePlan
    asset_plan: AssetPlan
    learning_insights: LearningInsights
    experiment_plan: ExperimentPlan
    experiment_assignment: ExperimentAssignment | None
    generated_at: str
    orchestrator_version: str
    account_health_status: str = "SAFE"
    recommended_constraints: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["strategy_profile"] = self.strategy_profile.to_dict()
        payload["trend_profile"] = self.trend_profile.to_dict()
        payload["script_plan"] = self.script_plan.to_dict()
        payload["voice_plan"] = self.voice_plan.to_dict()
        payload["asset_plan"] = self.asset_plan.to_dict()
        payload["asset_selection"] = self.asset_plan.to_dict()
        payload["learning_insights"] = self.learning_insights.to_dict()
        payload["experiment_plan"] = self.experiment_plan.to_dict()
        if self.experiment_assignment is not None:
            payload["experiment_assignment"] = self.experiment_assignment.to_dict()
        return payload
