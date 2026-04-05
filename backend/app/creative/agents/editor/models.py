from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import AssetPlan, ScriptPlan, StrategyProfile, TrendProfile, VoicePlan
from app.creative.contracts.edit_plan import EditPlan


@dataclass(frozen=True)
class EditorAgentInput:
    account_id: str
    niche: str
    topic: str
    script_plan: ScriptPlan
    voice_plan: VoicePlan
    asset_plan: AssetPlan
    strategy_profile: StrategyProfile | None = None
    trend_profile: TrendProfile | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["script_plan"] = self.script_plan.to_dict()
        payload["voice_plan"] = self.voice_plan.to_dict()
        payload["asset_plan"] = self.asset_plan.to_dict()
        if self.strategy_profile is not None:
            payload["strategy_profile"] = self.strategy_profile.to_dict()
        if self.trend_profile is not None:
            payload["trend_profile"] = self.trend_profile.to_dict()
        return payload


@dataclass(frozen=True)
class EditorAgentResult:
    edit_plan: EditPlan
    fallback: FallbackDecision

    def to_dict(self) -> dict[str, Any]:
        return {
            "edit_plan": self.edit_plan.to_dict(),
            "fallback": self.fallback.to_dict(),
        }
