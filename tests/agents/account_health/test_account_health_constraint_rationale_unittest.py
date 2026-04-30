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
        account_id="acc_constraint_rationale",
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


def _rationale_by_key(result) -> dict[str, dict[str, object]]:  # noqa: ANN001
    return {item["constraint_key"]: item for item in result.constraint_rationale}


class AccountHealthConstraintRationaleTests(unittest.TestCase):
    def test_empty_recommended_constraints_produces_empty_rationale_and_explicit_trace(self) -> None:
        result = AccountHealthAgentService().evaluate(_input())

        self.assertEqual(result.decision.status, "SAFE")
        self.assertEqual(result.decision.recommended_constraints, {})
        self.assertEqual(result.constraint_rationale, [])
        self.assertEqual(result.decision_trace["constraint_rationale"], [])
        self.assertFalse(result.decision_trace["constraint_rationale_summary"]["constraints_emitted"])
        self.assertTrue(result.decision_trace["constraint_rationale_summary"]["coverage_complete"])

    def test_degraded_input_caution_has_cautionary_rationale(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input(metric_status="STALE", metric_freshness="stale", qc_status="DEGRADED")
        )

        rationale = _rationale_by_key(result)["degraded_input_caution"]
        self.assertEqual(result.decision.status, "CAUTION")
        self.assertEqual(rationale["interpretation_mode"], "cautionary")
        self.assertEqual(rationale["source"], "degraded_input_policy")
        self.assertEqual(rationale["severity"], "medium")
        self.assertEqual(rationale["reason_code"], "DEGRADED_INPUT_CAUTION")

    def test_require_monitoring_has_rationale(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input(metric_status="STALE", metric_freshness="stale", qc_status="DEGRADED")
        )

        rationale = _rationale_by_key(result)["require_monitoring"]
        self.assertEqual(rationale["interpretation_mode"], "cautionary")
        self.assertIn(rationale["source"], {"degraded_input_policy", "confidence_calibration"})
        self.assertTrue(rationale["rationale"])
        self.assertTrue(rationale["downstream_interpretation"])

    def test_block_generation_has_blocking_rationale(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input(recent_views_drop_ratio=0.80, recent_low_performance_streak=4)
        )

        rationale = _rationale_by_key(result)["block_generation"]
        self.assertEqual(result.decision.status, "HOLD")
        self.assertEqual(rationale["interpretation_mode"], "blocking")
        self.assertEqual(rationale["severity"], "high")
        self.assertEqual(rationale["source"], "base_decision")
        self.assertEqual(rationale["reason_code"], "ACCOUNT_HEALTH_HOLD_BLOCK_GENERATION")

    def test_caution_constraints_are_cautionary_not_blocking(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input(
                recent_views_drop_ratio=0.45,
                recent_format_repetition_ratio=0.70,
                recent_low_performance_streak=2,
            )
        )

        rationales = _rationale_by_key(result)
        self.assertEqual(result.decision.status, "CAUTION")
        self.assertEqual(rationales["reduce_hook_aggressiveness"]["interpretation_mode"], "cautionary")
        self.assertEqual(rationales["max_daily_posts"]["interpretation_mode"], "cautionary")
        self.assertNotEqual(rationales["reduce_hook_aggressiveness"]["interpretation_mode"], "blocking")
        self.assertNotEqual(rationales["max_daily_posts"]["interpretation_mode"], "blocking")

    def test_hold_constraints_are_blocking_when_appropriate(self) -> None:
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

        rationale = _rationale_by_key(result)["block_generation"]
        self.assertEqual(result.decision.status, "HOLD")
        self.assertEqual(rationale["interpretation_mode"], "blocking")
        self.assertEqual(rationale["source"], "degraded_input_policy")

    def test_every_recommended_constraint_has_exactly_one_rationale(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input(
                recent_views_drop_ratio=0.45,
                recent_format_repetition_ratio=0.70,
                recent_low_performance_streak=2,
            )
        )

        constraint_keys = set(result.decision.recommended_constraints)
        rationale_keys = [item["constraint_key"] for item in result.constraint_rationale]
        self.assertEqual(set(rationale_keys), constraint_keys)
        self.assertEqual(len(rationale_keys), len(set(rationale_keys)))
        self.assertTrue(result.decision_trace["constraint_rationale_summary"]["coverage_complete"])

    def test_rationale_links_to_risk_degraded_confidence_evidence_when_available(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input(metric_status="STALE", metric_freshness="stale", qc_status="DEGRADED")
        )

        rationale = _rationale_by_key(result)["degraded_input_caution"]
        evidence = rationale["evidence_summary"]
        self.assertIn("risk_score", evidence)
        self.assertIn("confidence", evidence)
        self.assertEqual(evidence["degraded_input_severity"], "moderate")
        self.assertEqual(evidence["degraded_input_action"], "upgrade_to_caution")
        self.assertIn("source_status_distribution", evidence)

    def test_downstream_interpretation_is_present(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input(recent_views_drop_ratio=0.45, recent_format_repetition_ratio=0.70)
        )

        for rationale in result.constraint_rationale:
            self.assertTrue(rationale["downstream_interpretation"])
            self.assertIn(
                rationale["interpretation_mode"],
                {"advisory", "cautionary", "blocking"},
            )

    def test_rationale_is_deterministic(self) -> None:
        service = AccountHealthAgentService()
        data = _input(metric_status="STALE", metric_freshness="stale", qc_status="DEGRADED")

        first = service.evaluate(data).to_dict()
        second = service.evaluate(data).to_dict()

        self.assertEqual(first["constraint_rationale"], second["constraint_rationale"])
        self.assertEqual(
            first["decision_trace"]["constraint_rationale"],
            second["decision_trace"]["constraint_rationale"],
        )

    def test_existing_safe_caution_hold_behavior_remains_stable(self) -> None:
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
