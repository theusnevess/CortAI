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

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.api.v1.endpoints.ops_dashboard import router as ops_router


class OperatorConsoleD24Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "OUT"
        (self.out / "ops").mkdir(parents=True, exist_ok=True)
        (self.out / "rollout").mkdir(parents=True, exist_ok=True)
        (self.out / "events").mkdir(parents=True, exist_ok=True)
        app = FastAPI()
        app.include_router(ops_router, prefix="/api/v1/ops", tags=["ops"])
        self.client = TestClient(app)

    def _write_ops_artifacts(self) -> None:
        (self.out / "ops" / "slo_status.json").write_text(
            json.dumps(
                {
                    "overall_status": "WARN",
                    "metrics": [
                        {"metric_name": "event_query_p95_ms", "value": 180.0},
                        {"metric_name": "event_query_fallback_rate", "value": 0.12},
                    ],
                }
            ),
            encoding="utf-8",
        )
        with (self.out / "ops" / "alerts.jsonl").open("w", encoding="utf-8") as writer:
            writer.write(json.dumps({"severity": "CRITICAL", "metric_name": "event_query_error_rate", "reason_code": "EVENT_QUERY_ERROR_RATE_CRITICAL", "action": "BLOCK"}) + "\n")
            writer.write(json.dumps({"severity": "WARN", "metric_name": "event_query_fallback_rate", "reason_code": "EVENT_QUERY_FALLBACK_RATE_WARN", "action": "DEGRADE"}) + "\n")
        (self.out / "rollout" / "pilot_rollout_report.json").write_text(
            json.dumps(
                {
                    "rollout_name": "pilot_batch_72h",
                    "batch_summary": {
                        "window_id": "w_001",
                        "account_id": "acc_truecrime_001",
                        "scorecard": True,
                        "content_attribution": True,
                        "strategy_patch": True,
                        "patch_applied": "NOOP",
                    },
                    "alerts": [],
                }
            ),
            encoding="utf-8",
        )
        with (self.out / "events" / "events.jsonl").open("w", encoding="utf-8") as writer:
            writer.write(
                json.dumps(
                    {
                        "event_id": "evt_001",
                        "ts": "2026-03-06T12:00:00Z",
                        "event_type": "RUNTIME/task_started",
                        "account_id": "acc_truecrime_001",
                        "window_id": "w_001",
                        "op_key": "AGG:acc_truecrime_001:w_001",
                        "details": {"task_id": "task_001", "task_type": "WINDOW_AGGREGATION", "worker_id": "worker:1"},
                    }
                )
                + "\n"
            )
            writer.write(
                json.dumps(
                    {
                        "event_id": "evt_002",
                        "ts": "2026-03-06T12:01:00Z",
                        "event_type": "RUNTIME/task_finished",
                        "account_id": "acc_truecrime_001",
                        "window_id": "w_001",
                        "op_key": "AGG:acc_truecrime_001:w_001",
                        "details": {"task_id": "task_001", "task_type": "WINDOW_AGGREGATION", "worker_id": "worker:1", "status": "SUCCEEDED"},
                    }
                )
                + "\n"
            )

    def test_health_summary_retorna_shape_correto(self) -> None:
        self._write_ops_artifacts()
        with patch.dict(os.environ, {"OPS_DASHBOARD_BASE_DIR": str(self.out), "ROLL_OUT_ENABLED": "true"}, clear=False):
            response = self.client.get("/api/v1/ops/health-summary")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("rollout_enabled", body)
        self.assertIn("active_critical_alerts", body)
        self.assertEqual(body["active_critical_alerts"], 1)

    def test_rollout_status_respeita_artifacts_reais(self) -> None:
        self._write_ops_artifacts()
        with patch.dict(os.environ, {"OPS_DASHBOARD_BASE_DIR": str(self.out)}, clear=False):
            response = self.client.get("/api/v1/ops/rollout-status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["rollout_name"], "pilot_batch_72h")

    def test_windows_lista_batches_corretamente(self) -> None:
        self._write_ops_artifacts()
        with patch.dict(os.environ, {"OPS_DASHBOARD_BASE_DIR": str(self.out)}, clear=False):
            response = self.client.get("/api/v1/ops/windows")
        self.assertEqual(response.status_code, 200)
        items = response.json()["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["window_id"], "w_001")

    def test_alerts_endpoint_reflete_alerts_persistidos(self) -> None:
        self._write_ops_artifacts()
        with patch.dict(os.environ, {"OPS_DASHBOARD_BASE_DIR": str(self.out)}, clear=False):
            response = self.client.get("/api/v1/ops/alerts")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 2)

    def test_console_nao_expoe_mutation_endpoints(self) -> None:
        response = self.client.post("/api/v1/ops/alerts")
        self.assertIn(response.status_code, {405, 404})

    def test_integracao_com_trace_query_nao_quebra(self) -> None:
        self._write_ops_artifacts()
        with patch.dict(os.environ, {"OPS_DASHBOARD_BASE_DIR": str(self.out)}, clear=False):
            response = self.client.get("/api/v1/ops/tasks")
        self.assertEqual(response.status_code, 200)
        items = response.json()["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["task_id"], "task_001")

    def test_operator_console_html_renderiza(self) -> None:
        self._write_ops_artifacts()
        with patch.dict(os.environ, {"OPS_DASHBOARD_BASE_DIR": str(self.out)}, clear=False):
            response = self.client.get("/api/v1/ops/internal/operator-console")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Operator Console", response.text)


if __name__ == "__main__":
    unittest.main()
