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

from app.creative.agents.trend_analysis.freshness import TrendFreshnessEvaluator  # noqa: E402
from app.creative.agents.trend_analysis.models import TrendAnalysisInput  # noqa: E402
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService  # noqa: E402
from app.creative.agents.trend_analysis.source_governance import TrendSourceGovernanceEvaluator  # noqa: E402
from app.creative.contracts.creative_pack import TrendEvidenceReference, TrendProfile  # noqa: E402


class TrendAnalysisFreshnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.evaluator = TrendFreshnessEvaluator()
        self.source_governance = TrendSourceGovernanceEvaluator()
        self.current_time = datetime(2026, 4, 24, 12, 0, 0, tzinfo=timezone.utc)

    def _profile(self, *, trend_source: str = "manual_curation") -> TrendProfile:
        return TrendProfile(
            niche="horror",
            dominant_hooks=["story_opening"],
            avg_duration="35-60",
            pacing="fast_first_3s",
            visual_style="dark_backgrounds",
            text_style="large_caption_focus",
            region="US",
            trend_source=trend_source,
            confidence_scores={"overall": 0.82},
            updated_at="2026-04-24T00:00:00Z",
            valid_until="2026-04-30T00:00:00Z",
            sample_size=12,
            evidence=[
                TrendEvidenceReference(
                    evidence_type="manual_top_video",
                    source="manual_curation",
                    reference_id="manual_001",
                )
            ],
        )

    def _governance(self, *candidates: dict[str, object], selection_mode: str = "mixed_allowed") -> dict[str, object]:
        return self.source_governance.evaluate_candidates(
            candidates=[dict(candidate) for candidate in candidates],
            requested_region="US",
            selection_mode=selection_mode,
        ).to_dict()

    def test_fresh_classification(self) -> None:
        state = self.evaluator.evaluate_source(
            source={
                "source_id": "manual:fresh",
                "source_class": "manual_curation",
                "metadata": {"captured_at": "2026-04-24T11:00:00Z"},
            },
            current_time=self.current_time,
        )

        self.assertEqual(state.freshness_status, "fresh")
        self.assertEqual(state.reason_code, "SOURCE_FRESH")

    def test_aging_classification(self) -> None:
        state = self.evaluator.evaluate_source(
            source={
                "source_id": "manual:aging",
                "source_class": "manual_curation",
                "metadata": {"captured_at": "2026-04-22T12:00:00Z"},
            },
            current_time=self.current_time,
        )

        self.assertEqual(state.freshness_status, "aging")

    def test_stale_classification(self) -> None:
        state = self.evaluator.evaluate_source(
            source={
                "source_id": "manual:stale",
                "source_class": "manual_curation",
                "metadata": {"captured_at": "2026-04-19T12:00:00Z"},
            },
            current_time=self.current_time,
        )

        self.assertEqual(state.freshness_status, "stale")

    def test_expired_classification(self) -> None:
        state = self.evaluator.evaluate_source(
            source={
                "source_id": "manual:expired",
                "source_class": "manual_curation",
                "metadata": {"captured_at": "2026-04-14T12:00:00Z"},
            },
            current_time=self.current_time,
        )

        self.assertEqual(state.freshness_status, "expired")
        self.assertFalse(state.within_valid_window)

    def test_missing_timestamp_classification(self) -> None:
        state = self.evaluator.evaluate_source(
            source={
                "source_id": "manual:missing",
                "source_class": "manual_curation",
                "metadata": {},
            },
            current_time=self.current_time,
        )

        self.assertEqual(state.freshness_status, "missing_timestamp")
        self.assertIsNone(state.age_seconds)

    def test_cache_primary_vs_fallback_distinction(self) -> None:
        governance = self._governance(
            {
                "source_id": "cache:horror",
                "source_class": "validated_cache",
                "region": "US",
                "metadata": {"captured_at": "2026-04-24T11:00:00Z"},
            },
            selection_mode="single_preferred",
        )

        states, primary_validity = self.evaluator.evaluate(
            trend_profile=self._profile(trend_source="creative_center"),
            source_governance=governance,
            current_time=self.current_time,
            fallback_used=False,
            fallback_reason="",
            cache_usage_mode="primary",
            decision_trace=[],
        )
        _, fallback_validity = self.evaluator.evaluate(
            trend_profile=self._profile(trend_source="creative_center"),
            source_governance=governance,
            current_time=self.current_time,
            fallback_used=True,
            fallback_reason="TREND_CACHE_FALLBACK",
            cache_usage_mode="fallback",
            decision_trace=[],
        )

        self.assertEqual(states[0].freshness_status, "fresh")
        self.assertEqual(primary_validity.cache_usage_mode, "primary")
        self.assertEqual(fallback_validity.cache_usage_mode, "fallback")
        self.assertTrue(primary_validity.uses_cache)
        self.assertTrue(fallback_validity.uses_cache)

    def test_validity_status_correct_mapping(self) -> None:
        governance = self._governance(
            {
                "source_id": "manual:fresh",
                "source_class": "manual_curation",
                "region": "US",
                "metadata": {"captured_at": "2026-04-24T11:00:00Z"},
            }
        )

        _, validity = self.evaluator.evaluate(
            trend_profile=self._profile(),
            source_governance=governance,
            current_time=self.current_time,
            fallback_used=False,
            fallback_reason="",
            cache_usage_mode="none",
            decision_trace=[],
        )

        self.assertEqual(validity.validity_status, "valid")
        self.assertTrue(validity.profile_valid)

    def test_degraded_validity_when_stale_dominates(self) -> None:
        governance = self._governance(
            {
                "source_id": "manual:stale",
                "source_class": "manual_curation",
                "region": "US",
                "metadata": {"captured_at": "2026-04-19T12:00:00Z"},
            },
            {
                "source_id": "cache:stale",
                "source_class": "validated_cache",
                "region": "US",
                "metadata": {"captured_at": "2026-04-19T11:00:00Z"},
            },
            {
                "source_id": "metrics:fresh",
                "source_class": "internal_runtime_metrics",
                "region": "US",
                "metadata": {"captured_at": "2026-04-24T11:00:00Z"},
            },
        )

        _, validity = self.evaluator.evaluate(
            trend_profile=self._profile(),
            source_governance=governance,
            current_time=self.current_time,
            fallback_used=False,
            fallback_reason="",
            cache_usage_mode="none",
            decision_trace=[],
        )

        self.assertEqual(validity.validity_status, "degraded")
        self.assertFalse(validity.profile_valid)

    def test_invalid_validity_when_only_fallback_exists(self) -> None:
        governance = self._governance(
            {
                "source_id": "safe_default",
                "source_class": "safe_default",
                "region": "US",
                "metadata": {"fallback_only": True},
            },
            selection_mode="single_preferred",
        )

        _, validity = self.evaluator.evaluate(
            trend_profile=self._profile(trend_source="safe_default"),
            source_governance=governance,
            current_time=self.current_time,
            fallback_used=True,
            fallback_reason="TREND_PROFILE_FALLBACK",
            cache_usage_mode="none",
            decision_trace=[],
        )

        self.assertEqual(validity.validity_status, "invalid")
        self.assertFalse(validity.profile_valid)

    def test_collector_trace_includes_freshness_and_validity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_dir = Path(tmp_dir)
            current_dir = trends_dir / "current"
            current_dir.mkdir(parents=True, exist_ok=True)
            self._write_current_profile(current_dir / "horror.json")
            service = TrendAnalysisAgentService(trends_dir=trends_dir)

            result = service.load(TrendAnalysisInput(niche="horror", current_time="2026-04-24T12:00:00Z"))

            self.assertIn("freshness", result.collector_trace)
            self.assertIn("validity", result.collector_trace)
            self.assertEqual(result.collector_trace["freshness"]["fresh_sources_count"], 1)
            self.assertEqual(result.collector_trace["validity"]["validity_status"], "valid")

    def test_no_change_to_trend_profile_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_dir = Path(tmp_dir)
            current_dir = trends_dir / "current"
            current_dir.mkdir(parents=True, exist_ok=True)
            self._write_current_profile(current_dir / "horror.json")
            service = TrendAnalysisAgentService(trends_dir=trends_dir)

            result = service.load(TrendAnalysisInput(niche="horror", current_time="2026-04-24T12:00:00Z"))

            self.assertEqual(result.trend_profile.dominant_hooks, ["story_opening"])
            self.assertEqual(result.trend_profile.confidence_scores["overall"], 0.82)
            self.assertEqual(result.validation_summary["freshness_state"], "fresh")

    def test_deterministic_behavior(self) -> None:
        governance = self._governance(
            {
                "source_id": "manual:fresh",
                "source_class": "manual_curation",
                "region": "US",
                "metadata": {"captured_at": "2026-04-24T11:00:00Z"},
            }
        )

        first_states, first_validity = self.evaluator.evaluate(
            trend_profile=self._profile(),
            source_governance=governance,
            current_time=self.current_time,
            fallback_used=False,
            fallback_reason="",
            cache_usage_mode="none",
            decision_trace=[],
        )
        second_states, second_validity = self.evaluator.evaluate(
            trend_profile=self._profile(),
            source_governance=governance,
            current_time=self.current_time,
            fallback_used=False,
            fallback_reason="",
            cache_usage_mode="none",
            decision_trace=[],
        )

        self.assertEqual([state.to_dict() for state in first_states], [state.to_dict() for state in second_states])
        self.assertEqual(first_validity.to_dict(), second_validity.to_dict())

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
