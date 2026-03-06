from __future__ import annotations

import base64
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

from app.api.v1.endpoints.events import router as events_router


class EventQueryApiEndpointD15Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "OUT"
        for name in ["events", "audit", "data"]:
            (self.out / name).mkdir(parents=True, exist_ok=True)
        self.events_file = self.out / "events" / "events.jsonl"
        app = FastAPI()
        app.include_router(events_router, prefix="/api/v1/events", tags=["events"])
        self.client = TestClient(app)

    def _write_rows(self, rows: list[dict]) -> None:
        with self.events_file.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")

    def _rows(self, count: int = 7, account_id: str = "acc_001") -> list[dict]:
        rows: list[dict] = []
        for i in range(count):
            rows.append(
                {
                    "event_id": f"evt_{i:03d}",
                    "ts": f"2026-03-05T10:{i:02d}:00Z",
                    "event_type": "PIPE/D10_FINISHED",
                    "severity": "INFO",
                    "action_taken": "OBSERVE",
                    "writer_id": "runner",
                    "account_id": account_id,
                    "window_id": "w_001",
                    "job_id": "job_001",
                    "publish_id": "pub_001",
                    "op_key": "AGG:acc_001:w_001",
                    "details": {"reason_code": "OK", "secret": "x"},
                }
            )
        return rows

    def _base_params(self, account_id: str = "acc_001") -> dict:
        return {
            "time_from": "2026-03-05T00:00:00Z",
            "time_to": "2026-03-06T00:00:00Z",
            "limit": 5,
            "account_id": account_id,
        }

    def test_happy_path_sem_cursor_base(self) -> None:
        self._write_rows(self._rows(7))
        with patch.dict(os.environ, {"EVENT_QUERY_BASE_DIR": str(self.out)}, clear=False):
            resp = self.client.get("/api/v1/events", params=self._base_params())
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["query_shape_id"], "BASE")
        self.assertEqual(len(body["items"]), 5)

    def test_page2_com_cursor_sem_duplicacao(self) -> None:
        self._write_rows(self._rows(8))
        with patch.dict(os.environ, {"EVENT_QUERY_BASE_DIR": str(self.out)}, clear=False):
            p1 = self.client.get("/api/v1/events", params=self._base_params()).json()
            p2 = self.client.get("/api/v1/events", params={**self._base_params(), "cursor": p1["next_cursor"]}).json()
        ids1 = {item["event_id"] for item in p1["items"]}
        ids2 = {item["event_id"] for item in p2["items"]}
        self.assertEqual(len(ids1.intersection(ids2)), 0)

    def test_cursor_filters_mismatch_409(self) -> None:
        self._write_rows(self._rows(8, account_id="acc_001") + self._rows(8, account_id="acc_002"))
        with patch.dict(os.environ, {"EVENT_QUERY_BASE_DIR": str(self.out)}, clear=False):
            p1 = self.client.get("/api/v1/events", params=self._base_params("acc_001")).json()
            resp = self.client.get("/api/v1/events", params={**self._base_params("acc_002"), "cursor": p1["next_cursor"]})
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()["error"]["code"], "CURSOR_FILTERS_MISMATCH")

    def test_cursor_adulterado_profile_b_401(self) -> None:
        self._write_rows(self._rows(7))
        with patch.dict(
            os.environ,
            {
                "EVENT_QUERY_BASE_DIR": str(self.out),
                "CURSOR_SIGNATURE_ENFORCEMENT": "true",
                "CURSOR_SIGNATURE_SECRET": "secret",
            },
            clear=False,
        ):
            p1 = self.client.get("/api/v1/events", params=self._base_params()).json()
            raw = base64.urlsafe_b64decode(p1["next_cursor"] + "==")
            payload = json.loads(raw.decode("utf-8"))
            payload["last"]["event_id"] = "evt_999"
            tampered = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii").rstrip("=")
            resp = self.client.get("/api/v1/events", params={**self._base_params(), "cursor": tampered})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()["error"]["code"], "CURSOR_SIGNATURE_INVALID")

    def test_time_range_ausente_400(self) -> None:
        self._write_rows(self._rows(3))
        with patch.dict(os.environ, {"EVENT_QUERY_BASE_DIR": str(self.out)}, clear=False):
            resp = self.client.get("/api/v1/events", params={"limit": 5, "account_id": "acc_001"})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "TIME_RANGE_REQUIRED")

    def test_filtros_fracos_so_prefix_400(self) -> None:
        self._write_rows(self._rows(3))
        with patch.dict(os.environ, {"EVENT_QUERY_BASE_DIR": str(self.out)}, clear=False):
            resp = self.client.get(
                "/api/v1/events",
                params={
                    "time_from": "2026-03-05T00:00:00Z",
                    "time_to": "2026-03-06T00:00:00Z",
                    "limit": 5,
                    "event_type_prefix": "PIPE/",
                },
            )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "INSUFFICIENT_FILTERS")


if __name__ == "__main__":
    unittest.main()
