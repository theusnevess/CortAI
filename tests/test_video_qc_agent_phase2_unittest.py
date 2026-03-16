from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.models import ExecutionEnvelope
from app.content.pipeline.publish import StubPublishAdapter
from app.content.pipeline.render import StubRenderAdapter
from app.content.pipeline.service import ContentPipelineService
from app.content.pipeline.tts import StubTtsAdapter
from app.creative.agents.video_qc.service import VideoQcAgentService


class VideoQcAgentPhase2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "OUT"
        self.service = ContentPipelineService(
            tts_adapter=StubTtsAdapter(base_dir=self.out / "content"),
            render_adapter=StubRenderAdapter(base_dir=self.out / "content"),
            publish_adapter=StubPublishAdapter(),
            event_path=self.out / "events" / "events.jsonl",
        )

    def _execute_pipeline(self) -> tuple[str, dict[str, object]]:
        result = self.service.execute(
            ExecutionEnvelope(
                job_id="job_qc",
                account_id="acc_qc",
                creative_pack_id="cp_qc",
                publish_slot="2026-03-16T12:00:00Z",
            ),
            script_text="Someone wrote on the mirror. Who left the warning? The door wouldn't open.",
        )
        return str(result["result"]["render_job_id"]), result["result"]["artifacts"]

    def test_approves_valid_generated_video(self) -> None:
        render_job_id, artifacts = self._execute_pipeline()

        qc = VideoQcAgentService().evaluate(
            render_job_id=render_job_id,
            artifacts=artifacts,
            base_dir=self.out / "content",
        )

        self.assertEqual(qc.status, "APPROVE")
        self.assertEqual(qc.reasons, [])

    def test_returns_controlled_reject_when_metadata_is_missing(self) -> None:
        render_job_id, artifacts = self._execute_pipeline()
        metadata_path = self.out / "content" / "metadata" / f"{render_job_id}.json"
        metadata_path.unlink()

        qc = VideoQcAgentService().evaluate(
            render_job_id=render_job_id,
            artifacts=artifacts,
            base_dir=self.out / "content",
        )

        self.assertEqual(qc.status, "REJECT")
        self.assertIn("QC_METADATA_MISSING", qc.reasons)

    def test_rejects_payoff_that_is_too_dark(self) -> None:
        render_job_id, artifacts = self._execute_pipeline()
        metadata_path = self.out / "content" / "metadata" / f"{render_job_id}.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["payoff_background_mean_luma"] = 20.0
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        qc = VideoQcAgentService().evaluate(
            render_job_id=render_job_id,
            artifacts=artifacts,
            base_dir=self.out / "content",
        )

        self.assertEqual(qc.status, "REJECT")
        self.assertIn("QC_PAYOFF_TOO_DARK", qc.reasons)


if __name__ == "__main__":
    unittest.main()
