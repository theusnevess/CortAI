from datetime import date, datetime, timedelta
from decimal import Decimal
import uuid
import asyncio

import pytest
from sqlalchemy import delete

from app.db.models import MetricsEndpointDaily
from app.api.v1.endpoints.metrics import process_read_refresh_jobs_once
from app.api.v1.endpoints import status as status_endpoint
from app.observability import runtime_health


async def _ensure_metrics_endpoint_daily_table(db_session) -> None:
    conn = await db_session.connection()
    await conn.run_sync(
        lambda sync_conn: MetricsEndpointDaily.__table__.create(bind=sync_conn, checkfirst=True)
    )


async def _clear_metric_day(db_session, metric_day: date) -> None:
    await db_session.execute(delete(MetricsEndpointDaily).where(MetricsEndpointDaily.metric_date == metric_day))
    await db_session.flush()


async def _clear_metric_window(db_session, window_days: int) -> None:
    """
    Limpa janela recente para manter os testes deterministas mesmo com historico.
    """
    window_start = date.today() - timedelta(days=window_days)
    await db_session.execute(delete(MetricsEndpointDaily).where(MetricsEndpointDaily.metric_date >= window_start))
    await db_session.flush()


@pytest.mark.anyio
async def test_status_guardrail_window_days(client):
    response = await client.get("/api/v1/status", params={"window_days": 31})
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error_type"] == "RangeTooLarge"
    assert detail["window_days_requested"] == 31
    assert detail["window_days_max"] == 30


@pytest.mark.anyio
async def test_status_warn_when_missing_endpoints(client, db_session):
    metric_day = date.today()
    await _ensure_metrics_endpoint_daily_table(db_session)
    await _clear_metric_window(db_session, 7)
    db_session.add(
        MetricsEndpointDaily(
            id=uuid.uuid4(),
            metric_date=metric_day,
            endpoint="/api/v1/metrics/runs",
            count_requests=20,
            p50_ms=20,
            p95_ms=80,
            p99_ms=120,
            error_rate=Decimal("0.0000"),
        )
    )
    await db_session.flush()

    response = await client.get("/api/v1/status", params={"window_days": 7})
    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] == "WARN"
    assert payload["slo_status"]["status"] == "WARN"
    assert "/api/v1/metrics/overview" in payload["slo_status"]["missing_endpoints"]


@pytest.mark.anyio
async def test_status_pass_with_all_endpoints_present(client, db_session):
    metric_day = date.today()
    await _ensure_metrics_endpoint_daily_table(db_session)
    await _clear_metric_window(db_session, 7)

    rows = [
        ("/api/v1/metrics/runs", 40, 40, 90, 140, "0.0050"),
        ("/api/v1/metrics/runs/{process_id}", 30, 30, 120, 180, "0.0000"),
        ("/api/v1/metrics/overview", 25, 20, 60, 120, "0.0000"),
        ("/api/v1/observability/report", 10, 40, 120, 200, "0.0000"),
    ]
    for endpoint, count, p50, p95, p99, error_rate in rows:
        db_session.add(
            MetricsEndpointDaily(
                id=uuid.uuid4(),
                metric_date=metric_day,
                endpoint=endpoint,
                count_requests=count,
                p50_ms=p50,
                p95_ms=p95,
                p99_ms=p99,
                error_rate=Decimal(error_rate),
            )
        )
    await db_session.flush()

    response = await client.get("/api/v1/status", params={"window_days": 7})
    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] == "PASS"
    assert payload["slo_status"]["status"] == "PASS"
    assert payload["error_budget_remaining"]["status"] == "PASS"
    assert payload["error_budget_remaining"]["remaining_errors"] >= 0


@pytest.mark.anyio
async def test_status_fail_on_slo_breach(client, db_session):
    metric_day = date.today()
    await _ensure_metrics_endpoint_daily_table(db_session)
    await _clear_metric_window(db_session, 7)

    db_session.add(
        MetricsEndpointDaily(
            id=uuid.uuid4(),
            metric_date=metric_day,
            endpoint="/api/v1/metrics/runs",
            count_requests=30,
            p50_ms=100,
            p95_ms=500,
            p99_ms=800,
            error_rate=Decimal("0.0500"),
        )
    )
    await db_session.flush()

    response = await client.get("/api/v1/status", params={"window_days": 7})
    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] == "FAIL"
    assert payload["slo_status"]["status"] == "FAIL"
    failed_runs_endpoint = next(
        e for e in payload["slo_status"]["endpoints"] if e["endpoint"] == "/api/v1/metrics/runs"
    )
    assert failed_runs_endpoint["status"] == "FAIL"
    assert "p95_slo_breach" in failed_runs_endpoint["breaches"]


