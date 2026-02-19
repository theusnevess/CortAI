#!/usr/bin/env python
"""
Executa P2-B1 sintetico dentro do container backend (/app).

Este script gera evidencias em .tmp_p2 sem depender de runner externo.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import httpx

from app.cognitive_metrics import SessionLocal
from app.perf.p2b1_synthetic import (
    assert_monotonic_latency,
    count_events_for_date,
    generate_summary_rows,
    seed_synthetic_timing_observations,
    write_summary_csv,
)
from app.tasks.collector_tasks import aggregate_daily_metrics


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Roda P2-B1 sintetico no backend")
    parser.add_argument("--metric-date", default=date.today().isoformat(), help="Data alvo (YYYY-MM-DD)")
    parser.add_argument("--output-dir", default=".tmp_p2", help="Diretorio de saida dos artefatos")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL da API")
    parser.add_argument("--timing-minutes", type=int, default=60, help="Janela de timing para report")
    parser.add_argument("--runner-id", default="synthetic-runner", help="Identificador do runner no CSV")
    parser.add_argument("--sut-host", default="localhost:8000", help="Identificador do SUT no CSV")
    parser.add_argument("--api-workers", default="synthetic", help="Valor informativo no CSV")
    parser.add_argument("--skip-http", action="store_true", help="Pula chamadas HTTP de evidência")
    return parser.parse_args()


def _run_http_assertions(base_url: str, timing_minutes: int, output_dir: Path, expect_alerts: bool) -> None:
    with httpx.Client(timeout=30.0) as client:
        report_resp = client.get(
            f"{base_url}/api/v1/observability/report",
            params={"window_days": 1, "timing_minutes": timing_minutes},
        )
        report_resp.raise_for_status()
        report_payload = report_resp.json()
        assert int(report_payload.get("timing", {}).get("events", 0)) > 0
        assert bool(report_payload.get("slo_daily", {}).get("has_requests")) is True
        if expect_alerts:
            assert int(report_payload.get("slo_alerts", {}).get("count", 0)) > 0
        assert int(report_payload.get("timing", {}).get("bad_duration", -1)) == 0
        assert int(report_payload.get("publish_receipts", {}).get("path_leaks_30d", -1)) == 0
        (output_dir / "report_after_synth.json").write_text(
            json.dumps(report_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        status_resp = client.get(f"{base_url}/api/v1/status", params={"window_days": 1})
        status_resp.raise_for_status()
        (output_dir / "status_after_synth.json").write_text(
            json.dumps(status_resp.json(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def main() -> None:
    args = _parse_args()
    metric_date = date.fromisoformat(args.metric_date)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    direct_rows = generate_summary_rows(
        path_label="direct",
        runner=args.runner_id,
        sut_host=args.sut_host,
        api_workers=args.api_workers,
    )
    edge_rows = generate_summary_rows(
        path_label="edge",
        runner=args.runner_id,
        sut_host=args.sut_host,
        api_workers=args.api_workers,
    )
    assert_monotonic_latency(direct_rows)
    assert_monotonic_latency(edge_rows)
    write_summary_csv(output_dir / "p2_a_summary_direct.csv", direct_rows)
    write_summary_csv(output_dir / "p2_a_summary_edge.csv", edge_rows)

    with SessionLocal() as session:
        inserted = seed_synthetic_timing_observations(session=session, metric_date=metric_date)
    assert inserted > 0

    first = aggregate_daily_metrics(metric_date.isoformat())
    assert first.get("status") == "done"
    with SessionLocal() as session:
        alert_count_first = count_events_for_date(
            session,
            metric_date=metric_date,
            event_type="metrics_slo_alert",
        )

    second = aggregate_daily_metrics(metric_date.isoformat())
    assert second.get("status") == "done"
    with SessionLocal() as session:
        alert_count_second = count_events_for_date(
            session,
            metric_date=metric_date,
            event_type="metrics_slo_alert",
        )
    assert alert_count_second == alert_count_first

    if not args.skip_http:
        _run_http_assertions(
            args.base_url.rstrip("/"),
            args.timing_minutes,
            output_dir,
            expect_alerts=alert_count_second > 0,
        )

    print("P2-B1 sintetico concluido")
    print(f"metric_date={metric_date.isoformat()} inserted={inserted} alerts={alert_count_second}")


if __name__ == "__main__":
    main()

