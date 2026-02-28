import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
        yield c


class _FakeJob:
    def __init__(self, *, status: str, step: str | None, error: str | None, duration_ms: int):
        self.id = "job-test-123"
        self.status = status
        self.step = step
        self.error = error
        self.duration_ms = duration_ms


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
async def test_internal_maestro_run_requires_gate(client, monkeypatch):
    monkeypatch.delenv("EXPOSE_C1_HEALTH_STATUS", raising=False)

    response = await client.post("/internal/maestro/run", json={"source_ref": "https://example.com/video"})

    assert response.status_code == 404


@pytest.mark.anyio
async def test_internal_maestro_run_returns_done_payload_in_demo_mode(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")

    response = await client.post(
        "/internal/maestro/run?demo=1",
        headers={"X-Internal-Status": "1"},
        json={"source_ref": "https://example.com/video"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "done"
    assert body["step"] is None
    assert body["error"] is None
    assert isinstance(body["job_id"], str) and body["job_id"]
    assert isinstance(body["duration_ms"], int)
    assert body["duration_ms"] >= 0


@pytest.mark.anyio
async def test_internal_maestro_run_returns_failed_payload_in_real_mode(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    monkeypatch.setattr(
        "app.api.v1.endpoints.internal_maestro.MaestroOrchestrator",
        _make_fake_orchestrator(
            status="failed",
            step="audio_extractor",
            error="audio extractor exploded",
            duration_ms=87,
        ),
    )

    response = await client.post(
        "/internal/maestro/run",
        headers={"X-Internal-Status": "1"},
        json={"source_ref": "https://example.com/video"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "job_id": "job-test-123",
        "status": "failed",
        "step": "audio_extractor",
        "error": "audio extractor exploded",
        "duration_ms": 87,
    }
