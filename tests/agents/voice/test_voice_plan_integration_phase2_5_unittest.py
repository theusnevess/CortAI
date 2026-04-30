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

from app.content.pipeline.publish import StubPublishAdapter
from app.content.pipeline.render import StubRenderAdapter
from app.content.pipeline.service import ContentPipelineService
from app.content.pipeline.tts import StubTtsAdapter, TtsResponse
from app.content.script_gen.models import ScriptGenerationResponse, StructuredScriptPayload
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import ScriptPlan
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput


class _StructuredGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        return ScriptGenerationResponse(
            script_plan=ScriptPlan(
                hook="What happened at 3:04 AM?",
                setup="Dispatcher's frantic voice escalates.",
                payoff="Officer Johnson's final transmission.",
                generation_mode="test_structured",
            ),
            payload=StructuredScriptPayload(
                hook="What happened at 3:04 AM?",
                setup="Dispatcher's frantic voice escalates.",
                payoff="Officer Johnson's final transmission.",
                narrative_mode="recovered_recording",
            ),
            provider_used="test",
            model_used="test",
            prompt_used="prompt",
            raw_output="{}",
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )


class _TracingTtsAdapter(StubTtsAdapter):
    def __init__(self, *, base_dir: Path) -> None:
        super().__init__(base_dir=base_dir)
        self.calls: list[str] = []

    def supports_provider(self, provider: str) -> bool:
        return provider in {"piper"}

    def generate_audio_for_provider(self, *, provider: str, script_text: str, voice_profile: str | None, language: str | None, render_job_id: str, attempt_count: int, overall_rate: float | None = None, inter_segment_pause_ms: list[int] | None = None) -> TtsResponse:
        del script_text, voice_profile, language, attempt_count, overall_rate, inter_segment_pause_ms
        self.calls.append(provider)
        target = self.base_dir / "audio" / f"{render_job_id}_{provider}.wav"
        target.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(target), "wb") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(16000)
            writer.writeframes(b"\x00" * 16000)
        return TtsResponse(audio_path=str(target), duration_s=1.0, segment_durations=[0.3, 0.3, 0.4])


class VoicePlanIntegrationPhase25Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_orchestrator_pipeline_and_tts_trace_obey_voice_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "OUT"
            tts_adapter = _TracingTtsAdapter(base_dir=out / "content")
            pipeline = ContentPipelineService(
                tts_adapter=tts_adapter,
                render_adapter=StubRenderAdapter(base_dir=out / "content"),
                publish_adapter=StubPublishAdapter(),
                event_path=out / "events" / "events.jsonl",
            )
            orchestrator = CreativeOrchestratorService(
                pipeline_service=pipeline,
                script_agent=ScriptAgentService(generator=_StructuredGenerator()),
                voice_agent=VoiceAgentService(),
                video_qc_agent=VideoQcAgentService(),
                event_emitter=CreativeEventEmitter(event_path=out / "events" / "creative_events.jsonl"),
            )

            execution = orchestrator.execute(
                CreativeOrchestratorInput(
                    account_id="acc_1",
                    niche="true_crime",
                    topic="dispatcher tape reopened",
                    publish_slot="2026-03-18T12:00:00Z",
                )
            )

            self.assertEqual(execution.pipeline_output["result"]["status"], "READY")
            self.assertEqual(execution.creative_pack.voice_plan.provider, "kokoro")
            self.assertEqual(execution.pipeline_output["result"]["tts_trace"]["provider_requested"], "kokoro")
            self.assertEqual(execution.pipeline_output["result"]["tts_trace"]["provider_executed"], "kokoro")
            self.assertFalse(execution.pipeline_output["result"]["tts_trace"]["fallback_used"])
            self.assertEqual(tts_adapter.calls, [])


if __name__ == "__main__":
    unittest.main()
