from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.voice.service import VoiceAgentService
from app.creative.contracts.creative_pack import ScriptPlan, StrategyProfile


class VoiceAgentServicePhase25Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_generates_operational_voice_plan(self) -> None:
        service = VoiceAgentService()

        result = service.resolve(
            account_id="acc_1",
            niche="true_crime",
            script_plan=ScriptPlan(
                hook="What happened at 3:04 AM?",
                setup="Dispatcher's frantic voice escalates.",
                payoff="Officer Johnson's final transmission.",
                generation_mode="groq_structured",
            ),
            strategy_profile=StrategyProfile(content_mode="standard"),
        )

        self.assertEqual(result.voice_plan.provider, "kokoro")
        self.assertEqual(result.voice_plan.voice_id, "af_heart")
        self.assertEqual(result.voice_plan.style, "investigative")
        self.assertIn("hook", result.voice_plan.segments)
        self.assertIn("setup", result.voice_plan.segments)
        self.assertIn("payoff", result.voice_plan.segments)
        self.assertEqual(result.voice_plan.runtime_constraints.fallback_order, ["kokoro", "piper"])
        self.assertFalse(result.fallback.used)

    def test_ignores_premium_env_and_keeps_kokoro_operational_path(self) -> None:
        os.environ["CORTAI_PREMIUM_TTS_PROVIDER"] = "elevenlabs"
        os.environ["CORTAI_PREMIUM_TTS_VOICE"] = "adam"
        service = VoiceAgentService()

        result = service.resolve(
            account_id="acc_1",
            niche="horror",
            script_plan=ScriptPlan(hook="h", setup="s", payoff="p", generation_mode="structured"),
        )

        self.assertEqual(result.voice_plan.provider, "kokoro")
        self.assertEqual(result.voice_plan.voice_id, "af_heart")
        self.assertIn("piper", result.voice_plan.runtime_constraints.fallback_order)
        self.assertFalse(result.fallback.used)


if __name__ == "__main__":
    unittest.main()
