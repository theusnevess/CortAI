from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.kokoro_adapter import KokoroAdapter


class KokoroAdapterPhase25BTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = dict(os.environ)
        assets = ROOT / "OUT" / "audit" / "phase2_5b_kokoro" / "kokoro_assets"
        os.environ["CORTAI_KOKORO_MODEL_PATH"] = str(assets / "kokoro-v1.0.onnx")
        os.environ["CORTAI_KOKORO_VOICES_PATH"] = str(assets / "voices-v1.0.bin")
        os.environ["CORTAI_KOKORO_DEVICE"] = "cpu"

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_generates_audio_with_real_kokoro_assets(self) -> None:
        adapter = KokoroAdapter(base_dir=ROOT / "OUT" / "audit" / "phase2_5b_kokoro" / "test_adapter")
        self.assertTrue(adapter.available())

        result = adapter.generate_audio(
            script_text="This is a short CortAI Kokoro test.",
            voice_profile="af_heart",
            language="en-us",
            render_job_id="kokoro_adapter_test",
            overall_rate=1.0,
            inter_segment_pause_ms=[],
        )

        self.assertTrue(Path(result.audio_path).exists())
        self.assertGreater(result.duration_s or 0.0, 0.1)
        self.assertEqual(result.segment_durations and len(result.segment_durations), 1)


if __name__ == "__main__":
    unittest.main()
