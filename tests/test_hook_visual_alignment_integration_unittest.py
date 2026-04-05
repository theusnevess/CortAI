from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.publish import StubPublishAdapter
from app.content.pipeline.render import StubRenderAdapter
from app.content.pipeline.service import ContentPipelineService
from app.content.pipeline.tts import StubTtsAdapter
from app.content.script_gen.models import ScriptGenerationResponse, StructuredScriptPayload
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import ScriptPlan
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService


class _InferentialGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        return ScriptGenerationResponse(
            script_plan=ScriptPlan(
                hook="The night watch log contained a date from the future.",
                setup="The clerk checked the archive twice before dawn.",
                payoff="The next entry was signed three days early.",
                generation_mode="test_structured",
            ),
            payload=StructuredScriptPayload(
                hook="The night watch log contained a date from the future.",
                setup="The clerk checked the archive twice before dawn.",
                payoff="The next entry was signed three days early.",
                narrative_mode="contradiction_timeline",
            ),
            provider_used="test",
            model_used="test",
            prompt_used="prompt",
            raw_output="{}",
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )


class _ExperientialGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        return ScriptGenerationResponse(
            script_plan=ScriptPlan(
                hook="The camera went dark in sector 4.",
                setup="The station cameras failed one by one before dawn.",
                payoff="The backup feed showed a hallway that was already sealed.",
                generation_mode="test_structured",
            ),
            payload=StructuredScriptPayload(
                hook="The camera went dark in sector 4.",
                setup="The station cameras failed one by one before dawn.",
                payoff="The backup feed showed a hallway that was already sealed.",
                narrative_mode="procedural_anomaly",
            ),
            provider_used="test",
            model_used="test",
            prompt_used="prompt",
            raw_output="{}",
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )


class HookVisualAlignmentIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = dict(os.environ)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "OUT"
        self.pipeline = ContentPipelineService(
            tts_adapter=StubTtsAdapter(base_dir=self.out / "content"),
            render_adapter=StubRenderAdapter(base_dir=self.out / "content"),
            publish_adapter=StubPublishAdapter(),
            event_path=self.out / "events" / "events.jsonl",
        )

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)

    def _orchestrator(self) -> CreativeOrchestratorService:
        return CreativeOrchestratorService(
            pipeline_service=self.pipeline,
            script_agent=ScriptAgentService(generator=_InferentialGenerator()),
            voice_agent=VoiceAgentService(),
            video_qc_agent=VideoQcAgentService(),
            event_emitter=CreativeEventEmitter(event_path=self.out / "events" / "creative_events.jsonl"),
        )

    def _experiential_orchestrator(self) -> CreativeOrchestratorService:
        return CreativeOrchestratorService(
            pipeline_service=self.pipeline,
            script_agent=ScriptAgentService(generator=_ExperientialGenerator()),
            voice_agent=VoiceAgentService(),
            video_qc_agent=VideoQcAgentService(),
            event_emitter=CreativeEventEmitter(event_path=self.out / "events" / "creative_events.jsonl"),
        )

    def test_flag_off_keeps_baseline_hook_asset_selection(self) -> None:
        os.environ["CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT"] = "0"
        orchestrator = self._orchestrator()

        result = orchestrator.build_creative_pack(
            CreativeOrchestratorInput(
                account_id="acc_1",
                niche="investigative",
                topic="night watch log with future date",
                publish_slot="2026-03-19T12:00:00Z",
            )
        )

        self.assertTrue(result.creative_pack.asset_plan.hook_asset)
        self.assertEqual(result.creative_pack.asset_plan.visual_anchor, "document")
        self.assertEqual(result.creative_pack.asset_plan.segments["hook"].category, "document")

    def test_flag_on_keeps_first_frame_semantically_resolved(self) -> None:
        orchestrator = self._experiential_orchestrator()
        os.environ["CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT"] = "0"
        baseline = orchestrator.build_creative_pack(
            CreativeOrchestratorInput(
                account_id="acc_1",
                niche="true_crime",
                topic="camera blackout in sector 4",
                publish_slot="2026-03-19T12:00:00Z",
            )
        )

        os.environ["CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT"] = "1"
        os.environ["CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT_MODE"] = "baseline"
        result = orchestrator.build_creative_pack(
            CreativeOrchestratorInput(
                account_id="acc_1",
                niche="true_crime",
                topic="camera blackout in sector 4",
                publish_slot="2026-03-19T12:00:00Z",
            )
        )

        self.assertTrue(result.creative_pack.asset_plan.hook_asset)
        self.assertEqual(result.creative_pack.asset_plan.visual_anchor, "device")
        self.assertEqual(result.creative_pack.asset_plan.segments["hook"].category, "monitor_screen")
        self.assertEqual(result.creative_pack.asset_plan.setup_asset, baseline.creative_pack.asset_plan.setup_asset)
        self.assertEqual(result.creative_pack.asset_plan.payoff_asset, baseline.creative_pack.asset_plan.payoff_asset)

    def test_refined_mode_leaves_inferential_path_intact(self) -> None:
        orchestrator = self._orchestrator()
        os.environ["CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT"] = "1"
        os.environ["CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT_MODE"] = "baseline"
        baseline = orchestrator.build_creative_pack(
            CreativeOrchestratorInput(
                account_id="acc_1",
                niche="investigative",
                topic="night watch log with future date",
                publish_slot="2026-03-19T12:00:00Z",
            )
        )

        os.environ["CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT_MODE"] = "refined_experiential"
        refined = orchestrator.build_creative_pack(
            CreativeOrchestratorInput(
                account_id="acc_1",
                niche="investigative",
                topic="night watch log with future date",
                publish_slot="2026-03-19T12:00:00Z",
            )
        )

        self.assertEqual(refined.creative_pack.asset_plan.hook_asset, baseline.creative_pack.asset_plan.hook_asset)


if __name__ == "__main__":
    unittest.main()
