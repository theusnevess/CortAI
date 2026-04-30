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

from app.analysis.service import AnalysisService
from app.data.publish_records.writer import write_publish_record
from app.data.video_metrics.writer import write_video_metrics
from app.experiments.service import ExperimentService


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


class AnalysisResearchLayerD34Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "OUT"
        self.publish_path = self.out / "data" / "publish_records" / "publish_records.jsonl"
        self.metrics_path = self.out / "metrics" / "video_metrics.jsonl"
        self.experiments_path = self.out / "experiments" / "experiments.jsonl"
        self.assignments_path = self.out / "experiments" / "assignments.jsonl"
        self.results_path = self.out / "experiments" / "results.jsonl"
        self.hook_path = self.out / "attribution" / "hook_performance.jsonl"
        self.account_health_path = self.out / "intelligence" / "account_health.jsonl"
        self.risk_profiles_path = self.out / "intelligence" / "risk_profiles.jsonl"
        self.creative_packs_path = self.out / "content" / "creative_packs" / "creative_packs.jsonl"
        self.events_path = self.out / "events" / "events.jsonl"
        self.analysis_dir = self.out / "analysis"
        self.service = AnalysisService(
            publish_records_path=self.publish_path,
            video_metrics_path=self.metrics_path,
            experiments_path=self.experiments_path,
            assignments_path=self.assignments_path,
            hook_performance_path=self.hook_path,
            account_health_path=self.account_health_path,
            risk_profiles_path=self.risk_profiles_path,
            creative_packs_path=self.creative_packs_path,
            events_path=self.events_path,
            analysis_dir=self.analysis_dir,
        )
        self.experiment_service = ExperimentService(
            experiments_path=self.experiments_path,
            assignments_path=self.assignments_path,
            results_path=self.results_path,
        )

    def _read_json(self, name: str) -> dict:
        path = self.analysis_dir / name
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _seed_publish_metrics(self) -> None:
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
                "published_at": "2026-03-07T10:00:00Z",
                "created_at": "2026-03-07T10:00:00Z",
                "metadata": {"creative_pack_id": "cp_001"},
            },
            path=self.publish_path,
        )
        write_publish_record(
            {
                "publish_id": "pub_002",
                "account_id": "acc_002",
                "job_id": "job_002",
                "video_id": "vid_002",
                "window_id": "w_002",
                "platform": "tiktok",
                "publish_mode": "auto",
                "status": "posted",
                "published_at": "2026-03-07T11:00:00Z",
                "created_at": "2026-03-07T11:00:00Z",
                "metadata": {"creative_pack_id": "cp_002"},
            },
            path=self.publish_path,
        )
        write_video_metrics(
            {
                "metrics_id": "vm_001",
                "publish_id": "pub_001",
                "account_id": "acc_001",
                "video_id": "vid_001",
                "captured_at": "2026-03-07T12:00:00Z",
                "captured_window_id": "w_001",
                "source_kind": "PLATFORM_ANALYTICS",
                "ingested_at": "2026-03-07T12:00:05Z",
                "views": 100,
                "likes": 10,
                "comments": 2,
                "shares": 1,
                "watch_time_total": 400.0,
                "avg_watch_time": 4.0,
                "completion_rate": 0.20,
                "view_3s_rate": 0.50,
                "view_5s_rate": 0.30,
                "collected_at": "2026-03-07T12:00:00Z",
                "collected_at_bucket": "2026-03-07T12:00:00Z",
                "age_hours": 2.0,
                "provider": "tiktok",
            },
            path=self.metrics_path,
        )
        write_video_metrics(
            {
                "metrics_id": "vm_002",
                "publish_id": "pub_002",
                "account_id": "acc_002",
                "video_id": "vid_002",
                "captured_at": "2026-03-07T12:00:00Z",
                "captured_window_id": "w_002",
                "source_kind": "PLATFORM_ANALYTICS",
                "ingested_at": "2026-03-07T12:00:05Z",
                "views": 300,
                "likes": 30,
                "comments": 5,
                "shares": 3,
                "watch_time_total": 1800.0,
                "avg_watch_time": 6.0,
                "completion_rate": 0.40,
                "view_3s_rate": 0.70,
                "view_5s_rate": 0.55,
                "collected_at": "2026-03-07T12:00:00Z",
                "collected_at_bucket": "2026-03-07T12:00:00Z",
                "age_hours": 1.0,
                "provider": "tiktok",
            },
            path=self.metrics_path,
        )

    def _seed_experiments(self) -> None:
        experiment, _ = self.experiment_service.create_experiment(
            name="hook pilot test",
            scope="HOOK_STYLE",
            variant_a={"hook_style": "question"},
            variant_b={"hook_style": "curiosity"},
            created_at="2026-03-07T09:00:00Z",
        )
        _write_jsonl(
            self.assignments_path,
            [
                {
                    "assignment_id": "asg_001",
                    "experiment_id": experiment.experiment_id,
                    "subject_key": "pub_001",
                    "variant": "A",
                    "assigned_at": "2026-03-07T09:05:00Z",
                },
                {
                    "assignment_id": "asg_002",
                    "experiment_id": experiment.experiment_id,
                    "subject_key": "pub_002",
                    "variant": "B",
                    "assigned_at": "2026-03-07T09:05:00Z",
                },
            ],
        )

    def _seed_hook_and_creative(self) -> None:
        _write_jsonl(
            self.creative_packs_path,
            [
                {
                    "creative_pack_id": "cp_001",
                    "account_id": "acc_001",
                    "hook_candidates": ["why did this happen?"],
                },
                {
                    "creative_pack_id": "cp_002",
                    "account_id": "acc_002",
                    "hook_candidates": ["this changed everything"],
                },
            ],
        )
        _write_jsonl(
            self.hook_path,
            [
                {
                    "hook_performance_id": "hp_002",
                    "publish_id": "pub_002",
                    "creative_pack_id": "cp_002",
                    "hook_id": "hook_b",
                    "hook_type": "STATEMENT",
                    "completion_rate": 0.40,
                    "watch_time": 6.0,
                },
                {
                    "hook_performance_id": "hp_001",
                    "publish_id": "pub_001",
                    "creative_pack_id": "cp_001",
                    "hook_id": "hook_a",
                    "hook_type": "QUESTION",
                    "completion_rate": 0.20,
                    "watch_time": 4.0,
                },
                {
                    "hook_performance_id": "hp_003",
                    "publish_id": "pub_003",
                    "creative_pack_id": "cp_001",
                    "hook_id": "hook_a",
                    "hook_type": "QUESTION",
                    "completion_rate": 0.30,
                    "watch_time": 5.0,
                },
            ],
        )

    def _seed_account_health(self) -> None:
        _write_jsonl(
            self.account_health_path,
            [
                {
                    "snapshot_id": "ah_001",
                    "account_id": "acc_001",
                    "risk_level": "LOW",
                    "cooldown_active": False,
                    "generated_at": "2026-03-07T12:00:00Z",
                },
                {
                    "snapshot_id": "ah_002",
                    "account_id": "acc_002",
                    "risk_level": "HIGH",
                    "cooldown_active": True,
                    "generated_at": "2026-03-07T12:00:00Z",
                },
            ],
        )
        _write_jsonl(
            self.risk_profiles_path,
            [
                {
                    "profile_id": "rp_001",
                    "account_id": "acc_001",
                    "risk_level": "LOW",
                    "generated_at": "2026-03-07T12:00:00Z",
                },
                {
                    "profile_id": "rp_002",
                    "account_id": "acc_002",
                    "risk_level": "HIGH",
                    "generated_at": "2026-03-07T12:00:00Z",
                },
            ],
        )
        _write_jsonl(
            self.events_path,
            [
                {"event_type": "SAFETY/pacing_delay", "account_id": "acc_001", "ts": "2026-03-07T12:10:00Z"},
                {"event_type": "SAFETY/risk_detected", "account_id": "acc_002", "ts": "2026-03-07T12:20:00Z"},
                {"event_type": "SAFETY/publish_blocked", "account_id": "acc_002", "ts": "2026-03-07T12:30:00Z"},
                {"event_type": "SAFETY/cooldown_started", "account_id": "acc_002", "ts": "2026-03-07T12:40:00Z"},
            ],
        )

    def test_pilot_metrics_summary_correto(self) -> None:
        self._seed_publish_metrics()
        result = self.service.generate_analysis_snapshots(generated_at="2026-03-07T13:00:00Z")
        summary = result["pilot_metrics_summary"]
        self.assertEqual(summary["total_accounts"], 2)
        self.assertEqual(summary["total_videos"], 2)
        self.assertEqual(summary["total_views"], 400)
        self.assertAlmostEqual(summary["avg_watch_time"], 5.0)
        self.assertAlmostEqual(summary["avg_completion_rate"], 0.30)
        self.assertAlmostEqual(summary["avg_3s_view_rate"], 0.60)
        self.assertEqual(summary["top_account_id"], "acc_002")

    def test_experiment_winners_deterministico(self) -> None:
        self._seed_publish_metrics()
        self._seed_experiments()
        first = self.service.generate_analysis_snapshots(generated_at="2026-03-07T13:00:00Z")
        second = self.service.generate_analysis_snapshots(generated_at="2026-03-07T13:00:00Z")
        winner_a = first["experiment_winners"]["experiments"][0]
        winner_b = second["experiment_winners"]["experiments"][0]
        self.assertEqual(winner_a, winner_b)
        self.assertEqual(winner_a["winner_variant"], "B")
        self.assertEqual(winner_a["supporting_metric"], "completion_rate")

    def test_hook_performance_summary_consistente(self) -> None:
        self._seed_publish_metrics()
        self._seed_hook_and_creative()
        result = self.service.generate_analysis_snapshots(generated_at="2026-03-07T13:00:00Z")
        hooks = result["hook_performance_summary"]["hooks"]
        self.assertEqual(len(hooks), 2)
        self.assertEqual(hooks[0]["hook_id"], "hook_b")
        self.assertEqual(hooks[0]["performance_rank"], 1)
        self.assertEqual(hooks[1]["hook_id"], "hook_a")
        self.assertEqual(hooks[1]["video_count"], 2)
        self.assertEqual(hooks[1]["performance_rank"], 2)

    def test_account_health_summary_reflete_safety(self) -> None:
        self._seed_publish_metrics()
        self._seed_account_health()
        result = self.service.generate_analysis_snapshots(generated_at="2026-03-07T13:00:00Z")
        accounts = {item["account_id"]: item for item in result["account_health_summary"]["accounts"]}
        self.assertEqual(accounts["acc_001"]["risk_level"], "LOW")
        self.assertFalse(accounts["acc_001"]["cooldown_active"])
        self.assertEqual(accounts["acc_001"]["pacing_delays_count"], 1)
        self.assertEqual(accounts["acc_001"]["health_status"], "HEALTHY")
        self.assertEqual(accounts["acc_002"]["risk_level"], "HIGH")
        self.assertTrue(accounts["acc_002"]["cooldown_active"])
        self.assertEqual(accounts["acc_002"]["recent_risk_events_count"], 2)
        self.assertEqual(accounts["acc_002"]["health_status"], "COOLDOWN")

    def test_determinismo_de_saida(self) -> None:
        self._seed_publish_metrics()
        self._seed_experiments()
        self._seed_hook_and_creative()
        self._seed_account_health()
        first = self.service.generate_analysis_snapshots(generated_at="2026-03-07T13:00:00Z")
        second = self.service.generate_analysis_snapshots(generated_at="2026-03-07T13:00:00Z")
        self.assertEqual(first["pilot_metrics_summary"], second["pilot_metrics_summary"])
        self.assertEqual(first["experiment_winners"], second["experiment_winners"])
        self.assertEqual(first["hook_performance_summary"], second["hook_performance_summary"])
        self.assertEqual(first["account_health_summary"], second["account_health_summary"])

    def test_persistencia_correta_em_out_analysis(self) -> None:
        self._seed_publish_metrics()
        self._seed_experiments()
        self._seed_hook_and_creative()
        self._seed_account_health()
        self.service.generate_analysis_snapshots(generated_at="2026-03-07T13:00:00Z")
        self.assertTrue((self.analysis_dir / "pilot_metrics_summary.json").exists())
        self.assertTrue((self.analysis_dir / "experiment_winners.json").exists())
        self.assertTrue((self.analysis_dir / "hook_performance_summary.json").exists())
        self.assertTrue((self.analysis_dir / "account_health_summary.json").exists())
        self.assertIn("total_views", self._read_json("pilot_metrics_summary.json"))
        self.assertIn("experiments", self._read_json("experiment_winners.json"))
        self.assertIn("hooks", self._read_json("hook_performance_summary.json"))
        self.assertIn("accounts", self._read_json("account_health_summary.json"))

    def test_dados_parciais_nao_quebram(self) -> None:
        result = self.service.generate_analysis_snapshots(generated_at="2026-03-07T13:00:00Z")
        self.assertEqual(result["pilot_metrics_summary"]["total_accounts"], 0)
        self.assertEqual(result["pilot_metrics_summary"]["total_videos"], 0)
        self.assertEqual(result["pilot_metrics_summary"]["total_views"], 0)
        self.assertEqual(result["experiment_winners"]["experiments"], [])
        self.assertEqual(result["hook_performance_summary"]["hooks"], [])
        self.assertEqual(result["account_health_summary"]["accounts"], [])


if __name__ == "__main__":
    unittest.main()
