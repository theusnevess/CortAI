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


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")


class LearningAgentPhase2Tests(unittest.TestCase):
    def test_generates_learning_insights_from_existing_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            publish_path = root / "data" / "publish_records" / "publish_records.jsonl"
            metrics_path = root / "metrics" / "video_metrics.jsonl"
            analysis_dir = root / "analysis"
            output_path = root / "learning" / "learning_insights.json"

            _write_jsonl(
                publish_path,
                [
                    {"account_id": "acc_1", "publish_id": "pub_1"},
                    {"account_id": "acc_1", "publish_id": "pub_2"},
                ],
            )
            _write_jsonl(
                metrics_path,
                [
                    {"account_id": "acc_1", "views": 220, "completion_rate": 0.62, "duration_s": 9.8},
                    {"account_id": "acc_1", "views": 180, "completion_rate": 0.57, "duration_s": 10.4},
                ],
            )
            analysis_dir.mkdir(parents=True, exist_ok=True)
            (analysis_dir / "hook_performance_summary.json").write_text(
                json.dumps({"hooks": [{"hook_style": "question"}]}),
                encoding="utf-8",
            )

            service = LearningAgentService()
            result = service.generate(
                LearningAgentInput(
                    account_id="acc_1",
                    publish_records_path=publish_path,
                    video_metrics_path=metrics_path,
                    analysis_dir=analysis_dir,
                    qc_events_path=root / "missing_events.jsonl",
                    execution_history_dir=root / "missing_out",
                    output_path=output_path,
                )
            )

            self.assertFalse(result.fallback.used)
            self.assertEqual(result.learning_insights.recommended_hook_type, "question")
            self.assertEqual(result.learning_insights.target_duration_range, "8-12s")
            self.assertGreater(result.learning_insights.signal_summary["avg_views"], 0)
            self.assertEqual(result.learning_policy.duration_bias.value, "8-12s")
            self.assertLess(result.learning_insights.confidence, 0.35)
            self.assertEqual(result.learning_policy.confidence_summary["policy_strength"], "weak")
            self.assertIn("confidence_calibration", result.learning_insights.learning_trace)
            self.assertIn("temporal_analysis", result.learning_insights.learning_trace)
            self.assertIn("contamination_analysis", result.learning_insights.learning_trace)
            self.assertIn("pattern_type", result.learning_insights.temporal_analysis)
            self.assertIn("dominant_problem", result.learning_insights.contamination_summary)
            self.assertTrue(output_path.exists())

    def test_falls_back_when_history_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            service = LearningAgentService()

            result = service.generate(
                LearningAgentInput(
                    account_id="acc_1",
                    publish_records_path=root / "missing_publish.jsonl",
                    video_metrics_path=root / "missing_metrics.jsonl",
                    analysis_dir=root / "missing_analysis",
                    qc_events_path=root / "missing_events.jsonl",
                    execution_history_dir=root / "missing_out",
                    output_path=root / "learning" / "learning_insights.json",
                )
            )

            self.assertTrue(result.fallback.used)
            self.assertEqual(result.fallback.reason, "LEARNING_INSIGHTS_FALLBACK")
            self.assertEqual(result.learning_insights.recommendations, ["fallback_default"])
            self.assertEqual(result.learning_policy.risk_adjustment_hint.value, "standard")
            self.assertEqual(result.learning_policy.confidence_summary["policy_strength"], "weak")
            self.assertIn("confidence_calibration", result.learning_policy.policy_trace)
            self.assertIn("temporal_analysis", result.learning_insights.learning_trace)
            self.assertIn("contamination_analysis", result.learning_insights.learning_trace)

    def test_ingests_qc_history_builds_policy_and_filters_contaminated_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            analysis_dir = root / "analysis"
            analysis_dir.mkdir(parents=True, exist_ok=True)
            (analysis_dir / "hook_performance_summary.json").write_text(
                json.dumps({"hooks": [{"hook_style": "story_opening"}]}),
                encoding="utf-8",
            )
            execution_dir = root / "OUT" / "batch"
            execution_dir.mkdir(parents=True, exist_ok=True)

            def write_execution(name: str, *, status: str, overall: float, payoff_quality: float, contaminated: bool, variation: str) -> None:
                payload = {
                    "creative_pack": {
                        "account_id": "acc_1",
                        "strategy_profile": {
                            "variation_policy": variation,
                            "target_duration_range": "8-12s",
                        },
                        "script_plan": {
                            "hook": "HOOK",
                            "setup": "SETUP",
                            "payoff": "THE FINAL DETAIL NAMED DOOR 16, REMOVED FROM THE FLOORPLAN",
                            "generation_mode": "fallback_contextual" if contaminated else "contextual",
                        },
                        "asset_plan": {
                            "segments": {"payoff": {"category": "map_blueprint"}},
                        },
                        "voice_plan": {
                            "style": "ominous_minimal",
                            "fallback_used": False,
                        },
                        "edit_plan": {
                            "editor_style_profile": "trend_conditioned_dark_backgrounds__clean_snap",
                        },
                    },
                    "video_qc": {
                        "status": status,
                        "publishable": status == "APPROVE",
                        "reasons": [],
                        "decision": {
                            "status": status,
                            "publishable": status == "APPROVE",
                            "score_summary": {
                                "overall_score": overall,
                                "product_quality": overall,
                            },
                            "product_signals": {
                                "hook_quality": 0.88,
                                "payoff_quality": payoff_quality,
                            },
                        },
                    },
                    "learning": {
                        "fallback": {"used": False},
                    },
                    "asset_selection": {
                        "fallback": {"used": False},
                    },
                }
                (execution_dir / name / "execution_outputs.json").parent.mkdir(parents=True, exist_ok=True)
                (execution_dir / name / "execution_outputs.json").write_text(json.dumps(payload), encoding="utf-8")

            write_execution("run_1", status="APPROVE", overall=0.91, payoff_quality=0.9, contaminated=False, variation="medium")
            write_execution("run_2", status="APPROVE", overall=0.89, payoff_quality=0.82, contaminated=False, variation="medium")
            write_execution("run_3", status="HOLD", overall=0.52, payoff_quality=0.2, contaminated=True, variation="low")

            service = LearningAgentService()
            result = service.generate(
                LearningAgentInput(
                    account_id="acc_1",
                    analysis_dir=analysis_dir,
                    execution_history_dir=root / "OUT",
                    qc_events_path=root / "missing_events.jsonl",
                    output_path=root / "learning" / "learning_result.json",
                )
            )

            self.assertFalse(result.fallback.used)
            self.assertEqual(result.learning_policy.hook_type_bias.value, "story_opening")
            self.assertEqual(result.learning_policy.payoff_specificity_bias.value, "high")
            self.assertEqual(result.learning_policy.variation_tolerance_hint.value, "medium")
            self.assertEqual(result.learning_insights.signal_summary["clean_execution_count"], 2)
            self.assertAlmostEqual(result.learning_insights.signal_summary["fallback_contamination_rate"], 0.3333, places=4)
            self.assertEqual(result.learning_insights.qc_summary["sample_size"], 3)
            self.assertEqual(result.learning_insights.qc_summary["clean_sample_size"], 2)
            self.assertAlmostEqual(result.learning_insights.qc_summary["contamination_rate"], 0.3333, places=4)
            self.assertIn("qc_analysis", result.learning_insights.learning_trace)
            self.assertIn("confidence_calibration", result.learning_insights.learning_trace)
            self.assertIn("temporal_analysis", result.learning_insights.learning_trace)
            self.assertIn("contamination_analysis", result.learning_insights.learning_trace)
            self.assertIn("qc_analysis", result.learning_policy.policy_trace)
            self.assertIn("confidence_calibration", result.learning_policy.policy_trace)
            self.assertIn("contamination_analysis", result.learning_policy.policy_trace)
            self.assertEqual(result.learning_policy.confidence_summary["bootstrap_bias_risk"], "high")
            self.assertEqual(result.learning_policy.confidence_summary["policy_strength"], "weak")
            self.assertEqual(result.learning_policy.confidence_summary["temporal_pattern_type"], "recent_spike")
            self.assertEqual(result.learning_insights.contamination_summary["clean_sample_size"], 2)
            self.assertFalse(result.learning_insights.contamination_summary["policy_safe"])
            self.assertIn("contamination_impact", result.learning_policy.confidence_summary)
            pattern_names = {item.pattern_name for item in result.pattern_findings_summary}
            self.assertIn("payoff_structure:named_location_removed", pattern_names)
            self.assertIn("visual_payoff_family:map_blueprint", pattern_names)
            self.assertTrue(all(item.confidence <= 0.35 for item in result.pattern_findings_summary))


if __name__ == "__main__":
    unittest.main()
