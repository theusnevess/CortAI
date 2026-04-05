from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.contracts.creative_pack import LearningInsights
from app.creative.experiments.models import ExperimentCapabilityInput
from app.creative.experiments.service import ExperimentCapabilityService


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


class ExperimentCapabilityPhase2Tests(unittest.TestCase):
    def test_generates_experiment_plan_from_local_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            config_path = root / "experiments" / "experiment_config.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                json.dumps(
                    {
                        "name": "creative_pack_baseline",
                        "scope": "CREATIVE_PACK",
                        "variant_a": {"variant_type": "hook_style", "hook_style": "question"},
                        "variant_b": {"variant_type": "hook_style", "hook_style": "story_opening"},
                        "status": "ACTIVE",
                    }
                ),
                encoding="utf-8",
            )
            service = ExperimentCapabilityService(
                default_config_path=config_path,
                default_output_path=root / "experiments" / "experiment_plan.json",
                default_experiments_path=root / "experiments" / "experiments.jsonl",
                default_assignments_path=root / "experiments" / "assignments.jsonl",
                default_results_path=root / "experiments" / "results.jsonl",
            )

            result = service.generate(
                ExperimentCapabilityInput(
                    account_id="acc_1",
                    niche="horror",
                    topic="sealed tunnel",
                    publish_slot="2026-03-17T10:00:00Z",
                    learning_insights=LearningInsights(),
                )
            )

            self.assertFalse(result.fallback.used)
            self.assertTrue(result.experiment_plan.experiment_id.startswith("exp_"))
            self.assertIn(result.experiment_plan.variant_id, {"A", "B"})
            self.assertIsNotNone(result.experiment_assignment)
            self.assertTrue(result.experiment_assignment.assignment_id.startswith("asg_"))
            self.assertEqual(result.experiment_assignment.experiment_id, result.experiment_plan.experiment_id)
            self.assertEqual(result.experiment_assignment.variant_id, result.experiment_plan.variant_id)
            self.assertEqual(result.experiment_assignment.subject_key, "acc_1|2026-03-17T10:00:00Z|sealed tunnel")
            self.assertTrue((root / "experiments" / "experiment_plan.json").exists())
            self.assertEqual(result.decision_trace["assignment_path_used"], "framework_assign")
            self.assertTrue(result.decision_trace["config_exists"])
            self.assertEqual(result.decision_trace["subject_key"], result.experiment_assignment.subject_key)
            assignment_rows = _read_jsonl(root / "experiments" / "assignments.jsonl")
            self.assertEqual(len(assignment_rows), 1)
            self.assertEqual(assignment_rows[0]["assignment_id"], result.experiment_assignment.assignment_id)
            self.assertEqual(assignment_rows[0]["variant"], result.experiment_plan.variant_id)
            recorded, action = service.record_runtime_result(
                result=result,
                window_id="2026-03-17T10:00:00Z",
                metrics={
                    "qc_status": "APPROVE",
                    "publishable": True,
                    "overall_score": 0.91,
                    "product_quality": 0.88,
                    "hook_quality": 0.87,
                    "payoff_quality": 0.89,
                    "render_status": "READY",
                },
            )
            self.assertEqual(action, "WRITTEN")
            self.assertIsNotNone(recorded)
            self.assertEqual(recorded["experiment_id"], result.experiment_plan.experiment_id)
            self.assertEqual(recorded["subject_key"], result.experiment_assignment.subject_key)
            result_rows = _read_jsonl(root / "experiments" / "results.jsonl")
            self.assertEqual(len(result_rows), 1)
            self.assertEqual(result_rows[0]["result_id"], recorded["result_id"])
            self.assertTrue(result.experiment_trace["assignment_recorded"])

    def test_falls_back_when_no_experiment_is_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            service = ExperimentCapabilityService(
                default_config_path=root / "missing_config.json",
                default_output_path=root / "experiments" / "experiment_plan.json",
                default_experiments_path=root / "experiments" / "experiments.jsonl",
                default_assignments_path=root / "experiments" / "assignments.jsonl",
                default_results_path=root / "experiments" / "results.jsonl",
            )

            result = service.generate(
                ExperimentCapabilityInput(
                    account_id="acc_1",
                    niche="horror",
                    topic="sealed tunnel",
                    publish_slot="2026-03-17T10:00:00Z",
                    learning_insights=LearningInsights(),
                )
            )

            self.assertTrue(result.fallback.used)
            self.assertEqual(result.fallback.reason, "EXPERIMENT_PLAN_FALLBACK")
            self.assertEqual(result.experiment_plan.variant_type, "baseline")
            self.assertIsNone(result.experiment_assignment)
            self.assertEqual(result.decision_trace["assignment_path_used"], "none_fallback")
            self.assertEqual(result.decision_trace["variant_resolution_source"], "fallback_default")
            self.assertEqual(_read_jsonl(root / "experiments" / "assignments.jsonl"), [])
            recorded, action = service.record_runtime_result(
                result=result,
                window_id="2026-03-17T10:00:00Z",
                metrics={"qc_status": "HOLD", "publishable": False, "render_status": "HOLD"},
            )
            self.assertIsNone(recorded)
            self.assertEqual(action, "SKIPPED_NO_ASSIGNMENT")
            self.assertEqual(_read_jsonl(root / "experiments" / "results.jsonl"), [])

    def test_blocks_assignment_when_health_is_hold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            config_path = root / "experiments" / "experiment_config.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                json.dumps(
                    {
                        "name": "creative_pack_baseline",
                        "scope": "CREATIVE_PACK",
                        "variant_a": {"variant_type": "hook_style", "hook_style": "question"},
                        "variant_b": {"variant_type": "hook_style", "hook_style": "story_opening"},
                        "status": "ACTIVE",
                    }
                ),
                encoding="utf-8",
            )
            service = ExperimentCapabilityService(
                default_config_path=config_path,
                default_output_path=root / "experiments" / "experiment_plan.json",
                default_experiments_path=root / "experiments" / "experiments.jsonl",
                default_assignments_path=root / "experiments" / "assignments.jsonl",
                default_results_path=root / "experiments" / "results.jsonl",
            )

            result = service.generate(
                ExperimentCapabilityInput(
                    account_id="acc_hold",
                    niche="horror",
                    topic="sealed tunnel",
                    publish_slot="2026-03-17T10:00:00Z",
                    learning_insights=LearningInsights(),
                    account_health_status="HOLD",
                )
            )

            self.assertFalse(result.fallback.used)
            self.assertIsNone(result.experiment_assignment)
            self.assertEqual(result.experiment_plan.experiment_id, "exp_policy_default")
            self.assertFalse(result.experiment_trace["eligibility_allowed"])
            self.assertEqual(result.experiment_trace["eligibility_reason"], "ACCOUNT_HEALTH_HOLD")
            self.assertEqual(result.decision_trace["assignment_path_used"], "none_policy_blocked")
            self.assertEqual(_read_jsonl(root / "experiments" / "assignments.jsonl"), [])

    def test_allows_standard_envelope_when_novelty_pressure_is_high(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            config_path = root / "experiments" / "experiment_config.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                json.dumps(
                    {
                        "name": "creative_pack_baseline",
                        "scope": "CREATIVE_PACK",
                        "variant_a": {
                            "variant_type": "hook_style",
                            "hook_style": "question",
                            "narrative_mode": "official_warning",
                            "extra_param": "discard_me_only_if_conservative",
                        },
                        "variant_b": {"variant_type": "hook_style", "hook_style": "story_opening"},
                        "status": "ACTIVE",
                    }
                ),
                encoding="utf-8",
            )
            service = ExperimentCapabilityService(
                default_config_path=config_path,
                default_experiments_path=root / "experiments" / "experiments.jsonl",
                default_assignments_path=root / "experiments" / "assignments.jsonl",
                default_results_path=root / "experiments" / "results.jsonl",
            )

            result = service.generate(
                ExperimentCapabilityInput(
                    account_id="acc_pressure",
                    niche="horror",
                    topic="sealed tunnel",
                    publish_slot="2026-03-17T10:00:00Z",
                    learning_insights=LearningInsights(),
                    novelty_pressure_level="high",
                )
            )

            self.assertTrue(result.experiment_trace["eligibility_allowed"])
            self.assertEqual(result.experiment_trace["eligibility_reason"], "NOVELTY_PRESSURE_ALLOW")
            self.assertEqual(result.experiment_trace["eligibility_envelope"], "standard")
            self.assertEqual(result.decision_trace["assignment_path_used"], "framework_assign")

    def test_reuses_existing_experiment_definition_across_multiple_generations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            config_path = root / "experiments" / "experiment_config.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                json.dumps(
                    {
                        "name": "creative_pack_baseline",
                        "scope": "CREATIVE_PACK",
                        "variant_a": {"variant_type": "hook_style", "hook_style": "question"},
                        "variant_b": {"variant_type": "hook_style", "hook_style": "story_opening"},
                        "status": "ACTIVE",
                    }
                ),
                encoding="utf-8",
            )
            service = ExperimentCapabilityService(
                default_config_path=config_path,
                default_experiments_path=root / "experiments" / "experiments.jsonl",
                default_assignments_path=root / "experiments" / "assignments.jsonl",
                default_results_path=root / "experiments" / "results.jsonl",
            )

            first = service.generate(
                ExperimentCapabilityInput(
                    account_id="acc_1",
                    niche="horror",
                    topic="sealed tunnel",
                    publish_slot="2026-03-17T10:00:00Z",
                    learning_insights=LearningInsights(),
                )
            )
            second = service.generate(
                ExperimentCapabilityInput(
                    account_id="acc_2",
                    niche="horror",
                    topic="second sealed tunnel",
                    publish_slot="2026-03-17T11:00:00Z",
                    learning_insights=LearningInsights(),
                )
            )

            self.assertFalse(first.fallback.used)
            self.assertFalse(second.fallback.used)
            self.assertIsNotNone(first.experiment_assignment)
            self.assertIsNotNone(second.experiment_assignment)
            self.assertEqual(first.experiment_plan.experiment_id, second.experiment_plan.experiment_id)
            self.assertNotEqual(first.experiment_assignment.assignment_id, second.experiment_assignment.assignment_id)
            experiments_rows = _read_jsonl(root / "experiments" / "experiments.jsonl")
            self.assertEqual(len(experiments_rows), 1)

    def test_record_result_is_idempotent_for_same_subject_window_and_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            config_path = root / "experiments" / "experiment_config.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                json.dumps(
                    {
                        "name": "creative_pack_baseline",
                        "scope": "CREATIVE_PACK",
                        "variant_a": {"variant_type": "hook_style", "hook_style": "question"},
                        "variant_b": {"variant_type": "hook_style", "hook_style": "story_opening"},
                        "status": "ACTIVE",
                    }
                ),
                encoding="utf-8",
            )
            service = ExperimentCapabilityService(
                default_config_path=config_path,
                default_experiments_path=root / "experiments" / "experiments.jsonl",
                default_assignments_path=root / "experiments" / "assignments.jsonl",
                default_results_path=root / "experiments" / "results.jsonl",
            )
            result = service.generate(
                ExperimentCapabilityInput(
                    account_id="acc_1",
                    niche="horror",
                    topic="sealed tunnel",
                    publish_slot="2026-03-17T10:00:00Z",
                    learning_insights=LearningInsights(),
                )
            )
            metrics = {
                "qc_status": "APPROVE",
                "publishable": True,
                "overall_score": 0.91,
                "render_status": "READY",
            }

            first_record, first_action = service.record_runtime_result(
                result=result,
                window_id="2026-03-17T10:00:00Z",
                metrics=metrics,
            )
            second_record, second_action = service.record_runtime_result(
                result=result,
                window_id="2026-03-17T10:00:00Z",
                metrics=metrics,
            )

            self.assertEqual(first_action, "WRITTEN")
            self.assertEqual(second_action, "NOOP")
            self.assertEqual(first_record["result_id"], second_record["result_id"])
            result_rows = _read_jsonl(root / "experiments" / "results.jsonl")
            self.assertEqual(len(result_rows), 1)


if __name__ == "__main__":
    unittest.main()
