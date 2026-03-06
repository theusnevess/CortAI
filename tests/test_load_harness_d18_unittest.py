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

from app.perf.load_harness import LoadHarnessDeps, run_load_suite
from app.perf.scenarios import LoadScenario


class FakePerfRunners:
    def __init__(self) -> None:
        self.query_calls = 0

    def window_pipeline(self, **kwargs) -> dict:
        return {
            "status": "FINISHED",
            "reason_code": "PIPELINE_OK",
            "account_id": kwargs["account_id"],
            "window_id": kwargs["window_id"],
        }

    def window_post_pipeline(self, **kwargs) -> dict:
        if kwargs["account_id"].endswith("050"):
            return {
                "status": "SKIPPED_BLOCKED_CONFLICT",
                "reason_code": "IDEMPOTENCY_CONFLICT",
            }
        return {
            "status": "FINISHED",
            "reason_code": "PIPELINE_OK",
        }

    def query(self, **kwargs) -> dict:
        self.query_calls += 1
        force_hot_store_failure = bool(kwargs.get("force_hot_store_failure"))
        if force_hot_store_failure:
            return {
                "status": "OK",
                "fallback_level": "INDEX",
                "path_used": "INDEX",
            }
        return {"status": "OK", "path_used": "HOT_STORE"}

    def rebuild(self, **kwargs) -> dict:
        return {"status": "WRITTEN", "reason_code": "REBUILD_OK"}


class LoadHarnessD18Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.runners = FakePerfRunners()
        self.deps = LoadHarnessDeps(
            window_pipeline_runner=self.runners.window_pipeline,
            window_post_pipeline_runner=self.runners.window_post_pipeline,
            query_runner=self.runners.query,
            rebuild_runner=self.runners.rebuild,
        )

    def test_10_contas_gera_relatorio_valido(self) -> None:
        scenario = LoadScenario(
            name="load_10_accounts",
            account_count=10,
            videos_per_account=10,
            query_burst=10,
        )
        result = run_load_suite([scenario], deps=self.deps, max_workers=4)[0]

        self.assertEqual(result.scenario_name, "load_10_accounts")
        self.assertEqual(result.total_ops, 30)
        self.assertEqual(result.error_count, 0)
        self.assertIn("window_pipeline_latency_ms", result.latency)

    def test_50_contas_computa_conflict_rate(self) -> None:
        scenario = LoadScenario(
            name="load_50_accounts",
            account_count=50,
            videos_per_account=10,
            query_burst=25,
        )
        result = run_load_suite([scenario], deps=self.deps, max_workers=8)[0]

        self.assertGreater(result.idempotency_conflict_rate, 0.0)
        self.assertEqual(result.error_rate, 0.0)

    def test_100_contas_com_rebuild(self) -> None:
        scenario = LoadScenario(
            name="load_100_accounts",
            account_count=100,
            videos_per_account=10,
            query_burst=50,
            run_rebuild=True,
        )
        result = run_load_suite([scenario], deps=self.deps, max_workers=12)[0]

        self.assertEqual(result.total_ops, 251)
        self.assertIn("rebuild_latency_ms", result.latency)

    def test_query_burst_contabiliza_fallback(self) -> None:
        scenario = LoadScenario(
            name="query_burst_fallback",
            account_count=10,
            videos_per_account=10,
            query_burst=100,
            force_hot_store_failure=True,
        )
        result = run_load_suite([scenario], deps=self.deps, max_workers=6)[0]

        self.assertGreater(result.fallback_hit_rate, 0.0)
        self.assertEqual(result.error_count, 0)

    def test_suite_grava_relatorios_json_e_md(self) -> None:
        scenario = LoadScenario(
            name="load_10_accounts",
            account_count=10,
            videos_per_account=10,
            query_burst=5,
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = Path(tmp_dir) / "OUT" / "perf"
            results = run_load_suite([scenario], deps=self.deps, output_dir=out)

            json_path = out / "load_test_report.json"
            md_path = out / "load_test_report.md"
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["scenarios"]), 1)
            self.assertEqual(payload["scenarios"][0]["scenario_name"], results[0].scenario_name)


if __name__ == "__main__":
    unittest.main()
