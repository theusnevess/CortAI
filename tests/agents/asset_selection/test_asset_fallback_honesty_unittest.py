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
from app.creative.agents.asset_selection.fallback_honesty import AssetFallbackHonestyEvaluator
from app.creative.agents.asset_selection.models import AssetSelectionInput
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import AssetPlan, ScriptPlan, StrategyProfile, TrendProfile
from app.runtime.asset_selector import AssetSelector


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


def _catalog_path(category: str = "warning_display") -> str:
    selector = AssetSelector()
    for entry in selector._load_catalog():  # noqa: SLF001 - test fixture reads catalog metadata.
        if entry.category == category and selector._is_runtime_eligible_entry(entry=entry):  # noqa: SLF001
            return entry.path
    raise AssertionError(f"missing eligible path for {category}")


class AssetFallbackHonestyTests(unittest.TestCase):
    def setUp(self) -> None:
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()

    def test_asset_fallback_honesty_is_added_to_result_payload(self) -> None:
        result = AssetSelectionAgentService().select(_input())
        payload = result.to_dict()

        self.assertIn("asset_fallback_honesty", payload)
        self.assertEqual(
            result.asset_fallback_honesty["honesty_version"],
            "asset_fallback_honesty_v2_6",
        )
        json.dumps(payload)

    def test_no_fallback_case_is_explicit(self) -> None:
        result = AssetSelectionAgentService().select(_input())
        honesty = result.asset_fallback_honesty

        self.assertFalse(honesty["global_fallback_used"])
        self.assertEqual(honesty["global_fallback_mode"], "NONE")
        self.assertEqual(honesty["fallback_segments"], [])
        for segment in honesty["segment_fallbacks"].values():
            self.assertFalse(segment["fallback_used"])
            self.assertEqual(segment["fallback_mode"], "none")
            self.assertIn("ASSET_FALLBACK_NOT_USED", segment["reason_codes"])

    def test_global_safe_default_fallback_is_marked_as_weak_visual_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = AssetSelectionAgentService(
                background_service=BackgroundGeneratorService(local_assets_dir=Path(tmp_dir))
            )

            result = service.select(_input())
            honesty = result.asset_fallback_honesty

            self.assertTrue(result.fallback.used)
            self.assertTrue(honesty["global_fallback_used"])
            self.assertEqual(honesty["global_fallback_mode"], FallbackMode.SAFE_DEFAULT.value)
            self.assertEqual(honesty["global_fallback_reason"], "ASSET_SELECTION_FALLBACK")
            self.assertEqual(honesty["fallback_segments"], ["hook", "setup", "payoff"])
            self.assertEqual(honesty["safe_default_segments"], ["hook", "setup", "payoff"])
            self.assertFalse(honesty["fallback_evidence_is_strong"])
            for segment in honesty["segment_fallbacks"].values():
                self.assertTrue(segment["fallback_used"])
                self.assertTrue(segment["safe_default_used"])
                self.assertEqual(segment["semantic_match_strength"], "weak")
                self.assertEqual(segment["visual_evidence_strength"], "weak")
                self.assertIn("SAFE_DEFAULT_VISUAL_EVIDENCE_WEAK", segment["reason_codes"])

    def test_segment_safe_fallback_is_exposed_without_global_fallback(self) -> None:
        path = _catalog_path()
        honesty = AssetFallbackHonestyEvaluator().evaluate(
            asset_selection=AssetPlan(hook_asset=path),
            fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
            segment_fallback_trace={
                "hook": {
                    "primary_selector_returned_asset": False,
                    "safe_fallback_used": True,
                }
            },
            visual_alignment={
                "segment_alignments": {
                    "hook": {"alignment_level": "high", "alignment_score": 0.9}
                }
            },
            visual_truthfulness={
                "segment_truthfulness": {
                    "hook": {"risk_level": "low", "truthfulness_status": "supported"}
                }
            },
        ).to_dict()

        hook = honesty["segment_fallbacks"]["hook"]
        self.assertFalse(honesty["global_fallback_used"])
        self.assertEqual(honesty["fallback_segments"], ["hook"])
        self.assertTrue(hook["fallback_used"])
        self.assertFalse(hook["safe_default_used"])
        self.assertEqual(hook["fallback_mode"], "local_safe_fallback")
        self.assertEqual(hook["fallback_reason"], "SEGMENT_SAFE_FALLBACK_USED")
        self.assertEqual(hook["semantic_match_strength"], "weak")
        self.assertEqual(hook["visual_evidence_strength"], "weak")
        self.assertIn("SEGMENT_SAFE_FALLBACK_USED", hook["reason_codes"])

    def test_safe_default_is_never_reported_as_strong_semantic_match(self) -> None:
        honesty = AssetFallbackHonestyEvaluator().evaluate(
            asset_selection=AssetPlan(),
            fallback=FallbackDecision(
                used=True,
                mode=FallbackMode.SAFE_DEFAULT.value,
                reason="ASSET_SELECTION_FALLBACK",
            ),
        ).to_dict()

        self.assertFalse(honesty["fallback_evidence_is_strong"])
        for segment in honesty["segment_fallbacks"].values():
            self.assertEqual(segment["semantic_match_strength"], "weak")
            self.assertEqual(segment["visual_evidence_strength"], "weak")
            self.assertEqual(segment["evidence_status"], "fallback_weak")

    def test_fallback_reason_is_preserved(self) -> None:
        honesty = AssetFallbackHonestyEvaluator().evaluate(
            asset_selection=AssetPlan(),
            fallback=FallbackDecision(
                used=True,
                mode=FallbackMode.SAFE_DEFAULT.value,
                reason="CUSTOM_ASSET_FALLBACK_REASON",
            ),
        ).to_dict()

        self.assertEqual(honesty["global_fallback_reason"], "CUSTOM_ASSET_FALLBACK_REASON")
        self.assertEqual(
            honesty["segment_fallbacks"]["hook"]["fallback_reason"],
            "CUSTOM_ASSET_FALLBACK_REASON",
        )

    def test_fallback_honesty_is_deterministic_and_does_not_change_selection(self) -> None:
        first = AssetSelectionAgentService().select(_input())
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()
        second = AssetSelectionAgentService().select(_input())

        self.assertEqual(first.asset_selection.to_dict(), second.asset_selection.to_dict())
        self.assertEqual(first.asset_fallback_honesty, second.asset_fallback_honesty)

    def test_prior_asset_layers_remain_present(self) -> None:
        result = AssetSelectionAgentService().select(_input())
        payload = result.to_dict()

        self.assertIn("asset_context_governance", payload)
        self.assertIn("asset_source_governance", payload)
        self.assertIn("segment_visual_intent", payload)
        self.assertIn("visual_alignment", payload)
        self.assertIn("visual_truthfulness", payload)
        self.assertIn("asset_fallback_honesty", payload)

    def test_boundary_statement_preserves_selection_authority(self) -> None:
        honesty = AssetSelectionAgentService().select(_input()).asset_fallback_honesty

        self.assertEqual(
            honesty["boundary_statement"],
            "Asset fallback honesty is audit-only; fallback selection, ranking, and providers are unchanged.",
        )
        self.assertTrue(honesty["fallback_trace"]["selection_ranking_unchanged"])
        self.assertTrue(honesty["fallback_trace"]["fallback_behavior_unchanged"])
        self.assertFalse(honesty["fallback_trace"]["external_provider_added"])


if __name__ == "__main__":
    unittest.main()
