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


class AccountHealthAgentPhase2Tests(unittest.TestCase):
    def test_returns_safe_for_healthy_account(self) -> None:
        service = AccountHealthAgentService()

        result = service.evaluate(
            AccountHealthInput(
                account_id="acc_1",
                recent_publish_count=1,
                recent_format_repetition_ratio=0.10,
                recent_views_drop_ratio=0.05,
                recent_low_performance_streak=0,
            )
        )

        self.assertEqual(result.decision.status, "SAFE")
        self.assertIn("HEALTHY_BASELINE", result.decision.reasons)
        self.assertFalse(result.fallback.used)
        self.assertEqual(result.input_summary["recent_publish_count"], 1)
        self.assertEqual(result.decision_trace["final_status"], "SAFE")
        self.assertEqual(result.decision_trace["triggered_conditions"], [])

    def test_returns_caution_when_signals_are_degrading(self) -> None:
        service = AccountHealthAgentService()

        result = service.evaluate(
            AccountHealthInput(
                account_id="acc_1",
                recent_publish_count=3,
                recent_format_repetition_ratio=0.70,
                recent_views_drop_ratio=0.45,
                recent_low_performance_streak=2,
            )
        )

        self.assertEqual(result.decision.status, "CAUTION")
        self.assertIn("RECENT_VIEWS_DROP", result.decision.reasons)
        self.assertTrue(result.decision.recommended_constraints["reduce_hook_aggressiveness"])
        self.assertTrue(result.decision_trace["threshold_evaluations"]["caution_on_views_drop"])
        self.assertTrue(result.decision_trace["threshold_evaluations"]["caution_on_format_repetition"])
        self.assertIn("recent_views_drop_ratio>=0.40", result.decision_trace["triggered_conditions"])
        self.assertIn("recent_low_performance_streak>=2", result.decision_trace["triggered_conditions"])

    def test_returns_hold_with_explicit_trace_when_threshold_is_crossed(self) -> None:
        service = AccountHealthAgentService()

        result = service.evaluate(
            AccountHealthInput(
                account_id="acc_1",
                recent_publish_count=5,
                recent_format_repetition_ratio=0.30,
                recent_views_drop_ratio=0.80,
                recent_low_performance_streak=4,
            )
        )

        self.assertEqual(result.decision.status, "HOLD")
        self.assertIn("RECENT_VIEWS_DROP", result.decision.reasons)
        self.assertIn("LOW_PERFORMANCE_STREAK", result.decision.reasons)
        self.assertTrue(result.decision.recommended_constraints["block_generation"])
        self.assertTrue(result.decision_trace["threshold_evaluations"]["hold_on_views_drop"])
        self.assertTrue(result.decision_trace["threshold_evaluations"]["hold_on_low_performance_streak"])
        self.assertEqual(result.decision_trace["final_status"], "HOLD")

    def test_fallback_never_returns_hold(self) -> None:
        service = AccountHealthAgentService()

        result = service.evaluate(
            AccountHealthInput(
                account_id="acc_1",
                recent_publish_count=-1,
                recent_format_repetition_ratio=0.0,
                recent_views_drop_ratio=0.0,
                recent_low_performance_streak=0,
            )
        )

        self.assertTrue(result.fallback.used)
        self.assertEqual(result.decision.status, "SAFE")
        self.assertEqual(result.decision.reasons, ["fallback_default"])
        self.assertEqual(result.fallback.reason, "ACCOUNT_HEALTH_COLD_START")
        self.assertTrue(result.decision_trace["fallback_used"])
        self.assertEqual(result.decision_trace["fallback_reason"], "ACCOUNT_HEALTH_COLD_START")


if __name__ == "__main__":
    unittest.main()
