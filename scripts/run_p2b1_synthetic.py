#!/usr/bin/env python
"""
Executa P2-B1 sintetico para validar pipeline de observabilidade em ambiente local.

Importante:
- Este fluxo NAO substitui P2-B1 estrutural com runner externo.
- O objetivo e validar evidencias, agregacao, dedupe e contratos dos endpoints.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

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
    parser = argparse.ArgumentParser(description="Roda P2-B1 sintetico e gera artefatos em .tmp_p2")
    parser.add_argument("--metric-date", default=date.today().isoformat(), help="Data alvo (YYYY-MM-DD)")
    parser.add_argument("--output-dir", default=".tmp_p2", help="Diretorio de saida dos artefatos")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL da API")
    parser.add_argument("--timing-minutes", type=int, default=60, help="Janela de timing para report")
    parser.add_argument("--runner-id", default="synthetic-runner", help="Identificador do runner no CSV")
    parser.add_argument("--sut-host", default="localhost:8000", help="Identificador do SUT no CSV")
    parser.add_argument("--api-workers", default="synthetic", help="Valor informativo no CSV")
    parser.add_argument("--skip-http", action="store_true", help="Pula chamadas HTTP de evidência")
    return parser.parse_args()


def _assert_http_contracts(report_payload: dict, *, expect_alerts: bool) -> None:
    """
    Valida asserts de evidência descritos no checklist D.
    """
    timing = report_payload.get("timing", {})
    slo_daily = report_payload.get("slo_daily", {})
    slo_alerts = report_payload.get("slo_alerts", {})
    receipts = report_payload.get("publish_receipts", {})
    assert int(timing.get("events", 0)) > 0, "report.timing.events deve ser > 0"
    assert bool(slo_daily.get("has_requests")) is True, "report.slo_daily.has_requests deve ser true"
    if expect_alerts:
        assert int(slo_alerts.get("count", 0)) > 0, "report.slo_alerts.count deve ser > 0 com breach"
    assert int(timing.get("bad_duration", -1)) == 0, "bad_duration deve ser 0"
    assert int(receipts.get("path_leaks_30d", -1)) == 0, "path_leaks_30d deve ser 0"


def _run_http_evidence(
    *,
    base_url: str,
    output_dir: Path,
    timing_minutes: int,
    expect_alerts: bool,
) -> None:
    """
    Coleta evidencias via /observability/report e /status apos agregacao.
    """
    report_path = output_dir / "report_after_synth.json"
    status_path = output_dir / "status_after_synth.json"
    with httpx.Client(timeout=30.0) as client:
        report_resp = client.get(
            f"{base_url}/api/v1/observability/report",
            params={"window_days": 1, "timing_minutes": timing_minutes},
        )
        report_resp.raise_for_status()
        report_payload = report_resp.json()
        _assert_http_contracts(report_payload, expect_alerts=expect_alerts)
        report_path.write_text(json.dumps(report_payload, indent=2, ensure_ascii=False), encoding="utf-8")

        status_resp = client.get(f"{base_url}/api/v1/status", params={"window_days": 1})
        status_resp.raise_for_status()
        status_payload = status_resp.json()
        status_path.write_text(json.dumps(status_payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    args = _parse_args()
    metric_date = date.fromisoformat(args.metric_date)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Gera matriz sintetica por path para preservar contrato dos artefatos P2.
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

    direct_csv = output_dir / "p2_a_summary_direct.csv"
    edge_csv = output_dir / "p2_a_summary_edge.csv"
    write_summary_csv(direct_csv, direct_rows)
    write_summary_csv(edge_csv, edge_rows)

    with SessionLocal() as session:
        inserted = seed_synthetic_timing_observations(session=session, metric_date=metric_date)
        if inserted <= 0:
            raise RuntimeError("Nenhuma observation sintetica foi inserida")

    # Agrega duas vezes para provar idempotencia de alerta SLO.
    result_first = aggregate_daily_metrics(metric_date.isoformat())
    if result_first.get("status") != "done":
        raise RuntimeError(f"aggregate_daily_metrics 1 falhou: {result_first}")

    with SessionLocal() as session:
        alert_count_after_first = count_events_for_date(
            session,
            metric_date=metric_date,
            event_type="metrics_slo_alert",
        )

    result_second = aggregate_daily_metrics(metric_date.isoformat())
    if result_second.get("status") != "done":
        raise RuntimeError(f"aggregate_daily_metrics 2 falhou: {result_second}")

    with SessionLocal() as session:
        alert_count_after_second = count_events_for_date(
            session,
            metric_date=metric_date,
            event_type="metrics_slo_alert",
        )

    if alert_count_after_first != alert_count_after_second:
        raise AssertionError(
            "Dedupe falhou: quantidade de metrics_slo_alert mudou apos segunda agregacao"
        )

    if not args.skip_http:
        _run_http_evidence(
            base_url=args.base_url.rstrip("/"),
            output_dir=output_dir,
            timing_minutes=args.timing_minutes,
            expect_alerts=alert_count_after_second > 0,
        )

    print("P2-B1 sintetico concluido com sucesso")
    print(f"- metric_date: {metric_date.isoformat()}")
    print(f"- inserted_timing_events: {inserted}")
    print(f"- alerts_count: {alert_count_after_second}")
    print(f"- direct_csv: {direct_csv}")
    print(f"- edge_csv: {edge_csv}")
    if not args.skip_http:
        print(f"- report_json: {output_dir / 'report_after_synth.json'}")
        print(f"- status_json: {output_dir / 'status_after_synth.json'}")


if __name__ == "__main__":
    main()

