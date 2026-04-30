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

from app.creative.agents.trend_analysis.downstream_utility import TrendDownstreamUtilityMapper  # noqa: E402
from app.creative.agents.trend_analysis.models import TrendAnalysisInput  # noqa: E402
from app.creative.agents.trend_analysis.provenance import TrendProvenanceBuilder  # noqa: E402
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService  # noqa: E402
from app.creative.contracts.creative_pack import TrendEvidenceReference, TrendProfile  # noqa: E402


class TrendAnalysisDownstreamUtilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mapper = TrendDownstreamUtilityMapper()
        self.provenance_builder = TrendProvenanceBuilder()

    def _profile(
        self,
        *,
        dominant_hooks: list[str] | None = None,
        visual_style: str = "dark_backgrounds",
        pacing: str = "fast_first_3s",
        evidence: list[TrendEvidenceReference] | None = None,
        trend_source: str = "manual_curation",
    ) -> TrendProfile:
        return TrendProfile(
            niche="horror",
            dominant_hooks=dominant_hooks if dominant_hooks is not None else ["story_opening"],
            avg_duration="35-60",
            pacing=pacing,
            visual_style=visual_style,
            text_style="large_caption_focus",
            region="US",
            trend_source=trend_source,
            confidence_scores={"overall": 0.82},
            updated_at="2026-04-24T11:00:00Z",
            valid_until="2026-04-30T00:00:00Z",
            sample_size=12,
            evidence=evidence
            if evidence is not None
            else [
                TrendEvidenceReference(
                    evidence_type="manual_top_video",
                    source="manual_curation",
                    reference_id="manual_001",
                )
            ],
        )

    def _provenance(self, profile: TrendProfile, *, support_level: str = "strong") -> dict[str, object]:
        field_provenance = {}
        for field_name in self.provenance_builder.important_fields:
            if field_name in profile.to_dict():
                field_provenance[field_name] = {
                    "field_name": field_name,
                    "value_present": bool(profile.to_dict().get(field_name)),
                    "source_classes": ["manual_curation"],
                    "source_ids": ["manual:horror"],
                    "evidence_ids": ["manual_001"],
                    "support_level": support_level,
                    "rationale": "test provenance",
                }
        return {
            "provenance_complete": support_level not in {"unknown", "weak", "fallback"},
            "field_provenance": field_provenance,
            "fallback_fields": ["dominant_hooks"] if support_level == "fallback" else [],
            "weakly_supported_fields": ["dominant_hooks"] if support_level == "weak" else [],
            "unknown_source_fields": ["dominant_hooks"] if support_level == "unknown" else [],
        }

    def _utility(
        self,
        profile: TrendProfile | None = None,
        *,
        support_level: str = "strong",
        confidence_level: str = "high",
        validity_status: str = "valid",
        fallback_used: bool = False,
    ) -> dict[str, object]:
        resolved_profile = profile or self._profile()
        return self.mapper.map(
            trend_profile=resolved_profile,
            provenance=self._provenance(resolved_profile, support_level=support_level),
            confidence_calibration={
                "confidence": 0.82,
                "confidence_level": confidence_level,
                "confidence_meaning": "trust_in_trend_context",
            },
            validity={"validity_status": validity_status},
            fallback_used=fallback_used,
        ).to_dict()

    def _field(self, utility: dict[str, object], field_name: str) -> dict[str, object]:
        fields = utility["utility_trace"]["field_utilities"]
        return next(item for item in fields if item["field_name"] == field_name)

    def test_dominant_hooks_marked_material_for_strategy_and_script(self) -> None:
        utility = self._utility()
        dominant_hooks = self._field(utility, "dominant_hooks")

        self.assertEqual(dominant_hooks["interpretation_mode"], "material_context")
        self.assertEqual(dominant_hooks["strategy_relevance"], "high")
        self.assertEqual(dominant_hooks["script_relevance"], "high")

    def test_visual_style_marked_material_for_asset(self) -> None:
        utility = self._utility()
        visual_style = self._field(utility, "visual_style")

        self.assertEqual(visual_style["interpretation_mode"], "material_context")
        self.assertEqual(visual_style["asset_relevance"], "high")

    def test_pacing_marked_material_for_strategy(self) -> None:
        utility = self._utility()
        pacing = self._field(utility, "pacing")

        self.assertEqual(pacing["interpretation_mode"], "material_context")
        self.assertEqual(pacing["strategy_relevance"], "high")

    def test_evidence_and_source_metadata_marked_audit_only(self) -> None:
        utility = self._utility()
        evidence = self._field(utility, "evidence")
        trend_source = self._field(utility, "trend_source")

        self.assertEqual(evidence["interpretation_mode"], "audit_only")
        self.assertEqual(trend_source["interpretation_mode"], "audit_only")
        self.assertEqual(evidence["authority_level"], "none")

    def test_low_or_missing_field_marked_low_utility(self) -> None:
        utility = self._utility(self._profile(dominant_hooks=[]))
        dominant_hooks = self._field(utility, "dominant_hooks")

        self.assertEqual(dominant_hooks["interpretation_mode"], "low_utility")
        self.assertEqual(dominant_hooks["authority_level"], "none")

    def test_boundary_statement_present(self) -> None:
        utility = self._utility()

        self.assertEqual(
            utility["boundary_statement"],
            "Trend provides context only; Strategy remains the control layer.",
        )

    def test_authority_level_never_exceeds_advisory(self) -> None:
        utility = self._utility()

        levels = {
            item["authority_level"]
            for item in utility["utility_trace"]["field_utilities"]
        }
        self.assertTrue(levels.issubset({"none", "advisory"}))

    def test_no_publishability_or_prediction_fields_exist(self) -> None:
        utility = self._utility()
        serialized = json.dumps(utility)

        self.assertNotIn("publishability", serialized)
        self.assertNotIn("expected_performance", serialized)
        self.assertNotIn("prediction", serialized)

    def test_collector_trace_and_validation_summary_include_downstream_utility(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_dir = Path(tmp_dir)
            current_dir = trends_dir / "current"
            current_dir.mkdir(parents=True, exist_ok=True)
            self._write_current_profile(current_dir / "horror.json")
            service = TrendAnalysisAgentService(trends_dir=trends_dir)

            result = service.load(TrendAnalysisInput(niche="horror", current_time="2026-04-24T12:00:00Z"))

            self.assertIn("downstream_utility", result.collector_trace)
            self.assertIn("downstream_utility", result.validation_summary)
            self.assertTrue(result.validation_summary["downstream_utility"]["boundary_preserved"])

    def test_trend_analysis_result_remains_backward_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_dir = Path(tmp_dir)
            current_dir = trends_dir / "current"
            current_dir.mkdir(parents=True, exist_ok=True)
            self._write_current_profile(current_dir / "horror.json")
            service = TrendAnalysisAgentService(trends_dir=trends_dir)

            payload = service.load(TrendAnalysisInput(niche="horror", current_time="2026-04-24T12:00:00Z")).to_dict()

            self.assertEqual(set(payload), {"trend_profile", "fallback", "validation_summary", "collector_trace"})

    def test_strategy_and_asset_visible_fields_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_dir = Path(tmp_dir)
            current_dir = trends_dir / "current"
            current_dir.mkdir(parents=True, exist_ok=True)
            self._write_current_profile(current_dir / "horror.json")
            service = TrendAnalysisAgentService(trends_dir=trends_dir)

            result = service.load(TrendAnalysisInput(niche="horror", current_time="2026-04-24T12:00:00Z"))

            self.assertEqual(result.trend_profile.pacing, "fast_first_3s")
            self.assertEqual(result.trend_profile.visual_style, "dark_backgrounds")
            self.assertEqual(result.trend_profile.dominant_hooks, ["story_opening"])

    def test_deterministic_same_input_same_utility_output(self) -> None:
        first = self._utility()
        second = self._utility()

        self.assertEqual(first, second)

    def test_fallback_or_weak_provenance_does_not_become_high_authority_utility(self) -> None:
        utility = self._utility(
            self._profile(trend_source="safe_default"),
            support_level="fallback",
            confidence_level="low",
            validity_status="invalid",
            fallback_used=True,
        )
        dominant_hooks = self._field(utility, "dominant_hooks")

        self.assertNotEqual(dominant_hooks["interpretation_mode"], "material_context")
        self.assertIn(dominant_hooks["authority_level"], {"none", "advisory"})

    def _write_current_profile(self, path: Path) -> None:
        path.write_text(
            json.dumps(
                {
                    "niche": "horror",
                    "dominant_hooks": ["story_opening"],
                    "avg_duration": "35-60",
                    "pacing": "fast_first_3s",
                    "visual_style": "dark_backgrounds",
                    "text_style": "large_caption_focus",
                    "region": "US",
                    "trend_source": "manual_curation",
                    "updated_at": "2026-04-24T11:00:00Z",
                    "valid_until": "2026-04-30T00:00:00Z",
                    "sample_size": 12,
                    "confidence_scores": {"overall": 0.82},
                    "evidence": [
                        {
                            "evidence_type": "manual_top_video",
                            "source": "manual_curation",
                            "reference_id": "manual_001",
                            "captured_at": "2026-04-24T11:00:00Z",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
