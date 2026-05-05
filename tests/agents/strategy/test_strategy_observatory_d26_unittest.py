from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.api.v1.endpoints.ops_dashboard import router as ops_router
from app.api.v1.endpoints.strategy_observatory import router as strategy_router


class StrategyObservatoryD26Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "OUT"
        (self.out / "data").mkdir(parents=True, exist_ok=True)
        app = FastAPI()
        app.include_router(strategy_router, prefix="/api/v1/ops/strategy")
        app.include_router(ops_router, prefix="/api/v1/ops")
        self.client = TestClient(app)

    def _env(self):
        return patch.dict(
            os.environ,
            {"OPS_DASHBOARD_BASE_DIR": str(self.out), "CORTAI_OUT_DIR": str(self.out)},
            clear=False,
        )

    def _write_jsonl(self, path: Path, rows: list[dict]) -> None:
        with path.open("w", encoding="utf-8") as writer:
            for row in rows:
                writer.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _write_strategy_artifacts(self) -> None:
        self._write_jsonl(
            self.out / "data" / "strategy_patches.jsonl",
            [
                {
                    "patch_id": "sp_001",
                    "account_id": "acc_001",
                    "window_id": "w_001",
                    "policy_stage": "GROWTH",
                    "inputs": {"window_metrics_id": "wm_001", "scorecard_id": "sc_001", "attribution_count": 8},
                    "overrides": {"a4_defaults_override": {"hook_style": "curiosity_gap"}},
                    "active": True,
                    "layers_applied": ["A4"],
                    "reason_codes": ["HOOK_STRATEGY_CONSISTENT"],
                    "patch_kind": "STRATEGY_V1",
                    "generated_at": "2026-03-01T00:00:00Z",
                },
                {
                    "patch_id": "sp_002",
                    "account_id": "acc_001",
                    "window_id": "w_002",
                    "policy_stage": "GROWTH",
                    "inputs": {"window_metrics_id": "wm_002", "scorecard_id": "sc_002", "attribution_count": 8},
                    "overrides": {},
                    "active": False,
                    "layers_applied": [],
                    "reason_codes": ["NO_STRONG_SIGNAL"],
                    "patch_kind": "STRATEGY_V1",
                    "generated_at": "2026-03-04T00:00:00Z",
                },
            ],
        )
        self._write_jsonl(
            self.out / "data" / "strategy_patch_applications.jsonl",
            [
                {
                    "account_id": "acc_001",
                    "window_id": "w_001",
                    "policy_stage": "GROWTH",
                    "patch_id": "sp_001",
                    "patch_payload": {"patch_id": "sp_001"},
                    "applied_at": "2026-03-01T00:05:00Z",
                    "status": "APPLIED",
                }
            ],
        )
        self._write_jsonl(
            self.out / "data" / "scorecards.jsonl",
            [
                {
                    "scorecard_id": "sc_001",
                    "account_id": "acc_001",
                    "window_id": "w_001",
                    "generated_at": "2026-03-01T00:10:00Z",
                    "avg_completion_rate": 0.41,
                    "avg_rpm": 1.1,
                },
                {
                    "scorecard_id": "sc_002",
                    "account_id": "acc_001",
                    "window_id": "w_002",
                    "generated_at": "2026-03-04T00:10:00Z",
                    "avg_completion_rate": 0.47,
                    "avg_rpm": 1.3,
                },
            ],
        )
        self._write_jsonl(
            self.out / "data" / "window_metrics.jsonl",
            [
                {
                    "account_id": "acc_001",
                    "window_id": "w_001",
                    "computed_at": "2026-03-01T00:09:00Z",
                    "total_views": 1000,
                },
                {
                    "account_id": "acc_001",
                    "window_id": "w_002",
                    "computed_at": "2026-03-04T00:09:00Z",
                    "total_views": 1250,
                },
            ],
        )

    def test_lista_patches_corretamente(self) -> None:
        self._write_strategy_artifacts()
        with self._env():
            response = self.client.get("/api/v1/ops/strategy/patches")
        self.assertEqual(response.status_code, 200)
        items = response.json()["items"]
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["patch_id"], "sp_002")
        self.assertEqual(items[1]["status"], "applied")

    def test_link_patch_janela_scorecard_funciona(self) -> None:
        self._write_strategy_artifacts()
        with self._env():
            response = self.client.get("/api/v1/ops/strategy/patch/sp_001")
        self.assertEqual(response.status_code, 200)
        item = response.json()["item"]
        self.assertEqual(item["patch_id"], "sp_001")
        self.assertEqual(item["application"]["status"], "APPLIED")
        self.assertEqual(item["inputs"]["scorecard_id"], "sc_001")

    def test_calculo_de_impacto_correto(self) -> None:
        self._write_strategy_artifacts()
        with self._env():
            response = self.client.get("/api/v1/ops/strategy/impact")
        self.assertEqual(response.status_code, 200)
        first = response.json()["items"][0]
        self.assertEqual(first["window_id_before"], "w_002")
        first_patch = response.json()["items"][1]
        self.assertEqual(first_patch["patch_id"], "sp_001")
        self.assertEqual(first_patch["window_id_after"], "w_002")
        self.assertAlmostEqual(first_patch["scorecard_delta"]["avg_completion_rate"], 0.06)
        self.assertAlmostEqual(first_patch["scorecard_delta"]["avg_rpm"], 0.2)

    def test_timeline_ordenada(self) -> None:
        self._write_strategy_artifacts()
        with self._env():
            response = self.client.get("/api/v1/ops/strategy/timeline")
        self.assertEqual(response.status_code, 200)
        items = response.json()["items"]
        self.assertEqual([item["patch_id"] for item in items], ["sp_001", "sp_002"])

    def test_patch_inexistente_retorna_erro_claro(self) -> None:
        self._write_strategy_artifacts()
        with self._env():
            response = self.client.get("/api/v1/ops/strategy/patch/sp_missing")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "STRATEGY_PATCH_NOT_FOUND")

    def test_dados_inconsistentes_nao_quebram_api(self) -> None:
        self._write_strategy_artifacts()
        (self.out / "data" / "scorecards.jsonl").unlink()
        with self._env():
            response = self.client.get("/api/v1/ops/strategy/impact")
        self.assertEqual(response.status_code, 200)
        items = response.json()["items"]
        self.assertEqual(items[0]["scorecard_delta"], {})

    def test_console_renderiza_observatorio_de_estrategia(self) -> None:
        self._write_strategy_artifacts()
        (self.out / "ops").mkdir(parents=True, exist_ok=True)
        (self.out / "rollout").mkdir(parents=True, exist_ok=True)
        (self.out / "ops" / "slo_status.json").write_text(
            json.dumps({"overall_status": "PASS", "metrics": []}),
            encoding="utf-8",
        )
        (self.out / "rollout" / "pilot_rollout_report.json").write_text(
            json.dumps({"rollout_name": "pilot", "batch_summary": {}, "alerts": []}),
            encoding="utf-8",
        )
        with self._env():
            response = self.client.get("/api/v1/ops/internal/operator-console")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Strategy Observatory / Patches", response.text)
        self.assertIn("sp_001", response.text)


if __name__ == "__main__":
    unittest.main()
