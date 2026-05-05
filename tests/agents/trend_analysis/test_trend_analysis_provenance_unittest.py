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

from app.creative.agents.trend_analysis.models import TrendAnalysisInput  # noqa: E402
from app.creative.agents.trend_analysis.provenance import TrendProvenanceBuilder  # noqa: E402
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService  # noqa: E402
from app.creative.agents.trend_analysis.source_governance import TrendSourceGovernanceEvaluator  # noqa: E402
from app.creative.contracts.creative_pack import TrendEvidenceReference, TrendProfile  # noqa: E402


class TrendAnalysisProvenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = TrendProvenanceBuilder()
        self.governance = TrendSourceGovernanceEvaluator()

    def _profile(
        self,
        *,
        evidence: list[TrendEvidenceReference] | None = None,
        confidence_scores: dict[str, float] | None = None,
    ) -> TrendProfile:
        resolved_evidence = evidence if evidence is not None else [
            TrendEvidenceReference(
                evidence_type="manual_top_video",
                source="manual_curation",
                reference_id="manual_001",
                captured_at="2026-04-24T00:00:00Z",
            )
        ]
        return TrendProfile(
            niche="horror",
            dominant_hooks=["story_opening", "shock_statement"],
            avg_duration="35-60",
            pacing="fast_first_3s",
            visual_style="dark_backgrounds",
            text_style="large_caption_focus",
            region="US",
            trend_source="manual_curation",
            confidence_scores=confidence_scores
            or {
                "dominant_hooks": 0.81,
                "avg_duration": 0.81,
                "pacing": 0.81,
                "visual_style": 0.81,
                "text_style": 0.81,
                "overall": 0.81,
            },
            updated_at="2026-04-24T00:00:00Z",
            valid_until="2026-04-30T00:00:00Z",
            sample_size=12,
            evidence=resolved_evidence,
        )

    def _governance_result(
        self,
        *candidates: dict[str, object],
        selection_mode: str = "mixed_allowed",
    ) -> dict[str, object]:
        return self.governance.evaluate_candidates(
            candidates=[dict(item) for item in candidates],
            requested_region="US",
            selection_mode=selection_mode,
        ).to_dict()

    def test_field_provenance_is_generated_for_present_trend_profile_fields(self) -> None:
        summary = self.builder.build(
            trend_profile=self._profile(),
            source_governance=self._governance_result(
                {
                    "source_id": "manual:horror",
                    "source_class": "manual_curation",
                    "region": "US",
                    "metadata": {
                        "supported_fields": [
                            "niche",
                            "region",
                            "dominant_hooks",
                            "avg_duration",
                            "pacing",
                            "visual_style",
                            "text_style",
                            "trend_source",
                            "confidence_scores",
                            "updated_at",
                            "valid_until",
                            "sample_size",
                            "evidence",
                        ],
                        "evidence_ids": ["manual_001"],
                    },
                }
            ),
            fallback_used=False,
            fallback_reason="",
        )

        self.assertIn("dominant_hooks", summary.field_provenance)
        self.assertTrue(summary.field_provenance["dominant_hooks"].value_present)
        self.assertEqual(summary.field_provenance["dominant_hooks"].support_level, "strong")

    def test_accepted_manual_curation_source_supports_fields(self) -> None:
        summary = self.builder.build(
            trend_profile=self._profile(),
            source_governance=self._governance_result(
                {
                    "source_id": "manual:horror",
                    "source_class": "manual_curation",
                    "region": "US",
                    "metadata": {
                        "supported_fields": ["dominant_hooks", "visual_style", "evidence"],
                        "evidence_ids": ["manual_001"],
                    },
                }
            ),
            fallback_used=False,
            fallback_reason="",
        )

        payload = summary.field_provenance["dominant_hooks"]
        self.assertEqual(payload.source_classes, ("manual_curation",))
        self.assertEqual(payload.source_ids, ("manual:horror",))
        self.assertEqual(payload.evidence_ids, ("manual_001",))

    def test_accepted_validated_cache_source_supports_fields(self) -> None:
        summary = self.builder.build(
            trend_profile=self._profile(),
            source_governance=self._governance_result(
                {
                    "source_id": "cache:horror",
                    "source_class": "validated_cache",
                    "region": "US",
                    "metadata": {
                        "supported_fields": ["pacing", "avg_duration", "evidence"],
                        "evidence_ids": ["manual_001"],
                    },
                }
            ),
            fallback_used=False,
            fallback_reason="",
        )

        self.assertEqual(summary.field_provenance["pacing"].support_level, "strong")
        self.assertEqual(summary.field_provenance["pacing"].source_classes, ("validated_cache",))

    def test_safe_default_fields_are_marked_fallback_not_strong(self) -> None:
        fallback_profile = TrendProfile(
            niche="default",
            dominant_hooks=["question"],
            avg_duration="8-12",
            pacing="baseline",
            visual_style="phase1_baseline",
            text_style="caption_focus",
            region="US",
            trend_source="safe_default",
            confidence_scores={"overall": 0.25},
            updated_at="2026-04-24T00:00:00Z",
            valid_until="2026-05-01T00:00:00Z",
            sample_size=0,
            evidence=[],
        )
        summary = self.builder.build(
            trend_profile=fallback_profile,
            source_governance=self._governance_result(
                {
                    "source_id": "safe_default",
                    "source_class": "safe_default",
                    "region": "US",
                    "metadata": {
                        "supported_fields": [
                            "niche",
                            "region",
                            "dominant_hooks",
                            "avg_duration",
                            "pacing",
                            "visual_style",
                            "text_style",
                            "trend_source",
                            "confidence_scores",
                            "updated_at",
                            "valid_until",
                            "sample_size",
                        ],
                        "evidence_ids": [],
                    },
                },
                selection_mode="single_preferred",
            ),
            fallback_used=True,
            fallback_reason="TREND_PROFILE_FALLBACK",
        )

        self.assertEqual(summary.field_provenance["dominant_hooks"].support_level, "fallback")
        self.assertIn("dominant_hooks", summary.fallback_fields)
        self.assertNotEqual(summary.field_provenance["dominant_hooks"].support_level, "strong")

    def test_rejected_source_cannot_provide_strong_support(self) -> None:
        summary = self.builder.build(
            trend_profile=self._profile(),
            source_governance=self._governance_result(
                {
                    "source_id": "bad",
                    "source_class": "unsupported_external",
                    "region": "US",
                    "metadata": {
                        "supported_fields": ["dominant_hooks", "evidence"],
                        "evidence_ids": ["manual_001"],
                    },
                }
            ),
            fallback_used=False,
            fallback_reason="",
        )

        self.assertEqual(summary.field_provenance["dominant_hooks"].support_level, "unknown")
        self.assertFalse(summary.provenance_complete)

    def test_ignored_source_is_visible_but_not_counted_as_support(self) -> None:
        governance = self._governance_result(
            {
                "source_id": "manual:horror",
                "source_class": "manual_curation",
                "region": "US",
                "metadata": {
                    "supported_fields": ["dominant_hooks", "evidence"],
                    "evidence_ids": ["manual_001"],
                },
            },
            {
                "source_id": "history:horror",
                "source_class": "history_snapshot",
                "region": "US",
                "metadata": {
                    "supported_fields": ["dominant_hooks", "evidence"],
                    "evidence_ids": ["manual_001"],
                },
            },
            selection_mode="single_preferred",
        )
        summary = self.builder.build(
            trend_profile=self._profile(),
            source_governance=governance,
            fallback_used=False,
            fallback_reason="",
        )

        self.assertEqual(summary.ignored_sources[0]["source_id"], "history:horror")
        self.assertEqual(summary.field_provenance["dominant_hooks"].source_ids, ("manual:horror",))

    def test_missing_evidence_produces_weak_or_unknown_provenance_not_fake_evidence(self) -> None:
        summary = self.builder.build(
            trend_profile=self._profile(evidence=[]),
            source_governance=self._governance_result(
                {
                    "source_id": "manual:horror",
                    "source_class": "manual_curation",
                    "region": "US",
                    "metadata": {
                        "supported_fields": ["visual_style", "trend_source"],
                        "evidence_ids": [],
                    },
                }
            ),
            fallback_used=False,
            fallback_reason="",
        )

        self.assertEqual(summary.field_provenance["visual_style"].support_level, "weak")
        self.assertEqual(summary.field_provenance["dominant_hooks"].support_level, "unknown")
        self.assertEqual(summary.evidence_references, ())

    def test_source_mix_is_deterministic(self) -> None:
        first = self.builder.build(
            trend_profile=self._profile(),
            source_governance=self._governance_result(
                {
                    "source_id": "manual:horror",
                    "source_class": "manual_curation",
                    "region": "US",
                    "metadata": {"supported_fields": ["dominant_hooks"], "evidence_ids": ["manual_001"]},
                },
                {
                    "source_id": "cache:horror",
                    "source_class": "validated_cache",
                    "region": "US",
                    "metadata": {"supported_fields": ["pacing"], "evidence_ids": ["manual_001"]},
                },
                selection_mode="mixed_allowed",
            ),
            fallback_used=False,
            fallback_reason="",
        )
        second = self.builder.build(
            trend_profile=self._profile(),
            source_governance=self._governance_result(
                {
                    "source_id": "cache:horror",
                    "source_class": "validated_cache",
                    "region": "US",
                    "metadata": {"supported_fields": ["pacing"], "evidence_ids": ["manual_001"]},
                },
                {
                    "source_id": "manual:horror",
                    "source_class": "manual_curation",
                    "region": "US",
                    "metadata": {"supported_fields": ["dominant_hooks"], "evidence_ids": ["manual_001"]},
                },
                selection_mode="mixed_allowed",
            ),
            fallback_used=False,
            fallback_reason="",
        )

        self.assertEqual(first.source_mix, second.source_mix)

    def test_provenance_complete_true_when_all_emitted_fields_have_explicit_support(self) -> None:
        summary = self.builder.build(
            trend_profile=self._profile(),
            source_governance=self._governance_result(
                {
                    "source_id": "manual:horror",
                    "source_class": "manual_curation",
                    "region": "US",
                    "metadata": {
                        "supported_fields": list(self.builder.important_fields),
                        "evidence_ids": ["manual_001"],
                    },
                }
            ),
            fallback_used=False,
            fallback_reason="",
        )

        self.assertTrue(summary.provenance_complete)
        self.assertEqual(summary.unknown_source_fields, ())

    def test_provenance_complete_false_when_emitted_fields_lack_source_linkage(self) -> None:
        summary = self.builder.build(
            trend_profile=self._profile(),
            source_governance=self._governance_result(
                {
                    "source_id": "manual:horror",
                    "source_class": "manual_curation",
                    "region": "US",
                    "metadata": {
                        "supported_fields": ["dominant_hooks", "evidence"],
                        "evidence_ids": ["manual_001"],
                    },
                }
            ),
            fallback_used=False,
            fallback_reason="",
        )

        self.assertFalse(summary.provenance_complete)
        self.assertIn("visual_style", summary.unknown_source_fields)

    def test_collector_trace_includes_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_dir = Path(tmp_dir)
            current_dir = trends_dir / "current"
            current_dir.mkdir(parents=True, exist_ok=True)
            (current_dir / "horror.json").write_text(
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
                        "sample_size": 12,
                        "confidence_scores": {"overall": 0.82},
                        "evidence": [
                            {
                                "evidence_type": "manual_top_video",
                                "source": "manual_curation",
                                "reference_id": "manual_001",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            service = TrendAnalysisAgentService(trends_dir=trends_dir)

            result = service.load(TrendAnalysisInput(niche="horror", current_time="2026-04-24T00:00:00Z"))

            self.assertIn("provenance", result.collector_trace)
            self.assertIn("field_provenance", result.collector_trace["provenance"])

    def test_provenance_consumes_source_governance_when_present(self) -> None:
        summary = self.builder.build(
            trend_profile=self._profile(),
            source_governance=self._governance_result(
                {
                    "source_id": "manual:horror",
                    "source_class": "manual_curation",
                    "region": "US",
                    "metadata": {
                        "supported_fields": ["dominant_hooks", "evidence"],
                        "evidence_ids": ["manual_001"],
                    },
                }
            ),
            fallback_used=False,
            fallback_reason="",
        )

        self.assertTrue(summary.provenance_trace["source_governance_present"])
        self.assertEqual(summary.accepted_sources[0]["source_id"], "manual:horror")

    def test_existing_trend_analysis_result_remains_backward_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_dir = Path(tmp_dir)
            current_dir = trends_dir / "current"
            current_dir.mkdir(parents=True, exist_ok=True)
            (current_dir / "horror.json").write_text(
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
                        "sample_size": 12,
                        "evidence": [{"evidence_type": "manual_top_video", "source": "manual_curation", "reference_id": "manual_001"}],
                    }
                ),
                encoding="utf-8",
            )
            service = TrendAnalysisAgentService(trends_dir=trends_dir)

            payload = service.load(TrendAnalysisInput(niche="horror", current_time="2026-04-24T00:00:00Z")).to_dict()

            self.assertEqual(set(payload), {"trend_profile", "fallback", "validation_summary", "collector_trace"})

    def test_no_confidence_freshness_or_shift_values_are_modified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_dir = Path(tmp_dir)
            current_dir = trends_dir / "current"
            current_dir.mkdir(parents=True, exist_ok=True)
            (current_dir / "horror.json").write_text(
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
                        "updated_at": "2026-04-24T00:00:00Z",
                        "valid_until": "2026-04-30T00:00:00Z",
                        "sample_size": 12,
                        "confidence_scores": {
                            "dominant_hooks": 0.88,
                            "avg_duration": 0.88,
                            "pacing": 0.88,
                            "visual_style": 0.88,
                            "overall": 0.88,
                        },
                        "evidence": [{"evidence_type": "manual_top_video", "source": "manual_curation", "reference_id": "manual_001"}],
                    }
                ),
                encoding="utf-8",
            )
            service = TrendAnalysisAgentService(trends_dir=trends_dir)

            result = service.load(TrendAnalysisInput(niche="horror", current_time="2026-04-24T12:00:00Z"))

            self.assertEqual(result.trend_profile.confidence_scores["overall"], 0.88)
            self.assertEqual(result.validation_summary["freshness_state"], "fresh")
            self.assertIn("shift_analysis", result.collector_trace)

    def test_deterministic_same_input_same_provenance(self) -> None:
        governance = self._governance_result(
            {
                "source_id": "manual:horror",
                "source_class": "manual_curation",
                "region": "US",
                "metadata": {
                    "supported_fields": list(self.builder.important_fields),
                    "evidence_ids": ["manual_001"],
                },
            }
        )
        first = self.builder.build(
            trend_profile=self._profile(),
            source_governance=governance,
            fallback_used=False,
            fallback_reason="",
        ).to_dict()
        second = self.builder.build(
            trend_profile=self._profile(),
            source_governance=governance,
            fallback_used=False,
            fallback_reason="",
        ).to_dict()

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
