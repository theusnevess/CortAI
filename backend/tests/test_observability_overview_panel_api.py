from datetime import datetime, timedelta
import uuid

import pytest

from app.observability import runtime_health


def _internal_headers() -> dict[str, str]:
    return {"X-Internal-Status": "1"}


@pytest.fixture(autouse=True)
def _clear_runtime_health_cache():
    runtime_health.clear_runtime_c1_health_cache()
    yield
    runtime_health.clear_runtime_c1_health_cache()


@pytest.mark.anyio
async def test_insights_panel_gate_off_returns_404(client, monkeypatch):
    monkeypatch.delenv("EXPOSE_C1_HEALTH_STATUS", raising=False)
    response = await client.get("/api/v1/observability/overview")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_insights_panel_gate_on_without_header_returns_404(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    response = await client.get("/api/v1/observability/overview")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_insights_panel_gate_on_returns_200_and_min_shape(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    response = await client.get("/api/v1/observability/overview", headers=_internal_headers())
    assert response.status_code == 200
    payload = response.json()
    for key in ("panel_version", "as_of", "overall", "c1_health", "read_path", "guardrails"):
        assert key in payload
    assert payload["panel_version"] == "v1"
    assert "score" in payload["overall"]
    assert "decision" in payload["overall"]
    assert "reasons" in payload["overall"]


@pytest.mark.anyio
async def test_guardrails_summary_empty_when_no_events(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    response = await client.get("/api/v1/observability/overview", headers=_internal_headers())
    assert response.status_code == 200
    guardrails = response.json()["guardrails"]
    assert guardrails["window_minutes"] == 15
    assert guardrails["events"] == {
        "accepted_202": 0,
        "rate_limited_429": 0,
        "snapshot_missing_503": 0,
    }
    assert guardrails["last_events"] == []


@pytest.mark.anyio
async def test_guardrails_counts_and_last_events_populate(client, monkeypatch, seed_observation):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    now = datetime.utcnow()
    base_endpoint = "/api/v1/metrics/overview"
    common = {
        "event_type": "metrics_endpoint_timing",
        "endpoint": base_endpoint,
        "method": "GET",
        "duration_ms": 25,
    }

    await seed_observation(
        timestamp=now - timedelta(seconds=50),
        process_id="P_OBS_PANEL_202",
        source_outcome_id=str(uuid.uuid4()),
        facts={**common, "status_code": 202, "snapshot_status": "queued"},
    )
    await seed_observation(
        timestamp=now - timedelta(seconds=40),
        process_id="P_OBS_PANEL_429",
        source_outcome_id=str(uuid.uuid4()),
        facts={
            **common,
            "status_code": 429,
            "scope": "overview_force_live",
            "snapshot_status": "queued",
        },
    )
    await seed_observation(
        timestamp=now - timedelta(seconds=30),
        process_id="P_OBS_PANEL_503",
        source_outcome_id=str(uuid.uuid4()),
        facts={**common, "status_code": 503, "snapshot_status": "missing"},
    )

    response = await client.get("/api/v1/observability/overview", headers=_internal_headers())
    assert response.status_code == 200
    guardrails = response.json()["guardrails"]
    assert guardrails["events"]["accepted_202"] == 1
    assert guardrails["events"]["rate_limited_429"] == 1
    assert guardrails["events"]["snapshot_missing_503"] == 1
    assert len(guardrails["last_events"]) <= 5
    assert len(guardrails["last_events"]) >= 3

    first = guardrails["last_events"][0]
    for key in ("ts", "endpoint", "status_code", "scope", "snapshot_status"):
        assert key in first
    assert "T" in first["ts"]
    assert any(
        e["status_code"] == 429 and e["scope"] == "overview_force_live" and e["snapshot_status"] == "queued"
        for e in guardrails["last_events"]
    )


@pytest.mark.anyio
async def test_guardrails_ignores_events_outside_window(client, monkeypatch, seed_observation):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    now = datetime.utcnow()
    await seed_observation(
        timestamp=now - timedelta(minutes=20),
        process_id="P_OBS_PANEL_OLD_429",
        source_outcome_id=str(uuid.uuid4()),
        facts={
            "event_type": "metrics_endpoint_timing",
            "endpoint": "/api/v1/metrics/runs",
            "status_code": 429,
            "scope": "runs_force_live",
            "snapshot_status": "queued",
            "duration_ms": 30,
        },
    )

    response = await client.get("/api/v1/observability/overview", headers=_internal_headers())
    assert response.status_code == 200
    guardrails = response.json()["guardrails"]
    assert guardrails["events"] == {
        "accepted_202": 0,
        "rate_limited_429": 0,
        "snapshot_missing_503": 0,
    }
    assert guardrails["last_events"] == []


@pytest.mark.anyio
async def test_last_events_allows_null_scope_snapshot_status(client, monkeypatch, seed_observation):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    now = datetime.utcnow()
    await seed_observation(
        timestamp=now - timedelta(seconds=10),
        process_id="P_OBS_PANEL_NULLABLE_202",
        source_outcome_id=str(uuid.uuid4()),
        facts={
            "event_type": "metrics_endpoint_timing",
            "endpoint": "/api/v1/metrics/overview",
            "status_code": 202,
            "duration_ms": 22,
        },
    )

    response = await client.get("/api/v1/observability/overview", headers=_internal_headers())
    assert response.status_code == 200
    guardrails = response.json()["guardrails"]
    assert guardrails["events"]["accepted_202"] == 1
    event_202 = next(e for e in guardrails["last_events"] if e["status_code"] == 202)
    assert event_202["scope"] is None
    assert event_202["snapshot_status"] is None

