from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.account_health.confidence_calibrator import AccountHealthConfidenceCalibrator
from app.creative.agents.account_health.models import AccountHealthInput
from app.creative.agents.account_health.service import AccountHealthAgentService


def _input(
    *,
    recent_publish_count: int = 2,
    recent_views_drop_ratio: float = 0.05,
    recent_format_repetition_ratio: float = 0.10,
    recent_low_performance_streak: int = 0,
    metric_freshness: str = "fresh",
    qc_status: str = "REAL",
    failure_status: str = "REAL",
    include_all_sources: bool = True,
) -> AccountHealthInput:
    if not include_all_sources:
        return AccountHealthInput(
            account_id="acc_health_confidence",
            recent_publish_count=recent_publish_count,
            recent_views_drop_ratio=recent_views_drop_ratio,
            recent_format_repetition_ratio=recent_format_repetition_ratio,
            recent_low_performance_streak=recent_low_performance_streak,
        )
    return AccountHealthInput(
        account_id="acc_health_confidence",
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
            }
        ],
        metric_window_summary={
            "record_count": 8,
            "freshness_status": metric_freshness,
            "evidence_ref": "OUT/metrics/video_metrics.jsonl",
            "previous_window": {"views_drop_ratio": recent_views_drop_ratio},
            "recent_window": {"views_drop_ratio": recent_views_drop_ratio},
        },
        qc_history_summary={
            "source_status": qc_status,
            "record_count": 8,
            "freshness_status": "fresh",
            "evidence_ref": "OUT/history/qc_summary.json",
            "previous_window": {"low_quality_streak": recent_low_performance_streak},
            "recent_window": {"low_quality_streak": recent_low_performance_streak},
        },
        failure_history_summary={
            "source_status": failure_status,
            "available": True,
            "record_count": 0,
            "freshness_status": "fresh",
            "evidence_ref": "OUT/history/failures.json",
            "previous_window": {"fallback_rate": 0.0},
            "recent_window": {"fallback_rate": 0.0},
        },
        format_repetition_summary={
            "record_count": 8,
            "freshness_status": "fresh",
            "evidence_ref": "OUT/history/format_repetition.json",
            "previous_window": {"repetition_ratio": recent_format_repetition_ratio},
            "recent_window": {"repetition_ratio": recent_format_repetition_ratio},
        },
    )


