from __future__ import annotations

import sys
import tempfile
import unittest
import wave
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.tts import StubTtsAdapter, TtsResponse, TtsTransientError
from app.content.pipeline.tts_router import TtsRouter
from app.creative.contracts.creative_pack import (
    VoiceDeliveryProfile,
    VoicePlan,
    VoiceRuntimeConstraints,
    VoiceSegmentPlan,
)


class _FakeRoutedAdapter(StubTtsAdapter):
    def __init__(self, *, base_dir: Path, fail_first_provider: str | None = None) -> None:
        super().__init__(base_dir=base_dir)
        self.fail_first_provider = fail_first_provider
        self.calls: list[str] = []

    def supports_provider(self, provider: str) -> bool:
        return provider in {"piper", "openai"}

    def generate_audio_for_provider(self, *, provider: str, script_text: str, voice_profile: str | None, language: str | None, render_job_id: str, attempt_count: int, overall_rate: float | None = None, inter_segment_pause_ms: list[int] | None = None) -> TtsResponse:
        del script_text, voice_profile, language, attempt_count, overall_rate, inter_segment_pause_ms
        self.calls.append(provider)
        if provider == self.fail_first_provider:
            raise TtsTransientError(f"FORCED_{provider.upper()}_FAILURE")
        target = self.base_dir / "audio" / f"{render_job_id}_{provider}.wav"
        target.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(target), "wb") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(16000)
            writer.writeframes(b"\x00" * 16000)
        return TtsResponse(audio_path=str(target), duration_s=1.0, segment_durations=[0.3, 0.3, 0.4])


class TtsRouterPhase25Tests(unittest.TestCase):
    def test_respects_requested_provider_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            adapter = _FakeRoutedAdapter(base_dir=Path(tmp))
            router = TtsRouter(tts_adapter=adapter)
            voice_plan = VoicePlan(
                provider="openai",
                voice_id="alloy",
                style="investigative",
                delivery_profile=VoiceDeliveryProfile(overall_rate=0.98),
                segments={
                    "hook": VoiceSegmentPlan(pause_after_ms=320),
                    "setup": VoiceSegmentPlan(pause_after_ms=180),
                    "payoff": VoiceSegmentPlan(pause_before_ms=420),
                },
                runtime_constraints=VoiceRuntimeConstraints(fallback_order=["openai", "piper"]),
            )

            result = router.generate_audio(
                script_text="Hook.\n\nSetup.\n\nPayoff.",
                voice_plan=voice_plan,
                language="en",
                render_job_id="job_1",
                attempt_count=1,
            )

            self.assertEqual(result.trace.provider_requested, "openai")
            self.assertEqual(result.trace.provider_executed, "openai")
            self.assertFalse(result.trace.fallback_used)
            self.assertEqual(adapter.calls, ["openai"])

    def test_fallback_is_explicit_when_requested_provider_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            adapter = _FakeRoutedAdapter(base_dir=Path(tmp), fail_first_provider="openai")
            router = TtsRouter(tts_adapter=adapter)
            voice_plan = VoicePlan(
                provider="openai",
                voice_id="alloy",
                style="investigative",
                runtime_constraints=VoiceRuntimeConstraints(fallback_order=["openai", "piper"]),
            )

            result = router.generate_audio(
                script_text="Hook.\n\nSetup.\n\nPayoff.",
                voice_plan=voice_plan,
                language="en",
                render_job_id="job_2",
                attempt_count=1,
            )

            self.assertEqual(result.trace.provider_executed, "piper")
            self.assertTrue(result.trace.fallback_used)
            self.assertIn("openai:FORCED_OPENAI_FAILURE", result.trace.fallback_reason)
            self.assertEqual(adapter.calls, ["openai", "piper"])


if __name__ == "__main__":
    unittest.main()
