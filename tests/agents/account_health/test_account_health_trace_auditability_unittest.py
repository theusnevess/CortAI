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


REQUIRED_HEALTH_TRACE_SECTIONS = {
    "telemetry_lineage",
    "risk_assessment",
    "confidence_calibration",
    "temporal_health",
    "degraded_input_policy",
    "constraint_rationale",
    "final_decision_rationale",
    "downgraded_or_missing_inputs",
    "audit_summary",
}


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
        account_id="acc_health_trace",
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


class AccountHealthTraceAuditabilityTests(unittest.TestCase):
    def test_health_trace_exists_in_account_health_result(self) -> None:
        result = AccountHealthAgentService().evaluate(_input())

        self.assertIsInstance(result.health_trace, dict)
        self.assertTrue(result.health_trace)

    def test_health_trace_exists_in_decision_trace(self) -> None:
        result = AccountHealthAgentService().evaluate(_input())

        self.assertIn("health_trace", result.decision_trace)
        self.assertEqual(result.decision_trace["health_trace"], result.health_trace)

    def test_all_required_sections_are_present(self) -> None:
        result = AccountHealthAgentService().evaluate(_input())

        self.assertTrue(REQUIRED_HEALTH_TRACE_SECTIONS.issubset(set(result.health_trace)))
        self.assertTrue(result.health_trace["audit_summary"]["required_sections_present"])

    def test_final_decision_rationale_reconstructs_safe(self) -> None:
        result = AccountHealthAgentService().evaluate(_input())

        rationale = result.health_trace["final_decision_rationale"]
        self.assertEqual(result.decision.status, "SAFE")
        self.assertEqual(rationale["base_decision"], "SAFE")
        self.assertEqual(rationale["final_decision"], "SAFE")
        self.assertFalse(rationale["decision_adjusted"])
        self.assertFalse(rationale["hold_authority_invoked"])

    def test_final_decision_rationale_reconstructs_caution(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input(
                recent_views_drop_ratio=0.45,
                recent_format_repetition_ratio=0.70,
                recent_low_performance_streak=2,
            )
        )

        rationale = result.health_trace["final_decision_rationale"]
        self.assertEqual(result.decision.status, "CAUTION")
        self.assertEqual(rationale["base_decision"], "CAUTION")
        self.assertEqual(rationale["final_decision"], "CAUTION")
        self.assertIn("RECENT_VIEWS_DROP", rationale["dominant_reason_codes"])
        self.assertFalse(rationale["hold_authority_invoked"])

    def test_final_decision_rationale_reconstructs_hold(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input(recent_views_drop_ratio=0.80, recent_low_performance_streak=4)
        )

        rationale = result.health_trace["final_decision_rationale"]
        self.assertEqual(result.decision.status, "HOLD")
        self.assertEqual(rationale["base_decision"], "HOLD")
        self.assertEqual(rationale["final_decision"], "HOLD")
        self.assertTrue(rationale["hold_authority_invoked"])

    def test_degraded_safe_to_caution_adjustment_is_reconstructible(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input(metric_status="STALE", metric_freshness="stale", qc_status="DEGRADED")
        )

        rationale = result.health_trace["final_decision_rationale"]
        self.assertEqual(result.decision.status, "CAUTION")
        self.assertEqual(rationale["base_decision"], "SAFE")
        self.assertEqual(rationale["final_decision"], "CAUTION")
        self.assertTrue(rationale["decision_adjusted"])
        self.assertEqual(rationale["adjustment_reason"], "upgrade_to_caution")
        self.assertEqual(rationale["degraded_input_severity"], "moderate")

    def test_hold_authority_invocation_is_visible(self) -> None:
        result = AccountHealthAgentService().evaluate(_severe_degraded_safe_input())

        rationale = result.health_trace["final_decision_rationale"]
        self.assertEqual(result.decision.status, "HOLD")
        self.assertTrue(rationale["hold_authority_invoked"])
        self.assertEqual(rationale["base_decision"], "SAFE")
        self.assertEqual(rationale["adjustment_reason"], "upgrade_to_hold")

    def test_downgraded_or_missing_inputs_include_absent_stale_and_degraded_signals(self) -> None:
        absent_result = AccountHealthAgentService().evaluate(AccountHealthInput(account_id="acc_missing_trace"))
        degraded_result = AccountHealthAgentService().evaluate(
            _input(metric_status="STALE", metric_freshness="stale", qc_status="DEGRADED")
        )

        absent_statuses = {item["status"] for item in absent_result.health_trace["downgraded_or_missing_inputs"]}
        degraded_statuses = {item["status"] for item in degraded_result.health_trace["downgraded_or_missing_inputs"]}
        self.assertIn("ABSENT", absent_statuses)
        self.assertIn("STALE", degraded_statuses)
        self.assertIn("DEGRADED", degraded_statuses)
        for item in degraded_result.health_trace["downgraded_or_missing_inputs"]:
            self.assertIn(item["impact"], {"risk_component", "confidence", "degraded_input_policy", "temporal_health"})
            self.assertTrue(item["rationale"])

    def test_constraint_coverage_is_complete(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input(
                recent_views_drop_ratio=0.45,
                recent_format_repetition_ratio=0.70,
                recent_low_performance_streak=2,
            )
        )

        summary = result.health_trace["audit_summary"]
        constraint_keys = set(result.decision.recommended_constraints)
        rationale_keys = {item["constraint_key"] for item in result.health_trace["constraint_rationale"]}
        self.assertEqual(rationale_keys, constraint_keys)
        self.assertTrue(summary["constraint_coverage_complete"])

    def test_trace_is_deterministic_for_same_input(self) -> None:
        service = AccountHealthAgentService()
        data = _input(metric_status="STALE", metric_freshness="stale", qc_status="DEGRADED")

        first = service.evaluate(data).to_dict()
        second = service.evaluate(data).to_dict()

        self.assertEqual(first["health_trace"], second["health_trace"])
        self.assertEqual(first["decision_trace"]["health_trace"], second["decision_trace"]["health_trace"])

    def test_decision_trace_remains_backward_compatible(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input(
                recent_views_drop_ratio=0.45,
                recent_format_repetition_ratio=0.70,
                recent_low_performance_streak=2,
            )
        )

        expected_existing_keys = {
            "input_summary",
            "telemetry_enrichment",
            "risk_components",
            "overall_risk",
            "temporal_health",
            "confidence_calibration",
            "degraded_input_policy",
            "decision_adjustment",
            "constraint_rationale",
            "constraint_rationale_summary",
            "thresholds",
            "threshold_evaluations",
            "triggered_conditions",
            "reasons_emitted",
            "constraints_emitted",
            "final_status",
            "fallback_used",
            "fallback_reason",
        }
        self.assertTrue(expected_existing_keys.issubset(set(result.decision_trace)))
        self.assertTrue(result.health_trace["audit_summary"]["decision_trace_backward_compatible"])

    def test_no_safe_caution_hold_behavior_change(self) -> None:
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
