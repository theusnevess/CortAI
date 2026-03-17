from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.strategy.models import StrategyInput
from app.creative.agents.strategy.service import StrategyAgentService


class StrategyAgentPhase2Tests(unittest.TestCase):
    def test_generates_strategy_profile_for_safe_account(self) -> None:
        service = StrategyAgentService()

        result = service.generate(
            StrategyInput(
                account_id="acc_1",
                account_goal="retention",
                recent_metrics_summary={"views": 1200},
                health_status="SAFE",
                recommended_constraints={},
            )
        )

        self.assertEqual(result.strategy_profile.goal, "retention")
        self.assertEqual(result.strategy_profile.content_mode, "standard")
        self.assertEqual(result.strategy_profile.hook_aggressiveness, "medium")
        self.assertFalse(result.fallback.used)

    def test_falls_back_to_default_strategy_on_invalid_status(self) -> None:
        service = StrategyAgentService()

        result = service.generate(
            StrategyInput(
                account_id="acc_1",
                account_goal="",
                recent_metrics_summary={},
                health_status="UNKNOWN",
                recommended_constraints={},
            )
        )

        self.assertTrue(result.fallback.used)
        self.assertEqual(result.fallback.reason, "STRATEGY_COLD_START")
        self.assertEqual(result.strategy_profile.goal, "retention")
        self.assertEqual(result.strategy_profile.content_mode, "standard")


if __name__ == "__main__":
    unittest.main()
