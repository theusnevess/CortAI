from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.script.service import ScriptAgentService
from app.content.script_gen.service import ScriptGenerationError


class _FailingGenerator:
    def generate(self, **_: object) -> str:
        raise ScriptGenerationError("boom")


class _FixedGenerator:
    def generate(self, **_: object) -> str:
        return (
            "Someone wrote on the mirror. "
            "Who left the warning? "
            "The door wouldn't open."
        )


class ScriptAgentPhase2Tests(unittest.TestCase):
    def test_generates_contextual_script_plan(self) -> None:
        service = ScriptAgentService(generator=_FixedGenerator())

        result = service.generate(account_id="acc_1", niche="horror", topic="mirror warning")

        self.assertEqual(result.script_plan.hook, "SOMEONE WROTE ON THE MIRROR")
        self.assertEqual(result.script_plan.setup, "WHO LEFT THE WARNING?")
        self.assertEqual(result.script_plan.payoff, "THE DOOR WOULDN'T OPEN")
        self.assertEqual(result.script_plan.generation_mode, "contextual")
        self.assertFalse(result.fallback.used)

    def test_falls_back_to_safe_default_when_generation_fails(self) -> None:
        service = ScriptAgentService(generator=_FailingGenerator())

        result = service.generate(account_id="acc_1", niche="horror", topic="sealed tunnel")

        self.assertTrue(result.fallback.used)
        self.assertEqual(result.fallback.reason, "script_generation_fallback_used")
        self.assertEqual(result.script_plan.generation_mode, "fallback")
        self.assertTrue(result.script_plan.hook)
        self.assertTrue(result.script_plan.setup)
        self.assertTrue(result.script_plan.payoff)


if __name__ == "__main__":
    unittest.main()
