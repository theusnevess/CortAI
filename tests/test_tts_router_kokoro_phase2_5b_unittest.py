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

from app.content.pipeline.kokoro_adapter import KokoroAdapter
from app.content.pipeline.tts import StubTtsAdapter
from app.content.pipeline.tts_router import TtsRouter
from app.creative.contracts.creative_pack import VoicePlan, VoiceRuntimeConstraints


class TtsRouterKokoroPhase25BTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = dict(os.environ)
        assets = ROOT / "OUT" / "audit" / "phase2_5b_kokoro" / "kokoro_assets"
        os.environ["CORTAI_KOKORO_MODEL_PATH"] = str(assets / "kokoro-v1.0.onnx")
        os.environ["CORTAI_KOKORO_VOICES_PATH"] = str(assets / "voices-v1.0.bin")
        os.environ["CORTAI_KOKORO_DEVICE"] = "cpu"

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_router_executes_kokoro_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            router = TtsRouter(
                tts_adapter=StubTtsAdapter(base_dir=Path(tmp)),
                kokoro_adapter=KokoroAdapter(base_dir=Path(tmp)),
            )
            voice_plan = VoicePlan(
                provider="kokoro",
                voice_id="af_heart",
                style="investigative",
                runtime_constraints=VoiceRuntimeConstraints(fallback_order=["kokoro", "piper"]),
            )

            result = router.generate_audio(
                script_text="Hook.\n\nSetup.\n\nPayoff.",
                voice_plan=voice_plan,
                language="en-us",
                render_job_id="router_kokoro",
                attempt_count=1,
            )

            self.assertEqual(result.trace.provider_requested, "kokoro")
            self.assertEqual(result.trace.provider_executed, "kokoro")
            self.assertFalse(result.trace.fallback_used)
            self.assertTrue(Path(result.response.audio_path).exists())


if __name__ == "__main__":
    unittest.main()
