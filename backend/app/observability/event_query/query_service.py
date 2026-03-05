from __future__ import annotations

from typing import Any

from app.observability.event_query.indexer import EventIndexer
from app.observability.event_query.models import EventQuery


class EventQueryService:
    """Servico de consulta de eventos e trilha de pipeline (esqueleto D13.1)."""

    def __init__(self, indexer: EventIndexer | None = None) -> None:
        self.indexer = indexer or EventIndexer()

    def get_events(self, query: EventQuery) -> list[dict[str, Any]]:
        """Consulta eventos por filtro. Implementacao entra no D13.2."""
        raise NotImplementedError

    def get_pipeline_trace(self, account_id: str, window_id: str) -> list[dict[str, Any]]:
        """Reconstrui trilha de pipeline por janela. Implementacao entra no D13.3."""
        raise NotImplementedError
