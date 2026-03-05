from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EventQuery:
    """Filtro de consulta de eventos para a camada forense."""

    account_id: str | None = None
    window_id: str | None = None
    job_id: str | None = None
    publish_id: str | None = None
    op_key: str | None = None
    event_type: str | None = None
    timestamp_start: str | None = None
    timestamp_end: str | None = None
