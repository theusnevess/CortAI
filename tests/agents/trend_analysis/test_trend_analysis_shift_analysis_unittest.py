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
from app.creative.agents.trend_analysis.shift_analysis import TrendShiftAnalyzer  # noqa: E402
from app.creative.contracts.creative_pack import TrendProfile  # noqa: E402


class TrendAnalysisShiftAnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = TrendShiftAnalyzer()

    def _profile(
        self,
        *,
        dominant_hooks: list[str] | None = None,
        avg_duration: str = "35-60",
        pacing: str = "fast_first_3s",
        visual_style: str = "dark_backgrounds",
        text_style: str = "large_caption_focus",
        trend_source: str = "manual_curation",
        region: str = "US",
        sample_size: int = 12,
    ) -> TrendProfile:
        return TrendProfile(
            niche="horror",
            dominant_hooks=dominant_hooks or ["story_opening", "shock_statement"],
            avg_duration=avg_duration,
            pacing=pacing,
            visual_style=visual_style,
            text_style=text_style,
            region=region,
            trend_source=trend_source,
            confidence_scores={"overall": 0.82},
            updated_at="2026-04-24T00:00:00Z",
            valid_until="2026-04-30T00:00:00Z",
            sample_size=sample_size,
            evidence=[],
        )

    def test_no_baseline_returns_no_shift(self) -> None:
        result = self.analyzer.analyze(current_profile=self._profile(), baseline_profile=None).to_dict()

        self.assertFalse(result["baseline_available"])
        self.assertFalse(result["shift_detected"])
        self.assertEqual(result["shift_severity"], "none")
        self.assertEqual(result["operational_significance"], "none")
        self.assertIn("NO_BASELINE_AVAILABLE", result["rationale"])

    def test_identical_baseline_and_current_returns_no_shift(self) -> None:
        profile = self._profile()
        result = self.analyzer.analyze(current_profile=profile, baseline_profile=profile).to_dict()

        self.assertTrue(result["baseline_available"])
        self.assertFalse(result["shift_detected"])
        self.assertEqual(result["change_count"], 0)
        self.assertEqual(result["meaningful_change_count"], 0)

    def test_list_reorder_only_is_weak_variation(self) -> None:
        baseline = self._profile(dominant_hooks=["story_opening", "shock_statement"])
        current = self._profile(dominant_hooks=["shock_statement", "story_opening"])

        result = self.analyzer.analyze(current_profile=current, baseline_profile=baseline).to_dict()

        self.assertFalse(result["shift_detected"])
        self.assertEqual(result["shift_severity"], "weak")
        self.assertEqual(result["operational_significance"], "low")
        self.assertEqual(result["weak_variations"][0]["change_type"], "list_reordered")

    def test_dominant_hooks_added_removed_is_meaningful_shift(self) -> None:
        baseline = self._profile(dominant_hooks=["story_opening", "shock_statement", "question"])
        current = self._profile(dominant_hooks=["ominous_question", "warning_claim", "evidence_tease"])

        result = self.analyzer.analyze(current_profile=current, baseline_profile=baseline).to_dict()

        self.assertTrue(result["shift_detected"])
        self.assertEqual(result["shift_severity"], "strong")
        self.assertEqual(result["meaningful_shifts"][0]["field_name"], "dominant_hooks")

    def test_pacing_change_is_moderate_shift(self) -> None:
        baseline = self._profile(pacing="baseline")
        current = self._profile(pacing="fast_first_3s")

        result = self.analyzer.analyze(current_profile=current, baseline_profile=baseline).to_dict()

        self.assertTrue(result["shift_detected"])
        self.assertEqual(result["shift_severity"], "moderate")
        self.assertEqual(result["operational_significance"], "medium")

    def test_visual_style_change_is_moderate_shift(self) -> None:
        baseline = self._profile(visual_style="phase1_baseline")
        current = self._profile(visual_style="dark_backgrounds")

        result = self.analyzer.analyze(current_profile=current, baseline_profile=baseline).to_dict()

        self.assertTrue(result["shift_detected"])
        self.assertEqual(result["meaningful_shifts"][0]["field_name"], "visual_style")
        self.assertEqual(result["meaningful_shifts"][0]["severity"], "moderate")

    def test_multiple_core_fields_changed_is_strong_shift(self) -> None:
        baseline = self._profile(
            dominant_hooks=["story_opening", "shock_statement", "question"],
            pacing="baseline",
            visual_style="phase1_baseline",
        )
        current = self._profile(
            dominant_hooks=["ominous_question", "warning_claim", "evidence_tease"],
            pacing="fast_first_3s",
            visual_style="dark_backgrounds",
        )

        result = self.analyzer.analyze(current_profile=current, baseline_profile=baseline).to_dict()

        self.assertTrue(result["shift_detected"])
        self.assertEqual(result["shift_severity"], "strong")
        self.assertEqual(result["operational_significance"], "high")

    def test_fallback_to_governed_source_change_is_detected(self) -> None:
        baseline = self._profile(trend_source="safe_default")
        current = self._profile(trend_source="manual_curation")

        result = self.analyzer.analyze(current_profile=current, baseline_profile=baseline).to_dict()

        self.assertTrue(result["shift_detected"])
        self.assertEqual(result["shift_severity"], "strong")
        self.assertEqual(result["meaningful_shifts"][0]["field_name"], "trend_source")

    def test_missing_previous_field_is_explicit(self) -> None:
        change = self.analyzer._compare_field(  # noqa: SLF001
            field_name="pacing",
            previous_value=None,
            current_value="fast_first_3s",
        )

        self.assertTrue(change.changed)
        self.assertEqual(change.change_type, "missing_previous")
        self.assertTrue(change.operationally_significant)

    def test_operational_significance_low_medium_high_works(self) -> None:
        weak = self.analyzer.analyze(
            current_profile=self._profile(dominant_hooks=["shock_statement", "story_opening"]),
            baseline_profile=self._profile(dominant_hooks=["story_opening", "shock_statement"]),
        ).to_dict()
        medium = self.analyzer.analyze(
            current_profile=self._profile(pacing="fast_first_3s"),
            baseline_profile=self._profile(pacing="baseline"),
        ).to_dict()
        high = self.analyzer.analyze(
            current_profile=self._profile(region="BR"),
            baseline_profile=self._profile(region="US"),
        ).to_dict()

        self.assertEqual(weak["operational_significance"], "low")
        self.assertEqual(medium["operational_significance"], "medium")
        self.assertEqual(high["operational_significance"], "high")

    def test_collector_trace_includes_shift_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_dir = Path(tmp_dir)
            current_dir = trends_dir / "current"
            current_dir.mkdir(parents=True, exist_ok=True)
            self._write_profile(
                current_dir / "horror.json",
                dominant_hooks=["story_opening", "shock_statement"],
                pacing="fast_first_3s",
                visual_style="dark_backgrounds",
            )
            service = TrendAnalysisAgentService(trends_dir=trends_dir)

            result = service.load(TrendAnalysisInput(niche="horror", current_time="2026-04-24T12:00:00Z"))

            self.assertIn("shift_analysis", result.collector_trace)
            self.assertIn("field_changes", result.collector_trace["shift_analysis"])
            self.assertIn("baseline_summary", result.collector_trace["shift_analysis"])
            self.assertIn("current_summary", result.collector_trace["shift_analysis"])

    def test_legacy_shift_fields_remain_compatible(self) -> None:
        baseline = self._profile(pacing="baseline")
        current = self._profile(pacing="fast_first_3s")

        result = self.analyzer.analyze(current_profile=current, baseline_profile=baseline).to_dict()

        self.assertIn("shift_detected", result)
        self.assertIn("baseline_available", result)
        self.assertIn("changes", result)
        self.assertEqual(result["changes"][0]["field"], "pacing")
        self.assertEqual(result["changes"][0]["significance"], "medium")

    def test_deterministic_same_input_same_output(self) -> None:
        baseline = self._profile(pacing="baseline")
        current = self._profile(pacing="fast_first_3s")

        first = self.analyzer.analyze(current_profile=current, baseline_profile=baseline).to_dict()
        second = self.analyzer.analyze(current_profile=current, baseline_profile=baseline).to_dict()

        self.assertEqual(first, second)

    def test_no_strategy_core_downstream_behavior_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trends_dir = Path(tmp_dir)
            current_dir = trends_dir / "current"
            current_dir.mkdir(parents=True, exist_ok=True)
            self._write_profile(
                current_dir / "horror.json",
                dominant_hooks=["story_opening", "shock_statement"],
                pacing="fast_first_3s",
                visual_style="dark_backgrounds",
            )
            service = TrendAnalysisAgentService(trends_dir=trends_dir)

            result = service.load(TrendAnalysisInput(niche="horror", current_time="2026-04-24T12:00:00Z"))

            self.assertEqual(result.trend_profile.dominant_hooks, ["story_opening", "shock_statement"])
            self.assertEqual(result.validation_summary["overall_confidence"], 0.82)
            self.assertEqual(set(result.to_dict()), {"trend_profile", "fallback", "validation_summary", "collector_trace"})

    def _write_profile(
        self,
        path: Path,
        *,
        dominant_hooks: list[str],
        pacing: str,
        visual_style: str,
    ) -> None:
        path.write_text(
            json.dumps(
                {
                    "niche": "horror",
                    "dominant_hooks": dominant_hooks,
                    "avg_duration": "35-60",
                    "pacing": pacing,
                    "visual_style": visual_style,
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
