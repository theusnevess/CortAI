from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.backgrounds.service import BackgroundGeneratorService
from app.creative.agents.asset_selection.models import AssetSelectionInput
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.contracts.creative_pack import ScriptPlan, StrategyProfile, TrendProfile
from app.runtime.asset_selector import AssetSelector


class AssetSelectionAgentPhase2Tests(unittest.TestCase):
    def setUp(self) -> None:
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()

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

    def test_intercom_warning_prefers_specialized_local_assets(self) -> None:
        service = AssetSelectionAgentService()
        result = service.select(
            AssetSelectionInput(
                niche="true_crime",
                topic="station intercom warning",
                strategy_profile=StrategyProfile(content_mode="standard"),
                trend_profile=TrendProfile(niche="true_crime", pacing="baseline", visual_style="investigation_dark"),
            )
        )

        self.assertTrue(Path(result.asset_selection.hook_asset).exists())
        self.assertTrue(Path(result.asset_selection.payoff_asset).exists())
        hook_entry = service.selector.lookup_catalog_entry(path=result.asset_selection.hook_asset)
        setup_entry = service.selector.lookup_catalog_entry(path=result.asset_selection.setup_asset)
        payoff_entry = service.selector.lookup_catalog_entry(path=result.asset_selection.payoff_asset)
        self.assertIsNotNone(hook_entry)
        self.assertIsNotNone(setup_entry)
        self.assertIsNotNone(payoff_entry)
        self.assertEqual(result.asset_selection.segments["hook"].background.source, hook_entry.source_type)
        self.assertEqual(result.asset_selection.segments["payoff"].background.source, payoff_entry.source_type)
        self.assertEqual(result.asset_selection.segments["hook"].category, hook_entry.category)
        self.assertEqual(result.asset_selection.segments["setup"].category, setup_entry.category)
        self.assertEqual(result.asset_selection.segments["payoff"].category, payoff_entry.category)

    def test_variation_policy_changes_asset_behavior_deterministically(self) -> None:
        service = AssetSelectionAgentService()
        common = {
            "niche": "horror",
            "topic": "sealed corridor warning",
            "trend_profile": TrendProfile(niche="horror", pacing="fast_first_3s", visual_style="dark_backgrounds"),
        }

        low = service.select(
            AssetSelectionInput(
                strategy_profile=StrategyProfile(content_mode="standard", variation_policy="low"),
                **common,
            )
        )
        medium = service.select(
            AssetSelectionInput(
                strategy_profile=StrategyProfile(content_mode="standard", variation_policy="medium"),
                **common,
            )
        )

        self.assertIn("strategy_variation_medium", medium.asset_selection.segments["payoff"].tags)
        self.assertIn("anti_repetition_bias", medium.asset_selection.segments["payoff"].tags)
        self.assertNotIn("anti_repetition_bias", low.asset_selection.segments["payoff"].tags)
        self.assertNotEqual(low.asset_selection.runtime_constraints.deterministic_seed, medium.asset_selection.runtime_constraints.deterministic_seed)
        self.assertEqual(
            low.asset_selection.segments["payoff"].category,
            service.selector.lookup_catalog_entry(path=low.asset_selection.payoff_asset).category,
        )
        self.assertEqual(
            medium.asset_selection.segments["payoff"].category,
            service.selector.lookup_catalog_entry(path=medium.asset_selection.payoff_asset).category,
        )

    def test_payoff_evidence_strength_biases_payoff_asset_category(self) -> None:
        service = AssetSelectionAgentService()
        result = service.select(
            AssetSelectionInput(
                niche="horror",
                topic="sealed corridor mirror warning",
                script_plan=ScriptPlan(
                    hook="A warning flickered in the sealed corridor.",
                    setup="The second signal pointed to a missing floor.",
                    payoff="The final whisper named Room 312 on the floorplan.",
                    generation_mode="test",
                ),
                strategy_profile=StrategyProfile(content_mode="standard", variation_policy="low"),
                trend_profile=TrendProfile(niche="horror", pacing="fast_first_3s", visual_style="dark_backgrounds"),
            )
        )

        self.assertIn("payoff_evidence_bias", result.asset_selection.segments["payoff"].tags)
        self.assertTrue(Path(result.asset_selection.payoff_asset).exists())
        selected_entry = service.selector.lookup_catalog_entry(path=result.asset_selection.payoff_asset)
        self.assertIsNotNone(selected_entry)
        self.assertEqual(result.asset_selection.segments["payoff"].category, selected_entry.category)

    def test_selected_asset_category_matches_realized_segment_category(self) -> None:
        service = AssetSelectionAgentService()
        result = service.select(
            AssetSelectionInput(
                niche="horror",
                topic="sealed corridor mirror warning",
                script_plan=ScriptPlan(
                    hook="A witness saw a sealed corridor mirror warning.",
                    setup="Their story turned stranger every time the lights failed.",
                    payoff="The final detail put someone breathing behind the door.",
                    generation_mode="test",
                ),
                strategy_profile=StrategyProfile(content_mode="standard", variation_policy="low"),
                trend_profile=TrendProfile(niche="horror", pacing="fast_first_3s", visual_style="dark_backgrounds"),
            )
        )

        selected_entry = service.selector.lookup_catalog_entry(path=result.asset_selection.payoff_asset)
        self.assertIsNotNone(selected_entry)
        self.assertEqual(result.asset_selection.segments["payoff"].category, selected_entry.category)

    def test_route_erasure_payoff_prefers_warning_display_evidence(self) -> None:
        service = AssetSelectionAgentService()
        result = service.select(
            AssetSelectionInput(
                niche="horror",
                topic="sealed corridor mirror warning",
                script_plan=ScriptPlan(
                    hook="Locals still talk about sealed corridor mirror warning.",
                    setup="The warning only makes sense after the second sound.",
                    payoff="By then the exit sign is pointing into the wall.",
                    generation_mode="test",
                ),
                strategy_profile=StrategyProfile(content_mode="standard", variation_policy="low"),
                trend_profile=TrendProfile(niche="horror", pacing="fast_first_3s", visual_style="dark_backgrounds"),
            )
        )

        self.assertIn("route_erasure_reveal", result.asset_selection.segments["payoff"].tags)
        selected_entry = service.selector.lookup_catalog_entry(path=result.asset_selection.payoff_asset)
        self.assertIsNotNone(selected_entry)
        self.assertEqual(result.asset_selection.segments["payoff"].category, selected_entry.category)
        self.assertEqual(result.asset_selection.segments["payoff"].category, "warning_display")

    def test_blocked_visual_payoff_category_reroutes_payoff_family(self) -> None:
        service = AssetSelectionAgentService()
        result = service.select(
            AssetSelectionInput(
                niche="horror",
                topic="sealed corridor mirror warning",
                script_plan=ScriptPlan(
                    hook="A witness saw the sealed corridor breathe.",
                    setup="Their story turned stranger every time the lights failed.",
                    payoff="The final detail named door 16, removed from the floorplan.",
                    generation_mode="test",
                ),
                strategy_profile=StrategyProfile(
                    content_mode="standard",
                    variation_policy="medium",
                    novelty_hints={
                        "blocked_visual_payoff_categories": ["map_blueprint"],
                        "preferred_alternative_payoff_families": ["warning_display", "sealed_access"],
                    },
                ),
                trend_profile=TrendProfile(niche="horror", pacing="fast_first_3s", visual_style="dark_backgrounds"),
            )
        )

        self.assertNotEqual(result.asset_selection.segments["payoff"].category, "map_blueprint")
        self.assertIn(result.asset_selection.segments["payoff"].category, {"warning_display", "sealed_access"})

    def test_selector_partitions_batch_diversity_by_case_pack(self) -> None:
        selector = AssetSelector()
        horror_case = selector.requested_case_pack(
            tags=["case_family_institutional_alert_system", "case_object_warning_panel"],
            query_text="station corridor warning panel",
        )
        documentary_case = selector.requested_case_pack(
            tags=["case_family_live_evidence_review", "case_object_marked_page"],
            query_text="archive receipt timestamp evidence desk",
        )

        self.assertNotEqual(
            selector._signature_batch_key(requested_case_pack=horror_case),  # noqa: SLF001
            selector._signature_batch_key(requested_case_pack=documentary_case),  # noqa: SLF001
        )
        self.assertNotEqual(
            selector._batch_key_from_case_pack(requested_case_pack=horror_case),  # noqa: SLF001
            selector._batch_key_from_case_pack(requested_case_pack=documentary_case),  # noqa: SLF001
        )


if __name__ == "__main__":
    unittest.main()
