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

    def test_render_generates_ass_subtitles_with_stable_styles_and_escaping(self) -> None:
        result = self.service.execute(
            self._envelope(creative_pack_id="cp_ass"),
            script_text=(
                "In the old motel, someone wrote: \"don't look back,\" on the mirror. "
                "Who left that warning: the night guard, or someone else? "
                "Then the lights failed, and the door wouldn't open."
            ),
            caption="caption",
            hashtags=["#ass"],
        )

        self.assertEqual(result["result"]["status"], "READY")
        render_job_id = result["result"]["render_job_id"]
        metadata_path = self.out / "content" / "metadata" / f"{render_job_id}.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        subtitle_path = Path(metadata["subtitle_path"])
        self.assertTrue(subtitle_path.exists())

        subtitle_text = subtitle_path.read_text(encoding="utf-8")
        self.assertIn("Style: HookStyle", subtitle_text)
        self.assertIn("Style: BodyStyle", subtitle_text)
        self.assertIn("Style: PayoffStyle", subtitle_text)
        self.assertIn(r"{\fad(120,120)}", subtitle_text)
        self.assertIn(r"\N", subtitle_text)
        self.assertNotIn("\u2019", subtitle_text)
        self.assertNotIn("\u201c", subtitle_text)
        self.assertNotIn("\u201d", subtitle_text)
        self.assertIn(r"SOMEONE WROTE ON\NTHE MIRROR", subtitle_text)
        self.assertIn(r"WHO LEFT THE\NWARNING?", subtitle_text)
        self.assertIn(r"THE DOOR WOULDN'T\NOPEN", subtitle_text)

        cues = metadata["subtitle_cues"]
        self.assertEqual([cue["style_role"] for cue in cues], ["hook", "setup", "payoff"])
        self.assertEqual(cues[0]["start"], 0.0)
        self.assertLess(cues[0]["start"], cues[0]["end"])
        self.assertLess(cues[1]["start"], cues[1]["end"])
        self.assertLess(cues[2]["start"], cues[2]["end"])
        self.assertTrue(all(len(cue["text"].splitlines()) <= 3 for cue in cues))

    def test_render_preserves_three_line_body_when_needed(self) -> None:
        result = self.service.execute(
            self._envelope(creative_pack_id="cp_three_line"),
            script_text=(
                "Workers sealed the tunnel decades ago, but a single light still blinked behind the concrete. "
                "Nobody could explain the sound coming from inside. "
                "Then the wall answered with three knocks."
            ),
            caption="caption",
            hashtags=["#three"],
        )

        self.assertEqual(result["result"]["status"], "READY")
        render_job_id = result["result"]["render_job_id"]
        metadata_path = self.out / "content" / "metadata" / f"{render_job_id}.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        cues = metadata["subtitle_cues"]
        self.assertEqual(len(cues[1]["text"].splitlines()), 3)
        self.assertIn("INSIDE", cues[1]["text"])
        self.assertIn("EXPLAIN", cues[1]["text"])

    def test_render_preserves_three_line_hook_when_needed(self) -> None:
        result = self.service.execute(
            self._envelope(creative_pack_id="cp_three_line_hook"),
            script_text=(
                "Workers sealed the tunnel decades ago, but a single light still blinked behind the concrete. "
                "Nobody could explain the sound coming from inside. "
                "Then the wall answered with three knocks."
            ),
            caption="caption",
            hashtags=["#hook3"],
        )

        self.assertEqual(result["result"]["status"], "READY")
        render_job_id = result["result"]["render_job_id"]
        metadata_path = self.out / "content" / "metadata" / f"{render_job_id}.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        cues = metadata["subtitle_cues"]
        self.assertEqual(len(cues[0]["text"].splitlines()), 3)
        self.assertIn("WORKERS", cues[0]["text"])
        self.assertIn("DECADES", cues[0]["text"])

    def test_fit_text_preserves_semantic_tail_in_hook(self) -> None:
        normalized = self.service.render_adapter._normalize_block(  # noqa: SLF001
            "AT ABANDONED TRAIN PLATFORM, ONE TIMETABLE KEPT",
            role="hook",
        )

        self.assertIn("KEPT", normalized)
        self.assertNotIn("ONE", normalized.replace("\n", " ").split())
        self.assertLessEqual(len(normalized.splitlines()), 3)

    def test_fit_text_preserves_semantic_tail_in_payoff(self) -> None:
        normalized = self.service.render_adapter._normalize_block(  # noqa: SLF001
            "THEN FINAL DEPARTURE APPEARED STATION NEVER EXISTED",
            role="payoff",
        )

        self.assertIn("EXISTED", normalized)
        self.assertIn("NEVER", normalized)
        self.assertLessEqual(len(normalized.splitlines()), 3)


if __name__ == "__main__":
    unittest.main()
