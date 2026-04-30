from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.trend_analysis.confidence_calibration import TrendConfidenceCalibrator  # noqa: E402
from app.creative.agents.trend_analysis.freshness import TrendFreshnessEvaluator  # noqa: E402
from app.creative.agents.trend_analysis.models import TrendAnalysisInput  # noqa: E402
from app.creative.agents.trend_analysis.provenance import TrendProvenanceBuilder  # noqa: E402
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService  # noqa: E402
from app.creative.agents.trend_analysis.source_governance import TrendSourceGovernanceEvaluator  # noqa: E402
from app.creative.contracts.creative_pack import TrendEvidenceReference, TrendProfile  # noqa: E402


class TrendAnalysisConfidenceCalibrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calibrator = TrendConfidenceCalibrator()
        self.governance_evaluator = TrendSourceGovernanceEvaluator()
        self.provenance_builder = TrendProvenanceBuilder()
        self.freshness_evaluator = TrendFreshnessEvaluator()
        self.current_time = datetime(2026, 4, 24, 12, 0, 0, tzinfo=timezone.utc)

    def _profile(
        self,
        *,
        trend_source: str = "manual_curation",
        sample_size: int = 24,
        evidence_count: int = 2,
    ) -> TrendProfile:
        evidence = [
            TrendEvidenceReference(
                evidence_type="manual_top_video",
                source=trend_source,
                reference_id=f"evidence_{index}",
                captured_at="2026-04-24T11:00:00Z",
            )
            for index in range(evidence_count)
        ]
        return TrendProfile(
            niche="horror",
            dominant_hooks=["story_opening", "shock_statement"],
            avg_duration="35-60",
            pacing="fast_first_3s",
            visual_style="dark_backgrounds",
            text_style="large_caption_focus",
            region="US",
            trend_source=trend_source,
            confidence_scores={"overall": 0.88},
            updated_at="2026-04-24T11:00:00Z",
            valid_until="2026-04-30T00:00:00Z",
            sample_size=sample_size,
            evidence=evidence,
        )

    def _calibration(
        self,
        *,
        trend_profile: TrendProfile | None = None,
        candidates: list[dict[str, object]] | None = None,
        fallback_used: bool = False,
        fallback_reason: str = "",
        supported_fields: list[str] | None = None,
        evidence_ids: list[str] | None = None,
        selection_mode: str = "mixed_allowed",
        cache_usage_mode: str = "none",
    ):
        profile = trend_profile or self._profile()
        resolved_supported_fields = supported_fields or list(self.provenance_builder.important_fields)
        resolved_evidence_ids = evidence_ids or [item.reference_id for item in profile.evidence]
        resolved_candidates = candidates or [
            {
                "source_id": "manual:horror",
                "source_class": "manual_curation",
                "region": "US",
                "metadata": {
                    "captured_at": "2026-04-24T11:00:00Z",
                    "valid_until": "2026-04-30T00:00:00Z",
                    "supported_fields": resolved_supported_fields,
                    "evidence_ids": resolved_evidence_ids,
                },
            }
        ]
        governance = self.governance_evaluator.evaluate_candidates(
            candidates=[dict(candidate) for candidate in resolved_candidates],
            requested_region="US",
            selection_mode=selection_mode,
        )
        provenance = self.provenance_builder.build(
            trend_profile=profile,
            source_governance=governance.to_dict(),
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
        )
        freshness_states, validity = self.freshness_evaluator.evaluate(
            trend_profile=profile,
            source_governance=governance.to_dict(),
            current_time=self.current_time,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            cache_usage_mode=cache_usage_mode,
            decision_trace=[],
        )
        freshness = {
            "sources": [state.to_dict() for state in freshness_states],
            "fresh_sources_count": sum(1 for state in freshness_states if state.freshness_status == "fresh"),
            "aging_sources_count": sum(1 for state in freshness_states if state.freshness_status == "aging"),
            "stale_sources_count": sum(1 for state in freshness_states if state.freshness_status == "stale"),
            "expired_sources_count": sum(1 for state in freshness_states if state.freshness_status == "expired"),
            "missing_timestamp_count": sum(1 for state in freshness_states if state.freshness_status == "missing_timestamp"),
        }
        return self.calibrator.calibrate(
            trend_profile=profile,
            source_governance=governance.to_dict(),
            provenance=provenance.to_dict(),
            freshness=freshness,
            validity=validity.to_dict(),
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
        )

    def test_high_confidence_with_governed_fresh_source_and_complete_provenance(self) -> None:
        calibration = self._calibration()

        self.assertEqual(calibration.confidence_level, "high")
        self.assertGreaterEqual(calibration.confidence, 0.7)
        self.assertEqual(calibration.confidence_meaning, "trust_in_trend_context")

    def test_low_confidence_with_safe_default_fallback_only(self) -> None:
        profile = self._profile(trend_source="safe_default", sample_size=0, evidence_count=0)
        calibration = self._calibration(
            trend_profile=profile,
            candidates=[
                {
                    "source_id": "safe_default",
                    "source_class": "safe_default",
                    "region": "US",
                    "metadata": {
                        "fallback_only": True,
                        "supported_fields": list(self.provenance_builder.important_fields),
                        "evidence_ids": [],
                    },
                }
            ],
            fallback_used=True,
            fallback_reason="TREND_PROFILE_FALLBACK",
            selection_mode="single_preferred",
        )

        self.assertEqual(calibration.confidence_level, "low")
        self.assertLess(calibration.confidence, 0.35)
        self.assertIn("SAFE_DEFAULT_CONTEXT", calibration.penalties)

    def test_stale_source_reduces_confidence(self) -> None:
        high = self._calibration()
        stale = self._calibration(
            candidates=[
                {
                    "source_id": "manual:stale",
                    "source_class": "manual_curation",
                    "region": "US",
                    "metadata": {
                        "captured_at": "2026-04-19T12:00:00Z",
                        "supported_fields": list(self.provenance_builder.important_fields),
                        "evidence_ids": ["evidence_0", "evidence_1"],
                    },
                }
            ]
        )

        self.assertLess(stale.confidence, high.confidence)
        self.assertIn("STALE_SOURCE_PRESENT", stale.penalties)
        self.assertNotEqual(stale.confidence_level, "high")

    def test_expired_source_reduces_confidence_strongly(self) -> None:
        expired = self._calibration(
            candidates=[
                {
                    "source_id": "manual:expired",
                    "source_class": "manual_curation",
                    "region": "US",
                    "metadata": {
                        "captured_at": "2026-04-14T12:00:00Z",
                        "supported_fields": list(self.provenance_builder.important_fields),
                        "evidence_ids": ["evidence_0", "evidence_1"],
                    },
                }
            ]
        )

        self.assertEqual(expired.confidence_level, "low")
        self.assertIn("EXPIRED_SOURCE_PRESENT", expired.penalties)

    def test_missing_timestamp_reduces_confidence(self) -> None:
        missing = self._calibration(
            candidates=[
                {
                    "source_id": "manual:missing",
                    "source_class": "manual_curation",
                    "region": "US",
                    "metadata": {
                        "supported_fields": list(self.provenance_builder.important_fields),
                        "evidence_ids": ["evidence_0", "evidence_1"],
                    },
                }
            ]
        )

        self.assertLess(missing.confidence, 0.7)
        self.assertIn("MISSING_TIMESTAMP_PRESENT", missing.penalties)

    def test_incomplete_provenance_reduces_confidence(self) -> None:
        incomplete = self._calibration(
            supported_fields=["dominant_hooks", "evidence"],
            evidence_ids=["evidence_0"],
        )

        self.assertLess(incomplete.confidence, 0.7)
        self.assertIn("PROVENANCE_INCOMPLETE", incomplete.penalties)

    def test_rejected_source_cannot_produce_high_confidence(self) -> None:
        rejected = self._calibration(
            candidates=[
                {
                    "source_id": "bad",
                    "source_class": "unsupported_external",
                    "region": "US",
                    "metadata": {
                        "captured_at": "2026-04-24T11:00:00Z",
                        "supported_fields": list(self.provenance_builder.important_fields),
                        "evidence_ids": ["evidence_0", "evidence_1"],
                    },
                }
            ]
        )

        self.assertNotEqual(rejected.confidence_level, "high")
        self.assertIn("SOURCE_REJECTION_PRESENT", rejected.penalties)

    def test_mixed_accepted_rejected_source_mix_gets_medium_or_low_confidence(self) -> None:
        mixed = self._calibration(
            candidates=[
                {
                    "source_id": "manual:horror",
                    "source_class": "manual_curation",
                    "region": "US",
                    "metadata": {
                        "captured_at": "2026-04-24T11:00:00Z",
                        "supported_fields": list(self.provenance_builder.important_fields),
                        "evidence_ids": ["evidence_0", "evidence_1"],
                    },
                },
                {
                    "source_id": "bad",
                    "source_class": "unbounded_scrape",
                    "region": "US",
                    "metadata": {"captured_at": "2026-04-24T11:00:00Z"},
                },
            ]
        )

        self.assertIn(mixed.confidence_level, {"low", "medium"})
        self.assertIn("SOURCE_REJECTION_PRESENT", mixed.penalties)

    def test_confidence_not_constant_across_scenarios(self) -> None:
        values = {
            self._calibration().confidence,
            self._calibration(
                candidates=[
                    {
                        "source_id": "manual:expired",
                        "source_class": "manual_curation",
                        "region": "US",
                        "metadata": {
                            "captured_at": "2026-04-14T12:00:00Z",
                            "supported_fields": list(self.provenance_builder.important_fields),
                            "evidence_ids": ["evidence_0", "evidence_1"],
                        },
                    }
                ]
            ).confidence,
            self._calibration(
                trend_profile=self._profile(trend_source="safe_default", sample_size=0, evidence_count=0),
                candidates=[
                    {
                        "source_id": "safe_default",
                        "source_class": "safe_default",
                        "region": "US",
                        "metadata": {"fallback_only": True},
                    }
                ],
                fallback_used=True,
                fallback_reason="TREND_PROFILE_FALLBACK",
                selection_mode="single_preferred",
            ).confidence,
        }

        self.assertGreaterEqual(len(values), 3)

    def test_confidence_appears_in_collector_trace_and_validation_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_dir = Path(tmp_dir)
            current_dir = trends_dir / "current"
            current_dir.mkdir(parents=True, exist_ok=True)
            self._write_current_profile(current_dir / "horror.json")
            service = TrendAnalysisAgentService(trends_dir=trends_dir)

            result = service.load(TrendAnalysisInput(niche="horror", current_time="2026-04-24T12:00:00Z"))

            self.assertIn("confidence_calibration", result.collector_trace)
            self.assertIn("confidence_calibration", result.validation_summary)
            self.assertEqual(
                result.collector_trace["confidence_calibration"]["confidence_meaning"],
                "trust_in_trend_context",
            )

    def test_legacy_trend_analysis_result_remains_backward_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_dir = Path(tmp_dir)
            current_dir = trends_dir / "current"
            current_dir.mkdir(parents=True, exist_ok=True)
            self._write_current_profile(current_dir / "horror.json")
            service = TrendAnalysisAgentService(trends_dir=trends_dir)

            payload = service.load(TrendAnalysisInput(niche="horror", current_time="2026-04-24T12:00:00Z")).to_dict()

            self.assertEqual(set(payload), {"trend_profile", "fallback", "validation_summary", "collector_trace"})

    def test_no_change_to_downstream_visible_legacy_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_dir = Path(tmp_dir)
            current_dir = trends_dir / "current"
            current_dir.mkdir(parents=True, exist_ok=True)
            self._write_current_profile(current_dir / "horror.json")
            service = TrendAnalysisAgentService(trends_dir=trends_dir)

            result = service.load(TrendAnalysisInput(niche="horror", current_time="2026-04-24T12:00:00Z"))

            self.assertEqual(result.trend_profile.confidence_scores["overall"], 0.88)
            self.assertEqual(result.validation_summary["overall_confidence"], 0.88)
            self.assertEqual(result.trend_profile.dominant_hooks, ["story_opening", "shock_statement"])

    def test_deterministic_replay(self) -> None:
        first = self._calibration().to_dict()
        second = self._calibration().to_dict()

        self.assertEqual(first, second)

    def _write_current_profile(self, path: Path) -> None:
        path.write_text(
            json.dumps(
                {
                    "niche": "horror",
                    "dominant_hooks": ["story_opening", "shock_statement"],
                    "avg_duration": "35-60",
                    "pacing": "fast_first_3s",
                    "visual_style": "dark_backgrounds",
                    "text_style": "large_caption_focus",
                    "region": "US",
                    "trend_source": "manual_curation",
                    "updated_at": "2026-04-24T11:00:00Z",
                    "valid_until": "2026-04-30T00:00:00Z",
                    "sample_size": 24,
                    "confidence_scores": {"overall": 0.88},
                    "evidence": [
                        {
                            "evidence_type": "manual_top_video",
                            "source": "manual_curation",
                            "reference_id": "evidence_0",
                            "captured_at": "2026-04-24T11:00:00Z",
                        },
                        {
                            "evidence_type": "manual_top_video",
                            "source": "manual_curation",
                            "reference_id": "evidence_1",
                            "captured_at": "2026-04-24T11:00:00Z",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
