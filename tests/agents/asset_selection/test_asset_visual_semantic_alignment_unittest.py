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
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.agents.asset_selection.visual_semantic_alignment import AssetVisualSemanticAlignmentEvaluator
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


def _eligible_entry(*, category: str = "warning_display") -> CatalogEntry:
    selector = AssetSelector()
    for entry in selector._load_catalog():  # noqa: SLF001 - test fixture reads catalog metadata.
        if entry.category == category and selector._is_runtime_eligible_entry(entry=entry):  # noqa: SLF001
            return entry
    raise AssertionError(f"missing eligible catalog entry for {category}")


class AssetVisualSemanticAlignmentTests(unittest.TestCase):
    def setUp(self) -> None:
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()

    def test_visual_alignment_is_added_to_result_payload(self) -> None:
        result = AssetSelectionAgentService().select(_input())
        payload = result.to_dict()

        self.assertIn("visual_alignment", payload)
        self.assertEqual(result.visual_alignment["alignment_version"], "asset_visual_semantic_alignment_v2_6")
        json.dumps(payload)

    def test_payoff_requested_category_matches_selected_category_when_evidence_is_specific(self) -> None:
        alignment = AssetSelectionAgentService().select(_input()).visual_alignment
        payoff = alignment["segment_alignments"]["payoff"]

        self.assertEqual(payoff["requested_category"], "warning_display")
        self.assertEqual(payoff["selected_category"], "warning_display")
        self.assertTrue(payoff["category_match"])
        self.assertFalse(payoff["mismatch_detected"])
        self.assertIn("CATEGORY_MATCH", payoff["reason_codes"])

    def test_alignment_exposes_tag_and_query_overlap(self) -> None:
        entry = _eligible_entry(category="warning_display")
        tags = list(entry.tags[:3])
        result = AssetVisualSemanticAlignmentEvaluator().evaluate(
            selector=AssetSelector(),
            asset_selection=AssetPlan(
                hook_asset=entry.path,
                segments={"hook": AssetSegmentPlan(category=entry.category, tags=tags)},
            ),
            selection_requests={
                "hook": {
                    "requested_category": entry.category,
                    "requested_tags": tags,
                    "query_text": f"{entry.category} {' '.join(tags)}",
                }
            },
        ).to_dict()

        hook = result["segment_alignments"]["hook"]
        self.assertGreater(hook["tag_overlap_count"], 0)
        self.assertGreater(hook["query_overlap_count"], 0)
        self.assertGreaterEqual(hook["alignment_score"], 0.7)

    def test_category_mismatch_is_explicit_without_changing_selection(self) -> None:
        entry = _eligible_entry(category="warning_display")
        result = AssetVisualSemanticAlignmentEvaluator().evaluate(
            selector=AssetSelector(),
            asset_selection=AssetPlan(
                hook_asset=entry.path,
                segments={"hook": AssetSegmentPlan(category=entry.category, tags=list(entry.tags[:3]))},
            ),
            selection_requests={
                "hook": {
                    "requested_category": "map_blueprint",
                    "requested_tags": ["map", "blueprint", "route"],
                    "query_text": "map blueprint route corridor",
                }
            },
        ).to_dict()

        hook = result["segment_alignments"]["hook"]
        self.assertEqual(hook["selected_asset_path"], entry.path)
        self.assertEqual(hook["requested_category"], "map_blueprint")
        self.assertEqual(hook["selected_category"], "warning_display")
        self.assertTrue(hook["mismatch_detected"])
        self.assertIn(hook["mismatch_level"], {"medium", "high"})
        self.assertIn("CATEGORY_MISMATCH", hook["reason_codes"])

    def test_unregistered_selected_asset_has_unknown_alignment(self) -> None:
        result = AssetVisualSemanticAlignmentEvaluator().evaluate(
            selector=AssetSelector(),
            asset_selection=AssetPlan(
                hook_asset="assets/not-in-catalog/hook.jpg",
                segments={"hook": AssetSegmentPlan(category="warning_display", tags=["warning"])},
            ),
            selection_requests={
                "hook": {
                    "requested_category": "warning_display",
                    "requested_tags": ["warning"],
                    "query_text": "warning panel",
                }
            },
        ).to_dict()

        hook = result["segment_alignments"]["hook"]
        self.assertEqual(hook["alignment_level"], "unknown")
        self.assertIn("SELECTED_ASSET_METADATA_MISSING", hook["reason_codes"])
        self.assertIn("hook", result["missing_metadata_segments"])

    def test_fallback_without_selected_paths_is_visible_as_missing_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = AssetSelectionAgentService(
                background_service=BackgroundGeneratorService(local_assets_dir=Path(tmp_dir))
            )

            result = service.select(_input())
            alignment = result.visual_alignment

            self.assertTrue(result.fallback.used)
            self.assertFalse(alignment["alignment_complete"])
            self.assertEqual(alignment["missing_metadata_segments"], ["hook", "setup", "payoff"])
            for segment in alignment["segment_alignments"].values():
                self.assertEqual(segment["alignment_level"], "unknown")
                self.assertIn("SELECTED_ASSET_PATH_MISSING", segment["reason_codes"])

    def test_visual_alignment_is_deterministic_and_preserves_selection(self) -> None:
        first = AssetSelectionAgentService().select(_input())
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()
        second = AssetSelectionAgentService().select(_input())

        self.assertEqual(first.asset_selection.to_dict(), second.asset_selection.to_dict())
        self.assertEqual(first.visual_alignment, second.visual_alignment)
        self.assertFalse(first.fallback.used)

    def test_visual_alignment_is_metadata_only_and_read_only(self) -> None:
        alignment = AssetSelectionAgentService().select(_input()).visual_alignment
        trace = alignment["alignment_trace"]

        self.assertFalse(trace["image_analysis_used"])
        self.assertFalse(trace["ml_used"])
        self.assertTrue(trace["read_only"])
        self.assertTrue(trace["selection_ranking_unchanged"])
        self.assertTrue(trace["fallback_behavior_unchanged"])
        self.assertEqual(
            alignment["boundary_statement"],
            "Visual semantic alignment is metadata-only; it does not inspect images, change ranking, or make QC decisions.",
        )

    def test_prior_governance_layers_remain_present(self) -> None:
        result = AssetSelectionAgentService().select(_input())
        payload = result.to_dict()

        self.assertIn("asset_context_governance", payload)
        self.assertIn("asset_source_governance", payload)
        self.assertIn("segment_visual_intent", payload)
        self.assertIn("visual_alignment", payload)


if __name__ == "__main__":
    unittest.main()
