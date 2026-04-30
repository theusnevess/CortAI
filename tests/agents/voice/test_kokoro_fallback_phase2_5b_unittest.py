from __future__ import annotations

import os
import sys
import tempfile
import unittest
import wave
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.kokoro_adapter import KokoroAdapter
from app.content.pipeline.tts import StubTtsAdapter, TtsTransientError, TtsResponse
from app.content.pipeline.tts_router import TtsRouter
from app.creative.contracts.creative_pack import VoicePlan, VoiceRuntimeConstraints


class _FailingKokoroAdapter(KokoroAdapter):
    def available(self) -> bool:
        return True

    def generate_audio(self, **kwargs) -> TtsResponse:  # noqa: ANN003
        raise TtsTransientError("KOKORO_FORCED_FAILURE")


class _TracingPiperAdapter(StubTtsAdapter):
    def __init__(self, *, base_dir: Path) -> None:
        super().__init__(base_dir=base_dir)
        self.providers: list[str] = []

    def generate_audio_for_provider(self, *, provider: str, script_text: str, voice_profile: str | None, language: str | None, render_job_id: str, attempt_count: int, overall_rate: float | None = None, inter_segment_pause_ms: list[int] | None = None) -> TtsResponse:
        del script_text, voice_profile, language, attempt_count, overall_rate, inter_segment_pause_ms
        self.providers.append(provider)
        target = self.base_dir / "audio" / f"{render_job_id}_{provider}.wav"
        target.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(target), "wb") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(16000)
            writer.writeframes(b"\x00" * 16000)
        return TtsResponse(audio_path=str(target), duration_s=1.0, segment_durations=[0.3, 0.3, 0.4])


class KokoroFallbackPhase25BTests(unittest.TestCase):
    def test_router_falls_back_to_piper_when_kokoro_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            piper = _TracingPiperAdapter(base_dir=Path(tmp))
            router = TtsRouter(tts_adapter=piper, kokoro_adapter=_FailingKokoroAdapter(base_dir=Path(tmp)))
            voice_plan = VoicePlan(
                provider="kokoro",
                voice_id="af_heart",
                style="ominous_minimal",
                runtime_constraints=VoiceRuntimeConstraints(fallback_order=["kokoro", "piper"]),
            )

            result = router.generate_audio(
                script_text="Hook.\n\nSetup.\n\nPayoff.",
                voice_plan=voice_plan,
                language="en-us",
                render_job_id="kokoro_fallback",
                attempt_count=1,
            )

            self.assertEqual(result.trace.provider_requested, "kokoro")
            self.assertEqual(result.trace.provider_executed, "piper")
            self.assertTrue(result.trace.fallback_used)
            self.assertIn("kokoro:KOKORO_FORCED_FAILURE", result.trace.fallback_reason)
            self.assertEqual(piper.providers, ["piper"])


if __name__ == "__main__":
    unittest.main()
