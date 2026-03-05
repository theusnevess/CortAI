from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def parse_iso_utc(value: str) -> datetime:
    """Converte timestamp ISO8601 para datetime UTC normalizado."""
    normalized = value.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class EventRecord:
    """Shape normalizado de evento para query publica."""

    event_id: str
    ts: str
    event_type: str
    severity: str | None = None
    action_taken: str | None = None
    account_id: str | None = None
    window_id: str | None = None
    job_id: str | None = None
    publish_id: str | None = None
    op_key: str | None = None
    details: dict[str, Any] | None = None


class QueryProfile(str, Enum):
    """Perfil de consulta para separar trilha operacional e forense."""

    OPERATIONAL = "OPERATIONAL"
    FORENSICS = "FORENSICS"


@dataclass(frozen=True)
class EventQueryFilters:
    """Filtros canônicos de consulta; time range é obrigatório."""

    start_ts: str
    end_ts: str
    account_id: str | None = None
    window_id: str | None = None
    job_id: str | None = None
    publish_id: str | None = None
    op_key: str | None = None
    event_type: str | None = None
    event_type_prefix: str | None = None
    severity: str | None = None
    action_taken: str | None = None

    def start_dt(self) -> datetime:
        return parse_iso_utc(self.start_ts)

    def end_dt(self) -> datetime:
        return parse_iso_utc(self.end_ts)


@dataclass(frozen=True)
class EventQueryStats:
    """Contadores de saneamento e varredura da consulta."""

    scanned_files: int = 0
    scanned_lines: int = 0
    invalid_jsonl_lines: int = 0
    invalid_shape_lines: int = 0


@dataclass(frozen=True)
class EventQueryResult:
    """Resultado deterministico da consulta de eventos."""

    items: list[EventRecord] = field(default_factory=list)
    stats: EventQueryStats = field(default_factory=EventQueryStats)


@dataclass(frozen=True)
class TraceRequest:
    """Parametros para reconstruir timeline de pipeline."""

    job_id: str | None = None
    publish_id: str | None = None
    window_id: str | None = None
    account_id: str | None = None
    start_ts: str | None = None
    end_ts: str | None = None


@dataclass(frozen=True)
class TraceSummary:
    """Resumo deterministico de status final e causa dominante."""

    final_status: str
    dominant_family: str | None = None
    dominant_reason_code: str | None = None
    first_failure_event_id: str | None = None
    last_event_id: str | None = None


@dataclass(frozen=True)
class PipelineTrace:
    """Resposta completa de trace para debug forense."""

    trace_id: str
    account_id: str | None
    job_id: str | None
    publish_id: str | None
    window_id: str | None
    time_range: dict[str, str]
    timeline: list[EventRecord]
    summary: TraceSummary
    stats: dict[str, dict[str, int]]
