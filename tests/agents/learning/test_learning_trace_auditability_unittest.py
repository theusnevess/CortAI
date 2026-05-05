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


class LearningTraceAuditabilityHardeningTests(unittest.TestCase):
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

    def test_strong_durable_trace_is_reconstructible_and_positive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            analysis_dir = self._prepare(root)
            timestamps = ["2026-04-20T00:00:00Z"] * 8 + ["2026-04-08T00:00:00Z"] * 7 + ["2026-03-10T00:00:00Z"] * 5
            for index, timestamp in enumerate(timestamps, start=1):
                self._write_run(root, index, timestamp=timestamp)

            result = self._run_learning(root, analysis_dir)
            trace = result.learning_insights.learning_trace

            self.assertIn("lineage_summary", trace)
            self.assertIn("policy_safety_summary", trace)
            self.assertIn("pattern_rationale", trace)
            self.assertIn("downgraded_evidence", trace)
            self.assertEqual(trace["lineage_summary"]["total_evidence_count"], 20)
            self.assertEqual(trace["lineage_summary"]["clean_evidence_count"], 20)
            self.assertEqual(trace["temporal_analysis"]["pattern_type"], "durable_pattern")
            self.assertEqual(trace["strategy_pressure"]["pressure_mode"], "strong_bias")
            self.assertTrue(trace["policy_safety_summary"]["policy_safe"])
            self.assertEqual(trace["policy_safety_summary"]["confidence_level"], "high")
            self.assertGreater(len(trace["pattern_rationale"]), 0)
            self.assertTrue(all(item["rationale"] for item in trace["pattern_rationale"]))
            self.assertIn("rationale", trace["confidence_calibration"])
            self.assertIn("penalties_applied", trace["confidence_calibration"])
            self.assertIn("pressure_eligibility", trace["strategy_pressure"])
            self.assertIn("boundedness_reason", trace["strategy_pressure"])

    def test_contaminated_trace_shows_downgraded_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            analysis_dir = self._prepare(root)
            for index in range(1, 7):
                self._write_run(root, index, timestamp="2026-04-20T00:00:00Z", contaminated=True)

            result = self._run_learning(root, analysis_dir)
            trace = result.learning_insights.learning_trace

            self.assertEqual(trace["lineage_summary"]["contaminated_evidence_count"], 6)
            self.assertFalse(trace["policy_safety_summary"]["policy_safe"])
            self.assertIn("POLICY_NOT_SAFE_FROM_EVIDENCE_QUALITY", trace["policy_safety_summary"]["reason_codes"])
            self.assertGreater(len(trace["downgraded_evidence"]), 0)
            self.assertTrue(all(item["reason"] == "contaminated" for item in trace["downgraded_evidence"]))
            self.assertEqual(trace["strategy_pressure"]["pressure_mode"], "weak_bias")
            self.assertEqual(trace["strategy_pressure"]["target_suppression_reason"], "clean_sample_size_below_minimum")

    def test_volatile_trace_contains_temporal_rationale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            analysis_dir = self._prepare(root)
            for index in range(1, 5):
                self._write_run(root, index, timestamp="2026-04-20T00:00:00Z", status="REJECT", overall=0.45, payoff_quality=0.45, variation="low", duration="8-12s")
            for index in range(5, 13):
                self._write_run(root, index, timestamp="2026-03-10T00:00:00Z", status="APPROVE", overall=0.90, payoff_quality=0.88)

            result = self._run_learning(root, analysis_dir)
            trace = result.learning_insights.learning_trace

            self.assertEqual(trace["temporal_analysis"]["pattern_type"], "volatile")
            self.assertTrue(trace["temporal_analysis"]["volatility_detected"])
            self.assertIn("reducing confidence", trace["temporal_analysis"]["rationale"])
            self.assertIn("TEMPORAL_VOLATILE", trace["policy_safety_summary"]["reason_codes"])
            self.assertEqual(trace["strategy_pressure"]["pressure_mode"], "weak_bias")

    def test_policy_trace_is_coherent_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            analysis_dir = self._prepare(root)
            timestamps = ["2026-04-20T00:00:00Z"] * 8 + ["2026-04-08T00:00:00Z"] * 7 + ["2026-03-10T00:00:00Z"] * 5
            for index, timestamp in enumerate(timestamps, start=1):
                self._write_run(root, index, timestamp=timestamp)

            first = self._run_learning(root, analysis_dir)
            second = self._run_learning(root, analysis_dir)
            self.assertEqual(first.learning_insights.learning_trace, second.learning_insights.learning_trace)
            self.assertEqual(first.learning_policy.policy_trace, second.learning_policy.policy_trace)

            policy_trace = first.learning_policy.policy_trace
            self.assertIn("lineage_summary", policy_trace)
            self.assertIn("confidence_formation", policy_trace)
            self.assertIn("temporal_pattern_impact", policy_trace)
            self.assertIn("contamination_impact", policy_trace)
            self.assertIn("strategy_pressure_generation", policy_trace)
            self.assertIn("final_safety_classification", policy_trace)
            self.assertEqual(policy_trace["final_safety_classification"]["pressure_mode"], "strong_bias")

    def test_strategy_boundary_remains_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            analysis_dir = self._prepare(root)
            timestamps = ["2026-04-20T00:00:00Z"] * 8 + ["2026-04-08T00:00:00Z"] * 7 + ["2026-03-10T00:00:00Z"] * 5
            for index, timestamp in enumerate(timestamps, start=1):
                self._write_run(root, index, timestamp=timestamp)

            learning_result = self._run_learning(root, analysis_dir)
            strategy_result = StrategyAgentService().generate(
                StrategyInput(
                    account_id="acc_1",
                    account_goal="retention",
                    recent_metrics_summary=dict(learning_result.learning_insights.signal_summary),
                    health_status="HOLD",
                    recommended_constraints={},
                    learning_policy=learning_result.learning_policy,
                    pattern_findings_summary=learning_result.pattern_findings_summary,
                )
            )

            self.assertEqual(strategy_result.strategy_profile.content_mode, "paused")
            self.assertEqual(strategy_result.strategy_profile.variation_policy, "none")
            self.assertEqual(strategy_result.decision_trace["learning_adjustments"], [])
            self.assertTrue(learning_result.learning_policy.strategy_pressure.higher_authority_constraints_apply)


if __name__ == "__main__":
    unittest.main()
