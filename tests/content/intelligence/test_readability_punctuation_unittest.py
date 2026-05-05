from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.tts_readability_tuner import TtsReadabilityTuner


def _semantic_signature(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


class ReadabilityPunctuationUnitTests(unittest.TestCase):
    def test_adds_functional_comma_only_for_long_linear_sentence(self) -> None:
        tuner = TtsReadabilityTuner()
        source = "The dispatcher kept listening to the hallway but the security camera still showed nothing there."

        tuned = tuner.tune(source)

        self.assertIn("hallway but,", tuned)
        self.assertEqual(_semantic_signature(source), _semantic_signature(tuned))

    def test_leaves_short_or_already_punctuated_text_unchanged(self) -> None:
        tuner = TtsReadabilityTuner()
        source = "The line went dead, but the recorder kept running."

        tuned = tuner.tune(source)

        self.assertEqual(source, tuned)


if __name__ == "__main__":
    unittest.main()
