from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.contracts.creative_pack import AssetPlan


class HookVisualAlignmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = dict(os.environ)
        self.service = AssetSelectionAgentService()
        self.plan = AssetPlan(
            hook_asset="assets/backgrounds/horror/horror_02.jpg",
            setup_asset="assets/backgrounds/horror/horror_03.jpg",
            payoff_asset="assets/backgrounds/horror/horror_04.jpg",
            visual_style="dark_backgrounds",
            motion_profile="subtle_push_in",
        )

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_flag_off_keeps_current_hook_asset(self) -> None:
        os.environ["CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT"] = "0"

        result = self.service.align_first_frame(
            niche="investigative",
            topic="night watch log with future date",
            hook_text="THE NIGHT WATCH LOG CONTAINED A DATE FROM THE FUTURE",
            asset_plan=self.plan,
        )

        self.assertEqual(result.hook_asset, self.plan.hook_asset)
        self.assertEqual(result.setup_asset, self.plan.setup_asset)
        self.assertEqual(result.payoff_asset, self.plan.payoff_asset)

    def test_inferential_hook_maps_to_document_anchor(self) -> None:
        os.environ["CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT"] = "1"
        os.environ["CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT_MODE"] = "baseline"

        result = self.service.align_first_frame(
            niche="investigative",
            topic="night watch log with future date",
            hook_text="THE NIGHT WATCH LOG CONTAINED A DATE FROM THE FUTURE",
            asset_plan=self.plan,
        )

        self.assertEqual(Path(result.hook_asset), Path("assets/backgrounds/conspiracy/conspiracy_02.jpg"))
        self.assertEqual(result.setup_asset, self.plan.setup_asset)
        self.assertEqual(result.payoff_asset, self.plan.payoff_asset)

    def test_experiential_hook_maps_to_non_generic_anchor(self) -> None:
        os.environ["CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT"] = "1"
        os.environ["CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT_MODE"] = "baseline"

        result = self.service.align_first_frame(
            niche="horror",
            topic="camera blackout in sector 4",
            hook_text="THE CAMERA WENT DARK IN SECTOR 4",
            asset_plan=self.plan,
        )

        self.assertEqual(Path(result.hook_asset), Path("assets/backgrounds/horror/horror_03.jpg"))
        self.assertEqual(result.setup_asset, self.plan.setup_asset)
        self.assertEqual(result.payoff_asset, self.plan.payoff_asset)

    def test_refined_experiential_maps_map_corridor_to_document_like_anchor(self) -> None:
        os.environ["CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT"] = "1"
        os.environ["CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT_MODE"] = "refined_experiential"

        result = self.service.align_first_frame(
            niche="dark_storytelling",
            topic="bunker map missing corridor",
            hook_text="THE BUNKER MAP WAS MISSING A CORRIDOR",
            asset_plan=self.plan,
        )

        self.assertEqual(Path(result.hook_asset), Path("assets/backgrounds/conspiracy/conspiracy_02.jpg"))

    def test_refined_experiential_maps_sealed_access_to_barrier_asset(self) -> None:
        os.environ["CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT"] = "1"
        os.environ["CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT_MODE"] = "refined_experiential"

        result = self.service.align_first_frame(
            niche="dark_storytelling",
            topic="hospital wing sealed after 3 am",
            hook_text="AFTER 3 AM THE HOSPITAL WING WAS SEALED",
            asset_plan=self.plan,
        )

        self.assertEqual(Path(result.hook_asset), Path("assets/backgrounds/horror/horror_04.jpg"))


if __name__ == "__main__":
    unittest.main()
