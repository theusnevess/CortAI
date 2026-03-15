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
from app.content.pipeline.service import ContentPipelineService
from app.content.pipeline.tts import StubTtsAdapter
from app.content.pipeline.render import StubRenderAdapter
from app.content.pipeline.publish import StubPublishAdapter


class ContentPipelineD27Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "OUT"
        self.event_path = self.out / "events" / "events.jsonl"
        self.service = ContentPipelineService(
            tts_adapter=StubTtsAdapter(base_dir=self.out / "content"),
            render_adapter=StubRenderAdapter(base_dir=self.out / "content"),
            publish_adapter=StubPublishAdapter(),
            event_path=self.event_path,
        )

    def _envelope(self, *, creative_pack_id: str = "cp_001", account_id: str = "acc_001") -> ExecutionEnvelope:
        return ExecutionEnvelope(
            job_id=f"job_{creative_pack_id}_{account_id}",
            account_id=account_id,
            creative_pack_id=creative_pack_id,
            publish_slot="2026-03-15T12:00:00Z",
            experiment_variant="A",
        )

    def _read_events(self) -> list[dict]:
        if not self.event_path.exists():
            return []
        with self.event_path.open("r", encoding="utf-8") as reader:
            return [json.loads(line) for line in reader if line.strip()]

    def test_execute_generates_audio_video_and_manifest(self) -> None:
        result = self.service.execute(
            self._envelope(),
            script_text="roteiro de teste d27",
            caption="caption de teste",
            hashtags=["#um", "#dois"],
        )

        self.assertEqual(result["result"]["status"], "READY")
        manifest = result["result"]["publish_manifest"]
        self.assertEqual(manifest["account_id"], "acc_001")
        self.assertEqual(manifest["caption"], "caption de teste")
        self.assertEqual(manifest["hashtags"], ["#um", "#dois"])
        self.assertTrue(Path(result["result"]["artifacts"]["audio"]).exists())
        self.assertTrue(Path(result["result"]["artifacts"]["video"]).exists())

    def test_pipeline_emits_only_content_events(self) -> None:
        result = self.service.execute(
            self._envelope(),
            script_text="roteiro com eventos",
            caption="caption",
            hashtags=["#evt"],
        )

        self.assertEqual(
            result["result"]["events_emitted"],
            [
                "CONTENT/tts_started",
                "CONTENT/tts_completed",
                "CONTENT/render_started",
                "CONTENT/render_completed",
                "CONTENT/publish_manifest_created",
            ],
        )
        event_types = [row["event_type"] for row in self._read_events()]
        self.assertEqual(event_types, result["result"]["events_emitted"])

    def test_no_publish_record_side_effect(self) -> None:
        self.service.execute(
            self._envelope(),
            script_text="roteiro sem publish record",
            caption="caption",
            hashtags=["#sideeffect"],
        )
        publish_records_path = self.out / "data" / "publish_records" / "publish_records.jsonl"
        self.assertFalse(publish_records_path.exists())

    def test_duplicate_execution_returns_noop(self) -> None:
        envelope = self._envelope()
        first = self.service.execute(
            envelope,
            script_text="roteiro duplicado",
            caption="caption",
            hashtags=["#dup"],
        )
        second = self.service.execute(
            envelope,
            script_text="roteiro duplicado",
            caption="caption",
            hashtags=["#dup"],
        )

        self.assertEqual(first["result"]["status"], "READY")
        self.assertEqual(second["result"]["status"], "NOOP")

    def test_failure_emits_pipeline_failed(self) -> None:
        result = self.service.execute(
            self._envelope(),
            script_text="   ",
            caption="caption",
            hashtags=[],
        )

        self.assertEqual(result["result"]["status"], "FAILED")
        self.assertIn("CONTENT/pipeline_failed", result["result"]["events_emitted"])


if __name__ == "__main__":
    unittest.main()
