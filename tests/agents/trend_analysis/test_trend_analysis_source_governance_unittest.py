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
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService  # noqa: E402
from app.creative.agents.trend_analysis.source_governance import TrendSourceGovernanceEvaluator  # noqa: E402


class TrendAnalysisSourceGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.evaluator = TrendSourceGovernanceEvaluator()

    def test_allowed_manual_curation_source_is_accepted(self) -> None:
        result = self.evaluator.evaluate_candidates(
            candidates=[{"source_id": "manual:horror", "source_class": "manual_curation", "region": "US", "metadata": {}}],
            requested_region="US",
            selection_mode="single_preferred",
        )

        self.assertTrue(result.policy_respected)
        self.assertEqual(result.selected_source_class, "manual_curation")
        self.assertEqual(result.accepted_sources[0].reason_code, "SOURCE_ACCEPTED_MANUAL_CURATION_ALLOWED")

    def test_allowed_validated_cache_source_is_accepted(self) -> None:
        result = self.evaluator.evaluate_candidates(
            candidates=[{"source_id": "cache:horror", "source_class": "validated_cache", "region": "US", "metadata": {}}],
            requested_region="US",
            selection_mode="single_preferred",
        )

        self.assertEqual(result.selected_source_class, "validated_cache")
        self.assertEqual(result.accepted_sources[0].reason_code, "SOURCE_ACCEPTED_CACHE_ALLOWED")

    def test_allowed_current_store_source_is_accepted(self) -> None:
        result = self.evaluator.evaluate_candidates(
            candidates=[{"source_id": "current:horror", "source_class": "current_store", "region": "US", "metadata": {}}],
            requested_region="US",
            selection_mode="single_preferred",
        )

        self.assertEqual(result.selected_source_class, "current_store")
        self.assertEqual(result.accepted_sources[0].reason_code, "SOURCE_ACCEPTED_ALLOWED_CLASS")

    def test_safe_default_is_fallback_allowed_but_not_strong_evidence(self) -> None:
        result = self.evaluator.evaluate_candidates(
            candidates=[{"source_id": "safe_default", "source_class": "safe_default", "region": "US", "metadata": {}}],
            requested_region="US",
            selection_mode="single_preferred",
        )

        self.assertEqual(result.selected_source_class, "safe_default")
        self.assertTrue(result.fallback_required)
        self.assertEqual(result.fallback_reason, "ONLY_SAFE_DEFAULT_SOURCE_ALLOWED")
        self.assertEqual(result.accepted_sources[0].governance_status, "fallback_allowed")

    def test_unknown_source_class_is_rejected(self) -> None:
        result = self.evaluator.evaluate_candidates(
            candidates=[{"source_id": "bad", "source_class": "unknown", "region": "US", "metadata": {}}],
            requested_region="US",
            selection_mode="single_preferred",
        )

        self.assertFalse(result.policy_respected)
        self.assertEqual(result.rejected_sources[0].reason_code, "SOURCE_REJECTED_FORBIDDEN_CLASS")

    def test_missing_source_type_is_rejected(self) -> None:
        result = self.evaluator.evaluate_candidates(
            candidates=[{"source_id": "missing", "region": "US", "metadata": {}}],
            requested_region="US",
            selection_mode="single_preferred",
        )

        self.assertFalse(result.policy_respected)
        self.assertEqual(result.rejected_sources[0].reason_code, "SOURCE_REJECTED_MISSING_TYPE")

    def test_unsupported_external_source_is_rejected(self) -> None:
        result = self.evaluator.evaluate_candidates(
            candidates=[{"source_id": "ext", "source_class": "unsupported_external", "region": "US", "metadata": {}}],
            requested_region="US",
            selection_mode="single_preferred",
        )

        self.assertFalse(result.policy_respected)
        self.assertEqual(result.rejected_sources[0].reason_code, "SOURCE_REJECTED_FORBIDDEN_CLASS")

    def test_priority_order_is_deterministic(self) -> None:
        first = self.evaluator.evaluate_candidates(
            candidates=[
                {"source_id": "history", "source_class": "history_snapshot", "region": "US", "metadata": {}},
                {"source_id": "manual", "source_class": "manual_curation", "region": "US", "metadata": {}},
            ],
            requested_region="US",
            selection_mode="single_preferred",
        )
        second = self.evaluator.evaluate_candidates(
            candidates=[
                {"source_id": "manual", "source_class": "manual_curation", "region": "US", "metadata": {}},
                {"source_id": "history", "source_class": "history_snapshot", "region": "US", "metadata": {}},
            ],
            requested_region="US",
            selection_mode="single_preferred",
        )

        self.assertEqual(first.selected_source_class, second.selected_source_class)
        self.assertEqual(first.accepted_sources[0].source_id, second.accepted_sources[0].source_id)
        self.assertEqual(first.ignored_sources[0].source_id, second.ignored_sources[0].source_id)

    def test_lower_priority_source_can_be_ignored_when_higher_priority_selected(self) -> None:
        result = self.evaluator.evaluate_candidates(
            candidates=[
                {"source_id": "current", "source_class": "current_store", "region": "US", "metadata": {}},
                {"source_id": "manual", "source_class": "manual_curation", "region": "US", "metadata": {}},
            ],
            requested_region="US",
            selection_mode="single_preferred",
        )

        self.assertEqual(result.selected_source_class, "manual_curation")
        self.assertEqual(result.ignored_sources[0].reason_code, "SOURCE_IGNORED_LOWER_PRIORITY")
        self.assertEqual(result.ignored_sources[0].source_id, "current")

    def test_policy_respected_true_when_all_selected_sources_comply(self) -> None:
        result = self.evaluator.evaluate_candidates(
            candidates=[
                {"source_id": "manual", "source_class": "manual_curation", "region": "US", "metadata": {}},
                {"source_id": "history", "source_class": "history_snapshot", "region": "US", "metadata": {}},
            ],
            requested_region="US",
            selection_mode="mixed_allowed",
        )

        self.assertTrue(result.policy_respected)
        self.assertEqual(result.source_mix["manual_curation"], 1)
        self.assertEqual(result.source_mix["history_snapshot"], 1)

    def test_policy_respected_false_when_forbidden_source_would_be_selected_or_accepted(self) -> None:
        result = self.evaluator.evaluate_candidates(
            candidates=[{"source_id": "forbidden", "source_class": "unbounded_scrape", "region": "US", "metadata": {}}],
            requested_region="US",
            selection_mode="single_preferred",
        )

        self.assertFalse(result.policy_respected)
        self.assertEqual(result.accepted_sources, ())

    def test_source_governance_appears_in_collector_trace(self) -> None:
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
                        "trend_source": "manual_curation",
                        "sample_size": 12,
                        "evidence": [{"evidence_type": "manual_top_video", "source": "manual_curation", "reference_id": "vid_001"}],
                    }
                ),
                encoding="utf-8",
            )
            service = TrendAnalysisAgentService(trends_dir=trends_dir)

            result = service.load(TrendAnalysisInput(niche="horror", current_time="2026-04-03T00:00:00Z"))

            self.assertIn("source_governance", result.collector_trace)
            self.assertEqual(
                result.collector_trace["source_governance"]["policy_version"],
                "trend_source_governance_v2_6",
            )

    def test_fallback_remains_explicit_when_only_safe_default_is_usable(self) -> None:
        service = TrendAnalysisAgentService(trends_dir=Path(tempfile.mkdtemp()))

        result = service.load(TrendAnalysisInput(niche="history", current_time="2026-04-03T00:00:00Z"))

        self.assertTrue(result.fallback.used)
        self.assertEqual(result.collector_trace["source_governance"]["selected_source_class"], "safe_default")
        self.assertTrue(result.collector_trace["source_governance"]["fallback_required"])

    def test_region_fallback_does_not_create_fake_regional_claim(self) -> None:
        result = self.evaluator.evaluate_candidates(
            candidates=[{"source_id": "manual", "source_class": "manual_curation", "region": "", "metadata": {}}],
            requested_region="",
            selection_mode="single_preferred",
        )

        self.assertTrue(result.policy_respected)
        self.assertEqual(result.governance_trace["requested_region"], "US")
        self.assertEqual(result.governance_trace["region_effective"], "US")

    def test_existing_trend_analysis_result_remains_backward_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_dir = Path(tmp_dir)
            current_dir = trends_dir / "current"
            current_dir.mkdir(parents=True, exist_ok=True)
            (current_dir / "facts.json").write_text(
                json.dumps(
                    {
                        "niche": "facts",
                        "dominant_hooks": ["story_opening"],
                        "avg_duration": "35-60",
                        "pacing": "baseline",
                        "visual_style": "archive_dark",
                        "text_style": "caption_focus",
                        "trend_source": "manual_curation",
                        "sample_size": 12,
                        "evidence": [{"evidence_type": "manual_top_video", "source": "manual_curation", "reference_id": "vid_001"}],
                    }
                ),
                encoding="utf-8",
            )
            service = TrendAnalysisAgentService(trends_dir=trends_dir)

            payload = service.load(TrendAnalysisInput(niche="facts", current_time="2026-04-03T00:00:00Z")).to_dict()

            self.assertEqual(set(payload), {"trend_profile", "fallback", "validation_summary", "collector_trace"})


if __name__ == "__main__":
    unittest.main()
