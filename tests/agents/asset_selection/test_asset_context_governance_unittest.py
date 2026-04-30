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
from app.creative.contracts.creative_pack import ScriptPlan, StrategyProfile, TrendProfile
from app.runtime.asset_selector import AssetSelector


def _input(
    *,
    script_plan: ScriptPlan | None = None,
    trend_profile: TrendProfile | None = None,
    strategy_profile: StrategyProfile | None = None,
    niche: str = "horror",
    topic: str = "sealed corridor warning",
) -> AssetSelectionInput:
    return AssetSelectionInput(
        niche=niche,
        topic=topic,
        script_plan=script_plan
        if script_plan is not None
        else ScriptPlan(
            hook="A sealed corridor warning appeared after midnight.",
            setup="The second sign pointed toward a missing wing.",
            payoff="The final exit sign pointed into the wall.",
            generation_mode="test",
        ),
        strategy_profile=strategy_profile or StrategyProfile(content_mode="standard", variation_policy="low"),
        trend_profile=trend_profile
        or TrendProfile(niche=niche, pacing="fast_first_3s", visual_style="dark_backgrounds"),
    )


def _signal(governance: dict[str, object], context_key: str) -> dict[str, object]:
    for item in governance["context_signals"]:
        if item["context_key"] == context_key:
            return item
    raise AssertionError(f"missing context signal {context_key}")


class AssetContextGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()

    def test_context_governance_is_added_without_changing_asset_selection_contract(self) -> None:
        service = AssetSelectionAgentService()

        result = service.select(_input())
        payload = result.to_dict()
        governance = result.asset_context_governance

        self.assertIn("asset_selection", payload)
        self.assertIn("fallback", payload)
        self.assertIn("asset_context_governance", payload)
        self.assertEqual(governance["governance_version"], "asset_context_governance_v2_6")
        self.assertFalse(result.fallback.used)
        self.assertTrue(Path(result.asset_selection.hook_asset).exists())
        self.assertTrue(Path(result.asset_selection.setup_asset).exists())
        self.assertTrue(Path(result.asset_selection.payoff_asset).exists())
        json.dumps(payload)

    def test_available_context_is_mapped_as_used_for_normal_selection(self) -> None:
        service = AssetSelectionAgentService()

        governance = service.select(_input()).asset_context_governance

        for context_key in (
            "script_context",
            "strategy_context",
            "trend_context",
            "topic_context",
            "niche_context",
            "local_catalog_context",
        ):
            self.assertIn(context_key, governance["available_context"])
            self.assertIn(context_key, governance["used_context"])
            self.assertEqual(_signal(governance, context_key)["status"], "available")
        self.assertEqual(governance["ignored_context"], ["experiment_context"])
        self.assertTrue(governance["policy_respected"])

    def test_missing_script_context_is_explicit_and_uses_existing_fallback_script(self) -> None:
        service = AssetSelectionAgentService()
        data = _input()
        data = AssetSelectionInput(
            niche=data.niche,
            topic=data.topic,
            strategy_profile=data.strategy_profile,
            trend_profile=data.trend_profile,
            script_plan=None,
        )

        result = service.select(data)
        governance = result.asset_context_governance
        script_signal = _signal(governance, "script_context")

        self.assertFalse(result.fallback.used)
        self.assertIn("script_context", governance["missing_context"])
        self.assertIn("script_context", governance["degraded_context"])
        self.assertIn("script_context", governance["used_context"])
        self.assertFalse(script_signal["available"])
        self.assertTrue(script_signal["used"])
        self.assertEqual(script_signal["reason_code"], "SCRIPT_CONTEXT_MISSING_FALLBACK_USED")
        self.assertTrue(governance["context_summary"]["script_fallback_used"])

    def test_empty_script_segments_are_degraded_not_treated_as_complete(self) -> None:
        service = AssetSelectionAgentService()

        result = service.select(
            _input(
                script_plan=ScriptPlan(
                    hook="",
                    setup="The corridor stayed sealed.",
                    payoff="The sign pointed into the wall.",
                    generation_mode="test",
                )
            )
        )
        governance = result.asset_context_governance
        script_signal = _signal(governance, "script_context")

        self.assertIn("script_context", governance["degraded_context"])
        self.assertEqual(script_signal["reason_code"], "SCRIPT_CONTEXT_SEGMENT_EMPTY")
        self.assertEqual(script_signal["evidence_summary"]["missing_segments"], ["hook"])

    def test_missing_local_catalog_fallback_is_visible_without_changing_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            background_service = BackgroundGeneratorService(local_assets_dir=Path(tmp_dir))
            service = AssetSelectionAgentService(background_service=background_service)

            result = service.select(_input(niche="missing", topic="missing"))
            governance = result.asset_context_governance
            catalog_signal = _signal(governance, "local_catalog_context")

            self.assertTrue(result.fallback.used)
            self.assertEqual(result.fallback.reason, "ASSET_SELECTION_FALLBACK")
            self.assertIn("local_catalog_context", governance["missing_context"])
            self.assertFalse(catalog_signal["available"])
            self.assertFalse(catalog_signal["used"])
            self.assertEqual(catalog_signal["reason_code"], "LOCAL_CATALOG_CONTEXT_MISSING")
            self.assertTrue(catalog_signal["evidence_summary"]["asset_fallback_used"])

    def test_degraded_strategy_and_trend_context_are_visible(self) -> None:
        service = AssetSelectionAgentService()

        governance = service.select(
            _input(
                strategy_profile=StrategyProfile(content_mode="", variation_policy="", target_duration_range=""),
                trend_profile=TrendProfile(niche="horror", pacing="", visual_style="", trend_source=""),
            )
        ).asset_context_governance

        self.assertIn("strategy_context", governance["degraded_context"])
        self.assertIn("trend_context", governance["degraded_context"])
        self.assertEqual(_signal(governance, "strategy_context")["reason_code"], "STRATEGY_CONTEXT_DEGRADED")
        self.assertEqual(_signal(governance, "trend_context")["reason_code"], "TREND_CONTEXT_DEGRADED")

    def test_boundary_statement_preserves_asset_selection_authority(self) -> None:
        service = AssetSelectionAgentService()

        governance = service.select(_input()).asset_context_governance

        self.assertEqual(
            governance["boundary_statement"],
            "Asset Selection uses context for visual selection only; Strategy remains the control layer.",
        )

    def test_context_priority_and_governance_are_deterministic(self) -> None:
        data = _input()

        first = AssetSelectionAgentService().select(data)
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()
        second = AssetSelectionAgentService().select(data)

        self.assertEqual(first.asset_selection.to_dict(), second.asset_selection.to_dict())
        self.assertEqual(first.asset_context_governance, second.asset_context_governance)
        self.assertEqual(
            first.asset_context_governance["context_priority"],
            [
                "script_context",
                "strategy_context",
                "trend_context",
                "topic_context",
                "niche_context",
                "local_catalog_context",
                "experiment_context",
            ],
        )


if __name__ == "__main__":
    unittest.main()
