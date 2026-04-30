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

from app.attribution.service import AdvancedAttributionService
from app.data.publish_records.writer import write_publish_record
from app.data.video_metrics.writer import write_video_metrics
from app.experiments.service import ExperimentService


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


class AdvancedAttributionD32Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "OUT"
        self.publish_path = self.out / "data" / "publish_records" / "publish_records.jsonl"
        self.metrics_path = self.out / "data" / "video_metrics" / "video_metrics.jsonl"
        self.creative_path = self.out / "content" / "creative_packs" / "creative_packs.jsonl"
        self.assignments_path = self.out / "experiments" / "assignments.jsonl"
        self.experiments_path = self.out / "experiments" / "experiments.jsonl"
        self.results_path = self.out / "experiments" / "results.jsonl"
        self.attribution_dir = self.out / "attribution"
        self.service = AdvancedAttributionService(
            publish_records_path=self.publish_path,
            video_metrics_path=self.metrics_path,
            creative_packs_path=self.creative_path,
            assignments_path=self.assignments_path,
            attribution_dir=self.attribution_dir,
        )
        self.experiment_service = ExperimentService(
            experiments_path=self.experiments_path,
            assignments_path=self.assignments_path,
            results_path=self.results_path,
        )

    def _seed_publish_metrics_creative(self) -> None:
        _write_jsonl(
            self.creative_path,
            [
                {
                    "creative_pack_id": "cp_001",
                    "account_id": "acc_001",
                    "policy_stage": "GROWTH",
                    "theme": "crime real",
                    "variation_index": 1,
                    "angle": "case_breakdown",
                    "title": "1. crime real: o detalhe oculto",
                    "hook_candidates": ["3 sinais de que esse caso mudou tudo", "o que quase ninguem percebeu"],
                    "script_skeleton": "HOOK: x\nSETUP: y\nANGLE: z\nPAYOFF: p\nCTA: c",
                    "hashtags": ["#crime"],
                    "cta": "comenta parte 2",
                    "strategy_patch_id": None,
                    "generated_at": "2026-03-07T20:00:00Z",
                }
            ],
        )
        write_publish_record(
            {
                "publish_id": "pub_001",
                "account_id": "acc_001",
                "job_id": "job_001",
                "video_id": "vid_001",
                "window_id": "w_001",
                "platform": "tiktok",
                "publish_mode": "auto",
                "status": "posted",
                "published_at": "2026-03-07T14:00:00Z",
                "created_at": "2026-03-07T14:00:00Z",
                "metadata": {
                    "creative_pack_id": "cp_001",
                    "duration_s": 42,
                },
            },
            path=self.publish_path,
        )
        write_video_metrics(
            {
                "video_id": "vid_001",
                "provider": "tiktok",
                "external_video_id": "vid_001",
                "account_id": "acc_001",
                "captured_window_id": "w_001",
                "views": 2500,
                "likes": 120,
                "follows": 15,
                "retention_3s": 0.76,
                "completion_rate": 0.48,
                "captured_at": "2026-03-07T18:00:00Z",
                "ingested_at": "2026-03-07T18:05:00Z",
                "source_kind": "PLATFORM_ANALYTICS",
            },
            path=self.metrics_path,
        )

    def _rows(self, name: str) -> list[dict]:
        path = self.attribution_dir / name
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def test_analise_de_hook(self) -> None:
        self._seed_publish_metrics_creative()
        result = self.service.analyze_account(account_id="acc_001", generated_at="2026-03-07T20:00:00Z")
        item = result["hook_performance"][0]
        self.assertEqual(item["hook_type"], "LISTICLE")
        self.assertEqual(item["views"], 2500)
        self.assertAlmostEqual(item["watch_3s_rate"], 0.76)

    def test_analise_de_estrutura(self) -> None:
        self._seed_publish_metrics_creative()
        result = self.service.analyze_account(account_id="acc_001", generated_at="2026-03-07T20:00:00Z")
        item = result["structure_performance"][0]
        self.assertEqual(item["structure_key"], "HOOK>SETUP>ANGLE>PAYOFF>CTA")

    def test_analise_de_duracao(self) -> None:
        self._seed_publish_metrics_creative()
        result = self.service.analyze_account(account_id="acc_001", generated_at="2026-03-07T20:00:00Z")
        item = result["duration_analysis"][0]
        self.assertEqual(item["duration_s"], 42)
        self.assertEqual(item["duration_bucket"], "MEDIUM")
        self.assertAlmostEqual(item["dropoff_point"], 21.84)

    def test_persistencia_append_only(self) -> None:
        self._seed_publish_metrics_creative()
        self.service.analyze_account(account_id="acc_001", generated_at="2026-03-07T20:00:00Z")
        self.assertEqual(len(self._rows("hook_performance.jsonl")), 1)
        self.assertEqual(len(self._rows("structure_performance.jsonl")), 1)
        self.assertEqual(len(self._rows("duration_analysis.jsonl")), 1)
        self.assertEqual(len(self._rows("pattern_performance.jsonl")), 1)

    def test_recomputacao_deterministica(self) -> None:
        self._seed_publish_metrics_creative()
        first = self.service.analyze_account(account_id="acc_001", generated_at="2026-03-07T20:00:00Z")
        second = self.service.analyze_account(account_id="acc_001", generated_at="2026-03-07T20:00:00Z")
        self.assertEqual(first["hook_performance"], second["hook_performance"])
        self.assertEqual(second["actions"]["hook"], ["NOOP"])
        self.assertEqual(len(self._rows("hook_performance.jsonl")), 1)

    def test_compatibilidade_com_experiment_assignments(self) -> None:
        self._seed_publish_metrics_creative()
        experiment, _ = self.experiment_service.create_experiment(
            name="creative hook test",
            scope="CREATIVE_PACK",
            variant_a={"hook_style": "listicle"},
            variant_b={"hook_style": "curiosity_gap"},
            created_at="2026-03-07T19:00:00Z",
        )
        assignment, _ = self.experiment_service.assign(
            experiment=experiment,
            subject_key="cp_001",
            assigned_at="2026-03-07T19:05:00Z",
        )
        result = self.service.analyze_account(account_id="acc_001", generated_at="2026-03-07T20:00:00Z")
        self.assertEqual(result["hook_performance"][0]["experiment_variant"], assignment.variant)
        self.assertEqual(result["pattern_performance"][0]["experiment_variant"], assignment.variant)


if __name__ == "__main__":
    unittest.main()
