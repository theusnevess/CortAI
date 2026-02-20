from datetime import date, datetime, timedelta
from decimal import Decimal
import uuid

import pytest
from sqlalchemy import delete

from app.db.models import MetricsEndpointDaily
from app.api.v1.endpoints.metrics import process_read_refresh_jobs_once


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
