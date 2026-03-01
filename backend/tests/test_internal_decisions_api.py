from __future__ import annotations

import os
from datetime import datetime, timedelta
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows

    def first(self):
        return self._rows[0] if self._rows else None


class _FakeAsyncSession:
    def __init__(self, rows):
        self._rows = rows

    async def execute(self, statement):
        return _FakeResult(self._rows)


def _make_client(rows):
    fake_db = _FakeAsyncSession(rows)

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db
    os.environ["EXPOSE_C1_HEALTH_STATUS"] = "1"
    return TestClient(app)


def _make_row(*, did: str, ts: datetime, state: str, decision: str, signals: dict, projection: dict):
    return SimpleNamespace(
        id=did,
        ts=ts,
        payload={
            "policy": {
                "version": "v0.2",
                "score": 80,
                "state": state,
                "decision": decision,
                "signals": signals,
            },
            "operational_decision": {
                "state": projection.get("status_public", {}).get("state"),
                "decision": projection.get("status_public", {}).get("action"),
            },
        },
    )


def teardown_function():
    app.dependency_overrides.clear()


def test_gate_required_returns_404():
    client = _make_client([])

    r = client.get("/internal/decisions")
    assert r.status_code == 404

    r2 = client.get("/internal/decisions/abc", headers={"X-Internal-Status": "0"})
    assert r2.status_code == 404


def test_list_decisions_shape_and_sanitization():
    now = datetime.utcnow().replace(microsecond=0)
    rows = [
        _make_row(
            did="d1",
            ts=now,
            state="degraded",
            decision="monitor",
            signals={
                "collector_failed": 1,
                "source_ref": "https://secret.example/?token=abc",
                "minio_path": "videos-raw/x",
                "nested": {"nope": True},
                "ok_list": [1, "a", True],
            },
            projection={"status_public": {"state": "degraded", "action": "monitor"}},
        ),
        _make_row(
            did="d2",
            ts=now - timedelta(minutes=1),
            state="stable",
            decision="monitor",
            signals={"collector_failed": 0},
            projection={"status_public": {"state": "stable", "action": "none"}},
        ),
    ]
    client = _make_client(rows)

    r = client.get("/internal/decisions?limit=10", headers={"X-Internal-Status": "1"})
    assert r.status_code == 200
    assert r.headers.get("cache-control") == "no-store"
    body = r.json()

    assert body["version"] == "v1"
    assert isinstance(body["items"], list)
    assert len(body["items"]) == 2

    item0 = body["items"][0]
    assert set(item0.keys()) == {"decision_id", "ts", "policy", "projection"}
    policy = item0["policy"]
    assert policy["state"] in ("stable", "degraded", "action_required")
    sig = policy["signals"]
    assert "source_ref" not in sig
    assert "minio_path" not in sig
    assert "nested" not in sig
    assert sig.get("collector_failed") == 1
    assert sig.get("ok_list") == [1, "a", True]
    assert item0["projection"]["status_public"] == {"state": "degraded", "action": "monitor"}


def test_detail_decision_shape():
    now = datetime.utcnow().replace(microsecond=0)
    rows = [
        _make_row(
            did="d9",
            ts=now,
            state="action_required",
            decision="inspect",
            signals={"collector_failed": 2, "job_id": "should_drop"},
            projection={"status_public": {"state": "action_required", "action": "inspect"}},
        )
    ]
    client = _make_client(rows)

    r = client.get("/internal/decisions/d9", headers={"X-Internal-Status": "1"})
    assert r.status_code == 200
    assert r.headers.get("cache-control") == "no-store"
    body = r.json()

    assert body["version"] == "v1"
    assert body["decision_id"] == "d9"
    sig = body["policy"].get("signals") or {}
    assert "job_id" not in sig
