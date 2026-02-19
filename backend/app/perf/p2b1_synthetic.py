"""
Utilitarios para gerar e persistir um cenario sintetico de P2-B1.

Este modulo existe para validar o pipeline de observabilidade e SLO em
ambiente Windows/Docker Desktop sem depender de runner externo.
"""

from __future__ import annotations

import csv
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from app.db.models import ObservationRecord

ENDPOINTS = (
    "/api/v1/metrics/overview",
    "/api/v1/metrics/runs",
    "/api/v1/observability/report",
)
CONCURRENCY_LEVELS = (1, 2, 5)

# Perfis sinteticos calibrados para manter ordem monotona (C1 < C2 < C5).
PATH_PROFILE_FACTORS = {"direct": 1.0, "edge": 1.08}
BASE_P90_MS = {
    "/api/v1/metrics/overview": {1: 120.0, 2: 240.0, 5: 520.0},
    "/api/v1/metrics/runs": {1: 140.0, 2: 280.0, 5: 560.0},
    "/api/v1/observability/report": {1: 170.0, 2: 300.0, 5: 620.0},
}


@dataclass(frozen=True)
class SyntheticSummaryRow:
    """
    Linha de resumo sintetico usada para os CSVs de evidência.
    """

    endpoint: str
    concurrency: int
    repeat: int
    p90_ms: float
    p99_ms: float
    rps: float
    timeouts: int
    runner: str
    sut_host: str
    api_workers: str


def _validate_path_label(path_label: str) -> None:
    if path_label not in PATH_PROFILE_FACTORS:
        raise ValueError(f"path_label invalido: {path_label}")


def generate_summary_rows(
    *,
    path_label: str,
    repeats: int = 1,
    runner: str = "synthetic-runner",
    sut_host: str = "synthetic-sut",
    api_workers: str = "synthetic",
) -> list[SyntheticSummaryRow]:
    """
    Gera linhas sinteticas do envelope (3 endpoints x 3 concorrencias x repeats).
    """
    _validate_path_label(path_label)
    factor = PATH_PROFILE_FACTORS[path_label]
    rows: list[SyntheticSummaryRow] = []

    for repeat in range(1, repeats + 1):
        repeat_factor = 1.0 + (repeat - 1) * 0.01
        for endpoint in ENDPOINTS:
            for concurrency in CONCURRENCY_LEVELS:
                p90 = BASE_P90_MS[endpoint][concurrency] * factor * repeat_factor
                p99 = p90 * 1.12
                rps = max(0.1, 6.2 / concurrency)
                rows.append(
                    SyntheticSummaryRow(
                        endpoint=endpoint,
                        concurrency=concurrency,
                        repeat=repeat,
                        p90_ms=round(p90, 2),
                        p99_ms=round(p99, 2),
                        rps=round(rps, 4),
                        timeouts=0,
                        runner=runner,
                        sut_host=sut_host,
                        api_workers=api_workers,
                    )
                )
    return rows


