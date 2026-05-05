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


class LearningStrategyPressureClarificationTests(unittest.TestCase):
    def _prepare(self, root: Path) -> Path:
        analysis_dir = root / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        (analysis_dir / "hook_performance_summary.json").write_text(
            json.dumps({"hooks": [{"hook_style": "story_opening"}]}),
            encoding="utf-8",
        )
        return analysis_dir

    def _write_run(
        self,
        root: Path,
        index: int,
        *,
        timestamp: str,
        status: str = "APPROVE",
        overall: float = 0.91,
        payoff_quality: float = 0.88,
        contaminated: bool = False,
        variation: str = "medium",
        duration: str = "10-14s",
    ) -> None:
        payload = {
            "creative_pack": {
                "account_id": "acc_1",
                "generated_at": timestamp,
                "strategy_profile": {
                    "variation_policy": variation,
                    "target_duration_range": duration,
                },
                "script_plan": {
                    "hook": "HOOK",
                    "hook_type": "story_opening",
                    "setup": "SETUP",
                    "payoff": "THE FINAL DETAIL NAMED DOOR 16, REMOVED FROM THE FLOORPLAN",
                    "generation_mode": "fallback_contextual" if contaminated else "contextual",
                },
                "asset_plan": {"segments": {"payoff": {"category": "map_blueprint"}}},
                "voice_plan": {"style": "ominous_minimal", "fallback_used": False},
                "edit_plan": {"editor_style_profile": "editor-agent-v2_2"},
            },
            "video_qc": {
                "status": status,
                "publishable": status == "APPROVE",
                "decision": {
                    "status": status,
                    "publishable": status == "APPROVE",
                    "score_summary": {"overall_score": overall, "product_quality": overall},
                    "product_signals": {"hook_quality": overall, "payoff_quality": payoff_quality},
                },
            },
            "learning": {"fallback": {"used": False}},
            "asset_selection": {"fallback": {"used": False}},
        }
        execution_path = root / "OUT" / f"run_{index:02d}" / "execution_outputs.json"
        execution_path.parent.mkdir(parents=True, exist_ok=True)
        execution_path.write_text(json.dumps(payload), encoding="utf-8")

    def _run_learning(self, root: Path, analysis_dir: Path):
        return LearningAgentService().generate(
            LearningAgentInput(
                account_id="acc_1",
                analysis_dir=analysis_dir,
                execution_history_dir=root / "OUT",
                qc_events_path=root / "missing_events.jsonl",
            )
        )

    def test_strong_clean_durable_evidence_allows_strong_bias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            analysis_dir = self._prepare(root)
            timestamps = ["2026-04-20T00:00:00Z"] * 8 + ["2026-04-08T00:00:00Z"] * 7 + ["2026-03-10T00:00:00Z"] * 5
            for index, timestamp in enumerate(timestamps, start=1):
                self._write_run(root, index, timestamp=timestamp)

            result = self._run_learning(root, analysis_dir)
            pressure = result.learning_policy.strategy_pressure

            self.assertEqual(pressure.pressure_mode, "strong_bias")
            self.assertGreaterEqual(pressure.confidence, 0.7)
            self.assertTrue(pressure.bounded)
            self.assertEqual(pressure.strategy_influence_mode, "bounded")
            self.assertTrue(pressure.strategy_override_allowed)
            self.assertTrue(pressure.higher_authority_constraints_apply)
            self.assertGreater(len(pressure.pressure_targets), 0)
            self.assertTrue(all(target.rationale for target in pressure.pressure_targets))
            self.assertIn("strategy_pressure", result.learning_insights.learning_trace)
            self.assertIn("strategy_pressure", result.learning_policy.policy_trace)

    def test_weak_recent_sample_keeps_weak_bias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            analysis_dir = self._prepare(root)
            for index in range(1, 4):
                self._write_run(root, index, timestamp="2026-04-20T00:00:00Z")

            result = self._run_learning(root, analysis_dir)
            pressure = result.learning_policy.strategy_pressure

            self.assertEqual(pressure.pressure_mode, "weak_bias")
            self.assertLess(result.learning_policy.confidence_summary["confidence"], 0.35)
            self.assertTrue(pressure.bounded)

    def test_contaminated_evidence_caps_or_removes_pressure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            analysis_dir = self._prepare(root)
            for index in range(1, 9):
                self._write_run(root, index, timestamp="2026-04-20T00:00:00Z", contaminated=True)

            result = self._run_learning(root, analysis_dir)
            pressure = result.learning_policy.strategy_pressure

            self.assertEqual(pressure.pressure_mode, "weak_bias")
            self.assertEqual(pressure.pressure_origin_summary["dominant_problem"], "contamination")
            self.assertFalse(pressure.pressure_origin_summary["policy_safe"])
            self.assertEqual(pressure.pressure_targets, [])

    def test_noisy_evidence_caps_pressure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            analysis_dir = self._prepare(root)
            for index in range(1, 4):
                self._write_run(root, index, timestamp="2026-04-20T00:00:00Z", status="APPROVE", overall=0.70, payoff_quality=0.70)
            for index in range(4, 7):
                self._write_run(root, index, timestamp="2026-04-20T00:00:00Z", status="REJECT", overall=0.66, payoff_quality=0.66)

            result = self._run_learning(root, analysis_dir)
            pressure = result.learning_policy.strategy_pressure

            self.assertEqual(pressure.pressure_mode, "weak_bias")
            self.assertEqual(pressure.pressure_origin_summary["dominant_problem"], "noise")
            self.assertFalse(pressure.pressure_origin_summary["policy_safe"])
            self.assertTrue(all(target.confidence <= 0.34 for target in pressure.pressure_targets))

    def test_insufficient_evidence_produces_no_meaningful_pressure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            analysis_dir = self._prepare(root)

            result = self._run_learning(root, analysis_dir)
            pressure = result.learning_policy.strategy_pressure

            self.assertEqual(pressure.pressure_mode, "weak_bias")
            self.assertEqual(pressure.pressure_targets, [])
            self.assertEqual(pressure.pressure_origin_summary["dominant_problem"], "insufficient")

    def test_same_input_same_pressure_and_strategy_ownership_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            analysis_dir = self._prepare(root)
            timestamps = ["2026-04-20T00:00:00Z"] * 8 + ["2026-04-08T00:00:00Z"] * 7 + ["2026-03-10T00:00:00Z"] * 5
            for index, timestamp in enumerate(timestamps, start=1):
                self._write_run(root, index, timestamp=timestamp)

            first = self._run_learning(root, analysis_dir)
            second = self._run_learning(root, analysis_dir)
            self.assertEqual(first.learning_policy.strategy_pressure.to_dict(), second.learning_policy.strategy_pressure.to_dict())

            strategy_result = StrategyAgentService().generate(
                StrategyInput(
                    account_id="acc_1",
                    account_goal="retention",
                    recent_metrics_summary=dict(first.learning_insights.signal_summary),
                    health_status="HOLD",
                    recommended_constraints={},
                    learning_policy=first.learning_policy,
                    pattern_findings_summary=first.pattern_findings_summary,
                )
            )
            self.assertEqual(strategy_result.strategy_profile.content_mode, "paused")
            self.assertEqual(strategy_result.strategy_profile.variation_policy, "none")
            self.assertEqual(strategy_result.decision_trace["learning_adjustments"], [])


if __name__ == "__main__":
    unittest.main()
