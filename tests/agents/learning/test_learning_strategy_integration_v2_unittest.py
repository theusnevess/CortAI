from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.learning.models import LearningAgentInput
from app.creative.agents.learning.service import LearningAgentService
from app.creative.agents.strategy.models import StrategyInput
from app.creative.agents.strategy.service import StrategyAgentService


class LearningStrategyIntegrationV2Tests(unittest.TestCase):
    def test_learning_policy_flows_into_strategy_and_changes_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            analysis_dir = root / "analysis"
            analysis_dir.mkdir(parents=True, exist_ok=True)
            (analysis_dir / "hook_performance_summary.json").write_text(
                json.dumps({"hooks": [{"hook_style": "story_opening"}]}),
                encoding="utf-8",
            )
            payload = {
                "creative_pack": {
                    "account_id": "acc_1",
                    "strategy_profile": {"variation_policy": "medium", "target_duration_range": "10-14s"},
                    "script_plan": {
                        "hook": "HOOK",
                        "setup": "SETUP",
                        "payoff": "THE FINAL DETAIL NAMED DOOR 16, REMOVED FROM THE FLOORPLAN",
                        "generation_mode": "contextual",
                    },
                    "asset_plan": {"segments": {"payoff": {"category": "map_blueprint"}}},
                    "voice_plan": {"style": "ominous_minimal", "fallback_used": False},
                    "edit_plan": {"editor_style_profile": "editor-agent-v2_2"},
                },
                "video_qc": {
                    "status": "APPROVE",
                    "publishable": True,
                    "reasons": [],
                    "decision": {
                        "status": "APPROVE",
                        "publishable": True,
                        "score_summary": {"overall_score": 0.91, "product_quality": 0.9},
                        "product_signals": {"hook_quality": 0.9, "payoff_quality": 0.88},
                    },
                },
                "learning": {"fallback": {"used": False}},
                "asset_selection": {"fallback": {"used": False}},
            }
            timestamps = (
                ["2026-04-20T00:00:00Z"] * 8
                + ["2026-04-08T00:00:00Z"] * 7
                + ["2026-03-10T00:00:00Z"] * 5
            )
            for index, timestamp in enumerate(timestamps):
                payload_for_run = json.loads(json.dumps(payload))
                payload_for_run["creative_pack"]["generated_at"] = timestamp
                execution_path = root / "OUT" / f"run_{index+1}" / "execution_outputs.json"
                execution_path.parent.mkdir(parents=True, exist_ok=True)
                execution_path.write_text(json.dumps(payload_for_run), encoding="utf-8")

            learning_result = LearningAgentService().generate(
                LearningAgentInput(
                    account_id="acc_1",
                    analysis_dir=analysis_dir,
                    execution_history_dir=root / "OUT",
                    qc_events_path=root / "missing_events.jsonl",
                )
            )

            strategy_result = StrategyAgentService().generate(
                StrategyInput(
                    account_id="acc_1",
                    account_goal="retention",
                    recent_metrics_summary=dict(learning_result.learning_insights.signal_summary),
                    health_status="SAFE",
                    recommended_constraints={},
                    learning_policy=learning_result.learning_policy,
                    pattern_findings_summary=learning_result.pattern_findings_summary,
                )
            )

            self.assertFalse(learning_result.fallback.used)
            self.assertEqual(learning_result.learning_policy.confidence_summary["policy_strength"], "strong")
            self.assertEqual(learning_result.learning_policy.confidence_summary["temporal_pattern_type"], "durable_pattern")
            self.assertGreaterEqual(learning_result.learning_policy.duration_bias.confidence, 0.7)
            self.assertFalse(strategy_result.fallback.used)
            self.assertEqual(strategy_result.strategy_profile.target_duration_range, "10-14s")
            self.assertEqual(strategy_result.strategy_profile.variation_policy, "medium")
            self.assertEqual(strategy_result.strategy_profile.hook_aggressiveness, "high")

    def test_weak_learning_confidence_does_not_override_strategy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            analysis_dir = root / "analysis"
            analysis_dir.mkdir(parents=True, exist_ok=True)
            (analysis_dir / "hook_performance_summary.json").write_text(
                json.dumps({"hooks": [{"hook_style": "story_opening"}]}),
                encoding="utf-8",
            )
            payload = {
                "creative_pack": {
                    "account_id": "acc_1",
                    "strategy_profile": {"variation_policy": "medium", "target_duration_range": "10-14s"},
                    "script_plan": {
                        "hook": "HOOK",
                        "setup": "SETUP",
                        "payoff": "THE FINAL DETAIL NAMED DOOR 16, REMOVED FROM THE FLOORPLAN",
                        "generation_mode": "contextual",
                    },
                    "asset_plan": {"segments": {"payoff": {"category": "map_blueprint"}}},
                    "voice_plan": {"style": "ominous_minimal", "fallback_used": False},
                    "edit_plan": {"editor_style_profile": "editor-agent-v2_2"},
                },
                "video_qc": {
                    "status": "APPROVE",
                    "publishable": True,
                    "decision": {
                        "status": "APPROVE",
                        "publishable": True,
                        "score_summary": {"overall_score": 0.91, "product_quality": 0.9},
                        "product_signals": {"hook_quality": 0.9, "payoff_quality": 0.88},
                    },
                },
                "learning": {"fallback": {"used": False}},
                "asset_selection": {"fallback": {"used": False}},
            }
            for index in range(3):
                payload_for_run = json.loads(json.dumps(payload))
                payload_for_run["creative_pack"]["generated_at"] = "2026-04-20T00:00:00Z"
                execution_path = root / "OUT" / f"run_{index+1}" / "execution_outputs.json"
                execution_path.parent.mkdir(parents=True, exist_ok=True)
                execution_path.write_text(json.dumps(payload_for_run), encoding="utf-8")

            learning_result = LearningAgentService().generate(
                LearningAgentInput(
                    account_id="acc_1",
                    analysis_dir=analysis_dir,
                    execution_history_dir=root / "OUT",
                    qc_events_path=root / "missing_events.jsonl",
                )
            )
            strategy_result = StrategyAgentService().generate(
                StrategyInput(
                    account_id="acc_1",
                    account_goal="retention",
                    recent_metrics_summary=dict(learning_result.learning_insights.signal_summary),
                    health_status="SAFE",
                    recommended_constraints={},
                    learning_policy=learning_result.learning_policy,
                    pattern_findings_summary=learning_result.pattern_findings_summary,
                )
            )

            self.assertEqual(learning_result.learning_policy.confidence_summary["policy_strength"], "weak")
            self.assertEqual(learning_result.learning_policy.confidence_summary["temporal_pattern_type"], "recent_spike")
            self.assertLess(learning_result.learning_policy.duration_bias.confidence, 0.55)
            self.assertEqual(strategy_result.strategy_profile.target_duration_range, "8-12s")
            self.assertEqual(strategy_result.strategy_profile.variation_policy, "low")


if __name__ == "__main__":
    unittest.main()
