from datetime import datetime, timedelta
import uuid

import pytest

from app.api.v1.endpoints import observability as observability_endpoint
from app.observability import runtime_health


def _internal_headers() -> dict[str, str]:
    return {"X-Internal-Status": "1"}


def _assert_trust_contract(trust: dict) -> None:
    assert isinstance(trust, dict)
    assert trust["state"] in {"green", "yellow", "red"}
    assert trust["decision"] in {"healthy", "degraded", "action_required"}
    assert isinstance(trust["message"], str)
    assert len(trust["message"]) > 0
    assert isinstance(trust["derived_from"], list)
    assert len(trust["derived_from"]) > 0
    # Nao vazar detalhes internos de jobs/queries.
    serialized = str(trust)
    assert "job_key" not in serialized
    assert "query_key" not in serialized


def _fake_c1_health_payload(score: str) -> dict:
    return {
        "enabled": True,
        "version": "v1.1",
        "score": score,
        "as_of": "2026-02-24T21:00:00Z",
        "inputs": {"window_minutes": 15, "source": "metrics_endpoint_timing"},
        "reasons": ["overview:rps<1"] if score == "FAIL" else [],
        "rows": [
            {
                "endpoint": "overview",
                "path": "direct",
                "p99_ms": 100.0,
                "rps": 2.0,
                "timeouts": 0,
                "pct_429": 0.0,
                "pct_503": 0.0,
                "pct_5xx": 0.0,
                "decision": score,
                "reasons": [],
            }
        ],
        "meta": {"cached": False, "cache_age_seconds": 0, "compute_ms": 1, "stale": False},
    }


def _make_panel_stubs(*, score: str, overview_snapshot_status: str, snapshot_missing_503: int, rate_limited_429: int):
    async def _fake_c1_health(*, db, db_stats):
        return _fake_c1_health_payload(score)

    async def _fake_read_path(*, db, db_stats):
        return {
            "overview_freshness_seconds": 5 if overview_snapshot_status == "fresh" else 120,
            "overview_snapshot_status": overview_snapshot_status,
            "overview_last_refreshed_at": "2026-02-24T21:00:00Z" if overview_snapshot_status != "missing" else None,
            "runs_freshness_seconds": 5,
            "runs_snapshot_status": "fresh",
            "runs_last_refreshed_at": "2026-02-24T21:00:00Z",
            "runs_key_count": 1,
            "jobs_queued_count": 0,
        }

    async def _fake_guardrails(*, db, db_stats, window_minutes=15, last_events_limit=5):
        return {
            "window_minutes": int(window_minutes),
            "events": {
                "accepted_202": 0,
                "rate_limited_429": int(rate_limited_429),
                "snapshot_missing_503": int(snapshot_missing_503),
            },
            "last_events": [],
        }

    return _fake_c1_health, _fake_read_path, _fake_guardrails


def _patch_panel_dependencies(monkeypatch, *, score: str, overview_snapshot_status: str, snapshot_missing_503: int, rate_limited_429: int) -> None:
    fake_c1_health, fake_read_path, fake_guardrails = _make_panel_stubs(
        score=score,
        overview_snapshot_status=overview_snapshot_status,
        snapshot_missing_503=snapshot_missing_503,
        rate_limited_429=rate_limited_429,
    )
    monkeypatch.setattr(observability_endpoint, "get_runtime_c1_health_cached", fake_c1_health)
    monkeypatch.setattr(observability_endpoint, "_get_read_path_compact", fake_read_path)
    monkeypatch.setattr(observability_endpoint, "_get_guardrails_summary", fake_guardrails)


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


@pytest.mark.anyio
async def test_trust_banner_green(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    _patch_panel_dependencies(
        monkeypatch,
        score="PASS",
        overview_snapshot_status="fresh",
        snapshot_missing_503=0,
        rate_limited_429=0,
    )

    response = await client.get("/api/v1/observability/overview", headers=_internal_headers())
    assert response.status_code == 200
    trust = response.json()["trust"]
    _assert_trust_contract(trust)
    assert trust["state"] == "green"
    assert trust["decision"] == "healthy"
    assert "c1_health" in trust["derived_from"]


@pytest.mark.anyio
async def test_trust_banner_yellow_from_warn(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    _patch_panel_dependencies(
        monkeypatch,
        score="WARN",
        overview_snapshot_status="fresh",
        snapshot_missing_503=0,
        rate_limited_429=0,
    )

    response = await client.get("/api/v1/observability/overview", headers=_internal_headers())
    assert response.status_code == 200
    trust = response.json()["trust"]
    _assert_trust_contract(trust)
    assert trust["state"] == "yellow"
    assert trust["decision"] == "degraded"
    assert "c1_health" in trust["derived_from"]


@pytest.mark.anyio
async def test_trust_banner_red_from_fail(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    _patch_panel_dependencies(
        monkeypatch,
        score="FAIL",
        overview_snapshot_status="fresh",
        snapshot_missing_503=0,
        rate_limited_429=0,
    )

    response = await client.get("/api/v1/observability/overview", headers=_internal_headers())
    assert response.status_code == 200
    trust = response.json()["trust"]
    _assert_trust_contract(trust)
    assert trust["state"] == "red"
    assert trust["decision"] == "action_required"
    assert "c1_health" in trust["derived_from"]


@pytest.mark.anyio
async def test_trust_banner_yellow_from_stale_read_path(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    _patch_panel_dependencies(
        monkeypatch,
        score="PASS",
        overview_snapshot_status="stale",
        snapshot_missing_503=0,
        rate_limited_429=0,
    )

    response = await client.get("/api/v1/observability/overview", headers=_internal_headers())
    assert response.status_code == 200
    trust = response.json()["trust"]
    _assert_trust_contract(trust)
    assert trust["state"] == "yellow"
    assert trust["decision"] == "degraded"
    assert "read_path" in trust["derived_from"]


@pytest.mark.anyio
async def test_trust_banner_red_from_snapshot_missing(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    _patch_panel_dependencies(
        monkeypatch,
        score="PASS",
        overview_snapshot_status="missing",
        snapshot_missing_503=0,
        rate_limited_429=0,
    )

    response = await client.get("/api/v1/observability/overview", headers=_internal_headers())
    assert response.status_code == 200
    trust = response.json()["trust"]
    _assert_trust_contract(trust)
    assert trust["state"] == "red"
    assert trust["decision"] == "action_required"
    assert "read_path" in trust["derived_from"]


@pytest.mark.anyio
async def test_trust_banner_precedence_red_over_yellow(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    _patch_panel_dependencies(
        monkeypatch,
        score="WARN",
        overview_snapshot_status="missing",
        snapshot_missing_503=0,
        rate_limited_429=0,
    )

    response = await client.get("/api/v1/observability/overview", headers=_internal_headers())
    assert response.status_code == 200
    trust = response.json()["trust"]
    _assert_trust_contract(trust)
    assert trust["state"] == "red"
    assert trust["decision"] == "action_required"
