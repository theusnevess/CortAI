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
from app.creative.agents.asset_selection.trace_auditability import AssetTraceBuilder
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import AssetPlan, ScriptPlan, StrategyProfile, TrendProfile
from app.runtime.asset_selector import AssetSelector


REQUIRED_SECTIONS = {
    "asset_context_governance",
    "catalog_governance",
    "segment_visual_intent",
    "visual_alignment",
    "visual_truthfulness",
    "asset_fallback_honesty",
    "asset_diversity",
    "confidence_calibration",
    "final_asset_plan_rationale",
    "missing_or_degraded_inputs",
    "audit_summary",
}


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


def _base_builder_payload() -> dict[str, object]:
    return {
        "asset_selection": AssetPlan(hook_asset="a.jpg", setup_asset="b.jpg", payoff_asset="c.jpg"),
        "fallback": FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
        "asset_context_governance": {"missing_context": [], "degraded_context": []},
        "asset_source_governance": {
            "coverage_limitations": ["NO_CATALOG_SOURCE_LIMITATIONS_DETECTED"],
            "selected_sources": [],
        },
        "segment_visual_intent": {"missing_segments": [], "degraded_segments": [], "intent_complete": True},
        "visual_alignment": {
            "overall_alignment_level": "high",
            "mismatched_segments": [],
            "missing_metadata_segments": [],
        },
        "visual_truthfulness": {
            "overall_risk_level": "low",
            "high_risk_segments": [],
            "unsupported_claim_segments": [],
            "generic_or_fallback_segments": [],
        },
        "asset_fallback_honesty": {
            "fallback_segments": [],
            "safe_default_segments": [],
        },
        "asset_diversity": {
            "repeated_asset_detected": False,
            "repeated_category_detected": False,
            "repeated_asset_paths": [],
            "repeated_categories": [],
            "visual_progression_level": "strong",
        },
        "confidence": 0.88,
        "confidence_level": "high",
        "confidence_components": {"semantic_alignment": 0.9},
        "confidence_rationale": {
            "confidence_meaning": "trust_in_asset_selection",
            "penalties": [],
        },
    }


def _build_trace(payload: dict[str, object]) -> dict[str, object]:
    return AssetTraceBuilder().build(
        asset_selection=payload["asset_selection"],
        fallback=payload["fallback"],
        asset_context_governance=payload["asset_context_governance"],
        asset_source_governance=payload["asset_source_governance"],
        segment_visual_intent=payload["segment_visual_intent"],
        visual_alignment=payload["visual_alignment"],
        visual_truthfulness=payload["visual_truthfulness"],
        asset_fallback_honesty=payload["asset_fallback_honesty"],
        asset_diversity=payload["asset_diversity"],
        confidence=payload["confidence"],
        confidence_level=payload["confidence_level"],
        confidence_components=payload["confidence_components"],
        confidence_rationale=payload["confidence_rationale"],
    )


class AssetTraceAuditabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()

    def test_asset_trace_exists_and_has_required_sections(self) -> None:
        result = AssetSelectionAgentService().select(_input())
        trace = result.asset_trace

        self.assertTrue(REQUIRED_SECTIONS <= set(trace))
        self.assertTrue(trace["audit_summary"]["reconstructible"])
        self.assertTrue(trace["audit_summary"]["required_sections_present"])
        json.dumps(result.to_dict())

    def test_final_asset_plan_rationale_reconstructs_strong_case(self) -> None:
        result = AssetSelectionAgentService().select(_input())
        rationale = result.asset_trace["final_asset_plan_rationale"]

        self.assertTrue(rationale["assets_emitted"])
        self.assertEqual(rationale["selection_mode"], "catalog_match")
        self.assertFalse(rationale["fallback_used"])
        self.assertEqual(rationale["confidence"], result.confidence)
        self.assertEqual(rationale["confidence_level"], result.confidence_level)
        self.assertEqual(
            rationale["boundary_statement"],
            "Asset Selection explains visual choice; QC retains final authority.",
        )

    def test_fallback_trace_exposes_safe_default_and_weak_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = AssetSelectionAgentService(
                background_service=BackgroundGeneratorService(local_assets_dir=Path(tmp_dir))
            )
            result = service.select(_input())

        trace = result.asset_trace
        final = trace["final_asset_plan_rationale"]

        self.assertTrue(result.fallback.used)
        self.assertEqual(final["selection_mode"], "fallback_safe_default")
        self.assertTrue(final["fallback_used"])
        self.assertFalse(final["assets_emitted"])
        self.assertTrue(trace["audit_summary"]["fallback_visible"])
        self.assertTrue(
            any(item["kind"] == "safe_default_used" for item in trace["missing_or_degraded_inputs"])
        )
        self.assertIn("SAFE_DEFAULT_VISUAL_EVIDENCE_WEAK", final["dominant_reason_codes"])

    def test_mismatch_appears_in_missing_or_degraded_inputs(self) -> None:
        payload = _base_builder_payload()
        payload["visual_alignment"] = {
            "overall_alignment_level": "low",
            "mismatched_segments": ["payoff"],
            "missing_metadata_segments": [],
        }
        payload["confidence_rationale"] = {
            "confidence_meaning": "trust_in_asset_selection",
            "penalties": ["VISUAL_SEMANTIC_MISMATCH_REDUCES_CONFIDENCE"],
        }

        trace = _build_trace(payload)

        self.assertTrue(trace["audit_summary"]["reconstructible"])
        self.assertTrue(any(item["kind"] == "visual_mismatch" and item["identifier"] == "payoff" for item in trace["missing_or_degraded_inputs"]))
        self.assertIn("VISUAL_SEMANTIC_MISMATCH", trace["final_asset_plan_rationale"]["dominant_reason_codes"])

    def test_missing_metadata_and_truthfulness_risk_are_visible(self) -> None:
        payload = _base_builder_payload()
        payload["visual_alignment"] = {
            "overall_alignment_level": "unknown",
            "mismatched_segments": [],
            "missing_metadata_segments": ["hook"],
        }
        payload["visual_truthfulness"] = {
            "overall_risk_level": "high",
            "high_risk_segments": ["hook"],
            "unsupported_claim_segments": ["hook"],
            "generic_or_fallback_segments": ["hook"],
        }

        trace = _build_trace(payload)
        kinds = {item["kind"] for item in trace["missing_or_degraded_inputs"]}

        self.assertIn("missing_asset_metadata", kinds)
        self.assertIn("truthfulness_high_risk", kinds)
        self.assertIn("unsupported_visual_claim", kinds)
        self.assertIn("generic_or_fallback_visual_risk", kinds)

    def test_repetition_and_weak_progression_are_visible(self) -> None:
        payload = _base_builder_payload()
        payload["asset_diversity"] = {
            "repeated_asset_detected": True,
            "repeated_category_detected": True,
            "repeated_asset_paths": ["a.jpg"],
            "repeated_categories": ["warning_display"],
            "visual_progression_level": "weak",
        }

        trace = _build_trace(payload)
        kinds = {item["kind"] for item in trace["missing_or_degraded_inputs"]}

        self.assertIn("repeated_asset", kinds)
        self.assertIn("repeated_category", kinds)
        self.assertIn("weak_visual_progression", kinds)
        self.assertEqual(trace["final_asset_plan_rationale"]["diversity_risk"], "high")

    def test_reconstructible_false_when_required_section_missing(self) -> None:
        payload = _base_builder_payload()
        trace = _build_trace(payload)
        del trace["visual_alignment"]
        summary = AssetTraceBuilder()._audit_summary(  # noqa: SLF001 - direct audit rule test.
            trace=trace,
            fallback=payload["fallback"],
            confidence_rationale=payload["confidence_rationale"],
            visual_alignment=payload["visual_alignment"],
        )

        self.assertFalse(summary["reconstructible"])
        self.assertFalse(summary["required_sections_present"])
        self.assertIn("MISSING_TRACE_SECTION:visual_alignment", summary["silent_failure_indicators"])

    def test_confidence_calibration_is_copied_not_recomputed(self) -> None:
        result = AssetSelectionAgentService().select(_input())
        confidence_trace = result.asset_trace["confidence_calibration"]

        self.assertEqual(confidence_trace["confidence"], result.confidence)
        self.assertEqual(confidence_trace["confidence_level"], result.confidence_level)
        self.assertEqual(confidence_trace["confidence_components"], result.confidence_components)
        self.assertEqual(confidence_trace["confidence_rationale"], result.confidence_rationale)

    def test_asset_trace_is_deterministic_and_preserves_selection(self) -> None:
        first = AssetSelectionAgentService().select(_input())
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()
        second = AssetSelectionAgentService().select(_input())

        self.assertEqual(first.asset_selection.to_dict(), second.asset_selection.to_dict())
        self.assertEqual(first.asset_trace, second.asset_trace)

    def test_asset_trace_does_not_create_qc_or_publishability_authority(self) -> None:
        trace = AssetSelectionAgentService().select(_input()).asset_trace
        final = trace["final_asset_plan_rationale"]

        self.assertEqual(
            final["boundary_statement"],
            "Asset Selection explains visual choice; QC retains final authority.",
        )
        self.assertNotIn("publishable", final)
        self.assertNotIn("qc_decision", final)


if __name__ == "__main__":
    unittest.main()
