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


def _input(
    *,
    recent_publish_count: int = 2,
    recent_views_drop_ratio: float = 0.05,
    recent_format_repetition_ratio: float = 0.10,
    recent_low_performance_streak: int = 0,
    publish_status: str = "REAL",
    metric_status: str = "REAL",
    metric_freshness: str = "fresh",
    qc_status: str = "REAL",
    failure_status: str = "REAL",
    format_status: str = "REAL",
) -> AccountHealthInput:
    return AccountHealthInput(
        account_id="acc_degraded_policy",
        recent_publish_count=recent_publish_count,
        recent_views_drop_ratio=recent_views_drop_ratio,
        recent_format_repetition_ratio=recent_format_repetition_ratio,
        recent_low_performance_streak=recent_low_performance_streak,
        telemetry_sources=[
            {
                "source_name": "publish_history",
                "source_status": publish_status,
                "record_count": max(recent_publish_count, 1),
                "freshness_status": "fresh",
            }
        ],
        metric_window_summary={
            "source_status": metric_status,
            "record_count": 8,
            "freshness_status": metric_freshness,
            "previous_window": {"views_drop_ratio": recent_views_drop_ratio},
            "recent_window": {"views_drop_ratio": recent_views_drop_ratio},
        },
        qc_history_summary={
            "source_status": qc_status,
            "record_count": 8,
            "freshness_status": "fresh",
            "previous_window": {"low_quality_streak": recent_low_performance_streak},
            "recent_window": {"low_quality_streak": recent_low_performance_streak},
        },
        failure_history_summary={
            "source_status": failure_status,
            "record_count": 8,
            "freshness_status": "fresh",
            "previous_window": {"fallback_rate": 0.0},
            "recent_window": {"fallback_rate": 0.0},
        },
        format_repetition_summary={
            "source_status": format_status,
            "record_count": 8,
            "freshness_status": "fresh",
            "previous_window": {"repetition_ratio": recent_format_repetition_ratio},
            "recent_window": {"repetition_ratio": recent_format_repetition_ratio},
        },
    )


def _severe_degraded_safe_input() -> AccountHealthInput:
    return _input(
        publish_status="DEGRADED",
        metric_status="STALE",
        metric_freshness="stale",
        qc_status="DEGRADED",
        failure_status="DEGRADED",
        format_status="STALE",
    )


