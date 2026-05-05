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

from app.experiments.repo import ExperimentConflictError
from app.experiments.service import ExperimentService


class ExperimentFrameworkD31Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        out = Path(self.tmp.name) / "OUT" / "experiments"
        self.service = ExperimentService(
            experiments_path=out / "experiments.jsonl",
            assignments_path=out / "assignments.jsonl",
            results_path=out / "results.jsonl",
        )
        self.out = out

    def _rows(self, name: str) -> list[dict]:
        path = self.out / name
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def test_criacao_de_experimento(self) -> None:
        experiment, action = self.service.create_experiment(
            name="hook test",
            scope="HOOK_STYLE",
            variant_a={"hook_style": "curiosity_gap"},
            variant_b={"hook_style": "story_arc"},
            created_at="2026-03-07T20:00:00Z",
        )
        self.assertEqual(action, "WRITTEN")
        self.assertEqual(experiment.scope, "HOOK_STYLE")
        self.assertEqual(len(self._rows("experiments.jsonl")), 1)

    def test_assignment_deterministico_estavel(self) -> None:
        experiment, _ = self.service.create_experiment(
            name="window test",
            scope="PUBLISH_WINDOW",
            variant_a={"window": "14:00"},
            variant_b={"window": "18:00"},
            created_at="2026-03-07T20:00:00Z",
        )
        first, action1 = self.service.assign(experiment=experiment, subject_key="acc_001|w_001", assigned_at="2026-03-07T20:01:00Z")
        second, action2 = self.service.assign(experiment=experiment, subject_key="acc_001|w_001", assigned_at="2026-03-07T20:01:00Z")
        self.assertEqual(first.variant, second.variant)
        self.assertEqual(action1, "WRITTEN")
        self.assertEqual(action2, "NOOP")

    def test_mesmo_input_mesma_variante(self) -> None:
        experiment, _ = self.service.create_experiment(
            name="creative test",
            scope="CREATIVE_PACK",
            variant_a={"title_style": "numbered"},
            variant_b={"title_style": "question"},
            created_at="2026-03-07T20:00:00Z",
        )
        variant1, payload1 = self.service.resolve_variant_payload(experiment=experiment, subject_key="acc_001|w_001")
        variant2, payload2 = self.service.resolve_variant_payload(experiment=experiment, subject_key="acc_001|w_001")
        self.assertEqual(variant1, variant2)
        self.assertEqual(payload1, payload2)

    def test_persistencia_append_only(self) -> None:
        experiment, _ = self.service.create_experiment(
            name="pacing test",
            scope="PACING_PROFILE",
            variant_a={"min_interval": 90},
            variant_b={"min_interval": 120},
            created_at="2026-03-07T20:00:00Z",
        )
        self.service.assign(experiment=experiment, subject_key="acc_001|w_001", assigned_at="2026-03-07T20:01:00Z")
        self.service.record_result(
            experiment=experiment,
            subject_key="acc_001|w_001",
            window_id="w_001",
            metrics={"views": 1200},
            recorded_at="2026-03-07T20:02:00Z",
        )
        self.assertEqual(len(self._rows("experiments.jsonl")), 1)
        self.assertEqual(len(self._rows("assignments.jsonl")), 1)
        self.assertEqual(len(self._rows("results.jsonl")), 1)

    def test_duplicidade_vira_noop(self) -> None:
        first, action1 = self.service.create_experiment(
            name="hook test",
            scope="HOOK_STYLE",
            variant_a={"hook_style": "curiosity_gap"},
            variant_b={"hook_style": "story_arc"},
            created_at="2026-03-07T20:00:00Z",
        )
        second, action2 = self.service.create_experiment(
            name="hook test",
            scope="HOOK_STYLE",
            variant_a={"hook_style": "curiosity_gap"},
            variant_b={"hook_style": "story_arc"},
            created_at="2026-03-07T20:00:00Z",
        )
        self.assertEqual(first.experiment_id, second.experiment_id)
        self.assertEqual(action1, "WRITTEN")
        self.assertEqual(action2, "NOOP")

    def test_conflito_vira_conflict(self) -> None:
        self.service.create_experiment(
            name="hook test",
            scope="HOOK_STYLE",
            variant_a={"hook_style": "curiosity_gap"},
            variant_b={"hook_style": "story_arc"},
            created_at="2026-03-07T20:00:00Z",
        )
        with self.assertRaises(ExperimentConflictError):
            self.service.create_experiment(
                name="hook test",
                scope="HOOK_STYLE",
                variant_a={"hook_style": "listicle"},
                variant_b={"hook_style": "story_arc"},
                created_at="2026-03-07T20:00:00Z",
            )


if __name__ == "__main__":
    unittest.main()
