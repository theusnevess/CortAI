from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import get_db
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


class _FakeDbSession:
    def __init__(self):
        self.commit_calls = 0
        self.rollback_calls = 0

    async def commit(self):
        self.commit_calls += 1

    async def rollback(self):
        self.rollback_calls += 1


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
        self.step_durations_json = {}


@pytest.fixture
def maestro_store(monkeypatch):
    store: dict[str, _Record] = {}

    async def _create_running_job(db, *, job_id: str, source_ref: str, demo_mode: bool):
        record = _Record(
            job_id=job_id,
            source_ref=source_ref,
            status="running",
            demo_mode=demo_mode,
        )
        store[job_id] = record
        return record

    async def _update_job_success(db, *, job_id: str, job):
        record = store[job_id]
        record.status = "done"
        record.step = job.step
        record.error = None
        record.finished_at = job.finished_at
        record.duration_ms = job.duration_ms
        record.step_durations_json = dict(job.step_durations_ms)
        return record

    async def _update_job_failure(db, *, job_id: str, job=None, step=None, error=None):
        record = store[job_id]
        record.status = "failed"
        record.step = job.step if job is not None else step
        record.error = job.error if job is not None else error
        record.finished_at = job.finished_at if job is not None else datetime(2026, 2, 28, 1, 0, 5)
        record.duration_ms = job.duration_ms if job is not None else None
        record.step_durations_json = dict(job.step_durations_ms) if job is not None else {}
        return record

    async def _get_job_by_id(db, job_id: str):
        return store.get(job_id)

    monkeypatch.setattr("app.api.v1.endpoints.internal_maestro.create_running_job", _create_running_job)
    monkeypatch.setattr("app.api.v1.endpoints.internal_maestro.update_job_success", _update_job_success)
    monkeypatch.setattr("app.api.v1.endpoints.internal_maestro.update_job_failure", _update_job_failure)
    monkeypatch.setattr("app.api.v1.endpoints.internal_maestro.get_job_by_id", _get_job_by_id)
    return store


@pytest.fixture
async def client():
    fake_db = _FakeDbSession()

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()


class _FakeJob:
    def __init__(self, *, status: str, step: str | None, error: str | None, duration_ms: int):
        self.id = "job-test-123"
        self.status = status
        self.step = step
        self.error = error
        self.duration_ms = duration_ms
        self.finished_at = datetime(2026, 2, 28, 1, 0, 1)
        self.step_durations_ms = {"collector": 5}


class _FakeResult:
    def __init__(self, *, status: str, step: str | None, error: str | None, duration_ms: int):
        self.job = _FakeJob(status=status, step=step, error=error, duration_ms=duration_ms)


def _make_fake_orchestrator(*, status: str, step: str | None, error: str | None, duration_ms: int):
    class _FakeOrchestrator:
        async def run(self, job_input):
            return _FakeResult(
                status=status,
                step=step,
                error=error,
                duration_ms=duration_ms,
            )

    return _FakeOrchestrator


@pytest.mark.anyio
async def test_internal_maestro_run_requires_gate(client, maestro_store, monkeypatch):
    monkeypatch.setenv("CORTAI_INTERNAL_CONTROL_PLANE_TOKEN", "test-internal-token")

    response = await client.post("/internal/maestro/run", json={"source_ref": "https://example.com/video"})

    assert response.status_code == 401
    assert maestro_store == {}


@pytest.mark.anyio
async def test_internal_maestro_demo_persists_done_job_and_get_returns_it(client, maestro_store, monkeypatch):
    monkeypatch.setenv("CORTAI_INTERNAL_CONTROL_PLANE_TOKEN", "test-internal-token")

    response = await client.post(
        "/internal/maestro/run?demo=1",
        headers={"Authorization": "Bearer test-internal-token"},
        json={"source_ref": "https://example.com/video"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "done"
    assert body["error"] is None
    job_id = body["job_id"]
    assert job_id in maestro_store

    get_response = await client.get(
        f"/internal/maestro/jobs/{job_id}",
        headers={"Authorization": "Bearer test-internal-token"},
    )

    assert get_response.status_code == 200
    assert get_response.headers["Cache-Control"] == "no-store"
    assert get_response.json() == {
        "job_id": job_id,
        "source_ref": "https://example.com/video",
        "status": "done",
        "step": None,
        "error": None,
        "started_at": "2026-02-28T01:00:00Z",
        "finished_at": maestro_store[job_id].finished_at.isoformat() + "Z",
        "duration_ms": maestro_store[job_id].duration_ms,
        "demo_mode": True,
    }


@pytest.mark.anyio
async def test_internal_maestro_real_mode_persists_failed_job(client, maestro_store, monkeypatch):
    monkeypatch.setenv("CORTAI_INTERNAL_CONTROL_PLANE_TOKEN", "test-internal-token")
    monkeypatch.setattr(
        "app.api.v1.endpoints.internal_maestro.MaestroOrchestrator",
        _make_fake_orchestrator(
            status="failed",
            step="collector",
            error="collector exploded",
            duration_ms=87,
        ),
    )

    response = await client.post(
        "/internal/maestro/run",
        headers={"Authorization": "Bearer test-internal-token"},
        json={"source_ref": "https://example.com/video", "job_id": "job-test-123"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "job_id": "job-test-123",
        "status": "failed",
        "step": "collector",
        "error": "collector exploded",
        "duration_ms": 87,
    }
    assert maestro_store["job-test-123"].status == "failed"
    assert maestro_store["job-test-123"].step == "collector"
    assert maestro_store["job-test-123"].error == "collector exploded"


@pytest.mark.anyio
async def test_internal_maestro_get_requires_gate(client, maestro_store, monkeypatch):
    monkeypatch.setenv("CORTAI_INTERNAL_CONTROL_PLANE_TOKEN", "test-internal-token")
    maestro_store["job-1"] = _Record(
        job_id="job-1",
        source_ref="https://example.com/video",
        status="done",
        demo_mode=False,
    )

    response = await client.get("/internal/maestro/jobs/job-1")

    assert response.status_code == 401
