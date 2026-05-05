from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.account_health.models import AccountHealthInput
from app.creative.agents.account_health.service import AccountHealthAgentService
from app.creative.agents.account_health.telemetry_enrichment import AccountHealthTelemetryEnricher


class AccountHealthTelemetryEnrichmentTests(unittest.TestCase):
    def test_enrichment_exposes_real_lineage_freshness_and_source_summaries(self) -> None:
        service = AccountHealthAgentService()

        result = service.evaluate(
            AccountHealthInput(
                account_id="acc_health_telemetry_real",
                recent_publish_count=3,
                recent_format_repetition_ratio=0.20,
                recent_views_drop_ratio=0.10,
                recent_low_performance_streak=0,
                telemetry_sources=[
                    {
                        "source_name": "publish_history",
                        "source_type": "jsonl",
                        "record_count": 3,
                        "freshness_status": "fresh",
                        "latest_timestamp": "2026-04-20T00:00:00Z",
                        "evidence_ref": "OUT/data/publish_records/publish_records.jsonl",
                    }
                ],
                metric_window_summary={
                    "record_count": 6,
                    "freshness_status": "fresh",
                    "evidence_ref": "OUT/metrics/video_metrics.jsonl",
                },
                qc_history_summary={"record_count": 4, "freshness_status": "fresh"},
                failure_history_summary={"available": True, "record_count": 0, "freshness_status": "fresh"},
                format_repetition_summary={"record_count": 5, "freshness_status": "fresh"},
            )
        )

        summary = result.telemetry_summary
        self.assertEqual(result.decision.status, "SAFE")
        self.assertEqual(summary["lineage_summary"]["absent_source_count"], 0)
        self.assertGreaterEqual(summary["lineage_summary"]["real_source_count"], 5)
        self.assertFalse(summary["degraded_input_mode"])
        self.assertIn("publish_history", summary["available_signals"])
        self.assertEqual(summary["freshness_summary"]["fresh_source_count"], 5)
        self.assertIn("telemetry_enrichment", result.decision_trace)
        self.assertEqual(
            result.decision_trace["telemetry_enrichment"]["lineage_summary"],
            summary["lineage_summary"],
        )

    def test_missing_optional_telemetry_is_visible_without_changing_decision(self) -> None:
        service = AccountHealthAgentService()

        result = service.evaluate(
            AccountHealthInput(
                account_id="acc_health_telemetry_missing",
                recent_publish_count=1,
                recent_format_repetition_ratio=0.10,
                recent_views_drop_ratio=0.05,
                recent_low_performance_streak=0,
            )
        )

        summary = result.telemetry_summary
        self.assertEqual(result.decision.status, "SAFE")
        self.assertEqual(summary["lineage_summary"]["real_source_count"], 1)
        self.assertEqual(summary["lineage_summary"]["absent_source_count"], 4)
        self.assertTrue(summary["degraded_input_mode"])
        self.assertIn("MISSING_OPTIONAL_TELEMETRY", summary["degradation_reasons"])
        self.assertIn("LEGACY_SCALAR_INPUT_ONLY", summary["degradation_reasons"])
        self.assertEqual(
            set(summary["missing_signals"]),
            {"failure_history", "format_repetition", "metric_window", "qc_history"},
        )

    def test_stale_and_degraded_telemetry_are_classified_explicitly(self) -> None:
        enricher = AccountHealthTelemetryEnricher()

        summary = enricher.enrich(
            AccountHealthInput(
                account_id="acc_health_telemetry_stale",
                recent_publish_count=2,
                telemetry_sources=[
                    {
                        "source_name": "metric_window",
                        "source_status": "REAL",
                        "record_count": 8,
                        "freshness_status": "stale",
                        "evidence_ref": "OUT/metrics/video_metrics.jsonl",
                    },
                    {
                        "source_name": "qc_history",
                        "source_status": "DEGRADED",
                        "record_count": 2,
                        "reason_codes": ["LOW_SIGNAL_QC_HISTORY"],
                    },
                ],
            )
        ).to_dict()

        statuses = {source["source_name"]: source for source in summary["source_summaries"]}
        self.assertEqual(statuses["metric_window"]["source_status"], "STALE")
        self.assertEqual(statuses["qc_history"]["source_status"], "DEGRADED")
        self.assertEqual(summary["source_status_distribution"]["STALE"], 1)
        self.assertEqual(summary["source_status_distribution"]["DEGRADED"], 1)
        self.assertIn("STALE_TELEMETRY_PRESENT", summary["degradation_reasons"])
        self.assertIn("DEGRADED_TELEMETRY_PRESENT", summary["degradation_reasons"])

    def test_result_serializes_telemetry_summary_and_remains_deterministic(self) -> None:
        service = AccountHealthAgentService()
        data = AccountHealthInput(
            account_id="acc_health_telemetry_serialized",
            recent_publish_count=4,
            recent_format_repetition_ratio=0.70,
            recent_views_drop_ratio=0.45,
            recent_low_performance_streak=2,
            telemetry_sources=[
                {
                    "source_name": "publish_history",
                    "record_count": 4,
                    "freshness_status": "fresh",
                }
            ],
        )

        first = service.evaluate(data).to_dict()
        second = service.evaluate(data).to_dict()

        self.assertEqual(first, second)
        self.assertEqual(first["decision"]["status"], "CAUTION")
        self.assertIn("telemetry_summary", first)
        self.assertIn("source_summaries", first["telemetry_summary"])
        self.assertIn("telemetry_enrichment", first["decision_trace"])
        self.assertEqual(
            first["decision_trace"]["telemetry_enrichment"]["source_status_distribution"],
            first["telemetry_summary"]["source_status_distribution"],
        )


if __name__ == "__main__":
    unittest.main()
