from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import ScriptPlan, StrategyProfile, VoicePlan


@dataclass(frozen=True)
class VoiceAgentInput:
    account_id: str
    niche: str
    script_plan: ScriptPlan | None = None
    strategy_profile: StrategyProfile | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.script_plan is not None:
            payload["script_plan"] = self.script_plan.to_dict()
        if self.strategy_profile is not None:
            payload["strategy_profile"] = self.strategy_profile.to_dict()
        return payload


@dataclass(frozen=True)
class VoiceAgentResult:
    voice_plan: VoicePlan
    fallback: FallbackDecision

    def to_dict(self) -> dict[str, Any]:
        return {
            "voice_plan": self.voice_plan.to_dict(),
            "fallback": self.fallback.to_dict(),
        }
