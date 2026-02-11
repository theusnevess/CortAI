from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import delete

from app.api.v1.endpoints.metrics import PROHIBITED_FACT_KEYS
from app.cognitive_metrics import aggregate_daily_metrics_for_date
from app.db.models import ObservationRecord


@pytest.mark.anyio
async def test_daily_sem_dados(client):
    """
    Valida retorno vazio do endpoint /metrics/daily sem dados no periodo.
    """
    response = await client.get(
        "/api/v1/metrics/daily",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("items"), list)
    assert payload["items"] == []


@pytest.mark.anyio
async def test_daily_um_dia_com_uma_linha(client, seed_daily_metric):
    """
    Valida serializacao de uma linha diaria com campos agregados.
    """
    await seed_daily_metric(
        metric_date=date(2026, 2, 10),
        total_runs=4,
        completed_runs=3,
        failed_runs=0,
        blocked_runs=0,
        truncated_runs=0,
        truncated_ratio=0,
        avg_actions_executed=Decimal("0.75"),
        last_action_type_distribution={"unknown": 1, "write_artifact": 3},
        latency_by_action={"write_artifact": {"n": 3, "avg_ms": 20, "p95_ms": 30}},
    )
    response = await client.get(
        "/api/v1/metrics/daily",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["metric_date"] == "2026-02-10"
    assert item["total_runs"] == 4
    assert item["completed_runs"] == 3
    assert item["failed_runs"] == 0
    assert item["blocked_runs"] == 0
    assert float(item["avg_actions_executed"]) == pytest.approx(0.75)
    assert item["last_action_type_distribution"]["write_artifact"] == 3


@pytest.mark.anyio
async def test_daily_alerted_true_quando_ha_alerta(client, seed_daily_metric, seed_observation):
    """
    Valida enrichment de alerta no /metrics/daily.
    """
    await seed_daily_metric(
        metric_date=date(2026, 2, 10),
        total_runs=4,
        completed_runs=3,
        failed_runs=0,
        blocked_runs=0,
        avg_actions_executed=Decimal("0.75"),
        last_action_type_distribution={"unknown": 1, "write_artifact": 3},
    )
    obs = await seed_observation(
        timestamp=datetime(2026, 2, 10, 12, 0, 0),
        process_id="P_METRICS_DAILY_2026-02-10",
        source_outcome_id="outcome-alert-b3",
        facts={
            "event_type": "cognitive_metrics_alert",
            "metric_date": "2026-02-10",
            "reasons": ["p95_latency:transcribe_segments"],
        },
    )
    response = await client.get(
        "/api/v1/metrics/daily",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["alerted"] is True
    assert item["alert_count"] == 1
    assert item["alert_reasons"] == ["p95_latency:transcribe_segments"]
    assert item["alert_observation_id"] == obs.observation_id


@pytest.mark.anyio
async def test_overview_soma_bate(client, seed_daily_metric):
    """
    Valida consistencia entre itens e summary no /metrics/overview.
    """
    await seed_daily_metric(
        metric_date=date(2026, 2, 8),
        total_runs=2,
        completed_runs=2,
        failed_runs=0,
        blocked_runs=0,
        avg_actions_executed=0.50,
        last_action_type_distribution={"unknown": 2},
    )
    await seed_daily_metric(
        metric_date=date(2026, 2, 9),
        total_runs=5,
        completed_runs=4,
        failed_runs=1,
        blocked_runs=0,
        avg_actions_executed=0.60,
        last_action_type_distribution={"unknown": 5},
    )
    await seed_daily_metric(
        metric_date=date(2026, 2, 10),
        total_runs=4,
        completed_runs=3,
        failed_runs=0,
        blocked_runs=1,
        avg_actions_executed=0.75,
        last_action_type_distribution={"unknown": 1, "write_artifact": 3},
    )
    response = await client.get(
        "/api/v1/metrics/overview",
        params={"start_date": "2026-02-08", "end_date": "2026-02-10"},
    )
    assert response.status_code == 200
    payload = response.json()
    items = payload["items"]
    summary = payload["summary"]
    assert [item["metric_date"] for item in items] == ["2026-02-08", "2026-02-09", "2026-02-10"]
    assert summary["total_runs"] == sum(item["total_runs"] for item in items)
    assert summary["completed_runs"] == sum(item["completed_runs"] for item in items)
    assert summary["failed_runs"] == sum(item["failed_runs"] for item in items)
    assert summary["blocked_runs"] == sum(item["blocked_runs"] for item in items)
    assert summary["alert_days"] == sum(1 for item in items if item["alerted"])


@pytest.mark.anyio
async def test_alerts_range_vazio(client):
    """
    Valida /metrics/alerts sem registros no periodo.
    """
    response = await client.get(
        "/api/v1/metrics/alerts",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10", "limit": 10, "offset": 0},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["items"] == []
    assert payload["total"] == 0
    assert payload["limit"] == 10
    assert payload["offset"] == 0


@pytest.mark.anyio
async def test_alerts_ordenado_desc_paginacao(client, seed_observation):
    """
    Valida ordenacao DESC e paginacao no /metrics/alerts.
    """
    common_facts = {
        "event_type": "cognitive_metrics_alert",
        "metric_date": "2026-02-10",
        "reasons": ["failed_ratio"],
    }
    obs_10 = await seed_observation(
        timestamp=datetime(2026, 2, 10, 10, 0, 0),
        process_id="P_METRICS_DAILY_2026-02-10_A",
        source_outcome_id="outcome-alert-d2-a",
        facts=common_facts,
    )
    await seed_observation(
        timestamp=datetime(2026, 2, 10, 11, 0, 0),
        process_id="P_METRICS_DAILY_2026-02-10_B",
        source_outcome_id="outcome-alert-d2-b",
        facts=common_facts,
    )
    await seed_observation(
        timestamp=datetime(2026, 2, 10, 12, 0, 0),
        process_id="P_METRICS_DAILY_2026-02-10_C",
        source_outcome_id="outcome-alert-d2-c",
        facts=common_facts,
    )
    page1 = await client.get(
        "/api/v1/metrics/alerts",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10", "limit": 2, "offset": 0},
    )
    assert page1.status_code == 200
    page1_items = page1.json()["items"]
    assert len(page1_items) == 2
    t0 = datetime.fromisoformat(page1_items[0]["timestamp"])
    t1 = datetime.fromisoformat(page1_items[1]["timestamp"])
    assert t0 >= t1
    page2 = await client.get(
        "/api/v1/metrics/alerts",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10", "limit": 2, "offset": 2},
    )
    assert page2.status_code == 200
    page2_items = page2.json()["items"]
    assert len(page2_items) == 1
    assert page2_items[0]["observation_id"] == obs_10.observation_id


def test_guardrail_max_per_day_1_bloqueia_segundo_alerta(monkeypatch, sync_session_factory):
    """
    Valida guardrail de limite diario de alertas.
    """
    target_date = date(2026, 2, 10)
    session = sync_session_factory()
    try:
        session.execute(
            delete(ObservationRecord).where(ObservationRecord.process_id.like("P_METRICS_DAILY_2026-02-10%"))
        )
        session.execute(
            delete(ObservationRecord).where(ObservationRecord.process_id.like("P_TEST_GUARDRAIL_%"))
        )
        session.commit()

        session.add(
            ObservationRecord(
                observation_id="obs-guardrail-source-1",
                timestamp=datetime(2026, 2, 10, 9, 0, 0),
                process_id="P_TEST_GUARDRAIL_1",
                source_outcome_id="outcome-guardrail-source-1",
                facts={
                    "event_type": "cognitive_loop_finished",
                    "pipeline_status": "failed",
                    "termination_reason": "video_failed",
                    "execution_status": "blocked",
                    "actions_executed": 1,
                    "last_action_type": "transcribe_segments",
                },
            )
        )
        session.commit()

        def _persist_observation_direct(observation):
            ts = datetime.fromisoformat(observation.timestamp.replace("Z", "+00:00"))
            local = sync_session_factory()
            try:
                local.merge(
                    ObservationRecord(
                        observation_id=observation.observation_id,
                        timestamp=ts,
                        process_id=observation.process_id,
                        source_outcome_id=observation.source_outcome_id,
                        facts=observation.facts,
                    )
                )
                local.commit()
            finally:
                local.close()

        monkeypatch.setenv("COGNITIVE_ALERT_MAX_PER_DAY", "1")
        monkeypatch.setattr("app.cognitive_metrics._append_minimal_outcome", lambda *_: None)
        monkeypatch.setattr("app.cognitive_metrics.persist_state_from_observation", lambda *_: None)
        monkeypatch.setattr("app.cognitive_metrics.persist_observation", _persist_observation_direct)

        aggregate_daily_metrics_for_date(target_date)
        aggregate_daily_metrics_for_date(target_date)

        alert_rows = (
            session.query(ObservationRecord)
            .filter(ObservationRecord.facts["event_type"].astext == "cognitive_metrics_alert")
            .filter(ObservationRecord.facts["metric_date"].astext == "2026-02-10")
            .all()
        )
        assert len(alert_rows) == 1
    finally:
        session.execute(
            delete(ObservationRecord).where(ObservationRecord.process_id.like("P_METRICS_DAILY_2026-02-10%"))
        )
        session.execute(
            delete(ObservationRecord).where(ObservationRecord.process_id.like("P_TEST_GUARDRAIL_%"))
        )
        session.commit()
        session.close()


@pytest.mark.anyio
async def test_integridade_facts_sem_paths(client, seed_daily_metric, seed_observation):
    """
    Valida que paths proibidos nao vazam nos endpoints de metricas.
    """
    await seed_daily_metric(
        metric_date=date(2026, 2, 10),
        total_runs=1,
        completed_runs=1,
        failed_runs=0,
        blocked_runs=0,
        avg_actions_executed=1.0,
        last_action_type_distribution={"write_artifact": 1},
    )
    await seed_observation(
        timestamp=datetime(2026, 2, 10, 12, 0, 0),
        process_id="P_METRICS_DAILY_2026-02-10_FACTS",
        source_outcome_id="outcome-f1",
        facts={
            "event_type": "cognitive_metrics_alert",
            "metric_date": "2026-02-10",
            "reasons": ["failed_ratio"],
            "raw_video_minio_path": "minio://bucket/raw.mp4",
            "audio_local_path": "/tmp/audio.wav",
        },
    )
    daily = await client.get(
        "/api/v1/metrics/daily",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    alerts = await client.get(
        "/api/v1/metrics/alerts",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    assert daily.status_code == 200
    assert alerts.status_code == 200
    for item in daily.json()["items"]:
        facts = item.get("facts")
        if isinstance(facts, dict):
            assert PROHIBITED_FACT_KEYS.isdisjoint(facts.keys())
    for item in alerts.json()["items"]:
        facts = item.get("facts", {})
        assert PROHIBITED_FACT_KEYS.isdisjoint(facts.keys())


@pytest.mark.anyio
async def test_reasons_dedup_sorted(client, seed_observation):
    """
    Valida dedupe e ordenacao de reasons no endpoint de alertas.
    """
    await seed_observation(
        timestamp=datetime(2026, 2, 10, 15, 0, 0),
        process_id="P_METRICS_DAILY_2026-02-10_R2",
        source_outcome_id="outcome-f2",
        facts={
            "event_type": "cognitive_metrics_alert",
            "metric_date": "2026-02-10",
            "reasons": ["b", "a", "a"],
        },
    )
    response = await client.get(
        "/api/v1/metrics/alerts",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    assert response.status_code == 200
    items = response.json()["items"]
    target = next(
        (
            it
            for it in items
            if it["metric_date"] == "2026-02-10" and "a" in it["reasons"] and "b" in it["reasons"]
        ),
        None,
    )
    assert target is not None
    assert target["reasons"] == ["a", "b"]
