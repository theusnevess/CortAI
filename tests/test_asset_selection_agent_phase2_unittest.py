from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.backgrounds.service import BackgroundGeneratorService
from app.creative.agents.asset_selection.models import AssetSelectionInput
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.contracts.creative_pack import StrategyProfile, TrendProfile


class AssetSelectionAgentPhase2Tests(unittest.TestCase):
    def test_selects_real_local_assets(self) -> None:
        service = AssetSelectionAgentService()
        result = service.select(
            AssetSelectionInput(
                niche="horror",
                topic="sealed tunnel",
                strategy_profile=StrategyProfile(content_mode="standard"),
                trend_profile=TrendProfile(niche="horror", pacing="fast_first_3s", visual_style="dark_backgrounds"),
            )
        )

        self.assertFalse(result.fallback.used)
        self.assertTrue(Path(result.asset_selection.hook_asset).exists())
        self.assertTrue(Path(result.asset_selection.setup_asset).exists())
        self.assertTrue(Path(result.asset_selection.payoff_asset).exists())
        self.assertEqual(result.asset_selection.visual_style, "dark_backgrounds")

    def test_falls_back_when_assets_directory_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            background_service = BackgroundGeneratorService(local_assets_dir=Path(tmp_dir))
            service = AssetSelectionAgentService(background_service=background_service)

            result = service.select(
                AssetSelectionInput(
                    niche="missing",
                    topic="missing",
                    strategy_profile=StrategyProfile(),
                    trend_profile=TrendProfile(),
                )
            )

            self.assertTrue(result.fallback.used)
            self.assertEqual(result.fallback.reason, "ASSET_SELECTION_FALLBACK")


if __name__ == "__main__":
    unittest.main()
