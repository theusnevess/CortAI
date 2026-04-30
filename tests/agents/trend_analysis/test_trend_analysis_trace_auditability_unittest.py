from __future__ import annotations

import copy
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
from app.creative.agents.trend_analysis.trace_auditability import TrendTraceBuilder  # noqa: E402


class TrendAnalysisTraceAuditabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = TrendTraceBuilder()

    def test_trend_trace_exists_in_collector_trace(self) -> None:
        with self._service_result() as result:
            self.assertIn("trend_trace", result.collector_trace)

    def test_all_required_sections_are_present(self) -> None:
        with self._service_result() as result:
            trend_trace = result.collector_trace["trend_trace"]

            for section_name in [
                "source_governance",
                "provenance",
                "freshness",
                "validity",
                "confidence_calibration",
                "shift_analysis",
                "downstream_utility",
                "fallback",
                "final_trend_profile_rationale",
                "missing_or_degraded_inputs",
                "audit_summary",
            ]:
                self.assertIn(section_name, trend_trace)

    def test_final_trend_profile_rationale_exists(self) -> None:
        with self._service_result() as result:
            rationale = result.collector_trace["trend_trace"]["final_trend_profile_rationale"]

            self.assertTrue(rationale["profile_emitted"])
            self.assertEqual(rationale["selected_source_class"], "current_store")
            self.assertIn("rationale", rationale)

    def test_audit_summary_reconstructible_true_when_all_sections_exist(self) -> None:
        with self._service_result() as result:
            audit_summary = result.collector_trace["trend_trace"]["audit_summary"]

            self.assertTrue(audit_summary["reconstructible"])
            self.assertTrue(audit_summary["required_sections_present"])
            self.assertEqual(audit_summary["silent_failure_indicators"], [])

    def test_reconstructible_false_when_required_section_missing(self) -> None:
        with self._service_result() as result:
            trace_without_shift = copy.deepcopy(result.collector_trace)
            trace_without_shift.pop("trend_trace", None)
            trace_without_shift.pop("shift_analysis")

            rebuilt = self.builder.build(
                trend_profile=result.trend_profile,
                fallback=result.fallback,
                validation_summary=result.validation_summary,
                collector_trace=trace_without_shift,
            )

            self.assertFalse(rebuilt["audit_summary"]["reconstructible"])
            self.assertIn("MISSING_SHIFT_ANALYSIS", rebuilt["audit_summary"]["silent_failure_indicators"])

    def test_missing_or_degraded_inputs_includes_stale_expired_and_missing_timestamp(self) -> None:
        with self._service_result() as result:
            trace_payload = copy.deepcopy(result.collector_trace)
            trace_payload.pop("trend_trace", None)
            trace_payload["freshness"] = {
                "sources": [
                    {
                        "source_id": "source:missing",
                        "source_class": "manual_curation",
                        "freshness_status": "missing_timestamp",
                        "rationale": "missing timestamp",
                    },
                    {
                        "source_id": "source:expired",
                        "source_class": "manual_curation",
                        "freshness_status": "expired",
                        "rationale": "expired source",
                    },
                    {
                        "source_id": "source:stale",
                        "source_class": "manual_curation",
                        "freshness_status": "stale",
                        "rationale": "stale source",
                    },
                ],
                "fresh_sources_count": 0,
                "stale_sources_count": 1,
                "expired_sources_count": 1,
                "missing_timestamp_count": 1,
            }

            rebuilt = self.builder.build(
                trend_profile=result.trend_profile,
                fallback=result.fallback,
                validation_summary=result.validation_summary,
                collector_trace=trace_payload,
            )
            kinds = {item["kind"] for item in rebuilt["missing_or_degraded_inputs"]}

            self.assertIn("missing_timestamp", kinds)
            self.assertIn("expired_source", kinds)
            self.assertIn("stale_source", kinds)

    def test_missing_or_degraded_inputs_includes_fallback_fields(self) -> None:
        with self._service_result() as result:
            trace_payload = copy.deepcopy(result.collector_trace)
            trace_payload.pop("trend_trace", None)
            trace_payload["provenance"]["fallback_fields"] = ["dominant_hooks"]

            rebuilt = self.builder.build(
                trend_profile=result.trend_profile,
                fallback=result.fallback,
                validation_summary=result.validation_summary,
                collector_trace=trace_payload,
            )

            self.assertIn(
                {"kind": "fallback_field", "identifier": "dominant_hooks", "impact": "fallback", "rationale": "Field dominant_hooks was emitted from fallback context."},
                rebuilt["missing_or_degraded_inputs"],
            )

    def test_missing_or_degraded_inputs_includes_weak_and_unknown_provenance_fields(self) -> None:
        with self._service_result() as result:
            trace_payload = copy.deepcopy(result.collector_trace)
            trace_payload.pop("trend_trace", None)
            trace_payload["provenance"]["weakly_supported_fields"] = ["visual_style"]
            trace_payload["provenance"]["unknown_source_fields"] = ["text_style"]

            rebuilt = self.builder.build(
                trend_profile=result.trend_profile,
                fallback=result.fallback,
                validation_summary=result.validation_summary,
                collector_trace=trace_payload,
            )
            by_kind = {(item["kind"], item["identifier"]) for item in rebuilt["missing_or_degraded_inputs"]}

            self.assertIn(("weak_field", "visual_style"), by_kind)
            self.assertIn(("unknown_field", "text_style"), by_kind)

    def test_fallback_status_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = TrendAnalysisAgentService(trends_dir=Path(tmp_dir))
            result = service.load(TrendAnalysisInput(niche="missing", current_time="2026-04-24T12:00:00Z"))
            fallback_trace = result.collector_trace["trend_trace"]["fallback"]

            self.assertTrue(fallback_trace["used"])
            self.assertTrue(fallback_trace["safe_default_used"])
            self.assertEqual(fallback_trace["reason"], "TREND_PROFILE_FALLBACK")
            self.assertTrue(fallback_trace["fallback_path_visible"])

    def test_validation_summary_traceability_exists(self) -> None:
        with self._service_result() as result:
            self.assertIn("traceability", result.validation_summary)
            self.assertTrue(result.validation_summary["traceability"]["trend_trace_present"])

    def test_legacy_collector_trace_fields_remain_present(self) -> None:
        with self._service_result() as result:
            for field_name in [
                "storage_mode",
                "resolved_path",
                "loaded_from_cache",
                "legacy_layout_used",
                "collector_version",
                "assembly_mode",
                "source_mix",
                "source_count",
                "creative_center_refresh",
                "decision_trace",
            ]:
                self.assertIn(field_name, result.collector_trace)

    def test_trend_analysis_result_remains_backward_compatible(self) -> None:
        with self._service_result() as result:
            payload = result.to_dict()

            self.assertEqual(set(payload), {"trend_profile", "fallback", "validation_summary", "collector_trace"})

    def test_deterministic_same_input_same_trend_trace(self) -> None:
        with self._service_result() as result:
            first_trace = copy.deepcopy(result.collector_trace["trend_trace"])
            rebuilt = self.builder.build(
                trend_profile=result.trend_profile,
                fallback=result.fallback,
                validation_summary=result.validation_summary,
                collector_trace=result.collector_trace,
            )

            self.assertEqual(first_trace, rebuilt)

    def test_trace_addition_does_not_change_trend_profile_output(self) -> None:
        with self._service_result() as result:
            self.assertEqual(result.trend_profile.dominant_hooks, ["story_opening"])
            self.assertEqual(result.trend_profile.pacing, "fast_first_3s")
            self.assertEqual(result.trend_profile.visual_style, "dark_backgrounds")
            self.assertEqual(result.trend_profile.trend_source, "manual_curation")

    def test_trace_copies_existing_sections_without_recalculation(self) -> None:
        with self._service_result() as result:
            trend_trace = result.collector_trace["trend_trace"]

            self.assertEqual(trend_trace["source_governance"], result.collector_trace["source_governance"])
            self.assertEqual(trend_trace["confidence_calibration"], result.collector_trace["confidence_calibration"])
            self.assertEqual(trend_trace["freshness"], result.collector_trace["freshness"])
            self.assertEqual(trend_trace["validity"], result.collector_trace["validity"])
            self.assertEqual(trend_trace["shift_analysis"], result.collector_trace["shift_analysis"])
            self.assertEqual(trend_trace["downstream_utility"], result.collector_trace["downstream_utility"])

    def _service_result(self):
        return _ServiceResultContext()


class _ServiceResultContext:
    def __enter__(self):  # noqa: ANN204
        self.temp_dir = tempfile.TemporaryDirectory()
        trends_dir = Path(self.temp_dir.name)
        current_dir = trends_dir / "current"
        current_dir.mkdir(parents=True, exist_ok=True)
        self._write_current_profile(current_dir / "horror.json")
        self.service = TrendAnalysisAgentService(trends_dir=trends_dir)
        return self.service.load(
            TrendAnalysisInput(
                niche="horror",
                current_time="2026-04-24T12:00:00Z",
            )
        )

    def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
        self.temp_dir.cleanup()

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
