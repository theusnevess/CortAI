from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.voice.interpreter import VoiceInterpreter
from app.creative.contracts.creative_pack import ScriptPlan, StrategyProfile


class VoiceInterpreterPhase25Tests(unittest.TestCase):
    def test_interpreter_is_deterministic_and_segment_aware(self) -> None:
        interpreter = VoiceInterpreter()
        script_plan = ScriptPlan(
            hook="Evidence Room 314 sealed abruptly.",
            setup="Security logs showed no breach attempts.",
            payoff="Tape recorder found with Detective James' voice.",
            generation_mode="groq_structured",
        )
        strategy = StrategyProfile(content_mode="conservative", target_duration_range="8-10s")

        first = interpreter.interpret(niche="horror", script_plan=script_plan, strategy_profile=strategy)
        second = interpreter.interpret(niche="horror", script_plan=script_plan, strategy_profile=strategy)

        self.assertEqual(first, second)
        self.assertEqual(first.style, "ominous_minimal")
        self.assertEqual(set(first.segments), {"hook", "setup", "payoff"})
        self.assertGreater(first.segments["hook"].pause_after_ms, first.segments["setup"].pause_after_ms)
        self.assertGreater(first.segments["payoff"].pause_before_ms, 0)
        self.assertEqual(first.segments["hook"].emphasis, "high")


if __name__ == "__main__":
    unittest.main()
