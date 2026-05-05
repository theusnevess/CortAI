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
from app.creative.agents.asset_selection.models import AssetSelectionInput
from app.creative.agents.asset_selection.segment_visual_intent import AssetSegmentVisualIntentMapper
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.contracts.creative_pack import AssetPlan, AssetSegmentPlan, ScriptPlan, StrategyProfile, TrendProfile
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


class AssetSegmentVisualIntentTests(unittest.TestCase):
    def setUp(self) -> None:
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()

    def test_segment_visual_intent_is_added_to_result_payload(self) -> None:
        result = AssetSelectionAgentService().select(_input())
        payload = result.to_dict()

        self.assertIn("segment_visual_intent", payload)
        self.assertEqual(
            result.segment_visual_intent["mapping_version"],
            "asset_segment_visual_intent_v2_6",
        )
        json.dumps(payload)

    def test_hook_setup_payoff_roles_are_mapped(self) -> None:
        intent = AssetSelectionAgentService().select(_input()).segment_visual_intent
        segments = intent["segments"]

        self.assertEqual(segments["hook"]["narrative_role"], "hook")
        self.assertEqual(segments["hook"]["visual_role"], "attention_anchor")
        self.assertEqual(segments["setup"]["visual_role"], "context_bridge")
        self.assertEqual(segments["payoff"]["visual_role"], "reveal_evidence")

    def test_requested_category_tags_and_rationale_are_exposed(self) -> None:
        intent = AssetSelectionAgentService().select(_input()).segment_visual_intent

        for segment_name in ("hook", "setup", "payoff"):
            segment_intent = intent["segments"][segment_name]
            self.assertTrue(segment_intent["requested_category"])
            self.assertTrue(segment_intent["requested_tags"])
            self.assertTrue(segment_intent["intent_complete"])
            self.assertTrue(segment_intent["rationale"])
            self.assertIn("SEGMENT_VISUAL_INTENT_COMPLETE", segment_intent["reason_codes"])

    def test_intent_mapping_uses_existing_asset_plan_without_changing_selection(self) -> None:
        first = AssetSelectionAgentService().select(_input())
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()
        second = AssetSelectionAgentService().select(_input())

        self.assertEqual(first.asset_selection.to_dict(), second.asset_selection.to_dict())
        self.assertEqual(first.segment_visual_intent, second.segment_visual_intent)
        self.assertFalse(first.fallback.used)

    def test_missing_local_assets_produce_incomplete_intent_without_changing_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = AssetSelectionAgentService(
                background_service=BackgroundGeneratorService(local_assets_dir=Path(tmp_dir))
            )

            result = service.select(_input())
            intent = result.segment_visual_intent

            self.assertTrue(result.fallback.used)
            self.assertFalse(intent["intent_complete"])
            self.assertEqual(intent["missing_segments"], ["hook", "setup", "payoff"])
            for segment_intent in intent["segments"].values():
                self.assertFalse(segment_intent["intent_complete"])
                self.assertIn("SEGMENT_PLAN_MISSING", segment_intent["reason_codes"])

    def test_empty_segment_intent_is_degraded_not_fabricated(self) -> None:
        mapping = AssetSegmentVisualIntentMapper().map(
            asset_selection=AssetPlan(
                hook_asset="assets/example.jpg",
                segments={"hook": AssetSegmentPlan()},
            )
        ).to_dict()

        hook = mapping["segments"]["hook"]
        self.assertFalse(hook["intent_complete"])
        self.assertEqual(hook["requested_category"], "")
        self.assertEqual(hook["requested_tags"], [])
        self.assertIn("REQUESTED_CATEGORY_MISSING", hook["reason_codes"])
        self.assertIn("REQUESTED_TAGS_MISSING", hook["reason_codes"])
        self.assertIn("visual_query", hook["degraded_fields"])

    def test_boundary_statement_is_advisory_and_not_qc_or_strategy(self) -> None:
        intent = AssetSelectionAgentService().select(_input()).segment_visual_intent

        self.assertEqual(
            intent["boundary_statement"],
            "Asset Selection explains visual intent only; it does not create Strategy, QC, or Publisher authority.",
        )

    def test_existing_context_and_source_governance_remain_present(self) -> None:
        result = AssetSelectionAgentService().select(_input())
        payload = result.to_dict()

        self.assertIn("asset_context_governance", payload)
        self.assertIn("asset_source_governance", payload)
        self.assertIn("segment_visual_intent", payload)
        self.assertTrue(result.asset_context_governance["policy_respected"])
        self.assertTrue(result.asset_source_governance["policy_respected"])


if __name__ == "__main__":
    unittest.main()
