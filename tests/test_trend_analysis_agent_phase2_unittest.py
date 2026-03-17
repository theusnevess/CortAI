from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.trend_analysis.models import TrendAnalysisInput
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService


class TrendAnalysisAgentPhase2Tests(unittest.TestCase):
    def test_loads_manual_curated_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_dir = Path(tmp_dir)
            (trends_dir / "horror.json").write_text(
                json.dumps(
                    {
                        "niche": "horror",
                        "dominant_hooks": ["question", "shock_statement"],
                        "avg_duration": "35-60",
                        "pacing": "fast_first_3s",
                        "visual_style": "dark_backgrounds",
                        "text_style": "large_caption_focus",
                    }
                ),
                encoding="utf-8",
            )
            service = TrendAnalysisAgentService(trends_dir=trends_dir)

            result = service.load(TrendAnalysisInput(niche="horror"))

            self.assertFalse(result.fallback.used)
            self.assertEqual(result.trend_profile.niche, "horror")
            self.assertEqual(result.trend_profile.pacing, "fast_first_3s")
            self.assertEqual(result.trend_profile.visual_style, "dark_backgrounds")

    def test_falls_back_when_profile_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = TrendAnalysisAgentService(trends_dir=Path(tmp_dir))

            result = service.load(TrendAnalysisInput(niche="history"))

            self.assertTrue(result.fallback.used)
            self.assertEqual(result.fallback.reason, "TREND_PROFILE_FALLBACK")
            self.assertEqual(result.trend_profile.niche, "default")


if __name__ == "__main__":
    unittest.main()
