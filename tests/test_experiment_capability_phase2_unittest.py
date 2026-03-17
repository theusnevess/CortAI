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
            self.assertTrue((root / "experiments" / "experiment_plan.json").exists())

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


if __name__ == "__main__":
    unittest.main()
