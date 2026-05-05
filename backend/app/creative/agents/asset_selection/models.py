from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import AssetPlan as AssetSelection, ScriptPlan, StrategyProfile, TrendProfile


@dataclass(frozen=True)
class AssetSelectionInput:
    niche: str
    topic: str
    strategy_profile: StrategyProfile
    trend_profile: TrendProfile
    script_plan: ScriptPlan | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "niche": self.niche,
            "topic": self.topic,
            "strategy_profile": self.strategy_profile.to_dict(),
            "trend_profile": self.trend_profile.to_dict(),
        }
        if self.script_plan is not None:
            payload["script_plan"] = self.script_plan.to_dict()
        return payload


@dataclass(frozen=True)
class AssetSelectionResult:
    asset_selection: AssetSelection
    fallback: FallbackDecision
    asset_context_governance: dict[str, Any] = field(default_factory=dict)
    asset_source_governance: dict[str, Any] = field(default_factory=dict)
    segment_visual_intent: dict[str, Any] = field(default_factory=dict)
    visual_alignment: dict[str, Any] = field(default_factory=dict)
    visual_truthfulness: dict[str, Any] = field(default_factory=dict)
    asset_fallback_honesty: dict[str, Any] = field(default_factory=dict)
    asset_diversity: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    confidence_level: str = "low"
    confidence_components: dict[str, float] = field(default_factory=dict)
    confidence_rationale: dict[str, Any] = field(default_factory=dict)
    asset_trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_selection": self.asset_selection.to_dict(),
            "fallback": self.fallback.to_dict(),
            "asset_context_governance": dict(self.asset_context_governance),
            "asset_source_governance": dict(self.asset_source_governance),
            "segment_visual_intent": dict(self.segment_visual_intent),
            "visual_alignment": dict(self.visual_alignment),
            "visual_truthfulness": dict(self.visual_truthfulness),
            "asset_fallback_honesty": dict(self.asset_fallback_honesty),
            "asset_diversity": dict(self.asset_diversity),
            "confidence": self.confidence,
            "confidence_level": self.confidence_level,
            "confidence_components": dict(self.confidence_components),
            "confidence_rationale": dict(self.confidence_rationale),
            "asset_trace": dict(self.asset_trace),
        }