class AccountHealthDegradedInputPolicyTests(unittest.TestCase):
    def test_clean_strong_telemetry_safe_remains_safe(self) -> None:
        result = AccountHealthAgentService().evaluate(_input())

        self.assertEqual(result.decision.status, "SAFE")
        self.assertFalse(result.degraded_input_decision["degraded_input_detected"])
        self.assertEqual(result.degraded_input_decision["severity"], "none")
        self.assertEqual(result.degraded_input_decision["action"], "no_change")
        self.assertFalse(result.decision_trace["decision_adjustment"]["changed"])

    def test_minor_degradation_safe_remains_safe_with_trace(self) -> None:
        result = AccountHealthAgentService().evaluate(replace(_input(), failure_history_summary={}))

        self.assertEqual(result.decision.status, "SAFE")
        self.assertTrue(result.degraded_input_decision["degraded_input_detected"])
        self.assertEqual(result.degraded_input_decision["severity"], "minor")
        self.assertEqual(result.degraded_input_decision["action"], "no_change")
        self.assertIn("degraded_input_policy", result.decision_trace)

    def test_moderate_degradation_safe_upgrades_to_caution(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input(metric_status="STALE", metric_freshness="stale", qc_status="DEGRADED")
        )

        self.assertEqual(result.degraded_input_decision["original_decision"], "SAFE")
        self.assertEqual(result.decision.status, "CAUTION")
        self.assertEqual(result.degraded_input_decision["severity"], "moderate")
        self.assertEqual(result.degraded_input_decision["action"], "upgrade_to_caution")
        self.assertTrue(result.decision.recommended_constraints["degraded_input_caution"])
        self.assertTrue(result.decision.recommended_constraints["require_monitoring"])

    def test_severe_degradation_and_high_fallback_risk_safe_upgrades_to_hold(self) -> None:
        result = AccountHealthAgentService().evaluate(_severe_degraded_safe_input())

        self.assertEqual(result.degraded_input_decision["original_decision"], "SAFE")
        self.assertEqual(result.decision.status, "HOLD")
        self.assertEqual(result.degraded_input_decision["severity"], "severe")
        self.assertEqual(result.degraded_input_decision["action"], "upgrade_to_hold")
        self.assertIn("SEVERE_DEGRADED_INPUT_WITH_HIGH_RISK", result.decision.reasons)
        self.assertTrue(result.decision.recommended_constraints["block_generation"])

    def test_caution_remains_caution_under_moderate_degradation(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input(
                recent_views_drop_ratio=0.45,
                recent_format_repetition_ratio=0.70,
                recent_low_performance_streak=2,
                metric_status="STALE",
                metric_freshness="stale",
            )
        )

        self.assertEqual(result.degraded_input_decision["original_decision"], "CAUTION")
        self.assertEqual(result.decision.status, "CAUTION")
        self.assertNotEqual(result.degraded_input_decision["action"], "upgrade_to_hold")

    def test_caution_upgrades_to_hold_only_under_severe_degradation_and_high_risk(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input(
                recent_views_drop_ratio=0.45,
                recent_format_repetition_ratio=0.70,
                recent_low_performance_streak=2,
                publish_status="DEGRADED",
                metric_status="STALE",
                metric_freshness="stale",
                qc_status="DEGRADED",
                failure_status="DEGRADED",
                format_status="STALE",
            )
        )

        self.assertEqual(result.degraded_input_decision["original_decision"], "CAUTION")
        self.assertEqual(result.decision.status, "HOLD")
        self.assertEqual(result.degraded_input_decision["action"], "upgrade_to_hold")

    def test_hold_remains_hold_and_is_never_downgraded(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input(recent_views_drop_ratio=0.80, recent_low_performance_streak=4)
        )

        self.assertEqual(result.degraded_input_decision["original_decision"], "HOLD")
        self.assertEqual(result.degraded_input_decision["final_decision"], "HOLD")
        self.assertEqual(result.decision.status, "HOLD")
        self.assertEqual(result.degraded_input_decision["action"], "no_change")

    def test_missing_telemetry_does_not_silently_remain_fully_trusted_safe(self) -> None:
        result = AccountHealthAgentService().evaluate(AccountHealthInput(account_id="acc_missing_only"))

        self.assertEqual(result.decision.status, "SAFE")
        self.assertTrue(result.degraded_input_decision["degraded_input_detected"])
        self.assertNotEqual(result.confidence_level, "high")
        self.assertIn("ABSENT_TELEMETRY_PRESENT", result.degraded_input_decision["reason_codes"])

    def test_degraded_policy_trace_and_decision_adjustment_are_explicit(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input(metric_status="STALE", metric_freshness="stale", qc_status="DEGRADED")
        )

        trace = result.decision_trace
        self.assertIn("degraded_input_policy", trace)
        self.assertIn("decision_adjustment", trace)
        self.assertTrue(trace["decision_adjustment"]["changed"])
        self.assertEqual(trace["decision_adjustment"]["from"], "SAFE")
        self.assertEqual(trace["decision_adjustment"]["to"], "CAUTION")

    def test_deterministic_same_input_same_output(self) -> None:
        service = AccountHealthAgentService()
        data = _input(metric_status="STALE", metric_freshness="stale", qc_status="DEGRADED")

        first = service.evaluate(data).to_dict()
        second = service.evaluate(data).to_dict()

        self.assertEqual(first, second)

    def test_normal_clean_safe_caution_hold_behavior_remains_stable(self) -> None:
        service = AccountHealthAgentService()

        self.assertEqual(service.evaluate(_input()).decision.status, "SAFE")
        self.assertEqual(
            service.evaluate(
                _input(
                    recent_views_drop_ratio=0.45,
                    recent_format_repetition_ratio=0.70,
                    recent_low_performance_streak=2,
                )
            ).decision.status,
            "CAUTION",
        )
        self.assertEqual(
            service.evaluate(
                _input(
                    recent_views_drop_ratio=0.80,
                    recent_low_performance_streak=4,
                )
            ).decision.status,
            "HOLD",
        )


if __name__ == "__main__":
    unittest.main()
