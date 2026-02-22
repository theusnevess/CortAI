from datetime import date, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1.endpoints.metrics import process_read_refresh_jobs_once
from app.db.session import get_db
from app.read_main import app as read_app


@pytest.fixture
async def read_client(db_session):
    """
    Cliente HTTP para validar o app dedicado de leitura.
    """

    async def _override_get_db():
        yield db_session

    read_app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(read_app), base_url="http://readtest") as client:
        yield client
    read_app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_read_api_health(read_client):
    """
    Health do read-api deve refletir servico dedicado.
    """
    response = await read_client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["services"]["read_api"] == "running"


@pytest.mark.anyio
async def test_read_api_overview_snapshot_first_flow(read_client, db_session, seed_daily_metric):
    """
    Read-api deve seguir contrato snapshot-first (503 -> 202 -> 200).
    """
    await seed_daily_metric(
        metric_date=date(2026, 2, 10),
        total_runs=2,
        completed_runs=2,
        failed_runs=0,
        blocked_runs=0,
        avg_actions_executed=1.0,
        last_action_type_distribution={"write_artifact": 2},
    )

    missing = await read_client.get(
        "/api/v1/metrics/overview",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    assert missing.status_code == 503
    missing_detail = missing.json()["detail"]
    assert missing_detail["snapshot_status"] == "missing"
    assert missing_detail["scope"] == "overview"
    assert missing_detail["next_action"] == "force_live"
    assert int(missing_detail["estimated_ready_seconds"]) >= 1

    accepted = await read_client.get(
        "/api/v1/metrics/overview",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10", "force_live": "true"},
    )
    assert accepted.status_code == 202
    accepted_payload = accepted.json()
    assert accepted_payload["snapshot_status"] == "queued"
    assert accepted_payload["scope"] == "overview"
    assert isinstance(accepted_payload["correlation_id"], str) and accepted_payload["correlation_id"]
    assert int(accepted_payload["retry_after_seconds"]) >= 1

    await process_read_refresh_jobs_once(db=db_session, limit=20)

    ready = await read_client.get(
        "/api/v1/metrics/overview",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    assert ready.status_code == 200
    payload = ready.json()
    assert payload["snapshot_status"] in {"fresh", "stale"}
    assert "last_refreshed_at" in payload


@pytest.mark.anyio
async def test_read_api_status_exposes_read_api_and_jobs(
    read_client,
    db_session,
    seed_observation,
    monkeypatch,
):
    """
    /status no read-api deve expor bloco read_api e contagem de jobs.
    """
    monkeypatch.setenv("READ_API_ENABLED", "true")
    monkeypatch.setenv("READ_API_BASE_URL", "http://cortai_read_api:8000")

    await seed_observation(
        timestamp=datetime(2026, 2, 10, 12, 0, 0),
        process_id="P_READ_API_STATUS_1",
        source_outcome_id="outcome-read-api-status-1",
        facts={
            "event_type": "cognitive_loop_finished",
            "pipeline_status": "completed",
            "actions_executed": 1,
        },
    )

    accepted = await read_client.get(
        "/api/v1/metrics/runs",
        params={
            "start_date": "2026-02-10",
            "end_date": "2026-02-10",
            "limit": 50,
            "offset": 0,
            "force_live": "true",
        },
    )
    assert accepted.status_code == 202

    status_before = await read_client.get("/api/v1/status", params={"window_days": 7})
    assert status_before.status_code == 200
    before_payload = status_before.json()
    assert before_payload["read_api"]["enabled"] is True
    assert before_payload["read_api"]["up"] is True
    assert "read_path" in before_payload
    assert before_payload["read_path"]["jobs_queued_count"] >= 1

    await process_read_refresh_jobs_once(db=db_session, limit=20)

    status_after = await read_client.get("/api/v1/status", params={"window_days": 7})
    assert status_after.status_code == 200
    after_payload = status_after.json()
    assert after_payload["read_path"]["jobs_queued_count"] >= 0

