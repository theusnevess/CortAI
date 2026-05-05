from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.models import ExecutionEnvelope
from app.content.pipeline.publish import StubPublishAdapter
from app.content.pipeline.render import RenderAdapter, RenderResponse
from app.content.pipeline.service import ContentPipelineService
from app.content.pipeline.tts import StubTtsAdapter
from app.content.script_gen.models import ScriptGenerationResponse, StructuredScriptPayload
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import ScriptPlan
from app.creative.orchestrator.service import CreativeOrchestratorService
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput


class _StructuredGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        return ScriptGenerationResponse(
            script_plan=ScriptPlan(
                hook="The warning panel started flashing.",
                setup="The corridor lights dimmed around the sealed door.",
                payoff="The breach seal was already broken from inside.",
                generation_mode="test_structured",
            ),
            payload=StructuredScriptPayload(
                hook="The warning panel started flashing.",
                setup="The corridor lights dimmed around the sealed door.",
                payoff="The breach seal was already broken from inside.",
                narrative_mode="official_warning",
            ),
            provider_used="test",
            model_used="test",
            prompt_used="prompt",
            raw_output="{}",
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )


class _CaptureRenderAdapter(RenderAdapter):
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.received_edit_plan = None

    def render_video(
        self,
        *,
        audio_path: str,
        script_text: str,
        asset_plan,
        edit_plan,
        screen_blocks: list[str] | None,
        segment_durations: list[float] | None,
        render_job_id: str,
        template_id: str | None,
        aspect_ratio: str | None,
        attempt_count: int,
    ) -> RenderResponse:
        del audio_path, script_text, asset_plan, screen_blocks, segment_durations, template_id, aspect_ratio, attempt_count
        self.received_edit_plan = edit_plan
        target = self.base_dir / "video" / f"{render_job_id}.mp4"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"video")
        return RenderResponse(video_path=str(target))


class EditorPipelineIntegrationTests(unittest.TestCase):
    def test_orchestrator_builds_edit_plan_and_pipeline_receives_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = Path(tmp_dir) / "OUT"
            render = _CaptureRenderAdapter(out / "content")
            pipeline = ContentPipelineService(
                tts_adapter=StubTtsAdapter(base_dir=out / "content"),
                render_adapter=render,
                publish_adapter=StubPublishAdapter(),
                event_path=out / "events" / "events.jsonl",
            )
            orchestrator = CreativeOrchestratorService(
                pipeline_service=pipeline,
                script_agent=ScriptAgentService(generator=_StructuredGenerator()),
                voice_agent=VoiceAgentService(),
            )
            result = orchestrator.build_creative_pack(
                CreativeOrchestratorInput(
                    account_id="acc_1",
                    niche="horror",
                    topic="sealed corridor alert",
                    publish_slot="2026-03-27T12:00:00Z",
                )
            )
            self.assertIsNotNone(result.creative_pack.edit_plan)
            assert result.creative_pack.edit_plan is not None
            self.assertTrue(result.creative_pack.edit_plan.caption_plan.segment_caption_blocks["hook"])

            output = pipeline.execute(
                ExecutionEnvelope(
                    job_id="job_1",
                    account_id="acc_1",
                    creative_pack_id=result.creative_pack.creative_pack_id,
                    publish_slot="2026-03-27T12:00:00Z",
                ),
                script_text=result.creative_pack.script_plan.narration_text(),
                asset_plan=result.creative_pack.asset_plan,
                edit_plan=result.creative_pack.edit_plan,
                voice_plan=result.creative_pack.voice_plan,
            )

            self.assertEqual(output["result"]["status"], "READY")
            self.assertIsNotNone(render.received_edit_plan)
            self.assertEqual(render.received_edit_plan.editor_version, "editor-agent-v2_2")
            self.assertEqual(render.received_edit_plan.caption_plan.caption_animation_mode, "progressive_word_reveal")
            self.assertTrue(render.received_edit_plan.timing_plan.emphasis_sync_points)
            self.assertTrue(output["result"]["edit_trace"])


if __name__ == "__main__":
    unittest.main()
