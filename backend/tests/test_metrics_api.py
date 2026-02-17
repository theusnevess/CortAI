import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
import json

import pytest
from sqlalchemy import delete, select

from app.api.v1.endpoints.metrics import PROHIBITED_FACT_KEYS
from app.cognitive_metrics import aggregate_daily_metrics_for_date
from app.db.models import CognitiveMetricsDaily, MetricsEndpointDaily, ObservationRecord


@pytest.mark.anyio
async def test_daily_sem_dados(client, seed_daily_metric):
    """
    Valida retorno vazio do endpoint /metrics/daily sem dados no periodo.
    """
    await seed_daily_metric(
        metric_date=date(2026, 2, 10),
        total_runs=0,
        completed_runs=0,
        failed_runs=0,
        blocked_runs=0,
        truncated_runs=0,
        truncated_ratio=0,
        avg_actions_executed=0,
        last_action_type_distribution={},
        latency_by_action={},
    )
    response = await client.get(
        "/api/v1/metrics/daily",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("items"), list)
    assert len(payload["items"]) == 1
    item = payload["items"][0]
    assert item["ces_default_version"] == "CES_v1"
    assert set(item["ces_versions"].keys()) == {"CES_v1", "CES_v2", "CES_v3"}
    assert item["ces"] == item["ces_versions"]["CES_v1"]["ces"]
    assert item["ces"] is None
    assert item["ces_versions"]["CES_v2"]["ces"] is None
    assert item["ces_versions"]["CES_v2"]["ces_reason"] == "no_runs"
    assert item["ces_versions"]["CES_v3"]["ces"] is None
    assert item["ces_versions"]["CES_v3"]["ces_reason"] == "no_runs"


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
    assert item["ces_default_version"] == "CES_v1"
    assert set(item["ces_versions"].keys()) == {"CES_v1", "CES_v2", "CES_v3"}
    assert item["ces"] == item["ces_versions"]["CES_v1"]["ces"]
    assert isinstance(item["ces_versions"]["CES_v2"]["ces"], float)
    assert isinstance(item["ces_versions"]["CES_v3"]["ces"], float)


