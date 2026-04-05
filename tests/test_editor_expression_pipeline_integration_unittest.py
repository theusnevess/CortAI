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
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService


class EditorExpressionPipelineIntegrationTests(unittest.TestCase):
    def test_pipeline_persists_expressive_edit_plan(self) -> None:
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
                video_qc_agent=VideoQcAgentService(),
                event_emitter=CreativeEventEmitter(event_path=out / "events" / "creative_events.jsonl"),
            )

            result = orchestrator.execute(
                CreativeOrchestratorInput(
                    account_id="acc_expr_001",
                    niche="true_crime",
                    topic="dispatch recording captured impossible reply",
                    publish_slot="2026-03-27T12:00:00Z",
                )
            )

            self.assertEqual(result.pipeline_output["result"]["status"], "READY")
            self.assertEqual(result.video_qc.status, "APPROVE")
            edit_trace = result.pipeline_output["result"]["edit_trace"]
            self.assertEqual(edit_trace["editor_version"], "editor-agent-v2_2")
            self.assertEqual(edit_trace["caption_plan"]["caption_animation_mode"], "progressive_word_reveal")
            self.assertTrue(edit_trace["timing_plan"]["emphasis_sync_points"])
            self.assertIn("__", edit_trace["editor_style_profile"])


if __name__ == "__main__":
    unittest.main()
