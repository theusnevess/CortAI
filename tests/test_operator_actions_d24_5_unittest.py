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

from app.api.v1.endpoints.operator_actions import router as actions_router
from app.api.v1.endpoints.ops_dashboard import router as dashboard_router


class OperatorActionsD245Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out_dir = Path(self.tmp.name) / "OUT"
        (self.out_dir / "events").mkdir(parents=True, exist_ok=True)
        (self.out_dir / "ops").mkdir(parents=True, exist_ok=True)
        app = FastAPI()
        app.include_router(actions_router, prefix="/api/v1/ops/actions")
        app.include_router(dashboard_router, prefix="/api/v1/ops")
        self.client = TestClient(app)

    def _env(self):
        return patch.dict(os.environ, {"OPS_DASHBOARD_BASE_DIR": str(self.out_dir), "CORTAI_OUT_DIR": str(self.out_dir)}, clear=False)

    def _write_alert(self) -> None:
        with (self.out_dir / "ops" / "alerts.jsonl").open("w", encoding="utf-8") as writer:
            writer.write(json.dumps({"alert_code": "ALERT_EVENT_QUERY", "severity": "WARN", "metric_name": "event_query_p95_ms", "reason_code": "EVENT_QUERY_P95_MS_WARN", "action": "DEGRADE"}) + "\n")

    def _write_event(self) -> None:
        with (self.out_dir / "events" / "events.jsonl").open("w", encoding="utf-8") as writer:
            writer.write(json.dumps({"event_id": "evt_1", "ts": "2026-03-06T12:00:00Z", "event_type": "RUNTIME/task_finished", "account_id": "acc_001", "window_id": "w_001", "op_key": "AGG:acc_001:w_001", "details": {"task_id": "task_001", "task_type": "WINDOW_AGGREGATION", "worker_id": "worker:1", "status": "FAILED"}}) + "\n")

    def test_pause_rollout_sucesso_com_audit(self) -> None:
        with self._env():
            response = self.client.post("/api/v1/ops/actions/pause-rollout", json={"operator_id": "op-1", "reason": "maintenance"})
        self.assertEqual(response.status_code, 200)
        payload = json.loads((self.out_dir / "ops" / "operator_control.json").read_text(encoding="utf-8"))
        self.assertFalse(payload["rollout_enabled"])
        events = (self.out_dir / "events" / "events.jsonl").read_text(encoding="utf-8")
        self.assertIn("OPS/action_executed", events)

    def test_resume_rollout_sucesso_com_audit(self) -> None:
        with self._env():
            self.client.post("/api/v1/ops/actions/pause-rollout", json={"operator_id": "op-1", "reason": "maintenance"})
            response = self.client.post("/api/v1/ops/actions/resume-rollout", json={"operator_id": "op-1", "reason": "done"})
        self.assertEqual(response.status_code, 200)
        payload = json.loads((self.out_dir / "ops" / "operator_control.json").read_text(encoding="utf-8"))
        self.assertTrue(payload["rollout_enabled"])

    def test_requeue_task_valida_e_requeue_duplicado_vira_noop(self) -> None:
        self._write_event()
        request = {
            "operator_id": "op-1",
            "reason": "retry transient failure",
            "task_id": "task_001",
            "task_type": "WINDOW_AGGREGATION",
            "status": "FAILED",
            "op_key": "AGG:acc_001:w_001",
            "account_id": "acc_001",
            "window_id": "w_001",
        }
        with self._env():
            first = self.client.post("/api/v1/ops/actions/requeue-task", json=request)
            second = self.client.post("/api/v1/ops/actions/requeue-task", json=request)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["status"], "WRITTEN")
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["status"], "NOOP")

    def test_rebuild_event_index_dispara_rebuild(self) -> None:
        self._write_event()
        with self._env():
            response = self.client.post("/api/v1/ops/actions/rebuild-event-index", json={"operator_id": "op-1", "reason": "refresh index"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue((self.out_dir / "index" / "event_index.sqlite3").exists())

    def test_ack_alert_marca_ack_sem_apagar_alerta(self) -> None:
        self._write_alert()
        with self._env():
            response = self.client.post("/api/v1/ops/actions/ack-alert", json={"operator_id": "op-1", "reason": "investigating", "alert_code": "ALERT_EVENT_QUERY"})
            alerts = self.client.get("/api/v1/ops/alerts")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(alerts.status_code, 200)
        self.assertTrue(alerts.json()["items"][0]["acknowledged"])

    def test_acao_sem_reason_retorna_erro(self) -> None:
        with self._env():
            response = self.client.post("/api/v1/ops/actions/pause-rollout", json={"operator_id": "op-1", "reason": ""})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "ACTION_REASON_REQUIRED")

    def test_acao_nao_permitida_pela_policy_requeue_running(self) -> None:
        with self._env():
            response = self.client.post("/api/v1/ops/actions/requeue-task", json={"operator_id": "op-1", "reason": "retry", "task_id": "task_001", "task_type": "WINDOW_AGGREGATION", "status": "RUNNING", "op_key": "AGG:acc_001:w_001"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "REQUEUE_STATUS_NOT_ALLOWED")

    def test_console_nao_expoe_mutacoes_fora_da_lista(self) -> None:
        with self._env():
            response = self.client.post("/api/v1/ops/actions/delete-events", json={"operator_id": "op-1", "reason": "forbidden"})
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
