from __future__ import annotations

from dataclasses import dataclass, field
import os
from time import perf_counter

from app.content.pipeline.kokoro_adapter import KokoroAdapter
from app.content.pipeline.models import TtsExecutionTrace
from app.content.pipeline.tts import DEFAULT_PIPER_MODEL, StubTtsAdapter, TtsAdapter, TtsResponse, TtsTransientError
from app.creative.contracts.creative_pack import VoicePlan


@dataclass(frozen=True)
class TtsRouterResult:
    response: TtsResponse
    trace: TtsExecutionTrace


@dataclass(frozen=True)
class TtsRouter:
    tts_adapter: TtsAdapter
    kokoro_adapter: KokoroAdapter | None = field(default=None)

    def generate_audio(
        self,
        *,
        script_text: str,
        voice_plan: VoicePlan,
        language: str | None,
        render_job_id: str,
        attempt_count: int,
    ) -> TtsRouterResult:
        fallback_reasons: list[str] = []
        forced_provider = self._forced_provider_from_env()
        if forced_provider:
            requested_provider = forced_provider
            fallback_order = [forced_provider]
        else:
            fallback_order = list(voice_plan.runtime_constraints.fallback_order or [voice_plan.provider, "piper"])
            if not fallback_order:
                fallback_order = [voice_plan.provider]
            requested_provider = self._normalize_provider(voice_plan.provider)
            if requested_provider not in fallback_order:
                fallback_order.insert(0, requested_provider)
        if os.getenv("CORTAI_ALLOW_SILENT_TTS_FALLBACK", "0") == "1" and "silent" not in fallback_order:
            fallback_order.append("silent")

        for provider in fallback_order:
            started = perf_counter()
            executed_voice_id = self._voice_id_for_provider(provider=provider, voice_plan=voice_plan)
            try:
                response = self._generate_for_provider(
                    provider=provider,
                    script_text=script_text,
                    voice_plan=voice_plan,
                    executed_voice_id=executed_voice_id,
                    language=language,
                    render_job_id=render_job_id,
                    attempt_count=attempt_count,
                )
                latency_s = round(perf_counter() - started, 3)
                return TtsRouterResult(
                    response=response,
                    trace=TtsExecutionTrace(
                        provider_requested=requested_provider,
                        provider_executed=self._normalize_provider(provider),
                        voice_id_requested=voice_plan.voice_id,
                        voice_id_executed=executed_voice_id,
                        style_requested=voice_plan.style,
                        fallback_used=self._normalize_provider(provider) != requested_provider,
                        fallback_reason="; ".join(fallback_reasons),
                        latency_s=latency_s,
                        audio_duration_s=response.duration_s,
                        segment_durations=list(response.segment_durations or []),
                    ),
                )
            except TtsTransientError as exc:
                fallback_reasons.append(f"{self._normalize_provider(provider)}:{exc}")
                if not voice_plan.runtime_constraints.allow_provider_fallback:
                    raise
        raise TtsTransientError("; ".join(fallback_reasons) or "TTS_ROUTER_FAILED")

    def _generate_for_provider(
        self,
        *,
        provider: str,
        script_text: str,
        voice_plan: VoicePlan,
        executed_voice_id: str,
        language: str | None,
        render_job_id: str,
        attempt_count: int,
    ) -> TtsResponse:
        normalized_provider = self._normalize_provider(provider)
        if normalized_provider == "kokoro":
            adapter = self.kokoro_adapter or KokoroAdapter()
            if not adapter.available():
                raise TtsTransientError("KOKORO_UNAVAILABLE")
            return adapter.generate_audio(
                script_text=script_text,
                voice_profile=executed_voice_id,
                language=language,
                render_job_id=render_job_id,
                overall_rate=voice_plan.delivery_profile.overall_rate,
                inter_segment_pause_ms=self._pause_profile(voice_plan),
            )
        if isinstance(self.tts_adapter, StubTtsAdapter):
            if not self.tts_adapter.supports_provider(normalized_provider):
                raise TtsTransientError(f"TTS_PROVIDER_UNSUPPORTED:{normalized_provider}")
            return self.tts_adapter.generate_audio_for_provider(
                provider=normalized_provider,
                script_text=script_text,
                voice_profile=executed_voice_id,
                language=language,
                render_job_id=render_job_id,
                attempt_count=attempt_count,
                overall_rate=voice_plan.delivery_profile.overall_rate,
                inter_segment_pause_ms=self._pause_profile(voice_plan),
            )
        if normalized_provider != "piper":
            raise TtsTransientError(f"TTS_PROVIDER_UNSUPPORTED:{normalized_provider}")
        return self.tts_adapter.generate_audio(
            script_text=script_text,
            voice_profile=executed_voice_id,
            language=language,
            render_job_id=render_job_id,
            attempt_count=attempt_count,
        )

    def _pause_profile(self, voice_plan: VoicePlan) -> list[int]:
        hook_pause = voice_plan.segments.get("hook").pause_after_ms if "hook" in voice_plan.segments else 0
        setup_pause = voice_plan.segments.get("setup").pause_after_ms if "setup" in voice_plan.segments else 0
        payoff_pause = voice_plan.segments.get("payoff").pause_before_ms if "payoff" in voice_plan.segments else 0
        return [hook_pause, max(setup_pause, payoff_pause)]

    def _normalize_provider(self, provider: str) -> str:
        normalized = str(provider or "").strip().lower()
        if normalized in {"edge_tts", "edge-tts"}:
            return "edge"
        return normalized

    def _forced_provider_from_env(self) -> str | None:
        mode = self._normalize_provider(os.getenv("CORTAI_TTS_MODE", ""))
        if mode in {"piper", "openai", "edge", "pyttsx3", "silent"}:
            return mode
        return None

    def _voice_id_for_provider(self, *, provider: str, voice_plan: VoicePlan) -> str:
        normalized_provider = self._normalize_provider(provider)
        if normalized_provider == "kokoro":
            return voice_plan.voice_id or os.getenv("CORTAI_KOKORO_VOICE", "af_heart")
        if normalized_provider == "piper":
            requested = str(voice_plan.voice_id or "").strip().lower()
            if requested.endswith(".onnx"):
                return voice_plan.voice_id
            return os.getenv("CORTAI_PIPER_MODEL", DEFAULT_PIPER_MODEL)
        return voice_plan.voice_id
