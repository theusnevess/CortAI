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
from app.creative.agents.asset_selection.confidence_calibration import AssetConfidenceCalibrator
from app.creative.agents.asset_selection.models import AssetSelectionInput
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.contracts.creative_pack import ScriptPlan, StrategyProfile, TrendProfile
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


def _strong_payload() -> dict[str, object]:
    return {
        "asset_context_governance": {
            "context_priority": ["script_context", "strategy_context", "trend_context"],
            "available_context": ["script_context", "strategy_context", "trend_context"],
            "missing_context": [],
            "degraded_context": [],
            "ignored_context": [],
        },
        "asset_source_governance": {
            "catalog_available": True,
            "policy_respected": True,
            "selected_sources": [
                {"governance_status": "accepted"},
                {"governance_status": "accepted"},
                {"governance_status": "accepted"},
            ],
            "fallback_sources": [],
        },
        "segment_visual_intent": {"intent_complete": True},
        "visual_alignment": {
            "alignment_complete": True,
            "overall_alignment_score": 0.92,
            "mismatched_segments": [],
            "missing_metadata_segments": [],
            "segment_alignments": {},
        },
        "visual_truthfulness": {
            "overall_risk_level": "low",
            "high_risk_segments": [],
            "unsupported_claim_segments": [],
            "generic_or_fallback_segments": [],
            "segment_truthfulness": {},
        },
        "asset_fallback_honesty": {
            "global_fallback_used": False,
            "fallback_segments": [],
            "safe_default_segments": [],
            "weak_evidence_segments": [],
        },
        "asset_diversity": {
            "repeated_asset_detected": False,
            "repeated_category_detected": False,
            "visual_progression_level": "strong",
        },
    }


def _calibrate(payload: dict[str, object]) -> dict[str, object]:
    result = AssetConfidenceCalibrator().calibrate(
        asset_context_governance=payload["asset_context_governance"],
        asset_source_governance=payload["asset_source_governance"],
        segment_visual_intent=payload["segment_visual_intent"],
        visual_alignment=payload["visual_alignment"],
        visual_truthfulness=payload["visual_truthfulness"],
        asset_fallback_honesty=payload["asset_fallback_honesty"],
        asset_diversity=payload["asset_diversity"],
    )
    return result.to_dict()


