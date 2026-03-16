from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import VoicePlan


@dataclass(frozen=True)
class VoiceAgentInput:
    account_id: str
    niche: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VoiceAgentResult:
    voice_plan: VoicePlan
    fallback: FallbackDecision

    def to_dict(self) -> dict[str, Any]:
        return {
            "voice_plan": self.voice_plan.to_dict(),
            "fallback": self.fallback.to_dict(),
        }
