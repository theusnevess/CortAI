from __future__ import annotations

import os
from dataclasses import dataclass, field

from app.content.pipeline.tts import DEFAULT_PIPER_MODEL
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

        premium_voice = os.getenv("CORTAI_PREMIUM_TTS_VOICE") or os.getenv("ELEVENLABS_VOICE_ID")
        premium_provider = os.getenv("CORTAI_PREMIUM_TTS_PROVIDER") or ("elevenlabs" if premium_voice else "")
        if premium_provider and premium_voice:
            return VoiceAgentResult(
                voice_plan=VoicePlan(
                    provider=premium_provider,
                    voice_id=premium_voice,
                    style=os.getenv("CORTAI_PREMIUM_TTS_STYLE", interpretation.style),
                    fallback_used=False,
                    delivery_profile=interpretation.delivery_profile,
                    segments=interpretation.segments,
                    runtime_constraints=VoiceRuntimeConstraints(
                        allow_provider_fallback=True,
                        fallback_order=[premium_provider, "piper"],
                    ),
                ),
                fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
            )

        piper_model = os.getenv("CORTAI_PIPER_MODEL", DEFAULT_PIPER_MODEL)
        return VoiceAgentResult(
            voice_plan=VoicePlan(
                provider="piper",
                voice_id=piper_model,
                style=interpretation.style,
                fallback_used=True,
                delivery_profile=interpretation.delivery_profile,
                segments=interpretation.segments,
                runtime_constraints=VoiceRuntimeConstraints(
                    allow_provider_fallback=True,
                    fallback_order=["piper"],
                ),
            ),
            fallback=FallbackDecision(
                used=True,
                mode=FallbackMode.LOCAL_DEFAULT.value,
                reason="voice_fallback_to_piper",
            ),
        )

    def _default_script_plan(self) -> ScriptPlan:
        return ScriptPlan(hook="", setup="", payoff="", generation_mode="voice_default")
