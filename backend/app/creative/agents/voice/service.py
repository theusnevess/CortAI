from __future__ import annotations

from dataclasses import dataclass, field

from app.content.pipeline.kokoro_adapter import DEFAULT_KOKORO_VOICE
from app.creative.agents.voice.interpreter import VoiceInterpreter
from app.creative.agents.voice.models import VoiceAgentInput, VoiceAgentResult
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import ScriptPlan, VoicePlan, VoiceRuntimeConstraints


@dataclass
class VoiceAgentService:
    interpreter: VoiceInterpreter = field(default_factory=VoiceInterpreter)

    def resolve(
        self,
        *,
        account_id: str,
        niche: str,
        script_plan: ScriptPlan | None = None,
        strategy_profile=None,
    ) -> VoiceAgentResult:
        return self.resolve_for_input(
            VoiceAgentInput(
                account_id=account_id,
                niche=niche,
                script_plan=script_plan,
                strategy_profile=strategy_profile,
            )
        )

    def resolve_for_input(self, request: VoiceAgentInput) -> VoiceAgentResult:
        interpretation = self.interpreter.interpret(
            niche=request.niche,
            script_plan=request.script_plan or self._default_script_plan(),
            strategy_profile=request.strategy_profile,
        )
        return VoiceAgentResult(
            voice_plan=VoicePlan(
                provider="kokoro",
                voice_id=DEFAULT_KOKORO_VOICE,
                style=interpretation.style,
                fallback_used=False,
                delivery_profile=interpretation.delivery_profile,
                segments=interpretation.segments,
                runtime_constraints=VoiceRuntimeConstraints(
                    allow_provider_fallback=True,
                    fallback_order=["kokoro", "piper"],
                ),
            ),
            fallback=FallbackDecision(
                used=False,
                mode=FallbackMode.NONE.value,
                reason="",
            ),
        )

    def _default_script_plan(self) -> ScriptPlan:
        return ScriptPlan(hook="", setup="", payoff="", generation_mode="voice_default")
