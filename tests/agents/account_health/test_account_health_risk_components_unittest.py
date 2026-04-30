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


def _clean_input(
    *,
    recent_publish_count: int = 2,
    recent_views_drop_ratio: float = 0.05,
    recent_format_repetition_ratio: float = 0.10,
    recent_low_performance_streak: int = 0,
) -> AccountHealthInput:
    return AccountHealthInput(
        account_id="acc_health_risk_components",
        recent_publish_count=recent_publish_count,
        recent_views_drop_ratio=recent_views_drop_ratio,
        recent_format_repetition_ratio=recent_format_repetition_ratio,
        recent_low_performance_streak=recent_low_performance_streak,
        telemetry_sources=[
            {
                "source_name": "publish_history",
                "source_type": "jsonl",
                "record_count": max(recent_publish_count, 1),
                "freshness_status": "fresh",
                "evidence_ref": "OUT/data/publish_records/publish_records.jsonl",
            }
        ],
        metric_window_summary={
            "record_count": 8,
            "freshness_status": "fresh",
            "evidence_ref": "OUT/metrics/video_metrics.jsonl",
        },
        qc_history_summary={
            "record_count": 8,
            "freshness_status": "fresh",
            "evidence_ref": "OUT/history/qc_summary.json",
        },
        failure_history_summary={
            "available": True,
            "record_count": 0,
            "freshness_status": "fresh",
            "evidence_ref": "OUT/history/failures.json",
        },
        format_repetition_summary={
            "record_count": 8,
            "freshness_status": "fresh",
            "evidence_ref": "OUT/history/format_repetition.json",
        },
    )


