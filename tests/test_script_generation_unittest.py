from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.script_gen.service import LocalScriptGeneratorService


class ScriptGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = LocalScriptGeneratorService()

    def test_normalize_script_removes_unbalanced_quotes(self) -> None:
        raw = 'Then I found a key under a floorboard with a note: "Welcome Home.'
        normalized = self.service._normalize_script(raw)
        self.assertNotIn('"', normalized)
        self.assertTrue(normalized.endswith("."))

    def test_normalize_script_limits_to_three_sentences(self) -> None:
        raw = "One. Two. Three. Four."
        normalized = self.service._normalize_script(raw)
        self.assertEqual(len([s for s in normalized.split('.') if s.strip()]), 3)

    def test_normalize_script_removes_labels(self) -> None:
        raw = "HOOK: The building looked empty. SETUP: But the lights kept moving. PAYOFF: Nobody could explain it."
        normalized = self.service._normalize_script(raw)
        self.assertNotIn("HOOK:", normalized)
        self.assertNotIn("SETUP:", normalized)
        self.assertNotIn("PAYOFF:", normalized)


if __name__ == "__main__":
    unittest.main()
