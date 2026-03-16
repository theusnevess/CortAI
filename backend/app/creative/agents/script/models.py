from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import ScriptPlan


@dataclass(frozen=True)
class ScriptAgentInput:
    account_id: str
    niche: str
    topic: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScriptAgentResult:
    script_plan: ScriptPlan
    fallback: FallbackDecision

    def to_dict(self) -> dict[str, Any]:
        return {
            "script_plan": self.script_plan.to_dict(),
            "fallback": self.fallback.to_dict(),
        }