@pytest.mark.anyio
async def test_status_expoe_overview_freshness_seconds(client, seed_daily_metric, db_session):
    """
    Status deve expor freshness do read model do overview quando houver snapshot.
    """
    await seed_daily_metric(
        metric_date=date.today(),
        total_runs=2,
        completed_runs=2,
        failed_runs=0,
        blocked_runs=0,
        avg_actions_executed=1.0,
        last_action_type_distribution={"write_artifact": 2},
    )
    overview = await client.get("/api/v1/metrics/overview", params={"days": 1, "force_live": "true"})
    assert overview.status_code == 202
    await process_read_refresh_jobs_once(db=db_session, limit=10)

    response = await client.get("/api/v1/status", params={"window_days": 7})
    assert response.status_code == 200
    payload = response.json()
    assert "read_path" in payload
    assert "overview_freshness_seconds" in payload["read_path"]
    assert "overview_snapshot_status" in payload["read_path"]
    assert "overview_last_refreshed_at" in payload["read_path"]
    assert payload["read_path"]["overview_freshness_seconds"] is None or payload["read_path"]["overview_freshness_seconds"] >= 0


@pytest.mark.anyio
async def test_status_expoe_runs_freshness_e_key_count(client, seed_observation, db_session):
    """
    Status deve expor freshness e quantidade de chaves do runs read model.
    """
    await seed_observation(
        timestamp=datetime(2026, 2, 10, 12, 0, 0),
        process_id="P_STATUS_RUNS_FRESHNESS_1",
        source_outcome_id="outcome-status-runs-freshness-1",
        facts={
            "event_type": "cognitive_loop_finished",
            "pipeline_status": "completed",
            "actions_executed": 1,
        },
    )
    runs = await client.get(
        "/api/v1/metrics/runs",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10", "limit": 50, "offset": 0, "force_live": "true"},
    )
    assert runs.status_code == 202
    await process_read_refresh_jobs_once(db=db_session, limit=10)

    response = await client.get("/api/v1/status", params={"window_days": 7})
    assert response.status_code == 200
    payload = response.json()
    assert "read_path" in payload
    assert "runs_freshness_seconds" in payload["read_path"]
    assert "runs_snapshot_status" in payload["read_path"]
    assert "runs_last_refreshed_at" in payload["read_path"]
    assert "runs_key_count" in payload["read_path"]
    assert "jobs_queued_count" in payload["read_path"]
    assert payload["read_path"]["runs_freshness_seconds"] is None or payload["read_path"]["runs_freshness_seconds"] >= 0
    assert isinstance(payload["read_path"]["runs_key_count"], int)


@pytest.mark.anyio
async def test_status_nao_expoe_c1_health_por_padrao(client, monkeypatch):
    monkeypatch.delenv("EXPOSE_C1_HEALTH_STATUS", raising=False)
    response = await client.get("/api/v1/status", params={"window_days": 7})
    assert response.status_code == 200
    payload = response.json()
    assert "c1_health" not in payload


