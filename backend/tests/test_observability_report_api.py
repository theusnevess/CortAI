from datetime import date, datetime, timedelta
from decimal import Decimal
import uuid

import pytest
from sqlalchemy import delete

from app.db.models import MetricsEndpointDaily, ObservationRecord, PublishReceipt


async def _ensure_tables(db_session) -> None:
    conn = await db_session.connection()
    await conn.run_sync(lambda sync_conn: MetricsEndpointDaily.__table__.create(bind=sync_conn, checkfirst=True))
    await conn.run_sync(lambda sync_conn: PublishReceipt.__table__.create(bind=sync_conn, checkfirst=True))


async def _seed_minimum_pass_data(db_session, seed_observation) -> None:
    now = datetime.utcnow()
    metric_day = date.today()
    await _ensure_tables(db_session)
    await db_session.execute(delete(ObservationRecord).where(ObservationRecord.process_id.like("P_OBS_REPORT_%")))
    await db_session.execute(delete(MetricsEndpointDaily).where(MetricsEndpointDaily.metric_date == metric_day))
    await db_session.execute(delete(PublishReceipt).where(PublishReceipt.process_id.like("P_OBS_REPORT_%")))
    await db_session.flush()

    await seed_observation(
        timestamp=now,
        process_id="P_OBS_REPORT_TIMING",
        source_outcome_id=str(uuid.uuid4()),
        facts={
            "event_type": "metrics_endpoint_timing",
            "endpoint": "/api/v1/metrics/runs",
            "method": "GET",
            "status_code": 200,
            "duration_ms": 15,
            "timestamp": now.isoformat(),
        },
    )
    db_session.add(
        MetricsEndpointDaily(
            id=uuid.uuid4(),
            metric_date=metric_day,
            endpoint="/api/v1/metrics/runs",
            count_requests=10,
            p50_ms=10,
            p95_ms=30,
            p99_ms=50,
            error_rate=Decimal("0.0000"),
        )
    )
    db_session.add(
        PublishReceipt(
            publish_decision_id=str(uuid.uuid4()),
            process_id="P_OBS_REPORT_OK",
            manifest_decision_id=str(uuid.uuid4()),
            pipeline_status="published",
            execution_status="success",
            target="test",
            external_post_id=None,
            error_type=None,
            error_message=None,
            published_at=now,
            created_at=now,
            updated_at=now,
        )
    )
    await db_session.flush()


@pytest.mark.anyio
async def test_report_happy_path_shape(client, db_session, seed_observation):
    await _seed_minimum_pass_data(db_session, seed_observation)
    now = datetime.utcnow()
    await seed_observation(
        timestamp=now,
        process_id="P_OBS_REPORT_FINISHED",
        source_outcome_id=str(uuid.uuid4()),
        facts={
            "event_type": "cognitive_loop_finished",
            "pipeline_status": "completed",
            "execution_status": "success",
            "ces_run_version": "CES_run_v1",
            "ces_run": "99.1",
            "ces_run_components": {
                "status": "1.0",
                "actions": "1.0",
                "latency": "1.0",
                "trunc": "1.0",
            },
        },
    )
    response = await client.get("/api/v1/observability/report")
    assert response.status_code == 200
    payload = response.json()
    for key in (
        "generated_at_utc",
        "version",
        "timing",
        "slo_daily",
        "slo_alerts",
        "runs",
        "publish_receipts",
        "checks",
        "status",
    ):
        assert key in payload
    assert payload["version"]["ces_default_version"] == "CES_v1"
    assert payload["status"] == "PASS"
    assert payload["runs"]["worst"] == []
    assert payload["slo_alerts"]["items"] == []
    assert payload["publish_receipts"]["errors_7d"] == []
    assert payload["publish_receipts"]["latest_7d"] == []


@pytest.mark.anyio
async def test_report_guardrail_window_days(client):
    response = await client.get("/api/v1/observability/report", params={"window_days": 31})
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error_type"] == "RangeTooLarge"
    assert detail["window_days_requested"] == 31
    assert detail["window_days_max"] == 30


