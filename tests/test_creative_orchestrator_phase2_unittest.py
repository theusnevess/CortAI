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
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput


class CreativeOrchestratorPhase2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "OUT"
        self.pipeline = ContentPipelineService(
            tts_adapter=StubTtsAdapter(base_dir=self.out / "content"),
            render_adapter=StubRenderAdapter(base_dir=self.out / "content"),
            publish_adapter=StubPublishAdapter(),
            event_path=self.out / "events" / "events.jsonl",
        )
        self.orchestrator = CreativeOrchestratorService(
            pipeline_service=self.pipeline,
            script_agent=ScriptAgentService(),
            voice_agent=VoiceAgentService(),
            video_qc_agent=VideoQcAgentService(),
            event_emitter=CreativeEventEmitter(event_path=self.out / "events" / "creative_events.jsonl"),
        )
        self.original_env = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_builds_minimal_creative_pack(self) -> None:
        data = CreativeOrchestratorInput(
            account_id="acc_1",
            niche="horror",
            topic="mirror warning",
            publish_slot="2026-03-16T12:00:00Z",
        )

        result = self.orchestrator.build_creative_pack(data)

        self.assertEqual(result.creative_pack.account_id, "acc_1")
        self.assertEqual(result.creative_pack.niche, "horror")
        self.assertTrue(result.creative_pack.script_plan.hook)
        self.assertTrue(result.creative_pack.voice_plan.voice_id)
        self.assertIn("CREATIVE/orchestrator_started", result.events_emitted)
        self.assertIn("CREATIVE/orchestrator_completed", result.events_emitted)

    def test_executes_pipeline_and_qc_without_touching_publish_record_contracts(self) -> None:
        data = CreativeOrchestratorInput(
            account_id="acc_1",
            niche="horror",
            topic="sealed tunnel",
            publish_slot="2026-03-16T12:00:00Z",
        )

        execution = self.orchestrator.execute(data)

        self.assertEqual(execution.pipeline_output["result"]["status"], "READY")
        self.assertEqual(execution.video_qc.status, "APPROVE")
        publish_records_path = self.out / "data" / "publish_records" / "publish_records.jsonl"
        self.assertFalse(publish_records_path.exists())


if __name__ == "__main__":
    unittest.main()
