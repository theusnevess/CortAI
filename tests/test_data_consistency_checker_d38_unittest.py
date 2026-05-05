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

from app.analysis.consistency.service import DataConsistencyCheckerService
from app.content.creative_pack.store_jsonl import append_pack
from app.data.publish_records.store_jsonl import append_record as append_publish
from app.experiments.store_jsonl import append_record as append_experiment
from app.metrics.store_jsonl import append_record as append_metric


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


class DataConsistencyCheckerD38Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "OUT"
        self.publish_records_path = self.out / "data" / "publish_records" / "publish_records.jsonl"
        self.video_metrics_path = self.out / "metrics" / "video_metrics.jsonl"
        self.experiments_path = self.out / "experiments" / "experiments.jsonl"
        self.assignments_path = self.out / "experiments" / "assignments.jsonl"
        self.results_path = self.out / "experiments" / "results.jsonl"
        self.creative_packs_path = self.out / "content" / "creative_packs" / "creative_packs.jsonl"
        self.hook_performance_path = self.out / "attribution" / "hook_performance.jsonl"
        self.account_health_path = self.out / "intelligence" / "account_health.jsonl"
        self.risk_profiles_path = self.out / "intelligence" / "risk_profiles.jsonl"
        self.safety_events_path = self.out / "events" / "events.jsonl"
        self.analysis_dir = self.out / "analysis"
        self.service = DataConsistencyCheckerService(
            publish_records_path=self.publish_records_path,
            video_metrics_path=self.video_metrics_path,
            experiments_path=self.experiments_path,
            assignments_path=self.assignments_path,
            results_path=self.results_path,
            creative_packs_path=self.creative_packs_path,
            hook_performance_path=self.hook_performance_path,
            account_health_path=self.account_health_path,
            risk_profiles_path=self.risk_profiles_path,
            safety_events_path=self.safety_events_path,
            analysis_dir=self.analysis_dir,
        )

    def _seed_consistent_fixture(self) -> None:
        append_publish(
            {
                "publish_id": "pub_001",
                "account_id": "acc_001",
                "video_id": "vid_001",
                "job_id": "job_001",
                "platform": "tiktok",
                "status": "posted",
                "metadata": {"creative_pack_id": "cp_001"},
            },
            self.publish_records_path,
        )
        append_metric(
            {
                "publish_id": "pub_001",
                "account_id": "acc_001",
                "video_id": "vid_001",
                "captured_at": "2026-03-07T10:00:00Z",
                "captured_window_id": "w_001",
                "source_kind": "PLATFORM_ANALYTICS",
                "views": 100,
                "ingested_at": "2026-03-07T10:05:00Z",
                "collected_at_bucket": "2026-03-07T10:00:00Z",
            },
            self.video_metrics_path,
        )
        append_experiment({"experiment_id": "exp_001"}, self.experiments_path)
        append_experiment(
            {"assignment_id": "asg_001", "experiment_id": "exp_001", "subject_key": "pub_001"},
            self.assignments_path,
        )
        append_experiment(
            {"result_id": "res_001", "assignment_id": "asg_001", "experiment_id": "exp_001"},
            self.results_path,
        )
        append_pack({"creative_pack_id": "cp_001"}, self.creative_packs_path)
        _write_jsonl(self.hook_performance_path, [{"hook_performance_id": "hp_001"}])
        _write_jsonl(self.safety_events_path, [{"event_type": "SAFETY/pacing_delay", "account_id": "acc_001"}])
        _write_jsonl(
            self.account_health_path,
            [{"snapshot_id": "ah_001", "account_id": "acc_001", "risk_level": "LOW"}],
        )
        _write_jsonl(
            self.risk_profiles_path,
            [{"profile_id": "rp_001", "account_id": "acc_001", "risk_level": "LOW"}],
        )
        _write_json(self.analysis_dir / "pilot_metrics_summary.json", {"status": "ok"})
        _write_json(self.analysis_dir / "experiment_winners.json", {"status": "ok"})
        _write_json(self.analysis_dir / "hook_performance_summary.json", {"status": "ok"})
        _write_json(self.analysis_dir / "account_health_summary.json", {"status": "ok"})

    def _load_summary_json(self) -> dict:
        return json.loads((self.analysis_dir / "consistency_check.json").read_text(encoding="utf-8"))

    def _check_status(self, summary, check_id: str) -> dict:
        for item in summary["checks"]:
            if item["check_id"] == check_id:
                return item
        raise AssertionError(f"missing check_id {check_id}")

    def test_tudo_consistente_ok(self) -> None:
        self._seed_consistent_fixture()

        summary = self.service.generate_consistency_report(generated_at="2026-03-07T22:00:00Z")

        self.assertEqual(summary.status, "OK")
        self.assertEqual(summary.checks_failed, 0)
        self.assertEqual(summary.checks_run, 6)
        self.assertTrue((self.analysis_dir / "consistency_check.json").exists())
        self.assertTrue((self.analysis_dir / "consistency_check.md").exists())

    def test_video_metrics_sem_publish_record_fail(self) -> None:
        append_metric(
            {
                "publish_id": "pub_missing",
                "account_id": "acc_001",
                "video_id": "vid_001",
                "captured_at": "2026-03-07T10:00:00Z",
                "captured_window_id": "w_001",
                "source_kind": "PLATFORM_ANALYTICS",
                "views": 100,
                "ingested_at": "2026-03-07T10:05:00Z",
                "collected_at_bucket": "2026-03-07T10:00:00Z",
            },
            self.video_metrics_path,
        )

        self.service.generate_consistency_report(generated_at="2026-03-07T22:00:00Z")
        summary = self._load_summary_json()
        check = self._check_status(summary, "video_metrics_reference_publish_record")

        self.assertEqual(summary["status"], "FAIL")
        self.assertEqual(check["status"], "FAIL")
        self.assertGreater(check["missing_count"], 0)

    def test_publish_record_sem_video_metrics_fail(self) -> None:
        append_publish(
            {
                "publish_id": "pub_001",
                "account_id": "acc_001",
                "video_id": "vid_001",
                "job_id": "job_001",
                "platform": "tiktok",
                "status": "posted",
            },
            self.publish_records_path,
        )

        self.service.generate_consistency_report(generated_at="2026-03-07T22:00:00Z")
        summary = self._load_summary_json()
        check = self._check_status(summary, "publish_record_has_video_metrics")

        self.assertEqual(check["status"], "FAIL")
        self.assertEqual(check["expected"], 1)
        self.assertEqual(check["found"], 0)
        self.assertEqual(check["missing_count"], 1)

    def test_assignment_sem_experimento_fail(self) -> None:
        append_experiment(
            {"assignment_id": "asg_001", "experiment_id": "exp_missing", "subject_key": "pub_001"},
            self.assignments_path,
        )

        self.service.generate_consistency_report(generated_at="2026-03-07T22:00:00Z")
        summary = self._load_summary_json()
        check = self._check_status(summary, "experiment_assignment_references_experiment")

        self.assertEqual(check["status"], "FAIL")
        self.assertGreater(check["missing_count"], 0)

    def test_result_sem_assignment_fail(self) -> None:
        append_experiment(
            {"result_id": "res_001", "assignment_id": "asg_missing", "experiment_id": "exp_001"},
            self.results_path,
        )

        self.service.generate_consistency_report(generated_at="2026-03-07T22:00:00Z")
        summary = self._load_summary_json()
        check = self._check_status(summary, "experiment_result_references_assignment")

        self.assertEqual(check["status"], "FAIL")
        self.assertGreater(check["missing_count"], 0)

    def test_creative_pack_id_ausente_fail(self) -> None:
        append_publish(
            {
                "publish_id": "pub_001",
                "account_id": "acc_001",
                "video_id": "vid_001",
                "job_id": "job_001",
                "platform": "tiktok",
                "status": "posted",
                "metadata": {"creative_pack_id": "cp_missing"},
            },
            self.publish_records_path,
        )

        self.service.generate_consistency_report(generated_at="2026-03-07T22:00:00Z")
        summary = self._load_summary_json()
        check = self._check_status(summary, "publish_record_metadata_creative_pack_exists")

        self.assertEqual(check["status"], "FAIL")
        self.assertGreater(check["missing_count"], 0)

    def test_outputs_de_analise_nao_derivaveis_fail(self) -> None:
        _write_json(self.analysis_dir / "experiment_winners.json", {"status": "ok"})

        self.service.generate_consistency_report(generated_at="2026-03-07T22:00:00Z")
        summary = self._load_summary_json()
        check = self._check_status(summary, "analysis_outputs_derivable_from_inputs")

        self.assertEqual(check["status"], "FAIL")
        self.assertGreater(check["missing_count"], 0)

    def test_determinismo(self) -> None:
        self._seed_consistent_fixture()

        first = self.service.generate_consistency_report(generated_at="2026-03-07T22:00:00Z").to_dict()
        second = self.service.generate_consistency_report(generated_at="2026-03-07T22:00:00Z").to_dict()

        self.assertEqual(first, second)

    def test_sem_side_effects_fora_dos_outputs(self) -> None:
        self._seed_consistent_fixture()
        before = sorted(
            str(path.relative_to(self.out))
            for path in self.out.rglob("*")
            if path.is_file()
        )

        self.service.generate_consistency_report(generated_at="2026-03-07T22:00:00Z")
        after = sorted(
            str(path.relative_to(self.out))
            for path in self.out.rglob("*")
            if path.is_file()
        )

        added = sorted(set(after) - set(before))
        self.assertEqual(
            [item.replace("\\", "/") for item in added],
            [
                "analysis/consistency_check.json",
                "analysis/consistency_check.md",
            ],
        )


if __name__ == "__main__":
    unittest.main()
