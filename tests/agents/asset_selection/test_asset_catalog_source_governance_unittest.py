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
from app.creative.agents.asset_selection.catalog_source_governance import AssetCatalogSourceGovernanceEvaluator
from app.creative.agents.asset_selection.models import AssetSelectionInput
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import AssetPlan, ScriptPlan, StrategyProfile, TrendProfile
from app.runtime.asset_selector import AssetSelector


def _input() -> AssetSelectionInput:
    return AssetSelectionInput(
        niche="horror",
        topic="sealed corridor warning",
        script_plan=ScriptPlan(
            hook="A sealed corridor warning appeared after midnight.",
            setup="The second sign pointed toward a missing wing.",
            payoff="The final exit sign pointed into the wall.",
            generation_mode="test",
        ),
        strategy_profile=StrategyProfile(content_mode="standard", variation_policy="low"),
        trend_profile=TrendProfile(niche="horror", pacing="fast_first_3s", visual_style="dark_backgrounds"),
    )


class AssetCatalogSourceGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()

    def test_source_governance_is_added_to_result_payload(self) -> None:
        result = AssetSelectionAgentService().select(_input())
        payload = result.to_dict()

        self.assertIn("asset_source_governance", payload)
        self.assertEqual(
            result.asset_source_governance["policy_version"],
            "local_catalog_only_v2_6",
        )
        json.dumps(payload)

    def test_catalog_availability_and_policy_are_explicit(self) -> None:
        governance = AssetSelectionAgentService().select(_input()).asset_source_governance

        self.assertTrue(governance["catalog_available"])
        self.assertGreater(governance["catalog_entry_count"], 0)
        self.assertGreater(governance["eligible_entry_count"], 0)
        self.assertEqual(governance["source_policy"]["policy"], "local_catalog_only_v2_6")
        self.assertFalse(governance["source_policy"]["external_collection_allowed"])
        self.assertFalse(governance["source_policy"]["ranking_change_allowed"])
        self.assertFalse(governance["source_policy"]["fallback_change_allowed"])

    def test_selected_sources_are_visible_and_runtime_eligible(self) -> None:
        result = AssetSelectionAgentService().select(_input())
        governance = result.asset_source_governance

        self.assertTrue(governance["policy_respected"])
        self.assertEqual(len(governance["selected_sources"]), 3)
        for source in governance["selected_sources"]:
            self.assertIn(source["segment"], {"hook", "setup", "payoff"})
            self.assertTrue(source["path"])
            self.assertEqual(source["source_class"], "local_catalog_asset")
            self.assertTrue(source["catalog_present"])
            self.assertTrue(source["eligible_for_runtime"])
            self.assertEqual(source["governance_status"], "accepted")
            self.assertEqual(source["reason_code"], "SELECTED_SOURCE_ACCEPTED_LOCAL_CATALOG")

    def test_ineligible_catalog_sources_are_summarized_without_affecting_selection(self) -> None:
        result = AssetSelectionAgentService().select(_input())
        governance = result.asset_source_governance

        self.assertTrue(result.asset_selection.hook_asset)
        self.assertTrue(governance["ineligible_sources"])
        reason_codes = {item["reason_code"] for item in governance["ineligible_sources"]}
        self.assertIn("SOURCE_REJECTED_LOCAL_CURATED_RUNTIME_DISABLED", reason_codes)
        self.assertIn(
            "CATALOG_CONTAINS_INELIGIBLE_LEGACY_OR_UNSUPPORTED_SOURCES",
            governance["coverage_limitations"],
        )

    def test_missing_local_asset_files_keep_existing_fallback_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = AssetSelectionAgentService(
                background_service=BackgroundGeneratorService(local_assets_dir=Path(tmp_dir))
            )

            result = service.select(_input())
            governance = result.asset_source_governance

            self.assertTrue(result.fallback.used)
            self.assertEqual(result.fallback.reason, "ASSET_SELECTION_FALLBACK")
            self.assertTrue(governance["fallback_sources"])
            self.assertIn("LOCAL_ASSET_FILES_NOT_AVAILABLE", governance["coverage_limitations"])
            self.assertIn("ASSET_SELECTION_FALLBACK_REPORTED", governance["coverage_limitations"])
            self.assertEqual(governance["source_status_distribution"].get("fallback"), 3)

    def test_unregistered_selected_source_is_rejected_by_policy(self) -> None:
        evaluator = AssetCatalogSourceGovernanceEvaluator()
        selector = AssetSelector()
        result = evaluator.evaluate(
            selector=selector,
            asset_selection=AssetPlan(
                hook_asset="assets/not-in-catalog/hook.jpg",
                setup_asset="assets/not-in-catalog/setup.jpg",
                payoff_asset="assets/not-in-catalog/payoff.jpg",
            ),
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
            local_assets_available=True,
        )

        payload = result.to_dict()
        self.assertFalse(payload["policy_respected"])
        self.assertEqual(payload["source_status_distribution"].get("rejected"), 3)
        self.assertEqual(payload["selected_sources"][0]["reason_code"], "SELECTED_SOURCE_NOT_IN_CATALOG")

    def test_cataloged_but_ineligible_selected_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            catalog_path = Path(tmp_dir) / "catalog.json"
            legacy_path = "assets/curated/room/legacy.jpg"
            catalog_path.write_text(
                json.dumps(
                    [
                        {
                            "path": legacy_path,
                            "source_type": "local_curated",
                            "category": "room",
                            "tags": ["room"],
                            "semantic_pattern_fit": [],
                            "entity_fit": [],
                            "phase1_legacy": True,
                            "eligible_for_runtime": False,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            result = AssetCatalogSourceGovernanceEvaluator().evaluate(
                selector=AssetSelector(catalog_path=catalog_path),
                asset_selection=AssetPlan(
                    hook_asset=legacy_path,
                    setup_asset=legacy_path,
                    payoff_asset=legacy_path,
                ),
                fallback=FallbackDecision(used=False, mode="NONE", reason=""),
                local_assets_available=True,
            ).to_dict()

        self.assertFalse(result["policy_respected"])
        self.assertEqual(result["selected_sources"][0]["reason_code"], "SOURCE_REJECTED_LOCAL_CURATED_RUNTIME_DISABLED")
        self.assertEqual(result["source_status_distribution"].get("rejected"), 3)

    def test_source_mix_is_deterministic_and_serializable(self) -> None:
        first = AssetSelectionAgentService().select(_input())
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()
        second = AssetSelectionAgentService().select(_input())

        self.assertEqual(first.asset_selection.to_dict(), second.asset_selection.to_dict())
        self.assertEqual(first.asset_source_governance, second.asset_source_governance)
        json.dumps(first.asset_source_governance)

    def test_source_governance_does_not_change_context_governance_or_fallback(self) -> None:
        result = AssetSelectionAgentService().select(_input())

        self.assertIn("asset_context_governance", result.to_dict())
        self.assertIn("asset_source_governance", result.to_dict())
        self.assertFalse(result.fallback.used)
        self.assertTrue(result.asset_context_governance["policy_respected"])
        self.assertTrue(result.asset_source_governance["policy_respected"])


if __name__ == "__main__":
    unittest.main()