class AssetConfidenceCalibrationTests(unittest.TestCase):
    def setUp(self) -> None:
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()

    def test_high_confidence_with_strong_governed_selection(self) -> None:
        confidence = _calibrate(_strong_payload())

        self.assertGreaterEqual(confidence["confidence"], 0.75)
        self.assertEqual(confidence["confidence_level"], "high")
        self.assertEqual(confidence["confidence_rationale"]["confidence_meaning"], "trust_in_asset_selection")
        self.assertEqual(confidence["confidence_rationale"]["penalties"], [])

    def test_fallback_caps_confidence_and_adds_penalty(self) -> None:
        payload = _strong_payload()
        payload["asset_fallback_honesty"] = {
            "global_fallback_used": True,
            "fallback_segments": ["hook"],
            "safe_default_segments": [],
            "weak_evidence_segments": ["hook"],
        }

        confidence = _calibrate(payload)

        self.assertLessEqual(confidence["confidence"], 0.65)
        self.assertIn("FALLBACK_REDUCES_CONFIDENCE", confidence["confidence_rationale"]["penalties"])
        self.assertIn({"cap": 0.65, "reason": "FALLBACK_USED_CAP"}, confidence["confidence_rationale"]["caps"])

    def test_safe_default_prevents_high_confidence(self) -> None:
        payload = _strong_payload()
        payload["asset_fallback_honesty"] = {
            "global_fallback_used": True,
            "fallback_segments": ["hook", "setup", "payoff"],
            "safe_default_segments": ["hook", "setup", "payoff"],
            "weak_evidence_segments": ["hook", "setup", "payoff"],
        }

        confidence = _calibrate(payload)

        self.assertLessEqual(confidence["confidence"], 0.55)
        self.assertNotEqual(confidence["confidence_level"], "high")
        self.assertIn("SAFE_DEFAULT_PREVENTS_HIGH_CONFIDENCE", confidence["confidence_rationale"]["penalties"])

    def test_high_mismatch_caps_confidence(self) -> None:
        payload = _strong_payload()
        payload["visual_alignment"] = {
            "alignment_complete": False,
            "overall_alignment_score": 0.35,
            "mismatched_segments": ["payoff"],
            "missing_metadata_segments": [],
            "segment_alignments": {
                "payoff": {"mismatch_level": "high"},
            },
        }

        confidence = _calibrate(payload)

        self.assertLessEqual(confidence["confidence"], 0.55)
        self.assertIn("VISUAL_SEMANTIC_MISMATCH_REDUCES_CONFIDENCE", confidence["confidence_rationale"]["penalties"])
        self.assertTrue(
            any(cap["reason"] == "HIGH_MISMATCH_CAP" for cap in confidence["confidence_rationale"]["caps"])
        )

    def test_generic_asset_risk_caps_confidence(self) -> None:
        payload = _strong_payload()
        payload["visual_truthfulness"] = {
            "overall_risk_level": "medium",
            "high_risk_segments": [],
            "unsupported_claim_segments": [],
            "generic_or_fallback_segments": ["setup"],
            "segment_truthfulness": {
                "setup": {"generic_asset_risk": True},
            },
        }

        confidence = _calibrate(payload)

        self.assertLessEqual(confidence["confidence"], 0.60)
        self.assertIn("GENERIC_OR_FALLBACK_VISUAL_RISK_REDUCES_CONFIDENCE", confidence["confidence_rationale"]["penalties"])
        self.assertTrue(
            any(cap["reason"] == "GENERIC_ASSET_RISK_CAP" for cap in confidence["confidence_rationale"]["caps"])
        )

    def test_repeated_asset_penalizes_confidence(self) -> None:
        payload = _strong_payload()
        payload["asset_diversity"] = {
            "repeated_asset_detected": True,
            "repeated_category_detected": True,
            "visual_progression_level": "weak",
        }

        confidence = _calibrate(payload)

        self.assertLessEqual(confidence["confidence"], 0.62)
        self.assertIn("REPEATED_ASSET_REDUCES_CONFIDENCE", confidence["confidence_rationale"]["penalties"])
        self.assertIn("REPEATED_CATEGORY_REDUCES_CONFIDENCE", confidence["confidence_rationale"]["penalties"])

    def test_service_exposes_confidence_fields(self) -> None:
        result = AssetSelectionAgentService().select(_input())
        payload = result.to_dict()

        self.assertIn("confidence", payload)
        self.assertIn("confidence_level", payload)
        self.assertIn("confidence_components", payload)
        self.assertIn("confidence_rationale", payload)
        self.assertEqual(payload["confidence_rationale"]["confidence_meaning"], "trust_in_asset_selection")
        json.dumps(payload)

    def test_fallback_service_result_cannot_have_high_confidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = AssetSelectionAgentService(
                background_service=BackgroundGeneratorService(local_assets_dir=Path(tmp_dir))
            )
            result = service.select(_input())

        self.assertTrue(result.fallback.used)
        self.assertLessEqual(result.confidence, 0.55)
        self.assertNotEqual(result.confidence_level, "high")
        self.assertIn("SAFE_DEFAULT_PREVENTS_HIGH_CONFIDENCE", result.confidence_rationale["penalties"])

    def test_confidence_is_not_constant_across_scenarios(self) -> None:
        strong = _calibrate(_strong_payload())
        fallback_payload = _strong_payload()
        fallback_payload["asset_fallback_honesty"] = {
            "global_fallback_used": True,
            "fallback_segments": ["hook", "setup", "payoff"],
            "safe_default_segments": ["hook", "setup", "payoff"],
            "weak_evidence_segments": ["hook", "setup", "payoff"],
        }
        fallback = _calibrate(fallback_payload)

        self.assertNotEqual(strong["confidence"], fallback["confidence"])

    def test_confidence_is_deterministic_and_preserves_selection(self) -> None:
        first = AssetSelectionAgentService().select(_input())
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()
        second = AssetSelectionAgentService().select(_input())

        self.assertEqual(first.asset_selection.to_dict(), second.asset_selection.to_dict())
        self.assertEqual(first.confidence, second.confidence)
        self.assertEqual(first.confidence_components, second.confidence_components)
        self.assertEqual(first.confidence_rationale, second.confidence_rationale)

    def test_boundary_statement_is_not_performance_prediction(self) -> None:
        confidence = _calibrate(_strong_payload())

        self.assertEqual(
            confidence["confidence_rationale"]["boundary_statement"],
            "Asset confidence is not performance prediction.",
        )
        self.assertNotIn("performance", confidence["confidence_rationale"]["confidence_meaning"])


if __name__ == "__main__":
    unittest.main()
