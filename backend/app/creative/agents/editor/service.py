from __future__ import annotations

from dataclasses import dataclass, field

from app.creative.agents.editor.interpreter import EditorInterpreter
from app.creative.agents.editor.models import EditorAgentInput, EditorAgentResult
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode


@dataclass
class EditorAgentService:
    interpreter: EditorInterpreter = field(default_factory=EditorInterpreter)

    def plan(self, request: EditorAgentInput) -> EditorAgentResult:
        edit_plan = self.interpreter.interpret(
            niche=request.niche,
            topic=request.topic,
            script_plan=request.script_plan,
            voice_plan=request.voice_plan,
            asset_plan=request.asset_plan,
            strategy_profile=request.strategy_profile,
            trend_profile=request.trend_profile,
        )
        return EditorAgentResult(
            edit_plan=edit_plan,
            fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
        )
