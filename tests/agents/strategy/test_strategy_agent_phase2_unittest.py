from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.strategy.models import StrategyInput
from app.creative.agents.novelty.models import NoveltyPressureProfile
from app.creative.agents.strategy.service import StrategyAgentService
from app.creative.contracts.creative_pack import (
    LearningPolicy,
    LearningPolicySignal,
    PatternFindingSummary,
    TrendProfile,
)


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

    def test_metrics_constraints_and_trend_change_profile_and_trace(self) -> None:
        service = StrategyAgentService()

        result = service.generate(
            StrategyInput(
                account_id="acc_1",
                account_goal="retention",
                recent_metrics_summary={
                    "avg_completion_rate": 0.31,
                    "avg_views": 90.0,
                    "publish_count": 6,
                    "metrics_count": 6,
                },
                health_status="SAFE",
                recommended_constraints={
                    "reduce_hook_aggressiveness": True,
                    "max_daily_posts": 1,
                },
                trend_profile=TrendProfile(
                    niche="horror",
                    dominant_hooks=["story_opening"],
                    pacing="fast_first_3s",
                    visual_style="dark_backgrounds",
                ),
            )
        )

        self.assertFalse(result.fallback.used)
        self.assertEqual(result.strategy_profile.content_mode, "conservative")
        self.assertEqual(result.strategy_profile.hook_aggressiveness, "medium")
        self.assertEqual(result.strategy_profile.target_duration_range, "8-10s")
        self.assertEqual(result.strategy_profile.variation_policy, "medium")
        self.assertTrue(result.decision_trace["constraint_adjustments"])
        self.assertTrue(result.decision_trace["metric_adjustments"])
        self.assertTrue(result.decision_trace["trend_adjustments"])

    def test_hold_health_remains_dominant_even_when_metrics_and_trend_are_present(self) -> None:
        service = StrategyAgentService()

        result = service.generate(
            StrategyInput(
                account_id="acc_1",
                account_goal="retention",
                recent_metrics_summary={
                    "avg_completion_rate": 0.22,
                    "publish_count": 10,
                    "metrics_count": 10,
                },
                health_status="HOLD",
                recommended_constraints={},
                trend_profile=TrendProfile(
                    niche="horror",
                    dominant_hooks=["shock_statement"],
                    pacing="fast_first_3s",
                    visual_style="dark_backgrounds",
                ),
            )
        )

        self.assertEqual(result.strategy_profile.content_mode, "paused")
        self.assertEqual(result.strategy_profile.hook_aggressiveness, "low")
        self.assertEqual(result.strategy_profile.variation_policy, "none")

    def test_novelty_pressure_upshifts_variation_and_attaches_block_hints(self) -> None:
        service = StrategyAgentService()

        result = service.generate(
            StrategyInput(
                account_id="acc_1",
                account_goal="retention",
                recent_metrics_summary={},
                health_status="SAFE",
                recommended_constraints={},
                novelty_pressure_profile=NoveltyPressureProfile(
                    semantic_saturation_level="medium",
                    visual_saturation_level="high",
                    structural_saturation_level="high",
                    novelty_budget="high",
                    pressure_level="high",
                    recommended_variation_policy="medium",
                    blocked_payoff_structures=["named_location_removed"],
                    blocked_visual_payoff_categories=["map_blueprint"],
                    preferred_alternative_payoff_families=["warning_display", "sealed_access"],
                ),
            )
        )

        self.assertEqual(result.strategy_profile.variation_policy, "medium")
        self.assertIn("named_location_removed", result.strategy_profile.novelty_hints["blocked_payoff_structures"])
        self.assertIn("map_blueprint", result.strategy_profile.novelty_hints["blocked_visual_payoff_categories"])
        self.assertTrue(result.decision_trace["novelty_adjustments"])

    def test_learning_policy_changes_strategy_conservatively_and_attaches_payoff_hint(self) -> None:
        service = StrategyAgentService()

        result = service.generate(
            StrategyInput(
                account_id="acc_1",
                account_goal="retention",
                recent_metrics_summary={},
                health_status="SAFE",
                recommended_constraints={},
                learning_policy=LearningPolicy(
                    hook_type_bias=LearningPolicySignal(value="story_opening", confidence=0.7, evidence_count=8),
                    duration_bias=LearningPolicySignal(value="10-14s", confidence=0.7, evidence_count=8),
                    payoff_specificity_bias=LearningPolicySignal(value="high", confidence=0.85, evidence_count=8),
                    risk_adjustment_hint=LearningPolicySignal(value="conservative_if_low_score_cluster", confidence=0.8, evidence_count=8),
                    variation_tolerance_hint=LearningPolicySignal(value="medium", confidence=0.83, evidence_count=4),
                ),
                pattern_findings_summary=(
                    PatternFindingSummary(pattern_name="variation_policy:medium", evidence_count=4, approve_rate=0.9),
                ),
            )
        )

        self.assertFalse(result.fallback.used)
        self.assertEqual(result.strategy_profile.content_mode, "conservative")
        self.assertEqual(result.strategy_profile.target_duration_range, "10-14s")
        self.assertEqual(result.strategy_profile.variation_policy, "medium")
        self.assertEqual(result.strategy_profile.hook_aggressiveness, "high")
        self.assertEqual(result.strategy_profile.novelty_hints["payoff_specificity_bias"], "high")
        self.assertTrue(result.decision_trace["learning_adjustments"])


if __name__ == "__main__":
    unittest.main()
