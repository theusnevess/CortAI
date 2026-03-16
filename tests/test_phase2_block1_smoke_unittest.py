from __future__ import annotations

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
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput


class Phase2Block1SmokeTests(unittest.TestCase):
    def test_minimal_flow_generates_video_and_returns_qc_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = Path(tmp_dir) / "OUT"
            pipeline = ContentPipelineService(
                tts_adapter=StubTtsAdapter(base_dir=out / "content"),
                render_adapter=StubRenderAdapter(base_dir=out / "content"),
                publish_adapter=StubPublishAdapter(),
                event_path=out / "events" / "events.jsonl",
            )
            orchestrator = CreativeOrchestratorService(
                pipeline_service=pipeline,
                script_agent=ScriptAgentService(),
                voice_agent=VoiceAgentService(),
                video_qc_agent=VideoQcAgentService(),
                event_emitter=CreativeEventEmitter(event_path=out / "events" / "creative_events.jsonl"),
            )

            execution = orchestrator.execute(
                CreativeOrchestratorInput(
                    account_id="acc_smoke",
                    niche="horror",
                    topic="abandoned platform",
                    publish_slot="2026-03-16T14:00:00Z",
                )
            )

            self.assertEqual(execution.pipeline_output["result"]["status"], "READY")
            self.assertEqual(execution.video_qc.status, "APPROVE")
            self.assertTrue(Path(execution.pipeline_output["result"]["artifacts"]["audio"]).exists())
            self.assertTrue(Path(execution.pipeline_output["result"]["artifacts"]["video"]).exists())


if __name__ == "__main__":
    unittest.main()
