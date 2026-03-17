from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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


if __name__ == "__main__":
    unittest.main()
