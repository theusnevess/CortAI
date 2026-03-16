from __future__ import annotations

import os
from dataclasses import dataclass

from app.content.pipeline.tts import DEFAULT_PIPER_MODEL
from app.creative.agents.voice.models import VoiceAgentResult
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import VoicePlan


@dataclass
class VoiceAgentService:
    def resolve(self, *, account_id: str, niche: str) -> VoiceAgentResult:
        del account_id, niche
        premium_voice = os.getenv("CORTAI_PREMIUM_TTS_VOICE") or os.getenv("ELEVENLABS_VOICE_ID")
        premium_provider = os.getenv("CORTAI_PREMIUM_TTS_PROVIDER") or ("elevenlabs" if premium_voice else "")
        if premium_provider and premium_voice:
            return VoiceAgentResult(
                voice_plan=VoicePlan(
                    provider=premium_provider,
                    voice_id=premium_voice,
                    style=os.getenv("CORTAI_PREMIUM_TTS_STYLE", "calm_dark"),
                    fallback_used=False,
                ),
                fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
            )

        piper_model = os.getenv("CORTAI_PIPER_MODEL", DEFAULT_PIPER_MODEL)
        return VoiceAgentResult(
            voice_plan=VoicePlan(
                provider="piper",
                voice_id=piper_model,
                style="phase1_baseline",
                fallback_used=True,
            ),
            fallback=FallbackDecision(
                used=True,
                mode=FallbackMode.LOCAL_DEFAULT.value,
                reason="voice_fallback_to_piper",
            ),
        )
