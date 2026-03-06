from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.ops.slo.runner import run_slo_evaluation
from app.runtime.rollout.pilot_runner import run_pilot_rollout


class OperationalEvidencePatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out_dir = Path(self.tmp.name) / "OUT"
        self.client = TestClient(app)

    def test_ready_retorna_503_sem_workers(self) -> None:
        with patch.dict(os.environ, {"CORTAI_OUT_DIR": str(self.out_dir)}, clear=False):
            response = self.client.get("/ready")
        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()["ready"])

    def test_pilot_runner_e_slo_runner_geram_artefatos_operacionais(self) -> None:
        with patch.dict(os.environ, {"CORTAI_OUT_DIR": str(self.out_dir)}, clear=False):
            rollout = run_pilot_rollout(base_dir=self.out_dir)
            slo = run_slo_evaluation(base_dir=self.out_dir)
            ready = self.client.get("/ready")

        self.assertGreaterEqual(rollout["plan_tasks"], 2)
        self.assertEqual(slo["overall_status"], "PASS")
        self.assertEqual(ready.status_code, 200)
        self.assertTrue((self.out_dir / "rollout" / "pilot_rollout_report.json").exists())
        self.assertTrue((self.out_dir / "rollout" / "pilot_batch_window_summary.json").exists())
        self.assertTrue((self.out_dir / "rollout" / "pilot_alerts.json").exists())
        self.assertTrue((self.out_dir / "ops" / "slo_status.json").exists())
        self.assertTrue((self.out_dir / "ops" / "alerts.jsonl").exists())
        self.assertTrue((self.out_dir / "index" / "event_index.sqlite3").exists())
        self.assertTrue((self.out_dir / "hot_store" / "events_hot.sqlite3").exists())

        status_payload = json.loads((self.out_dir / "ops" / "slo_status.json").read_text(encoding="utf-8"))
        self.assertEqual(status_payload["overall_status"], "PASS")


if __name__ == "__main__":
    unittest.main()