def write_summary_csv(path: Path, rows: Iterable[SyntheticSummaryRow]) -> None:
    """
    Escreve CSV no mesmo formato do runner P2 para reaproveitar leitura existente.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "endpoint",
                "C",
                "repeat",
                "p90_ms",
                "p99_ms",
                "rps",
                "timeouts",
                "runner",
                "sut_host",
                "api_workers",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.endpoint,
                    row.concurrency,
                    row.repeat,
                    row.p90_ms,
                    row.p99_ms,
                    row.rps,
                    row.timeouts,
                    row.runner,
                    row.sut_host,
                    row.api_workers,
                ]
            )


def assert_monotonic_latency(rows: Iterable[SyntheticSummaryRow]) -> None:
    """
    Valida monotonicidade C1 -> C2 -> C5 por endpoint para p90 e p99.
    """
    grouped: dict[str, dict[int, list[SyntheticSummaryRow]]] = {}
    for row in rows:
        grouped.setdefault(row.endpoint, {}).setdefault(row.concurrency, []).append(row)

    for endpoint, by_c in grouped.items():
        sequence_p90: list[float] = []
        sequence_p99: list[float] = []
        for concurrency in CONCURRENCY_LEVELS:
            current = by_c.get(concurrency)
            if not current:
                raise AssertionError(f"endpoint {endpoint} sem dados para C={concurrency}")
            avg_p90 = sum(r.p90_ms for r in current) / len(current)
            avg_p99 = sum(r.p99_ms for r in current) / len(current)
            sequence_p90.append(avg_p90)
            sequence_p99.append(avg_p99)
        if not (sequence_p90[0] < sequence_p90[1] < sequence_p90[2]):
            raise AssertionError(f"p90 nao monotono para {endpoint}: {sequence_p90}")
        if not (sequence_p99[0] < sequence_p99[1] < sequence_p99[2]):
            raise AssertionError(f"p99 nao monotono para {endpoint}: {sequence_p99}")


def seed_synthetic_timing_observations(
    *,
    session,
    metric_date: date,
    observations_per_cell: int = 24,
) -> int:
    """
    Insere observations sinteticas de metrics_endpoint_timing para o dia alvo.

    Os valores sao altos em C2/C5 para induzir breach de SLO e validar alertas.
    """
    if observations_per_cell < 3:
        raise ValueError("observations_per_cell deve ser >= 3")

    # Remove execucoes sinteticas antigas do mesmo dia para reprodutibilidade.
    session.query(ObservationRecord).filter(
        ObservationRecord.process_id.like(f"P2B1_SYNTH_{metric_date.isoformat()}_%")
    ).delete(synchronize_session=False)

    inserted = 0
    base_dt = datetime.combine(metric_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    for path_label in PATH_PROFILE_FACTORS:
        factor = PATH_PROFILE_FACTORS[path_label]
        for endpoint in ENDPOINTS:
            for concurrency in CONCURRENCY_LEVELS:
                base_duration = BASE_P90_MS[endpoint][concurrency] * factor
                for idx in range(observations_per_cell):
                    jitter = ((idx % 7) - 3) * 0.03  # +-9% deterministico
                    duration_ms = max(1, int(round(base_duration * (1.0 + jitter))))
                    timestamp = (base_dt + timedelta(minutes=inserted + idx)).replace(tzinfo=None)
                    process_id = (
                        f"P2B1_SYNTH_{metric_date.isoformat()}_{path_label}"
                        f"_C{concurrency}_{endpoint.split('/')[-1]}_{idx}"
                    )
                    session.add(
                        ObservationRecord(
                            observation_id=str(uuid.uuid4()),
                            timestamp=timestamp,
                            process_id=process_id,
                            source_outcome_id=str(uuid.uuid4()),
                            facts={
                                "event_type": "metrics_endpoint_timing",
                                "endpoint": endpoint,
                                "method": "GET",
                                "status_code": 200,
                                "duration_ms": duration_ms,
                                "query_fingerprint": f"p2b1_synth={path_label}&c={concurrency}",
                                "metric_date": metric_date.isoformat(),
                                "timestamp": timestamp.isoformat(),
                                "queue_us": 1200,
                                "handler_us": 900,
                                "server_total_us": 2100,
                                "db_us": 3500,
                                "db_queries": 2,
                                "db_pool_wait_us": 0,
                            },
                        )
                    )
                    inserted += 1

    # Garante eventos recentes para os checks de report (timing window em minutos).
    now_utc = datetime.utcnow()
    for endpoint in ENDPOINTS:
        recent_ts = now_utc - timedelta(seconds=inserted % 45)
        session.add(
            ObservationRecord(
                observation_id=str(uuid.uuid4()),
                timestamp=recent_ts,
                process_id=f"P2B1_SYNTH_{metric_date.isoformat()}_RECENT_{endpoint.split('/')[-1]}",
                source_outcome_id=str(uuid.uuid4()),
                facts={
                    "event_type": "metrics_endpoint_timing",
                    "endpoint": endpoint,
                    "method": "GET",
                    "status_code": 200,
                    "duration_ms": 50,
                    "query_fingerprint": "p2b1_synth_recent=1",
                    "metric_date": now_utc.date().isoformat(),
                    "timestamp": recent_ts.isoformat(),
                    "queue_us": 1000,
                    "handler_us": 700,
                    "server_total_us": 1700,
                    "db_us": 2500,
                    "db_queries": 2,
                    "db_pool_wait_us": 0,
                },
            )
        )
        inserted += 1
    session.commit()
    return inserted


def count_events_for_date(session, *, metric_date: date, event_type: str) -> int:
    """
    Conta observations por tipo de evento no dia alvo.
    """
    return int(
        session.query(ObservationRecord)
        .filter(ObservationRecord.facts["event_type"].astext == event_type)
        .filter(ObservationRecord.facts["metric_date"].astext == metric_date.isoformat())
        .count()
        or 0
    )