@pytest.mark.anyio
async def test_daily_dynamic_baseline_fallback(client, seed_daily_metric):
    """
    Sem historico elegivel, baseline dinamico deve usar fallback fixo v1.
    """
    await seed_daily_metric(
        metric_date=date(2026, 2, 10),
        total_runs=3,
        completed_runs=3,
        failed_runs=0,
        blocked_runs=0,
        avg_actions_executed=1.0,
        last_action_type_distribution={"write_artifact": 3},
        latency_by_action={},
    )
    response = await client.get(
        "/api/v1/metrics/daily",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    assert response.status_code == 200
    item = response.json()["items"][0]
    baseline = item["latency_dynamic_baseline"]
    assert item["latency_dynamic_baseline_window_days"] == 14
    assert baseline["write_artifact"]["source"] == "fallback_fixed_v1"
    assert baseline["write_artifact"]["budget_ms"] == 3000
    assert baseline["write_artifact"]["samples_used"] == 0


@pytest.mark.anyio
async def test_daily_dynamic_baseline_dynamic_14d(client, seed_daily_metric):
    """
    Com historico elegivel, baseline dinamico usa mediana p95_14d * 1.10.
    """
    await seed_daily_metric(
        metric_date=date(2026, 2, 7),
        total_runs=5,
        completed_runs=5,
        failed_runs=0,
        blocked_runs=0,
        avg_actions_executed=1.0,
        last_action_type_distribution={"write_artifact": 5},
        latency_by_action={"write_artifact": {"n": 10, "p95_ms": 100}},
    )
    await seed_daily_metric(
        metric_date=date(2026, 2, 8),
        total_runs=5,
        completed_runs=5,
        failed_runs=0,
        blocked_runs=0,
        avg_actions_executed=1.0,
        last_action_type_distribution={"write_artifact": 5},
        latency_by_action={"write_artifact": {"n": 10, "p95_ms": 200}},
    )
    await seed_daily_metric(
        metric_date=date(2026, 2, 9),
        total_runs=5,
        completed_runs=5,
        failed_runs=0,
        blocked_runs=0,
        avg_actions_executed=1.0,
        last_action_type_distribution={"write_artifact": 5},
        latency_by_action={"write_artifact": {"n": 10, "p95_ms": 300}},
    )
    # Nao elegivel (n<10) deve ser ignorado.
    await seed_daily_metric(
        metric_date=date(2026, 2, 10),
        total_runs=5,
        completed_runs=5,
        failed_runs=0,
        blocked_runs=0,
        avg_actions_executed=1.0,
        last_action_type_distribution={"write_artifact": 5},
        latency_by_action={"write_artifact": {"n": 9, "p95_ms": 9999}},
    )

    response = await client.get(
        "/api/v1/metrics/daily",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    assert response.status_code == 200
    item = response.json()["items"][0]
    baseline = item["latency_dynamic_baseline"]["write_artifact"]
    # median(100,200,300)=200 -> ceil(200*1.10)=220
    assert baseline["source"] == "dynamic_14d"
    assert baseline["budget_ms"] == 220
    assert baseline["samples_used"] == 3


@pytest.mark.anyio
async def test_daily_ces_v3_usa_budget_dinamico_14d(client, seed_daily_metric):
    """
    CES_v3 deve consumir budget dinamico quando houver baseline elegivel.
    """
    await seed_daily_metric(
        metric_date=date(2026, 2, 7),
        total_runs=5,
        completed_runs=5,
        failed_runs=0,
        blocked_runs=0,
        avg_actions_executed=1.0,
        last_action_type_distribution={"write_artifact": 5},
        latency_by_action={"write_artifact": {"n": 10, "p95_ms": 100}},
    )
    await seed_daily_metric(
        metric_date=date(2026, 2, 8),
        total_runs=5,
        completed_runs=5,
        failed_runs=0,
        blocked_runs=0,
        avg_actions_executed=1.0,
        last_action_type_distribution={"write_artifact": 5},
        latency_by_action={"write_artifact": {"n": 10, "p95_ms": 200}},
    )
    await seed_daily_metric(
        metric_date=date(2026, 2, 9),
        total_runs=5,
        completed_runs=5,
        failed_runs=0,
        blocked_runs=0,
        avg_actions_executed=1.0,
        last_action_type_distribution={"write_artifact": 5},
        latency_by_action={"write_artifact": {"n": 10, "p95_ms": 300}},
    )
    await seed_daily_metric(
        metric_date=date(2026, 2, 10),
        total_runs=5,
        completed_runs=5,
        failed_runs=0,
        blocked_runs=0,
        avg_actions_executed=1.0,
        last_action_type_distribution={"write_artifact": 5},
        latency_by_action={"write_artifact": {"n": 10, "p95_ms": 400}},
    )

    response = await client.get(
        "/api/v1/metrics/daily",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    assert response.status_code == 200
    item = response.json()["items"][0]
    ces_v3_budget = item["ces_versions"]["CES_v3"]["budgets_used"]["write_artifact"]
    ces_v1_budget = item["ces_versions"]["CES_v1"]["budgets_used"]["write_artifact"]
    assert ces_v3_budget["source"] == "dynamic_14d"
    assert ces_v3_budget["budget_ms"] == 220
    assert ces_v1_budget["budget_ms"] == 440


@pytest.mark.anyio
async def test_daily_ces_v3_fallback_para_budget_fixo(client, seed_daily_metric):
    """
    Sem historico elegivel, CES_v3 deve usar fallback para budget fixo v1.
    """
    await seed_daily_metric(
        metric_date=date(2026, 2, 10),
        total_runs=5,
        completed_runs=5,
        failed_runs=0,
        blocked_runs=0,
        avg_actions_executed=1.0,
        last_action_type_distribution={"write_artifact": 5},
        latency_by_action={"write_artifact": {"n": 10, "p95_ms": 1000}},
    )

    response = await client.get(
        "/api/v1/metrics/daily",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    assert response.status_code == 200
    item = response.json()["items"][0]
    ces_v3_budget = item["ces_versions"]["CES_v3"]["budgets_used"]["write_artifact"]
    assert ces_v3_budget["source"] == "fixed_v1"
    assert ces_v3_budget["budget_ms"] == 3000


@pytest.mark.anyio
async def test_overview_deterministico_mesma_request_mesmo_payload(client, seed_daily_metric):
    """
    Mesma request deve retornar payload identico.
    """
    await seed_daily_metric(
        metric_date=date(2026, 2, 10),
        total_runs=4,
        completed_runs=3,
        failed_runs=1,
        blocked_runs=0,
        avg_actions_executed=1.0,
        last_action_type_distribution={"write_artifact": 4},
        latency_by_action={"write_artifact": {"n": 10, "p95_ms": 500}},
    )
    params = {"start_date": "2026-02-10", "end_date": "2026-02-10"}
    first = await client.get("/api/v1/metrics/overview", params=params)
    second = await client.get("/api/v1/metrics/overview", params=params)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


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
    assert summary["ces_default_version"] == "CES_v1"
    assert set(summary["ces_versions"].keys()) == {"CES_v1", "CES_v2", "CES_v3"}
    assert summary["ces"] == summary["ces_versions"]["CES_v1"]["ces"]
    assert all(set(item["ces_versions"].keys()) == {"CES_v1", "CES_v2", "CES_v3"} for item in items)


@pytest.mark.anyio
async def test_overview_ces_bad_days_in_window(client, seed_daily_metric, monkeypatch):
    """
    Valida contador de dias ruins de CES com janela/threshold do alerta.
    """
    monkeypatch.setenv("COGNITIVE_ALERT_CES_WINDOW_DAYS", "3")
    monkeypatch.setenv("COGNITIVE_ALERT_CES_THRESHOLD", "90")

    # 2026-02-08: ruim
    await seed_daily_metric(
        metric_date=date(2026, 2, 8),
        total_runs=10,
        completed_runs=7,
        failed_runs=0,
        blocked_runs=3,
        avg_actions_executed=1.0,
        last_action_type_distribution={"write_artifact": 10},
    )
    # 2026-02-09: sem runs (nao conta)
    await seed_daily_metric(
        metric_date=date(2026, 2, 9),
        total_runs=0,
        completed_runs=0,
        failed_runs=0,
        blocked_runs=0,
        avg_actions_executed=0.0,
        last_action_type_distribution={},
    )
    # 2026-02-10: bom
    await seed_daily_metric(
        metric_date=date(2026, 2, 10),
        total_runs=10,
        completed_runs=10,
        failed_runs=0,
        blocked_runs=0,
        avg_actions_executed=1.0,
        last_action_type_distribution={"write_artifact": 10},
    )

    response = await client.get(
        "/api/v1/metrics/overview",
        params={"start_date": "2026-02-08", "end_date": "2026-02-10"},
    )
    assert response.status_code == 200
    summary = response.json()["summary"]
    # Dias validos: 08(ruim), 10(bom). Ultimos 3 validos => 2 efetivos e 1 ruim.
    assert summary["ces_window_days"] == 3
    assert summary["ces_window_effective_days"] == 2
    assert summary["ces_threshold"] == 90.0
    assert summary["ces_bad_days_required"] == 3
    assert summary["ces_bad_days_in_window"] == 1
    assert summary["ces_bad_days_ratio"] == 0.5


@pytest.mark.anyio
async def test_overview_ces_window_sem_runs_ratio_null(client, seed_daily_metric, monkeypatch):
    """
    Valida janela CES sem dias validos: effective_days=0 e ratio nulo.
    """
    monkeypatch.setenv("COGNITIVE_ALERT_CES_WINDOW_DAYS", "7")
    monkeypatch.setenv("COGNITIVE_ALERT_CES_THRESHOLD", "90")
    monkeypatch.setenv("COGNITIVE_ALERT_CES_BAD_DAYS", "3")

    await seed_daily_metric(
        metric_date=date(2026, 2, 10),
        total_runs=0,
        completed_runs=0,
        failed_runs=0,
        blocked_runs=0,
        avg_actions_executed=0.0,
        last_action_type_distribution={},
    )

    response = await client.get(
        "/api/v1/metrics/overview",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    assert response.status_code == 200
    summary = response.json()["summary"]
    assert summary["ces_window_days"] == 7
    assert summary["ces_window_effective_days"] == 0
    assert summary["ces_bad_days_in_window"] == 0
    assert summary["ces_bad_days_ratio"] is None


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
async def test_runs_range_vazio(client):
    """
    Valida /metrics/runs sem dados no periodo.
    """
    response = await client.get(
        "/api/v1/metrics/runs",
        params={"start_date": "2099-01-01", "end_date": "2099-01-01", "limit": 10, "offset": 0},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["items"] == []
    assert payload["total"] == 0
    assert payload["limit"] == 10
    assert payload["offset"] == 0


@pytest.mark.anyio
async def test_runs_guardrail_limit_too_high(client):
    """
    Valida guardrail de limit maximo no /metrics/runs.
    """
    response = await client.get(
        "/api/v1/metrics/runs",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10", "limit": 201},
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error_type"] == "LimitTooHigh"
    assert detail["limit_requested"] == 201
    assert detail["limit_max"] == 200


@pytest.mark.anyio
async def test_runs_guardrail_range_too_large(client):
    """
    Valida guardrail de range maximo (31 dias) no /metrics/runs.
    """
    response = await client.get(
        "/api/v1/metrics/runs",
        params={"start_date": "2026-01-01", "end_date": "2026-04-01", "limit": 50},
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error_type"] == "RangeTooLarge"
    assert detail["range_days"] == 91
    assert detail["range_max"] == 31


@pytest.mark.anyio
async def test_runs_emite_metrics_endpoint_timing(client, seed_observation, db_session):
    """
    Cada request no /metrics/runs deve emitir um timing event.
    """
    await seed_observation(
        timestamp=datetime(2026, 2, 10, 12, 0, 0),
        process_id="P_RUN_TIMING_1",
        source_outcome_id="outcome-run-timing-1",
        facts={
            "event_type": "cognitive_loop_finished",
            "pipeline_status": "completed",
            "actions_executed": 1,
        },
    )

    response = await client.get(
        "/api/v1/metrics/runs",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10", "limit": 50, "offset": 0},
    )
    assert response.status_code == 200

    stmt = (
        select(ObservationRecord)
        .where(ObservationRecord.facts["event_type"].astext == "metrics_endpoint_timing")
        .where(ObservationRecord.facts["endpoint"].astext == "/api/v1/metrics/runs")
        .order_by(ObservationRecord.created_at.desc())
        .limit(1)
    )
    rows = (await db_session.execute(stmt)).scalars().all()
    assert len(rows) == 1
    facts = rows[0].facts
    assert facts["method"] == "GET"
    assert facts["status_code"] == 200
    assert isinstance(facts["duration_ms"], int)
    assert "query_fingerprint" in facts
    assert "metric_date" in facts


@pytest.mark.anyio
async def test_runs_um_completed(client, seed_observation):
    """
    Valida CES_run_v1 para run completed.
    """
    await seed_observation(
        timestamp=datetime(2026, 2, 10, 12, 0, 0),
        process_id="P_RUN_COMPLETED_1",
        source_outcome_id="outcome-run-1",
        facts={
            "event_type": "cognitive_loop_finished",
            "pipeline_status": "completed",
            "actions_executed": 2,
            "termination_reason": "pipeline_complete",
        },
    )
    response = await client.get(
        "/api/v1/metrics/runs",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["process_id"] == "P_RUN_COMPLETED_1"
    assert item["pipeline_status"] == "completed"
    assert item["ces_run_version"] == "CES_run_v1"
    assert item["ces_run_reason"] is None
    assert item["latency_measured"] is False
    assert item["budgets_used"] == {}
    assert item["ces_run_components"]["latency"] == 1.0
    assert item["latency_pairs_used"] == 0
    assert item["latency_pairs_ignored"] == 0
    assert item["latency_pairs_inverted"] == 0
    assert isinstance(item["ces_run"], float)


@pytest.mark.anyio
async def test_runs_dedupe_por_process_id(client, seed_observation):
    """
    Valida dedupe por process_id usando o registro mais recente.
    """
    await seed_observation(
        timestamp=datetime(2026, 2, 10, 10, 0, 0),
        process_id="P_RUN_DEDUPE_1",
        source_outcome_id="outcome-run-old",
        facts={
            "event_type": "cognitive_loop_finished",
            "pipeline_status": "failed",
            "actions_executed": 1,
        },
    )
    await seed_observation(
        timestamp=datetime(2026, 2, 10, 12, 0, 0),
        process_id="P_RUN_DEDUPE_1",
        source_outcome_id="outcome-run-new",
        facts={
            "event_type": "cognitive_loop_finished",
            "pipeline_status": "published",
            "actions_executed": 1,
        },
    )
    response = await client.get(
        "/api/v1/metrics/runs",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    assert response.status_code == 200
    items = response.json()["items"]
    selected = next(i for i in items if i["process_id"] == "P_RUN_DEDUPE_1")
    assert selected["pipeline_status"] == "published"


@pytest.mark.anyio
async def test_runs_ordenacao_desc(client, seed_observation):
    """
    Valida ordenacao por timestamp_finished desc.
    """
    await seed_observation(
        timestamp=datetime(2026, 2, 10, 9, 0, 0),
        process_id="P_RUN_ORDER_OLD",
        source_outcome_id="outcome-order-old",
        facts={
            "event_type": "cognitive_loop_finished",
            "pipeline_status": "completed",
            "actions_executed": 1,
        },
    )
    await seed_observation(
        timestamp=datetime(2026, 2, 10, 13, 0, 0),
        process_id="P_RUN_ORDER_NEW",
        source_outcome_id="outcome-order-new",
        facts={
            "event_type": "cognitive_loop_finished",
            "pipeline_status": "completed",
            "actions_executed": 1,
        },
    )
    response = await client.get(
        "/api/v1/metrics/runs",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    assert response.status_code == 200
    items = response.json()["items"]
    idx_new = next(i for i, item in enumerate(items) if item["process_id"] == "P_RUN_ORDER_NEW")
    idx_old = next(i for i, item in enumerate(items) if item["process_id"] == "P_RUN_ORDER_OLD")
    assert idx_new < idx_old


def _write_jsonl(path, rows):
    """
    Escreve linhas JSONL para fixtures de latencia em testes.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row))
            f.write("\n")


@pytest.mark.anyio
async def test_runs_latency_measured_true_com_n_elegivel(client, seed_observation, monkeypatch, tmp_path):
    """
    Mede latencia real quando existe acao elegivel com n >= 3 no run.
    """
    process_id = "P_RUN_LAT_OK"
    await seed_observation(
        timestamp=datetime(2026, 2, 10, 12, 10, 0),
        process_id=process_id,
        source_outcome_id="outcome-run-lat-ok",
        facts={
            "event_type": "cognitive_loop_finished",
            "pipeline_status": "completed",
            "actions_executed": 2,
        },
    )

    monkeypatch.setenv("CORTAI_STORAGE_DIR", str(tmp_path))
    _write_jsonl(
        tmp_path / "decision_log.jsonl",
        [
            {
                "process_id": process_id,
                "decision_id": "d1",
                "timestamp": "2026-02-10T12:00:00Z",
                "action": {"type": "transcribe_segments"},
            },
            {
                "process_id": process_id,
                "decision_id": "d2",
                "timestamp": "2026-02-10T12:01:00Z",
                "action": {"type": "transcribe_segments"},
            },
            {
                "process_id": process_id,
                "decision_id": "d3",
                "timestamp": "2026-02-10T12:02:00Z",
                "action": {"type": "transcribe_segments"},
            },
        ],
    )
    _write_jsonl(
        tmp_path / "outcome_log.jsonl",
        [
            {
                "process_id": process_id,
                "source_decision_id": "d1",
                "timestamp": "2026-02-10T12:00:35Z",
                "metrics": {"last_action_type": "transcribe_segments"},
            },
            {
                "process_id": process_id,
                "source_decision_id": "d2",
                "timestamp": "2026-02-10T12:01:35Z",
                "metrics": {"last_action_type": "transcribe_segments"},
            },
            {
                "process_id": process_id,
                "source_decision_id": "d3",
                "timestamp": "2026-02-10T12:02:35Z",
                "metrics": {"last_action_type": "transcribe_segments"},
            },
        ],
    )

    response = await client.get(
        "/api/v1/metrics/runs",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    assert response.status_code == 200
    item = next(i for i in response.json()["items"] if i["process_id"] == process_id)
    assert item["latency_measured"] is True
    assert item["budgets_used"]["transcribe_segments"]["n"] == 3
    assert item["ces_run_components"]["latency"] < 1.0
    assert item["latency_pairs_used"] >= 3
    assert item["latency_pairs_inverted"] == 0


@pytest.mark.anyio
async def test_runs_latency_fallback_quando_n_menor_que_3(client, seed_observation, monkeypatch, tmp_path):
    """
    Mantem fallback de latencia quando n elegivel e insuficiente.
    """
    process_id = "P_RUN_LAT_LOW_N"
    await seed_observation(
        timestamp=datetime(2026, 2, 10, 12, 10, 0),
        process_id=process_id,
        source_outcome_id="outcome-run-lat-low",
        facts={
            "event_type": "cognitive_loop_finished",
            "pipeline_status": "completed",
            "actions_executed": 2,
        },
    )

    monkeypatch.setenv("CORTAI_STORAGE_DIR", str(tmp_path))
    _write_jsonl(
        tmp_path / "decision_log.jsonl",
        [
            {
                "process_id": process_id,
                "decision_id": "d1",
                "timestamp": "2026-02-10T12:00:00Z",
                "action": {"type": "transcribe_segments"},
            },
            {
                "process_id": process_id,
                "decision_id": "d2",
                "timestamp": "2026-02-10T12:01:00Z",
                "action": {"type": "transcribe_segments"},
            },
        ],
    )
    _write_jsonl(
        tmp_path / "outcome_log.jsonl",
        [
            {
                "process_id": process_id,
                "source_decision_id": "d1",
                "timestamp": "2026-02-10T12:00:05Z",
                "metrics": {"last_action_type": "transcribe_segments"},
            },
            {
                "process_id": process_id,
                "source_decision_id": "d2",
                "timestamp": "2026-02-10T12:01:05Z",
                "metrics": {"last_action_type": "transcribe_segments"},
            },
        ],
    )

    response = await client.get(
        "/api/v1/metrics/runs",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    assert response.status_code == 200
    item = next(i for i in response.json()["items"] if i["process_id"] == process_id)
    assert item["latency_measured"] is False
    assert item["ces_run_components"]["latency"] == 1.0
    assert item["budgets_used"] == {}
    assert item["latency_pairs_used"] == 2
    assert item["latency_pairs_inverted"] == 0


@pytest.mark.anyio
async def test_runs_latency_exclui_unknown(client, seed_observation, monkeypatch, tmp_path):
    """
    Garante que unknown nao participa do score de latencia do run.
    """
    process_id = "P_RUN_LAT_UNKNOWN"
    await seed_observation(
        timestamp=datetime(2026, 2, 10, 12, 10, 0),
        process_id=process_id,
        source_outcome_id="outcome-run-lat-unknown",
        facts={
            "event_type": "cognitive_loop_finished",
            "pipeline_status": "completed",
            "actions_executed": 2,
        },
    )

    monkeypatch.setenv("CORTAI_STORAGE_DIR", str(tmp_path))
    _write_jsonl(
        tmp_path / "decision_log.jsonl",
        [
            {
                "process_id": process_id,
                "decision_id": "d1",
                "timestamp": "2026-02-10T12:00:00Z",
                "action": {"type": "transcribe_segments"},
            },
            {
                "process_id": process_id,
                "decision_id": "d2",
                "timestamp": "2026-02-10T12:01:00Z",
                "action": {"type": "transcribe_segments"},
            },
            {
                "process_id": process_id,
                "decision_id": "d3",
                "timestamp": "2026-02-10T12:02:00Z",
                "action": {"type": "transcribe_segments"},
            },
            {
                "process_id": process_id,
                "decision_id": "u1",
                "timestamp": "2026-02-10T12:03:00Z",
                "action": {"type": "unknown"},
            },
            {
                "process_id": process_id,
                "decision_id": "u2",
                "timestamp": "2026-02-10T12:04:00Z",
                "action": {"type": "unknown"},
            },
            {
                "process_id": process_id,
                "decision_id": "u3",
                "timestamp": "2026-02-10T12:05:00Z",
                "action": {"type": "unknown"},
            },
        ],
    )
    _write_jsonl(
        tmp_path / "outcome_log.jsonl",
        [
            {
                "process_id": process_id,
                "source_decision_id": "d1",
                "timestamp": "2026-02-10T12:00:35Z",
                "metrics": {"last_action_type": "transcribe_segments"},
            },
            {
                "process_id": process_id,
                "source_decision_id": "d2",
                "timestamp": "2026-02-10T12:01:35Z",
                "metrics": {"last_action_type": "transcribe_segments"},
            },
            {
                "process_id": process_id,
                "source_decision_id": "d3",
                "timestamp": "2026-02-10T12:02:35Z",
                "metrics": {"last_action_type": "transcribe_segments"},
            },
            {
                "process_id": process_id,
                "source_decision_id": "u1",
                "timestamp": "2026-02-10T12:03:50Z",
                "metrics": {"last_action_type": "unknown"},
            },
            {
                "process_id": process_id,
                "source_decision_id": "u2",
                "timestamp": "2026-02-10T12:04:50Z",
                "metrics": {"last_action_type": "unknown"},
            },
            {
                "process_id": process_id,
                "source_decision_id": "u3",
                "timestamp": "2026-02-10T12:05:50Z",
                "metrics": {"last_action_type": "unknown"},
            },
        ],
    )

    response = await client.get(
        "/api/v1/metrics/runs",
        params={"start_date": "2026-02-10", "end_date": "2026-02-10"},
    )
    assert response.status_code == 200
    item = next(i for i in response.json()["items"] if i["process_id"] == process_id)
    assert item["latency_measured"] is True
    assert "transcribe_segments" in item["budgets_used"]
    assert "unknown" not in item["budgets_used"]
    assert item["latency_pairs_used"] == 3


@pytest.mark.anyio
async def test_run_debug_not_found(client):
    """
    Retorna 404 quando process_id nao possui cognitive_loop_finished.
    """
    response = await client.get("/api/v1/metrics/runs/P_RUN_DEBUG_NOT_FOUND")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_run_debug_view_basica(client, seed_observation):
    """
    Retorna visao de debug read-only para um run existente.
    """
    await seed_observation(
        timestamp=datetime(2026, 2, 10, 16, 0, 0),
        process_id="P_RUN_DEBUG_1",
        source_outcome_id="outcome-run-debug-1",
        facts={
            "event_type": "cognitive_loop_finished",
            "pipeline_status": "blocked",
            "execution_status": "blocked",
            "source_decision_id": "decision-run-debug-1",
            "actions_executed": 1,
        },
    )
    response = await client.get("/api/v1/metrics/runs/P_RUN_DEBUG_1")
    assert response.status_code == 200
    payload = response.json()
    run_summary = payload["run_summary"]
    assert run_summary["process_id"] == "P_RUN_DEBUG_1"
    assert run_summary["pipeline_status"] == "blocked"
    assert run_summary["execution_status"] == "blocked"
    assert isinstance(run_summary["latency_pairs_used"], int)
    assert isinstance(run_summary["latency_pairs_ignored"], int)
    assert isinstance(run_summary["latency_pairs_inverted"], int)
    assert payload["links"]["observation_id"] is not None
    assert payload["links"]["source_outcome_id"] == "outcome-run-debug-1"
    assert "latency_breakdown" in payload
    assert isinstance(payload["missing_fields"], list)


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


def test_metrics_slo_aggregate_daily_cria_linha_por_endpoint(sync_session_factory):
    """
    Agregacao diaria de timings deve persistir linha por endpoint.
    """
    target_date = date(2026, 5, 1)
    endpoint = "/api/v1/metrics/runs"
    session = sync_session_factory()
    try:
        MetricsEndpointDaily.__table__.create(bind=session.get_bind(), checkfirst=True)
        session.execute(
            delete(ObservationRecord).where(
                ObservationRecord.facts["event_type"].astext == "metrics_endpoint_timing"
            )
        )
        session.execute(delete(MetricsEndpointDaily).where(MetricsEndpointDaily.metric_date == target_date))
        session.commit()

        for i in range(20):
            session.add(
                ObservationRecord(
                    observation_id=str(uuid.uuid4()),
                    timestamp=datetime(2026, 5, 1, 12, 0, i),
                    process_id=f"P_TIMING_AGG_{i}",
                    source_outcome_id=str(uuid.uuid4()),
                    facts={
                        "event_type": "metrics_endpoint_timing",
                        "endpoint": endpoint,
                        "method": "GET",
                        "status_code": 200,
                        "duration_ms": 100 + i,
                        "query_fingerprint": "limit=50&offset=0&range=7d",
                        "metric_date": target_date.isoformat(),
                    },
                )
            )
        session.commit()

        aggregate_daily_metrics_for_date(target_date)

        row = (
            session.query(MetricsEndpointDaily)
            .filter(MetricsEndpointDaily.metric_date == target_date)
            .filter(MetricsEndpointDaily.endpoint == endpoint)
            .one_or_none()
        )
        assert row is not None
        assert row.count_requests == 20
        assert isinstance(row.p95_ms, int)
        assert isinstance(row.p99_ms, int)
        assert float(row.error_rate) == 0.0
    finally:
        session.execute(
            delete(ObservationRecord).where(ObservationRecord.process_id.like("P_TIMING_AGG_%"))
        )
        session.execute(delete(MetricsEndpointDaily).where(MetricsEndpointDaily.metric_date == target_date))
        session.commit()
        session.close()


def test_metrics_slo_alert_idempotente_por_endpoint(monkeypatch, sync_session_factory):
    """
    Alerta de SLO deve ser emitido uma unica vez por endpoint/reason no dia.
    """
    target_date = date(2026, 5, 2)
    endpoint = "/api/v1/metrics/runs"
    session = sync_session_factory()
    try:
        MetricsEndpointDaily.__table__.create(bind=session.get_bind(), checkfirst=True)
        session.execute(
            delete(ObservationRecord).where(
                ObservationRecord.facts["event_type"].astext.in_(["metrics_endpoint_timing", "metrics_slo_alert"])
            )
        )
        session.execute(delete(MetricsEndpointDaily).where(MetricsEndpointDaily.metric_date == target_date))
        session.commit()

        monkeypatch.setenv("METRICS_ALERT_MAX_PER_DAY", "5")

        for i in range(20):
            # Duracao alta para forcar breach de p95/p99.
            session.add(
                ObservationRecord(
                    observation_id=str(uuid.uuid4()),
                    timestamp=datetime(2026, 5, 2, 10, 0, i),
                    process_id=f"P_TIMING_ALERT_{i}",
                    source_outcome_id=str(uuid.uuid4()),
                    facts={
                        "event_type": "metrics_endpoint_timing",
                        "endpoint": endpoint,
                        "method": "GET",
                        "status_code": 200,
                        "duration_ms": 2500 + i,
                        "query_fingerprint": "limit=50&offset=0&range=7d",
                        "metric_date": target_date.isoformat(),
                    },
                )
            )
        session.commit()

        aggregate_daily_metrics_for_date(target_date)
        aggregate_daily_metrics_for_date(target_date)

        rows = (
            session.query(ObservationRecord)
            .filter(ObservationRecord.facts["event_type"].astext == "metrics_slo_alert")
            .filter(ObservationRecord.facts["metric_date"].astext == target_date.isoformat())
            .filter(ObservationRecord.facts["endpoint"].astext == endpoint)
            .all()
        )
        assert len(rows) == 1
        reasons = rows[0].facts.get("reasons", [])
        assert any(reason in reasons for reason in ["p95_slo_breach", "p99_slo_breach"])
    finally:
        session.execute(
            delete(ObservationRecord).where(ObservationRecord.process_id.like("P_TIMING_ALERT_%"))
        )
        session.execute(
            delete(ObservationRecord).where(ObservationRecord.process_id.like("P_METRICS_SLO_%"))
        )
        session.execute(delete(MetricsEndpointDaily).where(MetricsEndpointDaily.metric_date == target_date))
        session.commit()
        session.close()


def _seed_loop_finished_row(session, *, metric_date: date, process_id: str, blocked: bool) -> None:
    """
    Insere observation final do loop para alimentar agregacao diaria.
    """
    if blocked:
        execution_status = "blocked"
        pipeline_status = "blocked"
        termination_reason = "blocked"
    else:
        execution_status = "success"
        pipeline_status = "completed"
        termination_reason = "pipeline_complete"

    session.add(
        ObservationRecord(
            observation_id=str(uuid.uuid4()),
            timestamp=datetime(metric_date.year, metric_date.month, metric_date.day, 12, 0, 0),
            process_id=process_id,
            source_outcome_id=str(uuid.uuid4()),
            facts={
                "event_type": "cognitive_loop_finished",
                "execution_status": execution_status,
                "pipeline_status": pipeline_status,
                "termination_reason": termination_reason,
                "actions_executed": 1,
                "last_action_type": "write_artifact",
                "terminated": True,
            },
        )
    )


def _wire_alert_persist(monkeypatch, sync_session_factory):
    """
    Redireciona persistencia de alerta para o banco do teste.
    """
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

    monkeypatch.setattr("app.cognitive_metrics._append_minimal_outcome", lambda *_: None)
    monkeypatch.setattr("app.cognitive_metrics.persist_state_from_observation", lambda *_: None)
    monkeypatch.setattr("app.cognitive_metrics.persist_observation", _persist_observation_direct)


def test_ces_regression_nao_dispara_com_6_dias(monkeypatch, sync_session_factory):
    """
    Nao emite alerta CES com historico insuficiente (<= 6 dias com runs).
    """
    _wire_alert_persist(monkeypatch, sync_session_factory)
    monkeypatch.setenv("COGNITIVE_ALERT_CES_ENABLED", "1")
    monkeypatch.setenv("COGNITIVE_ALERT_CES_THRESHOLD", "85")
    monkeypatch.setenv("COGNITIVE_ALERT_CES_BAD_DAYS", "3")
    monkeypatch.setenv("COGNITIVE_ALERT_CES_WINDOW_DAYS", "7")
    monkeypatch.setenv("COGNITIVE_ALERT_MAX_PER_DAY", "5")

    start = date(2026, 2, 20)
    prefix = "P_CES_A_"
    session = sync_session_factory()
    try:
        session.execute(delete(ObservationRecord).where(ObservationRecord.process_id.like(f"{prefix}%")))
        session.execute(delete(ObservationRecord).where(ObservationRecord.process_id.like("P_METRICS_DAILY_%")))
        session.execute(
            delete(CognitiveMetricsDaily).where(
                CognitiveMetricsDaily.metric_date >= start,
                CognitiveMetricsDaily.metric_date < start + timedelta(days=6),
            )
        )
        for i in range(6):
            d = start + timedelta(days=i)
            _seed_loop_finished_row(session, metric_date=d, process_id=f"{prefix}{i}", blocked=(i < 3))
        session.commit()
        for i in range(6):
            aggregate_daily_metrics_for_date(start + timedelta(days=i))

        count = (
            session.query(ObservationRecord)
            .filter(ObservationRecord.facts["event_type"].astext == "cognitive_metrics_alert")
            .filter(ObservationRecord.facts["reasons"].contains(["ces_regression:CES_v1"]))
            .count()
        )
        assert count == 0
    finally:
        session.execute(delete(ObservationRecord).where(ObservationRecord.process_id.like(f"{prefix}%")))
        session.execute(delete(ObservationRecord).where(ObservationRecord.process_id.like("P_METRICS_DAILY_%")))
        session.execute(
            delete(CognitiveMetricsDaily).where(
                CognitiveMetricsDaily.metric_date >= start,
                CognitiveMetricsDaily.metric_date < start + timedelta(days=6),
            )
        )
        session.commit()
        session.close()


def test_ces_regression_dispara_com_3_de_7(monkeypatch, sync_session_factory):
    """
    Emite alerta CES quando janela de 7 dias possui ao menos 3 dias ruins.
    """
    _wire_alert_persist(monkeypatch, sync_session_factory)
    monkeypatch.setenv("COGNITIVE_ALERT_CES_ENABLED", "1")
    monkeypatch.setenv("COGNITIVE_ALERT_CES_THRESHOLD", "85")
    monkeypatch.setenv("COGNITIVE_ALERT_CES_BAD_DAYS", "3")
    monkeypatch.setenv("COGNITIVE_ALERT_CES_WINDOW_DAYS", "7")
    monkeypatch.setenv("COGNITIVE_ALERT_MAX_PER_DAY", "5")

    start = date(2026, 3, 1)
    target_day = start + timedelta(days=6)
    prefix = "P_CES_B_"
    session = sync_session_factory()
    try:
        session.execute(delete(ObservationRecord).where(ObservationRecord.process_id.like(f"{prefix}%")))
        session.execute(delete(ObservationRecord).where(ObservationRecord.process_id.like("P_METRICS_DAILY_%")))
        session.execute(
            delete(CognitiveMetricsDaily).where(
                CognitiveMetricsDaily.metric_date >= start,
                CognitiveMetricsDaily.metric_date <= target_day,
            )
        )
        for i in range(7):
            d = start + timedelta(days=i)
            _seed_loop_finished_row(session, metric_date=d, process_id=f"{prefix}{i}", blocked=(i < 3))
        session.commit()
        for i in range(7):
            aggregate_daily_metrics_for_date(start + timedelta(days=i))

        rows = (
            session.query(ObservationRecord)
            .filter(ObservationRecord.facts["event_type"].astext == "cognitive_metrics_alert")
            .filter(ObservationRecord.facts["metric_date"].astext == target_day.isoformat())
            .filter(ObservationRecord.facts["reasons"].contains(["ces_regression:CES_v1"]))
            .all()
        )
        assert len(rows) == 1
    finally:
        session.execute(delete(ObservationRecord).where(ObservationRecord.process_id.like(f"{prefix}%")))
        session.execute(delete(ObservationRecord).where(ObservationRecord.process_id.like("P_METRICS_DAILY_%")))
        session.execute(
            delete(CognitiveMetricsDaily).where(
                CognitiveMetricsDaily.metric_date >= start,
                CognitiveMetricsDaily.metric_date <= target_day,
            )
        )
        session.commit()
        session.close()


def test_ces_regression_idempotencia_e_guardrail(monkeypatch, sync_session_factory):
    """
    Garante idempotencia por (metric_date, reason) e respeito ao maximo diario.
    """
    _wire_alert_persist(monkeypatch, sync_session_factory)
    monkeypatch.setenv("COGNITIVE_ALERT_CES_ENABLED", "1")
    monkeypatch.setenv("COGNITIVE_ALERT_CES_THRESHOLD", "85")
    monkeypatch.setenv("COGNITIVE_ALERT_CES_BAD_DAYS", "3")
    monkeypatch.setenv("COGNITIVE_ALERT_CES_WINDOW_DAYS", "7")
    monkeypatch.setenv("COGNITIVE_ALERT_MAX_PER_DAY", "1")

    start = date(2026, 4, 1)
    target_day = start + timedelta(days=6)
    prefix = "P_CES_C_"
    session = sync_session_factory()
    try:
        session.execute(delete(ObservationRecord).where(ObservationRecord.process_id.like(f"{prefix}%")))
        session.execute(delete(ObservationRecord).where(ObservationRecord.process_id.like("P_METRICS_DAILY_%")))
        session.execute(
            delete(CognitiveMetricsDaily).where(
                CognitiveMetricsDaily.metric_date >= start,
                CognitiveMetricsDaily.metric_date <= target_day,
            )
        )
        # Primeiros 6 dias criam historico ruim. Dia alvo tambem e blocked para competir com alerta blocked_runs.
        for i in range(7):
            d = start + timedelta(days=i)
            _seed_loop_finished_row(session, metric_date=d, process_id=f"{prefix}{i}", blocked=(i < 3 or i == 6))
        session.commit()
        for i in range(7):
            aggregate_daily_metrics_for_date(start + timedelta(days=i))
        aggregate_daily_metrics_for_date(target_day)

        day_rows = (
            session.query(ObservationRecord)
            .filter(ObservationRecord.facts["event_type"].astext == "cognitive_metrics_alert")
            .filter(ObservationRecord.facts["metric_date"].astext == target_day.isoformat())
            .all()
        )
        ces_rows = [
            row for row in day_rows
            if isinstance(row.facts.get("reasons"), list) and "ces_regression:CES_v1" in row.facts["reasons"]
        ]
        assert len(day_rows) == 1
        assert len(ces_rows) in (0, 1)
    finally:
        session.execute(delete(ObservationRecord).where(ObservationRecord.process_id.like(f"{prefix}%")))
        session.execute(delete(ObservationRecord).where(ObservationRecord.process_id.like("P_METRICS_DAILY_%")))
        session.execute(
            delete(CognitiveMetricsDaily).where(
                CognitiveMetricsDaily.metric_date >= start,
                CognitiveMetricsDaily.metric_date <= target_day,
            )
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
