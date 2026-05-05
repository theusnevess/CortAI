from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.account_health.models import AccountHealthInput
from app.creative.agents.account_health.service import AccountHealthAgentService


def _input_with_windows(
    *,
    metric_previous: float = 0.10,
    metric_recent: float = 0.10,
    qc_previous: int = 0,
    qc_recent: int = 0,
    repetition_previous: float = 0.20,
    repetition_recent: float = 0.20,
    failure_previous: float = 0.0,
    failure_recent: float = 0.0,
    metric_freshness: str = "fresh",
    qc_status: str = "REAL",
) -> AccountHealthInput:
    return AccountHealthInput(
        account_id="acc_temporal_health",
        recent_publish_count=2,
        recent_views_drop_ratio=metric_recent,
        recent_low_performance_streak=qc_recent,
        recent_format_repetition_ratio=repetition_recent,
        telemetry_sources=[
            {
                "source_name": "publish_history",
                "record_count": 4,
                "freshness_status": "fresh",
            }
        ],
        metric_window_summary={
            "record_count": 8,
            "freshness_status": metric_freshness,
            "previous_window": {"views_drop_ratio": metric_previous},
            "recent_window": {"views_drop_ratio": metric_recent},
        },
        qc_history_summary={
            "source_status": qc_status,
            "record_count": 8,
            "freshness_status": "fresh",
            "previous_window": {"low_quality_streak": qc_previous},
            "recent_window": {"low_quality_streak": qc_recent},
        },
        failure_history_summary={
            "record_count": 8,
            "freshness_status": "fresh",
            "previous_window": {"fallback_rate": failure_previous},
            "recent_window": {"fallback_rate": failure_recent},
        },
        format_repetition_summary={
            "record_count": 8,
            "freshness_status": "fresh",
            "previous_window": {"repetition_ratio": repetition_previous},
            "recent_window": {"repetition_ratio": repetition_recent},
        },
    )


