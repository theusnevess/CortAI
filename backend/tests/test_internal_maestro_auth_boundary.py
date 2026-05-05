from __future__ import annotations

from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import get_db
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def cleanup_metrics():
    yield


class _FakeDbSession:
    async def commit(self):
        return None

    async def rollback(self):
        return None


class _Record:
    def __init__(self, *, job_id: str, source_ref: str, status: str, demo_mode: bool):
        self.job_id = job_id
        self.source_ref = source_ref
        self.status = status
        self.step = None
        self.error = None
        self.started_at = datetime(2026, 2, 28, 1, 0, 0)
        self.finished_at = None
        self.duration_ms = None
        self.demo_mode = demo_mode


class _FakeJob:
    id = "job-internal-1"
    status = "done"
    step = None
    error = None
    duration_ms = 12
    finished_at = datetime(2026, 2, 28, 1, 0, 1)
    step_durations_ms = {}


class _FakeResult:
    job = _FakeJob()


class _FakeOrchestrator:
    async def run(self, job_input):
        return _FakeResult()


@pytest.fixture
async def internal_client(monkeypatch):
    async def _override_get_db():
        yield _FakeDbSession()

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_internal_maestro_rejects_header_only_gate(monkeypatch, internal_client):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    monkeypatch.setenv("CORTAI_INTERNAL_CONTROL_PLANE_TOKEN", "test-internal-token")

    response = await internal_client.post(
        "/internal/maestro/run?demo=1",
        headers={"X-Internal-Status": "1"},
        json={"source_ref": "https://example.com/video"},
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_internal_maestro_accepts_verified_internal_identity(monkeypatch, internal_client):
    store: dict[str, _Record] = {}

    async def _create_running_job(db, *, job_id: str, source_ref: str, demo_mode: bool):
        record = _Record(job_id=job_id, source_ref=source_ref, status="running", demo_mode=demo_mode)
        store[job_id] = record
        return record

    async def _update_job_success(db, *, job_id: str, job):
        record = store[job_id]
        record.status = "done"
        record.step = job.step
        record.error = None
        record.finished_at = job.finished_at
        record.duration_ms = job.duration_ms
        return record

    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    monkeypatch.setenv("CORTAI_INTERNAL_CONTROL_PLANE_TOKEN", "test-internal-token")
    monkeypatch.setattr("app.api.v1.endpoints.internal_maestro.create_running_job", _create_running_job)
    monkeypatch.setattr("app.api.v1.endpoints.internal_maestro.update_job_success", _update_job_success)
    monkeypatch.setattr("app.api.v1.endpoints.internal_maestro.MaestroOrchestrator", lambda: _FakeOrchestrator())

    response = await internal_client.post(
        "/internal/maestro/run",
        headers={"Authorization": "Bearer test-internal-token", "X-Internal-Status": "1"},
        json={"source_ref": "https://example.com/video", "job_id": "job-internal-1"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "done"
    assert store["job-internal-1"].status == "done"
