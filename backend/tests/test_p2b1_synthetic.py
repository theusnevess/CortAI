from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.cognitive_metrics import SessionLocal
from app.db.models import MetricsEndpointDaily, ObservationRecord
from app.main import app
from app.perf.p2b1_synthetic import (
    ENDPOINTS,
    assert_monotonic_latency,
    count_events_for_date,
    generate_summary_rows,
    seed_synthetic_timing_observations,
    write_summary_csv,
)
from app.tasks.collector_tasks import aggregate_daily_metrics


def _count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        next(reader)  # header
        return sum(1 for _ in reader)


def _cleanup_metric_date(metric_date: date) -> None:
    """
    Remove dados sinteticos residuais para manter teste reprodutivel.
    """
    with SessionLocal() as session:
        session.execute(
            delete(ObservationRecord).where(
                ObservationRecord.process_id.like(f"P2B1_SYNTH_{metric_date.isoformat()}_%")
            )
        )
        session.execute(
            delete(ObservationRecord).where(
                ObservationRecord.process_id.like(f"P_METRICS_SLO_{metric_date.isoformat()}_%")
            )
        )
        session.execute(
            delete(MetricsEndpointDaily).where(MetricsEndpointDaily.metric_date == metric_date)
        )
        session.commit()


def test_p2b1_synthetic_csv_shape_and_monotonic(tmp_path):
    direct_rows = generate_summary_rows(path_label="direct")
    edge_rows = generate_summary_rows(path_label="edge")

    assert len(direct_rows) == len(ENDPOINTS) * 3
    assert len(edge_rows) == len(ENDPOINTS) * 3
    assert_monotonic_latency(direct_rows)
    assert_monotonic_latency(edge_rows)

    direct_csv = tmp_path / "p2_a_summary_direct.csv"
    edge_csv = tmp_path / "p2_a_summary_edge.csv"
    write_summary_csv(direct_csv, direct_rows)
    write_summary_csv(edge_csv, edge_rows)

    assert _count_csv_rows(direct_csv) == 9
    assert _count_csv_rows(edge_csv) == 9


def test_p2b1_synthetic_aggregation_alert_dedupe_and_endpoints():
    # Use recent synthetic data to keep report/status window assertions stable over time.
    metric_date = date.today() - timedelta(days=1)
    _cleanup_metric_date(metric_date)
    try:
        with SessionLocal() as session:
            inserted = seed_synthetic_timing_observations(session=session, metric_date=metric_date)
        assert inserted > 0

        result_first = aggregate_daily_metrics(metric_date.isoformat())
        assert result_first["status"] == "done"

        with SessionLocal() as session:
            timing_count = count_events_for_date(
                session,
                metric_date=metric_date,
                event_type="metrics_endpoint_timing",
            )
            alert_count_first = count_events_for_date(
                session,
                metric_date=metric_date,
                event_type="metrics_slo_alert",
            )
            daily_rows = (
                session.query(MetricsEndpointDaily)
                .filter(MetricsEndpointDaily.metric_date == metric_date)
                .all()
            )

        assert timing_count > 0
        assert len(daily_rows) >= 3
        assert alert_count_first > 0

        result_second = aggregate_daily_metrics(metric_date.isoformat())
        assert result_second["status"] == "done"

        with SessionLocal() as session:
            alert_count_second = count_events_for_date(
                session,
                metric_date=metric_date,
                event_type="metrics_slo_alert",
            )
        assert alert_count_second == alert_count_first

        # Evidencia via endpoints apos agregacao sintetica.
        with TestClient(app) as client:
            report_response = client.get(
                "/api/v1/observability/report",
                params={"window_days": 7, "timing_minutes": 60},
            )
            assert report_response.status_code == 200
            report_payload = report_response.json()
            assert int(report_payload["timing"]["events"]) > 0
            assert bool(report_payload["slo_daily"]["has_requests"]) is True
            assert int(report_payload["slo_alerts"]["count"]) > 0
            assert int(report_payload["timing"]["bad_duration"]) == 0
            assert int(report_payload["publish_receipts"]["path_leaks_30d"]) == 0

            status_response = client.get("/api/v1/status", params={"window_days": 7})
            assert status_response.status_code == 200
    finally:
        _cleanup_metric_date(metric_date)
