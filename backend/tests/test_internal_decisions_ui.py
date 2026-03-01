from __future__ import annotations

import os
from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app


def teardown_function() -> None:
    os.environ.pop("EXPOSE_C1_HEALTH_STATUS", None)


def test_internal_decisions_ui_requires_gate() -> None:
    with TestClient(app) as client:
        response = client.get("/internal/decision-history")
    assert response.status_code == 404


def test_internal_decisions_ui_renders_sanitized_list(monkeypatch) -> None:
    os.environ["EXPOSE_C1_HEALTH_STATUS"] = "1"

    async def fake_list_decision_history(db, *, limit=20, since_ts=None, state=None):
        return [
            {
                "decision_id": "d1",
                "ts": datetime(2026, 3, 1, 10, 0, 0).isoformat() + "Z",
                "policy": {
                    "version": "v0.2",
                    "score": 72,
                    "state": "degraded",
                    "decision": "monitor",
                    "signals": {
                        "collector_failed": 1,
                        "ok_list": [1, "a", True],
                    },
                },
                "projection": {
                    "status_public": {"state": "degraded", "action": "monitor"},
                },
            }
        ]

    import app.api.v1.endpoints.internal_decisions_ui as decisions_ui_mod

    monkeypatch.setattr(decisions_ui_mod, "list_decision_history", fake_list_decision_history)

    with TestClient(app) as client:
        response = client.get("/internal/decision-history", headers={"X-Internal-Status": "1"})

    assert response.status_code == 200
    assert response.headers.get("cache-control") == "no-store"
    body = response.text
    assert "Decision History" in body
    assert "d1" in body
    assert "degraded" in body
    assert "monitor" in body
    assert "source_ref" not in body
    assert "minio_path" not in body
    assert "job_id" not in body
