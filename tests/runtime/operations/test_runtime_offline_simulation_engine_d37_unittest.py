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

from app.analysis.consistency.service import DataConsistencyCheckerService
from app.simulation.runner import OfflineSimulationRunner


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


class OfflineSimulationEngineD37Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "OUT"
        self.simulation_dir = self.out / "simulation"
        self.runner = OfflineSimulationRunner(output_dir=self.simulation_dir)

    def _run(self, *, accounts: list[str] | None = None, publishes: int = 2):
        return self.runner.run_offline_simulation(
            simulation_run_id="run_001",
            account_ids=accounts or ["acc_001", "acc_002"],
            num_publishes_per_account=publishes,
            creative_pack_ids=["cp_001", "cp_002"],
            experiment_id="exp_001",
            variants=["A", "B"],
            start_at="2026-03-14T10:00:00Z",
            generated_at="2026-03-14T12:00:00Z",
        )

    def test_run_basico_gera_outputs(self) -> None:
        summary = self._run()

        publish_rows = _read_jsonl(self.simulation_dir / "simulated_publish_records.jsonl")
        metric_rows = _read_jsonl(self.simulation_dir / "simulated_video_metrics.jsonl")
        result_rows = _read_jsonl(self.simulation_dir / "simulated_experiment_results.jsonl")
        run_rows = _read_jsonl(self.simulation_dir / "simulation_runs.jsonl")

        self.assertEqual(summary.total_simulated_publishes, 4)
        self.assertEqual(summary.total_metrics, 4)
        self.assertEqual(summary.total_experiment_results, 4)
        self.assertEqual(len(publish_rows), 4)
        self.assertEqual(len(metric_rows), 4)
        self.assertEqual(len(result_rows), 4)
        self.assertEqual(len(run_rows), 1)

    def test_determinismo(self) -> None:
        self._run()
        first_publish = _read_jsonl(self.simulation_dir / "simulated_publish_records.jsonl")
        first_metrics = _read_jsonl(self.simulation_dir / "simulated_video_metrics.jsonl")
        first_results = _read_jsonl(self.simulation_dir / "simulated_experiment_results.jsonl")

        second_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(second_tmp.cleanup)
        second_runner = OfflineSimulationRunner(output_dir=Path(second_tmp.name) / "OUT" / "simulation")
        second_runner.run_offline_simulation(
            simulation_run_id="run_001",
            account_ids=["acc_001", "acc_002"],
            num_publishes_per_account=2,
            creative_pack_ids=["cp_001", "cp_002"],
            experiment_id="exp_001",
            variants=["A", "B"],
            start_at="2026-03-14T10:00:00Z",
            generated_at="2026-03-14T12:00:00Z",
        )
        second_publish = _read_jsonl(Path(second_tmp.name) / "OUT" / "simulation" / "simulated_publish_records.jsonl")
        second_metrics = _read_jsonl(Path(second_tmp.name) / "OUT" / "simulation" / "simulated_video_metrics.jsonl")
        second_results = _read_jsonl(Path(second_tmp.name) / "OUT" / "simulation" / "simulated_experiment_results.jsonl")

        self.assertEqual(first_publish, second_publish)
        self.assertEqual(first_metrics, second_metrics)
        self.assertEqual(first_results, second_results)

    def test_coerencia_de_referencias(self) -> None:
        self._run()

        publish_rows = _read_jsonl(self.simulation_dir / "simulated_publish_records.jsonl")
        metric_rows = _read_jsonl(self.simulation_dir / "simulated_video_metrics.jsonl")
        result_rows = _read_jsonl(self.simulation_dir / "simulated_experiment_results.jsonl")

        publish_ids = {item["simulated_publish_id"] for item in publish_rows}
        metric_ids = {item["simulated_publish_id"] for item in metric_rows}
        result_ids = {item["simulated_publish_id"] for item in result_rows}

        self.assertEqual(publish_ids, metric_ids)
        self.assertEqual(publish_ids, result_ids)

    def test_compatibilidade_com_d38(self) -> None:
        self._run()
        publish_rows = _read_jsonl(self.simulation_dir / "simulated_publish_records.jsonl")
        metric_rows = _read_jsonl(self.simulation_dir / "simulated_video_metrics.jsonl")
        result_rows = _read_jsonl(self.simulation_dir / "simulated_experiment_results.jsonl")

        checker_out = self.out / "checker"
        publish_path = checker_out / "data" / "publish_records" / "publish_records.jsonl"
        metrics_path = checker_out / "metrics" / "video_metrics.jsonl"
        experiments_path = checker_out / "experiments" / "experiments.jsonl"
        assignments_path = checker_out / "experiments" / "assignments.jsonl"
        results_path = checker_out / "experiments" / "results.jsonl"
        creative_packs_path = checker_out / "content" / "creative_packs" / "creative_packs.jsonl"
        hook_path = checker_out / "attribution" / "hook_performance.jsonl"
        events_path = checker_out / "events" / "events.jsonl"
        analysis_dir = checker_out / "analysis"

        _write_jsonl(
            publish_path,
            [
                {
                    "publish_id": item["simulated_publish_id"],
                    "account_id": item["account_id"],
                    "video_id": item["metadata"]["video_id"],
                    "job_id": f'job_{item["simulated_publish_id"]}',
                    "platform": "tiktok",
                    "status": "posted",
                    "metadata": {"creative_pack_id": item.get("creative_pack_id")},
                }
                for item in publish_rows
            ],
        )
        _write_jsonl(
            metrics_path,
            [
                {
                    "publish_id": item["simulated_publish_id"],
                    "account_id": next(row["account_id"] for row in publish_rows if row["simulated_publish_id"] == item["simulated_publish_id"]),
                    "video_id": next(row["metadata"]["video_id"] for row in publish_rows if row["simulated_publish_id"] == item["simulated_publish_id"]),
                    "captured_at": item["collected_at"],
                    "captured_window_id": "sim_window_001",
                    "source_kind": "PLATFORM_ANALYTICS",
                    "views": item["views"],
                    "ingested_at": item["collected_at"],
                    "collected_at_bucket": item["collected_at"],
                }
                for item in metric_rows
            ],
        )
        _write_jsonl(experiments_path, [{"experiment_id": "exp_001"}])
        _write_jsonl(
            assignments_path,
            [
                {
                    "assignment_id": f'asg_{item["simulated_publish_id"]}',
                    "experiment_id": "exp_001",
                    "subject_key": item["simulated_publish_id"],
                }
                for item in publish_rows
            ],
        )
        _write_jsonl(
            results_path,
            [
                {
                    "result_id": f'res_{item["simulated_publish_id"]}',
                    "assignment_id": f'asg_{item["simulated_publish_id"]}',
                    "experiment_id": item["experiment_id"],
                }
                for item in result_rows
            ],
        )
        _write_jsonl(
            creative_packs_path,
            [{"creative_pack_id": item["creative_pack_id"]} for item in publish_rows if item.get("creative_pack_id")],
        )
        _write_jsonl(hook_path, [{"hook_performance_id": "hp_001"}])
        _write_jsonl(events_path, [{"event_type": "SAFETY/pacing_delay", "account_id": "acc_001"}])
        _write_json(analysis_dir / "pilot_metrics_summary.json", {"status": "ok"})
        _write_json(analysis_dir / "experiment_winners.json", {"status": "ok"})
        _write_json(analysis_dir / "hook_performance_summary.json", {"status": "ok"})
        _write_json(analysis_dir / "account_health_summary.json", {"status": "ok"})

        checker = DataConsistencyCheckerService(
            publish_records_path=publish_path,
            video_metrics_path=metrics_path,
            experiments_path=experiments_path,
            assignments_path=assignments_path,
            results_path=results_path,
            creative_packs_path=creative_packs_path,
            hook_performance_path=hook_path,
            safety_events_path=events_path,
            analysis_dir=analysis_dir,
        )

        summary = checker.generate_consistency_report(generated_at="2026-03-14T12:30:00Z")

        self.assertEqual(summary.status, "OK")
        self.assertTrue((analysis_dir / "consistency_check.json").exists())
        self.assertTrue((analysis_dir / "consistency_check.md").exists())

    def test_nenhum_side_effect_fora_de_out_simulation(self) -> None:
        before = sorted(str(path.relative_to(self.out)).replace("\\", "/") for path in self.out.rglob("*") if path.is_file())

        self._run()

        after = sorted(str(path.relative_to(self.out)).replace("\\", "/") for path in self.out.rglob("*") if path.is_file())
        added = sorted(set(after) - set(before))
        self.assertEqual(
            added,
            [
                "simulation/simulated_experiment_results.jsonl",
                "simulation/simulated_publish_records.jsonl",
                "simulation/simulated_video_metrics.jsonl",
                "simulation/simulation_runs.jsonl",
            ],
        )

    def test_dados_minimos_nao_quebram(self) -> None:
        summary = self._run(accounts=["acc_001"], publishes=1)

        self.assertEqual(summary.total_accounts, 1)
        self.assertEqual(summary.total_simulated_publishes, 1)
        self.assertEqual(summary.total_metrics, 1)
        self.assertEqual(summary.total_experiment_results, 1)


if __name__ == "__main__":
    unittest.main()