@pytest.mark.anyio
async def test_report_worst_runs_empty_is_warn(client, db_session, seed_observation):
    await _seed_minimum_pass_data(db_session, seed_observation)
    response = await client.get(
        "/api/v1/observability/report",
        params={"include_worst_runs": True},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["runs"]["worst"] == []
    assert payload["status"] == "WARN"


@pytest.mark.anyio
async def test_report_guardrail_worst_runs_requires_small_window(client):
    response = await client.get(
        "/api/v1/observability/report",
        params={"include_worst_runs": True, "window_days": 8},
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error_type"] == "RangeTooLarge"
    assert detail["window_days_requested"] == 8
    assert detail["window_days_max_for_worst_runs"] == 7


@pytest.mark.anyio
async def test_report_opt_in_blocks_return_data(client, db_session, seed_observation):
    await _seed_minimum_pass_data(db_session, seed_observation)
    now = datetime.utcnow()
    await seed_observation(
        timestamp=now,
        process_id="P_OBS_REPORT_ALERT",
        source_outcome_id=str(uuid.uuid4()),
        facts={
            "event_type": "metrics_slo_alert",
            "metric_date": date.today().isoformat(),
            "endpoint": "/api/v1/metrics/runs",
            "reasons": ["p95_slo_breach"],
        },
    )
    await seed_observation(
        timestamp=now,
        process_id="P_OBS_REPORT_FINISHED",
        source_outcome_id=str(uuid.uuid4()),
        facts={
            "event_type": "cognitive_loop_finished",
            "pipeline_status": "completed",
            "execution_status": "success",
            "ces_run_version": "CES_run_v1",
            "ces_run": "80.0",
            "ces_run_components": {
                "status": "1.0",
                "actions": "0.7",
                "latency": "0.8",
                "trunc": "1.0",
            },
        },
    )
    db_session.add(
        PublishReceipt(
            publish_decision_id=str(uuid.uuid4()),
            process_id="P_OBS_REPORT_BLOCKED",
            manifest_decision_id=str(uuid.uuid4()),
            pipeline_status="blocked",
            execution_status="blocked",
            target="test",
            external_post_id=None,
            error_type="ArtifactNotFound",
            error_message="manifest ausente",
            published_at=None,
            created_at=now,
            updated_at=now,
        )
    )
    await db_session.flush()

    response = await client.get(
        "/api/v1/observability/report",
        params={
            "include_worst_runs": True,
            "include_alert_items": True,
            "include_receipts": True,
            "window_days": 7,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["runs"]["worst"]
    assert payload["slo_alerts"]["items"]
    assert payload["publish_receipts"]["errors_7d"]
    assert payload["publish_receipts"]["latest_7d"]


@pytest.mark.anyio
async def test_report_path_leak_check_fail(client, db_session, seed_observation):
    await _seed_minimum_pass_data(db_session, seed_observation)
    now = datetime.utcnow()
    db_session.add(
        PublishReceipt(
            publish_decision_id=str(uuid.uuid4()),
            process_id="P_OBS_REPORT_LEAK",
            manifest_decision_id=str(uuid.uuid4()),
            pipeline_status="blocked",
            execution_status="blocked",
            target="test",
            external_post_id=None,
            error_type="ArtifactNotFound",
            error_message="manifest em /tmp/agent_output/file.json",
            published_at=None,
            created_at=now,
            updated_at=now,
        )
    )
    await db_session.flush()

    response = await client.get("/api/v1/observability/report")
    assert response.status_code == 200
    payload = response.json()
    leaks_check = next(c for c in payload["checks"] if c["id"] == "receipts_path_leaks_30d")
    assert leaks_check["pass"] is False
    assert leaks_check["value"] >= 1
    assert payload["status"] == "FAIL"


@pytest.mark.anyio
async def test_report_timing_events_present_or_warn(client, db_session):
    await _ensure_tables(db_session)
    metric_day = date.today()
    await db_session.execute(delete(ObservationRecord).where(ObservationRecord.process_id.like("P_OBS_REPORT_%")))
    await db_session.execute(delete(MetricsEndpointDaily).where(MetricsEndpointDaily.metric_date == metric_day))
    await db_session.execute(delete(PublishReceipt).where(PublishReceipt.process_id.like("P_OBS_REPORT_%")))
    await db_session.flush()
    db_session.add(
        MetricsEndpointDaily(
            id=uuid.uuid4(),
            metric_date=metric_day,
            endpoint="/api/v1/metrics/runs",
            count_requests=5,
            p50_ms=5,
            p95_ms=10,
            p99_ms=20,
            error_rate=Decimal("0.0000"),
        )
    )
    await db_session.flush()

    response = await client.get("/api/v1/observability/report")
    assert response.status_code == 200
    payload = response.json()
    timing_check = next(c for c in payload["checks"] if c["id"] == "timing_events_window")
    assert timing_check["pass"] is False
    assert payload["status"] == "FAIL"