class AccountHealthTemporalHealthTests(unittest.TestCase):
    def test_stable_classification_with_consistent_windows(self) -> None:
        result = AccountHealthAgentService().evaluate(_input_with_windows())

        self.assertEqual(result.temporal_health["classification"], "stable")
        self.assertEqual(result.temporal_health["risk_direction"], "flat")
        self.assertEqual(result.temporal_health["confidence_impact"], "positive")
        self.assertIn("TEMPORAL_RISK_FLAT", result.temporal_health["reason_codes"])

    def test_degrading_classification_with_recent_risk_increase(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input_with_windows(
                metric_previous=0.10,
                metric_recent=0.45,
                qc_previous=0,
                qc_recent=2,
                repetition_previous=0.20,
                repetition_recent=0.70,
            )
        )

        self.assertEqual(result.temporal_health["classification"], "degrading")
        self.assertEqual(result.temporal_health["risk_direction"], "up")
        self.assertIn("RECENT_RISK_INCREASE", result.temporal_health["reason_codes"])

    def test_recovering_classification_with_recent_risk_decrease(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input_with_windows(
                metric_previous=0.70,
                metric_recent=0.20,
                qc_previous=3,
                qc_recent=1,
                repetition_previous=0.80,
                repetition_recent=0.30,
            )
        )

        self.assertEqual(result.temporal_health["classification"], "recovering")
        self.assertEqual(result.temporal_health["risk_direction"], "down")
        self.assertEqual(result.temporal_health["confidence_impact"], "positive")
        self.assertIn("RECENT_RISK_DECREASE", result.temporal_health["reason_codes"])

    def test_volatile_classification_with_conflicting_signals(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input_with_windows(
                metric_previous=0.10,
                metric_recent=0.55,
                qc_previous=3,
                qc_recent=0,
                repetition_previous=0.20,
                repetition_recent=0.70,
            )
        )

        self.assertEqual(result.temporal_health["classification"], "volatile")
        self.assertEqual(result.temporal_health["risk_direction"], "mixed")
        self.assertEqual(result.temporal_health["confidence_impact"], "negative")
        self.assertIn("TEMPORAL_SIGNAL_CONFLICT", result.temporal_health["reason_codes"])

    def test_insufficient_evidence_when_no_history_exists(self) -> None:
        result = AccountHealthAgentService().evaluate(AccountHealthInput(account_id="acc_no_temporal_history"))

        self.assertEqual(result.temporal_health["classification"], "insufficient_evidence")
        self.assertEqual(result.temporal_health["risk_direction"], "unknown")
        self.assertIn("TEMPORAL_HISTORY_INSUFFICIENT", result.temporal_health["reason_codes"])

    def test_stale_or_degraded_temporal_evidence_does_not_produce_fake_stable(self) -> None:
        stale = AccountHealthAgentService().evaluate(
            replace(
                _input_with_windows(),
                metric_window_summary={
                    "record_count": 8,
                    "freshness_status": "stale",
                    "previous_window": {"views_drop_ratio": 0.10},
                    "recent_window": {"views_drop_ratio": 0.10},
                },
                qc_history_summary={
                    "source_status": "DEGRADED",
                    "record_count": 8,
                    "previous_window": {"low_quality_streak": 0},
                    "recent_window": {"low_quality_streak": 0},
                },
                failure_history_summary={},
                format_repetition_summary={},
            )
        )

        self.assertEqual(stale.temporal_health["classification"], "insufficient_evidence")
        self.assertIn("TEMPORAL_EVIDENCE_NOT_REAL", stale.temporal_health["reason_codes"])

    def test_temporal_health_appears_in_result_and_trace(self) -> None:
        payload = AccountHealthAgentService().evaluate(_input_with_windows()).to_dict()

        self.assertIn("temporal_health", payload)
        self.assertEqual(payload["temporal_health"]["classification"], "stable")
        self.assertIn("temporal_health", payload["decision_trace"])
        self.assertEqual(payload["decision_trace"]["temporal_health"]["classification"], "stable")

    def test_temporal_classification_is_deterministic(self) -> None:
        service = AccountHealthAgentService()
        data = _input_with_windows(metric_previous=0.10, metric_recent=0.45, qc_previous=0, qc_recent=2)

        first = service.evaluate(data).to_dict()
        second = service.evaluate(data).to_dict()

        self.assertEqual(first["temporal_health"], second["temporal_health"])
        self.assertEqual(first["decision_trace"]["temporal_health"], second["decision_trace"]["temporal_health"])

    def test_temporal_impact_appears_in_confidence_rationale(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input_with_windows(metric_previous=0.10, metric_recent=0.55, qc_previous=3, qc_recent=0)
        )

        temporal = result.confidence_rationale["temporal_health"]
        self.assertEqual(temporal["classification"], result.temporal_health["classification"])
        self.assertEqual(temporal["confidence_impact"], result.temporal_health["confidence_impact"])

    def test_safe_caution_hold_behavior_remains_stable(self) -> None:
        service = AccountHealthAgentService()

        self.assertEqual(service.evaluate(_input_with_windows()).decision.status, "SAFE")
        self.assertEqual(
            service.evaluate(
                _input_with_windows(
                    metric_previous=0.45,
                    metric_recent=0.45,
                    qc_previous=2,
                    qc_recent=2,
                    repetition_previous=0.70,
                    repetition_recent=0.70,
                )
            ).decision.status,
            "CAUTION",
        )
        self.assertEqual(
            service.evaluate(
                _input_with_windows(
                    metric_previous=0.80,
                    metric_recent=0.80,
                    qc_previous=4,
                    qc_recent=4,
                )
            ).decision.status,
            "HOLD",
        )

    def test_hold_early_block_inputs_remain_preserved(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input_with_windows(metric_previous=0.70, metric_recent=0.80, qc_previous=3, qc_recent=4)
        )

        self.assertEqual(result.decision.status, "HOLD")
        self.assertTrue(result.decision.recommended_constraints["block_generation"])
        self.assertTrue(result.decision_trace["threshold_evaluations"]["hold_on_views_drop"])


if __name__ == "__main__":
    unittest.main()
