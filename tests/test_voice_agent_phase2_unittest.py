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

    def test_prefers_kokoro_as_primary_provider(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror")

        self.assertEqual(result.voice_plan.provider, "kokoro")
        self.assertEqual(result.voice_plan.voice_id, "af_heart")
        self.assertEqual(result.voice_plan.runtime_constraints.fallback_order, ["kokoro", "piper"])
        self.assertFalse(result.fallback.used)

    def test_keeps_kokoro_as_primary_even_if_premium_env_is_present(self) -> None:
        os.environ["CORTAI_PREMIUM_TTS_PROVIDER"] = "elevenlabs"
        os.environ["CORTAI_PREMIUM_TTS_VOICE"] = "adam"
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror")

        self.assertEqual(result.voice_plan.provider, "kokoro")
        self.assertEqual(result.voice_plan.voice_id, "af_heart")
        self.assertFalse(result.fallback.used)
        self.assertEqual(result.fallback.reason, "")


if __name__ == "__main__":
    unittest.main()
