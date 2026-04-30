from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.backgrounds.service import BackgroundGeneratorService
from app.creative.agents.asset_selection.diversity_guard import AssetDiversityGuard
from app.creative.agents.asset_selection.models import AssetSelectionInput
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import AssetPlan, AssetSegmentPlan, ScriptPlan, StrategyProfile, TrendProfile
from app.runtime.asset_selector import AssetSelector, CatalogEntry


def _input() -> AssetSelectionInput:
    return AssetSelectionInput(
        niche="horror",
        topic="sealed corridor warning",
        script_plan=ScriptPlan(
            hook="A sealed corridor warning appeared after midnight.",
            setup="The second sign pointed toward a missing wing.",
            payoff="By then the exit sign is pointing into the wall.",
            generation_mode="test",
        ),
        strategy_profile=StrategyProfile(content_mode="standard", variation_policy="low"),
        trend_profile=TrendProfile(niche="horror", pacing="fast_first_3s", visual_style="dark_backgrounds"),
    )


def _entries(category: str, count: int = 1) -> list[CatalogEntry]:
    selector = AssetSelector()
    entries = [
        entry
        for entry in selector._load_catalog()  # noqa: SLF001 - test fixture reads catalog metadata.
        if entry.category == category and selector._is_runtime_eligible_entry(entry=entry)  # noqa: SLF001
    ]
    if len(entries) < count:
        raise AssertionError(f"expected at least {count} eligible entries for {category}, found {len(entries)}")
    return entries[:count]


class AssetDiversityGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()

    def test_asset_diversity_is_added_to_result_payload(self) -> None:
        result = AssetSelectionAgentService().select(_input())
        payload = result.to_dict()

        self.assertIn("asset_diversity", payload)
        self.assertEqual(result.asset_diversity["diversity_version"], "asset_diversity_guard_v2_6")
        json.dumps(payload)

    def test_repeated_asset_path_is_detected(self) -> None:
        entry = _entries("warning_display")[0]
        asset_plan = AssetPlan(
            hook_asset=entry.path,
            setup_asset=entry.path,
            payoff_asset=entry.path,
            segments={
                "hook": AssetSegmentPlan(category=entry.category),
                "setup": AssetSegmentPlan(category=entry.category),
                "payoff": AssetSegmentPlan(category=entry.category),
            },
        )

        diversity = AssetDiversityGuard().evaluate(
            selector=AssetSelector(),
            asset_selection=asset_plan,
            fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
        ).to_dict()

        self.assertTrue(diversity["repeated_asset_detected"])
        self.assertEqual(diversity["repeated_asset_paths"], [entry.path])
        self.assertEqual(diversity["visual_progression_level"], "weak")
        for segment in diversity["segment_diversity"].values():
            self.assertTrue(segment["repeated_asset"])
            self.assertIn("SEGMENT_REPEATED_ASSET", segment["reason_codes"])

    def test_repeated_category_is_detected_without_requiring_asset_repeat(self) -> None:
        first, second = _entries("warning_display", count=2)
        corridor = _entries("corridor")[0]
        asset_plan = AssetPlan(
            hook_asset=first.path,
            setup_asset=corridor.path,
            payoff_asset=second.path,
            segments={
                "hook": AssetSegmentPlan(category=first.category),
                "setup": AssetSegmentPlan(category=corridor.category),
                "payoff": AssetSegmentPlan(category=second.category),
            },
        )

        diversity = AssetDiversityGuard().evaluate(
            selector=AssetSelector(),
            asset_selection=asset_plan,
            fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
        ).to_dict()

        self.assertFalse(diversity["repeated_asset_detected"])
        self.assertTrue(diversity["repeated_category_detected"])
        self.assertEqual(diversity["repeated_categories"], ["warning_display"])
        self.assertEqual(diversity["visual_progression_level"], "moderate")
        self.assertTrue(diversity["visual_progression_valid"])

    def test_strong_progression_with_three_categories(self) -> None:
        warning = _entries("warning_display")[0]
        corridor = _entries("corridor")[0]
        document = _entries("document")[0]
        asset_plan = AssetPlan(
            hook_asset=warning.path,
            setup_asset=corridor.path,
            payoff_asset=document.path,
            segments={
                "hook": AssetSegmentPlan(category=warning.category),
                "setup": AssetSegmentPlan(category=corridor.category),
                "payoff": AssetSegmentPlan(category=document.category),
            },
        )

        diversity = AssetDiversityGuard().evaluate(
            selector=AssetSelector(),
            asset_selection=asset_plan,
            fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
        ).to_dict()

        self.assertFalse(diversity["repeated_asset_detected"])
        self.assertFalse(diversity["repeated_category_detected"])
        self.assertEqual(diversity["visual_progression_level"], "strong")
        self.assertTrue(diversity["visual_progression_valid"])
        self.assertIn("VISUAL_PROGRESSION_STRONG", diversity["reason_codes"])

    def test_missing_fallback_assets_limit_diversity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = AssetSelectionAgentService(
                background_service=BackgroundGeneratorService(local_assets_dir=Path(tmp_dir))
            )

            result = service.select(_input())
            diversity = result.asset_diversity

            self.assertTrue(result.fallback.used)
            self.assertFalse(diversity["diversity_complete"])
            self.assertEqual(diversity["visual_progression_level"], "none")
            self.assertFalse(diversity["visual_progression_valid"])
            self.assertIn("FALLBACK_LIMITS_DIVERSITY_CONFIDENCE", diversity["reason_codes"])
            for segment in diversity["segment_diversity"].values():
                self.assertEqual(segment["progression_contribution"], "missing_asset")

    def test_service_selection_remains_deterministic(self) -> None:
        first = AssetSelectionAgentService().select(_input())
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()
        second = AssetSelectionAgentService().select(_input())

        self.assertEqual(first.asset_selection.to_dict(), second.asset_selection.to_dict())
        self.assertEqual(first.asset_diversity, second.asset_diversity)

    def test_diversity_guard_does_not_add_randomness_or_change_fallback(self) -> None:
        diversity = AssetSelectionAgentService().select(_input()).asset_diversity

        self.assertFalse(diversity["diversity_trace"]["randomness_added"])
        self.assertTrue(diversity["diversity_trace"]["selection_ranking_unchanged"])
        self.assertTrue(diversity["diversity_trace"]["fallback_behavior_unchanged"])
        self.assertEqual(
            diversity["boundary_statement"],
            "Asset diversity is an audit signal only; it does not add randomness or change selected assets.",
        )

    def test_prior_asset_layers_remain_present(self) -> None:
        result = AssetSelectionAgentService().select(_input())
        payload = result.to_dict()

        self.assertIn("asset_context_governance", payload)
        self.assertIn("asset_source_governance", payload)
        self.assertIn("segment_visual_intent", payload)
        self.assertIn("visual_alignment", payload)
        self.assertIn("visual_truthfulness", payload)
        self.assertIn("asset_fallback_honesty", payload)
        self.assertIn("asset_diversity", payload)


if __name__ == "__main__":
    unittest.main()
