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
from app.creative.agents.asset_selection.visual_truthfulness import AssetVisualTruthfulnessEvaluator
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import (
    AssetDecisionContract,
    AssetPlan,
    AssetSegmentPlan,
    ScriptPlan,
    StrategyProfile,
    TrendProfile,
    VisualQuery,
)
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


def _segment_for_entry(entry: CatalogEntry) -> AssetSegmentPlan:
    return AssetSegmentPlan(
        category=entry.category,
        tags=list(entry.tags[:6]),
        decision_contract=AssetDecisionContract(
            entity=entry.entity_fit[0] if entry.entity_fit else entry.category,
            event=entry.semantic_pattern_fit[0] if entry.semantic_pattern_fit else entry.category,
            anomaly_type=entry.category,
            visibility_requirement=entry.category,
            photographability=entry.framing,
            justification="metadata supported test segment",
        ),
        visual_query=VisualQuery(
            subject=entry.category,
            state_or_event=entry.semantic_pattern_fit[0] if entry.semantic_pattern_fit else entry.category,
            environment=entry.family,
            framing=entry.framing,
            mood=entry.mood,
            search_query_real=" ".join([entry.category, entry.family, *entry.tags[:4]]),
        ),
    )


class AssetVisualTruthfulnessTests(unittest.TestCase):
    def setUp(self) -> None:
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()

    def test_visual_truthfulness_is_added_to_result_payload(self) -> None:
        result = AssetSelectionAgentService().select(_input())
        payload = result.to_dict()

        self.assertIn("visual_truthfulness", payload)
        self.assertEqual(result.visual_truthfulness["truthfulness_version"], "asset_visual_truthfulness_v2_6")
        json.dumps(payload)

    def test_supported_metadata_has_low_truthfulness_risk(self) -> None:
        entry = _eligible_entry(category="warning_display")
        asset_plan = AssetPlan(
            hook_asset=entry.path,
            segments={"hook": _segment_for_entry(entry)},
        )
        alignment = AssetVisualSemanticAlignmentEvaluator().evaluate(
            selector=AssetSelector(),
            asset_selection=asset_plan,
            selection_requests={
                "hook": {
                    "requested_category": entry.category,
                    "requested_tags": list(entry.tags[:6]),
                    "query_text": " ".join([entry.category, entry.family, *entry.tags[:4]]),
                }
            },
        ).to_dict()

        truthfulness = AssetVisualTruthfulnessEvaluator().evaluate(
            selector=AssetSelector(),
            asset_selection=asset_plan,
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
            visual_alignment=alignment,
        ).to_dict()

        hook = truthfulness["segment_truthfulness"]["hook"]
        self.assertEqual(hook["risk_level"], "low")
        self.assertEqual(hook["truthfulness_status"], "supported")
        self.assertTrue(hook["visually_supported"])
        self.assertIn("VISUAL_TRUTHFULNESS_METADATA_SUPPORTED", hook["reason_codes"])

    def test_pretty_but_semantically_weak_asset_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            catalog_path = Path(tmp_dir) / "catalog.json"
            path = "assets/imports/pexels/generic/pretty.jpg"
            catalog_path.write_text(
                json.dumps(
                    [
                        {
                            "path": path,
                            "source_type": "pexels",
                            "category": "room",
                            "subtype": "pretty_room",
                            "family": "generic_room",
                            "framing": "wide",
                            "tags": ["beautiful", "room", "ambient"],
                            "mood": "neutral",
                            "semantic_pattern_fit": [],
                            "entity_fit": [],
                            "hook_strength_score": 0.9,
                            "payoff_strength_score": 0.9,
                            "setup_specificity_score": 0.5,
                            "realism_score": 0.98,
                            "usage_count": 0,
                            "freshness_score": 1.0,
                            "resolution": [1080, 1920],
                            "strength": 0.95,
                            "genericity": 0.1,
                            "eligible_for_runtime": True,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            selector = AssetSelector(catalog_path=catalog_path)
            asset_plan = AssetPlan(
                hook_asset=path,
                segments={
                    "hook": AssetSegmentPlan(
                        category="warning_display",
                        tags=["warning", "intercom"],
                        decision_contract=AssetDecisionContract(entity="intercom", event="warning"),
                        visual_query=VisualQuery(subject="intercom", state_or_event="warning signal", search_query_real="intercom warning panel"),
                    )
                },
            )
            alignment = AssetVisualSemanticAlignmentEvaluator().evaluate(
                selector=selector,
                asset_selection=asset_plan,
                selection_requests={
                    "hook": {
                        "requested_category": "warning_display",
                        "requested_tags": ["warning", "intercom"],
                        "query_text": "intercom warning panel",
                    }
                },
            ).to_dict()

            truthfulness = AssetVisualTruthfulnessEvaluator().evaluate(
                selector=selector,
                asset_selection=asset_plan,
                fallback=FallbackDecision(used=False, mode="NONE", reason=""),
                visual_alignment=alignment,
            ).to_dict()

        hook = truthfulness["segment_truthfulness"]["hook"]
        self.assertTrue(hook["generic_asset_risk"] or "PRETTY_BUT_SEMANTICALLY_WEAK_ASSET" in hook["reason_codes"])
        self.assertIn("PRETTY_BUT_SEMANTICALLY_WEAK_ASSET", hook["reason_codes"])
        self.assertEqual(hook["risk_level"], "high")

    def test_wrong_category_for_payoff_is_high_risk(self) -> None:
        entry = _eligible_entry(category="warning_display")
        asset_plan = AssetPlan(
            payoff_asset=entry.path,
            segments={
                "payoff": AssetSegmentPlan(
                    category=entry.category,
                    tags=list(entry.tags[:4]),
                    decision_contract=AssetDecisionContract(entity="map", event="route_erasure"),
                    visual_query=VisualQuery(subject="map blueprint", state_or_event="route erased", search_query_real="map blueprint route erased"),
                )
            },
        )
        alignment = AssetVisualSemanticAlignmentEvaluator().evaluate(
            selector=AssetSelector(),
            asset_selection=asset_plan,
            selection_requests={
                "payoff": {
                    "requested_category": "map_blueprint",
                    "requested_tags": ["map", "blueprint", "route"],
                    "query_text": "map blueprint route erased",
                }
            },
        ).to_dict()

        truthfulness = AssetVisualTruthfulnessEvaluator().evaluate(
            selector=AssetSelector(),
            asset_selection=asset_plan,
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
            visual_alignment=alignment,
        ).to_dict()

        payoff = truthfulness["segment_truthfulness"]["payoff"]
        self.assertTrue(payoff["wrong_category_risk"])
        self.assertEqual(payoff["risk_level"], "high")
        self.assertIn("WRONG_CATEGORY_FOR_SEGMENT_ROLE", payoff["reason_codes"])
        self.assertIn("payoff", truthfulness["high_risk_segments"])

    def test_unsupported_visual_claims_are_visible(self) -> None:
        entry = _eligible_entry(category="corridor")
        asset_plan = AssetPlan(
            setup_asset=entry.path,
            segments={
                "setup": AssetSegmentPlan(
                    category=entry.category,
                    tags=list(entry.tags[:4]),
                    decision_contract=AssetDecisionContract(entity="dragon", event="spaceship_launch"),
                    visual_query=VisualQuery(subject="dragon spaceship", state_or_event="spaceship launch", search_query_real="dragon spaceship launch"),
                )
            },
        )
        alignment = AssetVisualSemanticAlignmentEvaluator().evaluate(
            selector=AssetSelector(),
            asset_selection=asset_plan,
            selection_requests={
                "setup": {
                    "requested_category": entry.category,
                    "requested_tags": list(entry.tags[:4]),
                    "query_text": entry.category,
                }
            },
        ).to_dict()

        truthfulness = AssetVisualTruthfulnessEvaluator().evaluate(
            selector=AssetSelector(),
            asset_selection=asset_plan,
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
            visual_alignment=alignment,
        ).to_dict()

        setup = truthfulness["segment_truthfulness"]["setup"]
        self.assertTrue(setup["unsupported_visual_claims"])
        self.assertIn("UNSUPPORTED_VISUAL_CLAIMS", setup["reason_codes"])
        self.assertIn("setup", truthfulness["unsupported_claim_segments"])

    def test_fallback_generic_default_is_high_risk_but_does_not_change_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = AssetSelectionAgentService(
                background_service=BackgroundGeneratorService(local_assets_dir=Path(tmp_dir))
            )

            result = service.select(_input())
            truthfulness = result.visual_truthfulness

            self.assertTrue(result.fallback.used)
            self.assertEqual(result.fallback.reason, "ASSET_SELECTION_FALLBACK")
            self.assertEqual(truthfulness["overall_risk_level"], "high")
            self.assertEqual(truthfulness["high_risk_segments"], ["hook", "setup", "payoff"])
            for segment in truthfulness["segment_truthfulness"].values():
                self.assertTrue(segment["fallback_or_default_risk"])
                self.assertIn("FALLBACK_OR_DEFAULT_VISUAL_RISK", segment["reason_codes"])

    def test_visual_truthfulness_is_deterministic_and_preserves_selection(self) -> None:
        first = AssetSelectionAgentService().select(_input())
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()
        second = AssetSelectionAgentService().select(_input())

        self.assertEqual(first.asset_selection.to_dict(), second.asset_selection.to_dict())
        self.assertEqual(first.visual_truthfulness, second.visual_truthfulness)
        self.assertFalse(first.fallback.used)

    def test_visual_truthfulness_is_not_qc_or_publishability(self) -> None:
        truthfulness = AssetSelectionAgentService().select(_input()).visual_truthfulness
        trace = truthfulness["truthfulness_trace"]

        self.assertTrue(trace["metadata_only"])
        self.assertFalse(trace["image_pixels_inspected"])
        self.assertFalse(trace["ml_used"])
        self.assertFalse(trace["publishability_decision_made"])
        self.assertTrue(trace["selection_ranking_unchanged"])
        self.assertTrue(trace["fallback_behavior_unchanged"])
        self.assertEqual(
            truthfulness["boundary_statement"],
            "Visual truthfulness is an audit signal only; QC remains responsible for final product quality and publishability.",
        )

    def test_prior_asset_audit_layers_remain_present(self) -> None:
        result = AssetSelectionAgentService().select(_input())
        payload = result.to_dict()

        self.assertIn("asset_context_governance", payload)
        self.assertIn("asset_source_governance", payload)
        self.assertIn("segment_visual_intent", payload)
        self.assertIn("visual_alignment", payload)
        self.assertIn("visual_truthfulness", payload)


if __name__ == "__main__":
    unittest.main()