class AccountHealthRiskComponentTests(unittest.TestCase):
    def test_low_risk_clean_telemetry(self) -> None:
        result = AccountHealthAgentService().evaluate(_clean_input())

        self.assertEqual(result.decision.status, "SAFE")
        self.assertLess(result.risk_score, 0.34)
        self.assertEqual(result.risk_components["overall_risk_level"], "low")
        for component in result.risk_components["components"].values():
            self.assertEqual(component["level"], "low")
            self.assertEqual(component["evidence_status"], "REAL")
            self.assertTrue(component["rationale"])
            self.assertTrue(component["thresholds"])

    def test_medium_risk_telemetry(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _clean_input(
                recent_publish_count=5,
                recent_views_drop_ratio=0.45,
                recent_format_repetition_ratio=0.60,
                recent_low_performance_streak=2,
            )
        )

        self.assertEqual(result.decision.status, "CAUTION")
        self.assertEqual(result.risk_components["overall_risk_level"], "medium")
        self.assertEqual(result.risk_components["components"]["publish_frequency_risk"]["level"], "medium")
        self.assertEqual(result.risk_components["components"]["performance_drop_risk"]["level"], "medium")
        self.assertEqual(result.risk_components["components"]["repetition_risk"]["level"], "medium")
        self.assertEqual(result.risk_components["components"]["low_quality_streak_risk"]["level"], "medium")

    def test_high_risk_telemetry(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _clean_input(
                recent_publish_count=9,
                recent_views_drop_ratio=0.82,
                recent_format_repetition_ratio=0.90,
                recent_low_performance_streak=4,
            )
        )

        self.assertEqual(result.decision.status, "HOLD")
        self.assertEqual(result.risk_components["overall_risk_level"], "high")
        self.assertIn("performance_drop_risk", result.risk_components["dominant_components"])
        self.assertIn("low_quality_streak_risk", result.risk_components["dominant_components"])

    def test_missing_telemetry_produces_absent_evidence_status(self) -> None:
        result = AccountHealthAgentService().evaluate(
            AccountHealthInput(
                account_id="acc_missing_component_sources",
                recent_publish_count=0,
                recent_views_drop_ratio=0.0,
                recent_format_repetition_ratio=0.0,
                recent_low_performance_streak=0,
            )
        )

        components = result.risk_components["components"]
        self.assertEqual(components["publish_frequency_risk"]["evidence_status"], "ABSENT")
        self.assertEqual(components["performance_drop_risk"]["evidence_status"], "ABSENT")
        self.assertEqual(components["repetition_risk"]["evidence_status"], "ABSENT")
        self.assertEqual(components["low_quality_streak_risk"]["evidence_status"], "ABSENT")
        self.assertEqual(components["fallback_contamination_risk"]["evidence_status"], "ABSENT")
        self.assertGreaterEqual(result.risk_score, 0.34)
        self.assertEqual(result.risk_components["overall_risk_level"], "medium")
        self.assertEqual(
            set(result.risk_components["missing_component_inputs"]),
            {
                "publish_frequency_risk",
                "performance_drop_risk",
                "repetition_risk",
                "low_quality_streak_risk",
                "fallback_contamination_risk",
            },
        )

    def test_stale_telemetry_produces_stale_evidence_status(self) -> None:
        result = AccountHealthAgentService().evaluate(
            AccountHealthInput(
                account_id="acc_stale_metric_window",
                recent_publish_count=2,
                recent_views_drop_ratio=0.05,
                metric_window_summary={
                    "record_count": 8,
                    "freshness_status": "stale",
                    "evidence_ref": "OUT/metrics/video_metrics.jsonl",
                },
            )
        )

        component = result.risk_components["components"]["performance_drop_risk"]
        self.assertEqual(component["evidence_status"], "STALE")
        self.assertGreaterEqual(component["score"], 0.40)
        self.assertIn("performance_drop_risk", result.risk_components["degraded_component_inputs"])

    def test_degraded_telemetry_produces_degraded_evidence_status(self) -> None:
        result = AccountHealthAgentService().evaluate(
            AccountHealthInput(
                account_id="acc_degraded_qc_history",
                recent_publish_count=2,
                recent_low_performance_streak=0,
                qc_history_summary={
                    "source_status": "DEGRADED",
                    "record_count": 2,
                    "reason_codes": ["LOW_SIGNAL_QC_HISTORY"],
                },
            )
        )

        component = result.risk_components["components"]["low_quality_streak_risk"]
        self.assertEqual(component["evidence_status"], "DEGRADED")
        self.assertGreaterEqual(component["score"], 0.50)
        self.assertIn("low_quality_streak_risk", result.risk_components["degraded_component_inputs"])

    def test_overall_risk_score_is_deterministic(self) -> None:
        service = AccountHealthAgentService()
        data = _clean_input(
            recent_publish_count=5,
            recent_views_drop_ratio=0.45,
            recent_format_repetition_ratio=0.60,
            recent_low_performance_streak=2,
        )

        first = service.evaluate(data).to_dict()
        second = service.evaluate(data).to_dict()

        self.assertEqual(first["risk_score"], second["risk_score"])
        self.assertEqual(first["risk_components"], second["risk_components"])
        self.assertEqual(first["decision_trace"]["overall_risk"], second["decision_trace"]["overall_risk"])

    def test_risk_components_appear_in_result_and_decision_trace(self) -> None:
        result = AccountHealthAgentService().evaluate(_clean_input(recent_publish_count=5))
        payload = result.to_dict()

        self.assertIn("risk_score", payload)
        self.assertIn("risk_components", payload)
        self.assertIn("risk_components", payload["decision_trace"])
        self.assertIn("overall_risk", payload["decision_trace"])
        self.assertEqual(
            payload["decision_trace"]["overall_risk"]["score"],
            payload["risk_components"]["overall_risk_score"],
        )

    def test_safe_caution_hold_behavior_does_not_regress(self) -> None:
        service = AccountHealthAgentService()

        self.assertEqual(service.evaluate(_clean_input()).decision.status, "SAFE")
        self.assertEqual(
            service.evaluate(
                _clean_input(
                    recent_publish_count=3,
                    recent_views_drop_ratio=0.45,
                    recent_format_repetition_ratio=0.70,
                    recent_low_performance_streak=2,
                )
            ).decision.status,
            "CAUTION",
        )
        self.assertEqual(
            service.evaluate(
                _clean_input(
                    recent_publish_count=5,
                    recent_views_drop_ratio=0.80,
                    recent_low_performance_streak=4,
                )
            ).decision.status,
            "HOLD",
        )

    def test_missing_values_do_not_create_fake_healthy_risk(self) -> None:
        result = AccountHealthAgentService().evaluate(AccountHealthInput(account_id="acc_no_telemetry"))

        self.assertEqual(result.decision.status, "SAFE")
        self.assertEqual(result.risk_components["overall_risk_level"], "medium")
        self.assertGreaterEqual(result.risk_score, 0.34)
        for component in result.risk_components["components"].values():
            self.assertNotEqual(component["evidence_status"], "REAL")
            self.assertGreaterEqual(component["score"], 0.34)
            self.assertIn("ABSENT", component["reason_code"])


if __name__ == "__main__":
    unittest.main()