class AccountHealthConfidenceCalibratorTests(unittest.TestCase):
    def test_strong_clean_telemetry_aligned_low_risk_safe_has_high_confidence(self) -> None:
        result = AccountHealthAgentService().evaluate(_input())

        self.assertEqual(result.decision.status, "SAFE")
        self.assertEqual(result.confidence_level, "high")
        self.assertGreaterEqual(result.confidence, 0.70)
        self.assertEqual(result.confidence_components["risk_consistency"], 1.0)
        self.assertEqual(result.confidence_components["missing_signal_penalty"], 0.0)

    def test_missing_telemetry_safe_decision_has_low_confidence(self) -> None:
        result = AccountHealthAgentService().evaluate(_input(include_all_sources=False))

        self.assertEqual(result.decision.status, "SAFE")
        self.assertEqual(result.confidence_level, "low")
        self.assertLess(result.confidence, 0.35)
        self.assertIn("MISSING_TELEMETRY_PENALTY", result.confidence_rationale["dominant_reason_codes"])
        self.assertIn("ABSENT_RISK_COMPONENT_EVIDENCE", result.confidence_rationale["dominant_reason_codes"])

    def test_stale_telemetry_reduces_confidence(self) -> None:
        fresh = AccountHealthAgentService().evaluate(_input())
        stale = AccountHealthAgentService().evaluate(_input(metric_freshness="stale"))

        self.assertLess(stale.confidence, fresh.confidence)
        self.assertIn("STALE_TELEMETRY_PENALTY", stale.confidence_rationale["dominant_reason_codes"])

    def test_degraded_telemetry_reduces_confidence(self) -> None:
        clean = AccountHealthAgentService().evaluate(_input())
        degraded = AccountHealthAgentService().evaluate(_input(qc_status="DEGRADED"))

        self.assertLess(degraded.confidence, clean.confidence)
        self.assertIn("DEGRADED_INPUT_PENALTY", degraded.confidence_rationale["dominant_reason_codes"])
        self.assertGreater(degraded.confidence_components["degraded_input_penalty"], 0.0)

    def test_absent_risk_component_evidence_reduces_confidence(self) -> None:
        result = AccountHealthAgentService().evaluate(
            replace(
                _input(),
                qc_history_summary={},
            )
        )

        self.assertIn("ABSENT_RISK_COMPONENT_EVIDENCE", result.confidence_rationale["dominant_reason_codes"])
        self.assertGreater(result.confidence_components["missing_signal_penalty"], 0.0)

    def test_safe_decision_with_high_overall_risk_reduces_confidence(self) -> None:
        service = AccountHealthAgentService()
        data = _input()
        telemetry = service.telemetry_enricher.enrich(data).to_dict()
        risk = dict(service.risk_component_scorer.score(data, telemetry).to_dict())
        risk["overall_risk_score"] = 0.82
        risk["overall_risk_level"] = "high"

        confidence = AccountHealthConfidenceCalibrator().calibrate(
            decision_status="SAFE",
            telemetry_summary=telemetry,
            risk_summary=risk,
        )

        self.assertEqual(confidence.level, "medium")
        self.assertLess(confidence.confidence, 0.70)
        self.assertIn("DECISION_RISK_INCONSISTENCY", confidence.rationale["dominant_reason_codes"])

    def test_hold_decision_with_high_overall_risk_can_have_high_confidence(self) -> None:
        result = AccountHealthAgentService().evaluate(
            _input(
                recent_publish_count=9,
                recent_views_drop_ratio=0.82,
                recent_format_repetition_ratio=0.90,
                recent_low_performance_streak=4,
            )
        )

        self.assertEqual(result.decision.status, "HOLD")
        self.assertEqual(result.risk_components["overall_risk_level"], "high")
        self.assertEqual(result.confidence_level, "high")
        self.assertGreaterEqual(result.confidence, 0.70)

    def test_caution_with_moderate_risk_and_partial_telemetry_has_medium_confidence(self) -> None:
        result = AccountHealthAgentService().evaluate(
            replace(
                _input(
                    recent_publish_count=5,
                    recent_views_drop_ratio=0.45,
                    recent_format_repetition_ratio=0.60,
                    recent_low_performance_streak=2,
                ),
                failure_history_summary={},
            )
        )

        self.assertEqual(result.decision.status, "CAUTION")
        self.assertEqual(result.risk_components["overall_risk_level"], "medium")
        self.assertEqual(result.confidence_level, "medium")
        self.assertGreaterEqual(result.confidence, 0.35)
        self.assertLess(result.confidence, 0.70)

    def test_confidence_is_deterministic(self) -> None:
        service = AccountHealthAgentService()
        data = _input(
            recent_publish_count=5,
            recent_views_drop_ratio=0.45,
            recent_format_repetition_ratio=0.60,
            recent_low_performance_streak=2,
        )

        first = service.evaluate(data).to_dict()
        second = service.evaluate(data).to_dict()

        self.assertEqual(first["confidence"], second["confidence"])
        self.assertEqual(first["confidence_components"], second["confidence_components"])
        self.assertEqual(first["confidence_rationale"], second["confidence_rationale"])

    def test_confidence_fields_appear_in_result_and_trace(self) -> None:
        payload = AccountHealthAgentService().evaluate(_input()).to_dict()

        self.assertIn("confidence", payload)
        self.assertIn("confidence_level", payload)
        self.assertIn("confidence_components", payload)
        self.assertIn("confidence_rationale", payload)
        self.assertIn("confidence_calibration", payload["decision_trace"])
        self.assertEqual(payload["confidence"], payload["decision_trace"]["confidence_calibration"]["confidence"])

    def test_confidence_does_not_change_safe_caution_hold_behavior(self) -> None:
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