@pytest.mark.anyio
async def test_status_expoe_c1_health_com_env_e_header(client, seed_observation, monkeypatch):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    now = datetime.utcnow()
    for idx in range(4):
        await seed_observation(
            timestamp=now - timedelta(minutes=1),
            process_id=f"P_STATUS_C1_OV_{idx}",
            source_outcome_id=f"outcome-status-c1-ov-{idx}",
            facts={
                "event_type": "metrics_endpoint_timing",
                "endpoint": "/api/v1/metrics/overview",
                "status_code": 200,
                "duration_ms": 100,
            },
        )
        await seed_observation(
            timestamp=now - timedelta(minutes=1),
            process_id=f"P_STATUS_C1_RUN_{idx}",
            source_outcome_id=f"outcome-status-c1-run-{idx}",
            facts={
                "event_type": "metrics_endpoint_timing",
                "endpoint": "/api/v1/metrics/runs",
                "status_code": 200,
                "duration_ms": 120,
            },
        )
        await seed_observation(
            timestamp=now - timedelta(minutes=1),
            process_id=f"P_STATUS_C1_REP_{idx}",
            source_outcome_id=f"outcome-status-c1-rep-{idx}",
            facts={
                "event_type": "metrics_endpoint_timing",
                "endpoint": "/api/v1/observability/report",
                "status_code": 200,
                "duration_ms": 130,
            },
        )

    response = await client.get(
        "/api/v1/status",
        params={"window_days": 7},
        headers={"X-Internal-Status": "1"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "c1_health" in payload
    c1 = payload["c1_health"]
    assert c1["enabled"] is True
    assert c1["inputs"]["source"] == "metrics_endpoint_timing"
    assert c1["inputs"]["window_minutes"] == 15
    assert isinstance(c1["rows"], list)
    assert {row["endpoint"] for row in c1["rows"]} == {"overview", "runs", "report"}
    assert all(row["path"] == "direct" for row in c1["rows"])


def test_c1_health_classification_pass_warn_fail():
    row_pass = status_endpoint._classify_c1_health_row(
        endpoint="overview",
        p99_ms=500.0,
        rps=2.0,
        timeouts=0,
        pct_429=0.0,
        pct_503=0.0,
        pct_5xx=0.0,
    )
    assert row_pass["decision"] == "PASS"
    assert row_pass["reasons"] == []

    row_warn = status_endpoint._classify_c1_health_row(
        endpoint="runs",
        p99_ms=1700.0,
        rps=2.0,
        timeouts=0,
        pct_429=0.0,
        pct_503=0.0,
        pct_5xx=0.0,
    )
    assert row_warn["decision"] == "WARN"
    assert "p99>warn_limit" in row_warn["reasons"]

    row_fail = status_endpoint._classify_c1_health_row(
        endpoint="report",
        p99_ms=3000.0,
        rps=2.0,
        timeouts=0,
        pct_429=0.0,
        pct_503=0.0,
        pct_5xx=0.0,
    )
    assert row_fail["decision"] == "FAIL"
    assert "p99>fail_limit" in row_fail["reasons"]


@pytest.mark.anyio
async def test_status_c1_health_cache_hit_reduces_compute_calls(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    monkeypatch.setenv("C1_HEALTH_CACHE_TTL_SECONDS", "10")
    status_endpoint._clear_runtime_c1_health_cache()
    calls = {"n": 0}

    async def _fake_compute(**kwargs):
        calls["n"] += 1
        rows = [
            {
                "endpoint": "overview",
                "path": "direct",
                "p99_ms": 100.0,
                "rps": 2.0,
                "timeouts": 0,
                "pct_429": 0.0,
                "pct_503": 0.0,
                "pct_5xx": 0.0,
                "decision": "PASS",
                "reasons": [],
            },
            {
                "endpoint": "runs",
                "path": "direct",
                "p99_ms": 100.0,
                "rps": 2.0,
                "timeouts": 0,
                "pct_429": 0.0,
                "pct_503": 0.0,
                "pct_5xx": 0.0,
                "decision": "PASS",
                "reasons": [],
            },
            {
                "endpoint": "report",
                "path": "direct",
                "p99_ms": 100.0,
                "rps": 2.0,
                "timeouts": 0,
                "pct_429": 0.0,
                "pct_503": 0.0,
                "pct_5xx": 0.0,
                "decision": "PASS",
                "reasons": [],
            },
        ]
        return status_endpoint._build_c1_health_payload(rows, as_of=datetime.utcnow(), window_minutes=15)

    monkeypatch.setattr(runtime_health, "_compute_runtime_c1_health", _fake_compute)

    resp1 = await client.get("/api/v1/status", params={"window_days": 7}, headers={"X-Internal-Status": "1"})
    resp2 = await client.get("/api/v1/status", params={"window_days": 7}, headers={"X-Internal-Status": "1"})
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert calls["n"] == 1
    assert resp1.json()["c1_health"]["meta"]["cached"] is False
    assert resp2.json()["c1_health"]["meta"]["cached"] is True


@pytest.mark.anyio
async def test_status_c1_health_cache_expires(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    monkeypatch.setenv("C1_HEALTH_CACHE_TTL_SECONDS", "1")
    status_endpoint._clear_runtime_c1_health_cache()
    calls = {"n": 0}

    async def _fake_compute(**kwargs):
        calls["n"] += 1
        rows = [
            {
                "endpoint": "overview",
                "path": "direct",
                "p99_ms": 100.0,
                "rps": 2.0,
                "timeouts": 0,
                "pct_429": 0.0,
                "pct_503": 0.0,
                "pct_5xx": 0.0,
                "decision": "PASS",
                "reasons": [],
            },
            {
                "endpoint": "runs",
                "path": "direct",
                "p99_ms": 100.0,
                "rps": 2.0,
                "timeouts": 0,
                "pct_429": 0.0,
                "pct_503": 0.0,
                "pct_5xx": 0.0,
                "decision": "PASS",
                "reasons": [],
            },
            {
                "endpoint": "report",
                "path": "direct",
                "p99_ms": 100.0,
                "rps": 2.0,
                "timeouts": 0,
                "pct_429": 0.0,
                "pct_503": 0.0,
                "pct_5xx": 0.0,
                "decision": "PASS",
                "reasons": [],
            },
        ]
        return status_endpoint._build_c1_health_payload(rows, as_of=datetime.utcnow(), window_minutes=15)

    monkeypatch.setattr(runtime_health, "_compute_runtime_c1_health", _fake_compute)

    resp1 = await client.get("/api/v1/status", params={"window_days": 7}, headers={"X-Internal-Status": "1"})
    await asyncio.sleep(1.2)
    resp2 = await client.get("/api/v1/status", params={"window_days": 7}, headers={"X-Internal-Status": "1"})
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert calls["n"] == 2
    assert resp2.json()["c1_health"]["meta"]["cached"] is False


@pytest.mark.anyio
async def test_status_c1_health_reasons_present(client, monkeypatch):
    monkeypatch.setenv("EXPOSE_C1_HEALTH_STATUS", "1")
    monkeypatch.setenv("C1_HEALTH_CACHE_TTL_SECONDS", "10")
    status_endpoint._clear_runtime_c1_health_cache()

    async def _fake_compute(**kwargs):
        rows = [
            {
                "endpoint": "overview",
                "path": "direct",
                "p99_ms": 1200.0,
                "rps": 2.0,
                "timeouts": 0,
                "pct_429": 0.0,
                "pct_503": 0.0,
                "pct_5xx": 0.0,
                "decision": "PASS",
                "reasons": [],
            },
            {
                "endpoint": "runs",
                "path": "direct",
                "p99_ms": 1800.0,
                "rps": 2.0,
                "timeouts": 0,
                "pct_429": 0.0,
                "pct_503": 0.0,
                "pct_5xx": 0.0,
                "decision": "WARN",
                "reasons": ["p99>warn_limit"],
            },
            {
                "endpoint": "report",
                "path": "direct",
                "p99_ms": None,
                "rps": 2.0,
                "timeouts": 0,
                "pct_429": 0.0,
                "pct_503": 10.0,
                "pct_5xx": 0.0,
                "decision": "WARN",
                "reasons": ["p99_missing"],
            },
        ]
        return status_endpoint._build_c1_health_payload(rows, as_of=datetime.utcnow(), window_minutes=15)

    monkeypatch.setattr(runtime_health, "_compute_runtime_c1_health", _fake_compute)
    response = await client.get("/api/v1/status", params={"window_days": 7}, headers={"X-Internal-Status": "1"})
    assert response.status_code == 200
    c1 = response.json()["c1_health"]
    assert c1["meta"]["cached"] is False
    assert "reasons" in c1
    assert "runs:p99>warn_limit" in c1["reasons"]
    assert "report:p99_missing" in c1["reasons"]


@pytest.mark.anyio
async def test_status_public_returns_minimal_sanitized_payload(client, monkeypatch):
    async def _fake_builder(**kwargs):
        return {
            "as_of": "2026-02-27T10:00:00Z",
            "trust": {
                "state": "yellow",
                "decision": "degraded",
                "message": "internal detail",
                "derived_from": ["guardrails"],
            },
            "recommendation": {
                "action": "reduce_force_live_burst",
                "priority": "medium",
                "message": "internal detail",
                "derived_from": ["guardrails"],
            },
            "c1_health": {"score": "WARN", "rows": [], "meta": {"cached": True}},
            "read_path": {"overview_snapshot_status": "stale"},
            "guardrails": {"events": {"rate_limited_429": 3}},
        }

    monkeypatch.setattr(status_endpoint, "_build_observability_overview_payload", _fake_builder)

    response = await client.get("/api/v1/status/public")
    assert response.status_code == 200
    assert response.headers.get("cache-control") == "public, max-age=30"

    payload = response.json()
    assert set(payload.keys()) == {"state", "action", "as_of", "version"}
    assert payload["state"] == "degraded"
    assert payload["action"] == "monitor"
    assert payload["as_of"] == "2026-02-27T10:00:00Z"
    assert payload["version"] == "v1"

    serialized = str(payload)
    assert "derived_from" not in serialized
    assert "reasons" not in serialized
    assert "meta" not in serialized
    assert "c1_health" not in serialized
    assert "guardrails" not in serialized


@pytest.mark.anyio
async def test_status_public_action_mapping_defaults_to_inspect(client, monkeypatch):
    async def _fake_builder(**kwargs):
        return {
            "as_of": "2026-02-27T10:00:00Z",
            "trust": {"decision": "action_required"},
            "recommendation": {"action": "unknown_action"},
        }

    monkeypatch.setattr(status_endpoint, "_build_observability_overview_payload", _fake_builder)

    response = await client.get("/api/v1/status/public")
    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "action_required"
    assert payload["action"] == "inspect"
