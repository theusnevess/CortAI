from __future__ import annotations

import os
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
from app.content.pipeline.tts import StubTtsAdapter, TtsResponse
from app.creative.contracts.creative_pack import VoiceDeliveryProfile, VoicePlan, VoiceRuntimeConstraints, VoiceSegmentPlan


class _CapturingPiperAdapter(StubTtsAdapter):
    def __init__(self, *, base_dir: Path) -> None:
        super().__init__(base_dir=base_dir)
        self.last_script_text: str | None = None

    def supports_provider(self, provider: str) -> bool:
        return provider == "piper"

    def generate_audio_for_provider(
        self,
        *,
        provider: str,
        script_text: str,
        voice_profile: str | None,
        language: str | None,
        render_job_id: str,
        attempt_count: int,
        overall_rate: float | None = None,
        inter_segment_pause_ms: list[int] | None = None,
    ) -> TtsResponse:
        self.last_script_text = script_text
        return super().generate_audio_for_provider(
            provider=provider,
            script_text=script_text,
            voice_profile=voice_profile,
            language=language,
            render_job_id=render_job_id,
            attempt_count=attempt_count,
            overall_rate=overall_rate,
            inter_segment_pause_ms=inter_segment_pause_ms,
        )


class ReadabilityPipelineIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)

    def _voice_plan(self) -> VoicePlan:
        return VoicePlan(
            provider="piper",
            voice_id="tools/piper/voices/en_US-lessac-high.onnx",
            style="investigative",
            delivery_profile=VoiceDeliveryProfile(overall_mode="baseline", overall_rate=1.0, overall_intensity="medium"),
            segments={
                "hook": VoiceSegmentPlan(rate=1.0, emphasis="high", pause_after_ms=320),
                "setup": VoiceSegmentPlan(rate=1.0, emphasis="medium", pause_after_ms=180),
                "payoff": VoiceSegmentPlan(rate=0.95, emphasis="high", pause_before_ms=420),
            },
            runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=["piper"]),
        )

    def _execute(self, *, flag_on: bool) -> tuple[dict[str, object], str]:
        if flag_on:
            os.environ["CORTAI_EXPERIMENT_READABILITY_PUNCTUATION"] = "1"
        else:
            os.environ.pop("CORTAI_EXPERIMENT_READABILITY_PUNCTUATION", None)

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "OUT"
            adapter = _CapturingPiperAdapter(base_dir=out / "content")
            service = ContentPipelineService(
                tts_adapter=adapter,
                render_adapter=StubRenderAdapter(base_dir=out / "content"),
                publish_adapter=StubPublishAdapter(),
                event_path=out / "events" / "events.jsonl",
            )
            result = service.execute(
                ExecutionEnvelope(
                    job_id="job_readability",
                    account_id="acc_1",
                    creative_pack_id="cp_1",
                    publish_slot="2026-03-18T12:00:00Z",
                    experiment_variant="A",
                ),
                script_text=(
                    "The dispatcher kept listening to the hallway but the security camera still showed nothing there. "
                    "Nobody in the station could explain why the line stayed open. "
                    "Then the tape captured a second voice."
                ),
                voice_plan=self._voice_plan(),
                caption="caption",
                hashtags=["#readability"],
            )
            return result, adapter.last_script_text or ""

    def test_flag_off_preserves_baseline_text(self) -> None:
        result, tts_text = self._execute(flag_on=False)

        self.assertEqual(result["result"]["status"], "READY")
        self.assertEqual(result["result"]["tts_trace"]["provider_requested"], "piper")
        self.assertEqual(result["result"]["tts_trace"]["provider_executed"], "piper")
        self.assertNotIn("HALLWAY BUT,", tts_text)

    def test_flag_on_applies_readability_punctuation_without_breaking_pipeline(self) -> None:
        result, tts_text = self._execute(flag_on=True)

        self.assertEqual(result["result"]["status"], "READY")
        self.assertEqual(result["result"]["tts_trace"]["provider_requested"], "piper")
        self.assertEqual(result["result"]["tts_trace"]["provider_executed"], "piper")
        self.assertIn("HALLWAY BUT,", tts_text)


if __name__ == "__main__":
    unittest.main()
