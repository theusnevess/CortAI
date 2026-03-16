from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.voice.service import VoiceAgentService


class VoiceAgentPhase2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_prefers_premium_voice_when_configured(self) -> None:
        os.environ["CORTAI_PREMIUM_TTS_PROVIDER"] = "elevenlabs"
        os.environ["CORTAI_PREMIUM_TTS_VOICE"] = "adam"

        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror")

        self.assertEqual(result.voice_plan.provider, "elevenlabs")
        self.assertEqual(result.voice_plan.voice_id, "adam")
        self.assertFalse(result.fallback.used)

    def test_falls_back_to_piper_when_premium_is_unavailable(self) -> None:
        os.environ.pop("CORTAI_PREMIUM_TTS_PROVIDER", None)
        os.environ.pop("CORTAI_PREMIUM_TTS_VOICE", None)
        os.environ["CORTAI_PIPER_MODEL"] = "tools/piper/voices/en_US-lessac-high.onnx"

        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror")

        self.assertEqual(result.voice_plan.provider, "piper")
        self.assertTrue(result.voice_plan.voice_id.endswith(".onnx"))
        self.assertTrue(result.fallback.used)
        self.assertEqual(result.fallback.reason, "voice_fallback_to_piper")


if __name__ == "__main__":
    unittest.main()
