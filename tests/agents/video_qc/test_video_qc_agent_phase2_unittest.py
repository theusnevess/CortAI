from __future__ import annotations

import json
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
from app.content.pipeline.render import StubRenderAdapter
from app.content.pipeline.service import ContentPipelineService
from app.content.pipeline.tts import StubTtsAdapter
from app.creative.agents.video_qc.models import VideoQcDecision, VideoQcInput, VideoQcResult
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
            qc_input=VideoQcInput(
                render_job_id=render_job_id,
                video_path=str(artifacts["video"]),
                audio_path=str(artifacts["audio"]),
                metadata_path=str(self.out / "content" / "metadata" / f"{render_job_id}.json"),
                script_text="Someone wrote on the mirror. Who left the warning? The door wouldn't open.",
                tts_trace={"segment_durations": [2.4, 2.2, 2.6]},
                edit_trace={"editor_version": "test"},
            )
        )

        self.assertEqual(qc.status, "APPROVE")
        self.assertEqual(qc.reasons, [])
        self.assertTrue(qc.publishable)
        self.assertEqual(qc.decision.status, "APPROVE")
        self.assertGreaterEqual(qc.decision.score_summary["overall_score"], 0.74)

    def test_decision_and_result_serialize_with_hold_support(self) -> None:
        decision = VideoQcDecision(
            status="HOLD",
            publishable=False,
            hard_failures=[],
            soft_failures=["QC_PUBLISHABILITY_HOLD"],
            product_vetoes=[],
            score_summary={"overall_score": 0.66},
            product_signals={"hook_quality": 0.7, "payoff_quality": 0.58, "publishable": False},
            decision_trace={"mode": "test"},
            checked_at="2026-03-28T00:00:00Z",
        )
        result = VideoQcResult(
            decision=decision,
            status="HOLD",
            reasons=["QC_PUBLISHABILITY_HOLD"],
            checked_at="2026-03-28T00:00:00Z",
            publishable=False,
            details={"render_job_id": "rj_test"},
        )

        payload = result.to_dict()

        self.assertEqual(payload["decision"]["status"], "HOLD")
        self.assertFalse(payload["decision"]["publishable"])
        self.assertEqual(payload["status"], "HOLD")
        self.assertEqual(payload["reasons"], ["QC_PUBLISHABILITY_HOLD"])

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
        self.assertFalse(qc.publishable)
        self.assertIn("QC_METADATA_MISSING", qc.decision.hard_failures)

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
        self.assertIn("QC_PAYOFF_TOO_DARK", qc.decision.hard_failures)

    def test_returns_hold_for_borderline_hook_and_payoff_quality(self) -> None:
        render_job_id, artifacts = self._execute_pipeline()
        metadata_path = self.out / "content" / "metadata" / f"{render_job_id}.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["subtitle_cues"][0]["start"] = 0.6
        metadata["subtitle_cues"][0]["end"] = 1.6
        metadata["subtitle_cues"][0]["text"] = "LOOK BACK"
        metadata["subtitle_cues"][-1]["start"] = max(0.0, float(metadata["render_duration_s"]) - 1.2)
        metadata["subtitle_cues"][-1]["end"] = float(metadata["render_duration_s"]) - 0.2
        metadata["subtitle_cues"][-1]["text"] = "TURN NOW"
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        qc = VideoQcAgentService().evaluate(
            qc_input=VideoQcInput(
                render_job_id=render_job_id,
                video_path=str(artifacts["video"]),
                audio_path=str(artifacts["audio"]),
                metadata_path=str(metadata_path),
                script_text="Look back now. Turn away before the final door opens.",
                tts_trace={"segment_durations": [2.4, 2.2, 2.6]},
                edit_trace={"editor_version": "test"},
            )
        )

        self.assertEqual(qc.status, "HOLD")
        self.assertFalse(qc.publishable)
        self.assertIn("QC_HOOK_QUALITY_BORDERLINE", qc.decision.soft_failures)
        self.assertIn("QC_PUBLISHABILITY_HOLD", qc.decision.soft_failures)


if __name__ == "__main__":
    unittest.main()
