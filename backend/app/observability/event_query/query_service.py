from __future__ import annotations

from app.observability.event_query.errors import (
    InsufficientFiltersError,
    LimitOutOfRangeError,
    TimeRangeRequiredError,
)
from app.observability.event_query.indexer import EventIndexer
from app.observability.event_query.models import EventQueryFilters, EventQueryResult


class EventQueryService:
    """Servico de consulta de eventos e trilha de pipeline."""

    def __init__(self, indexer: EventIndexer | None = None) -> None:
        self.indexer = indexer or EventIndexer()

    def get_events(self, filters: EventQueryFilters, limit: int = 200) -> EventQueryResult:
        """Executa consulta deterministica por filtros com limite maximo."""
        if not filters.start_ts or not filters.end_ts:
            raise TimeRangeRequiredError()

        start_dt = filters.start_dt()
        end_dt = filters.end_dt()
        if end_dt <= start_dt:
            raise TimeRangeRequiredError()

        if limit < 1 or limit > 500:
            raise LimitOutOfRangeError()

        if not self._has_required_selector(filters):
            raise InsufficientFiltersError()

        return self.indexer.scan(filters=filters, limit=limit)

    def get_pipeline_trace(self, account_id: str, window_id: str):
        """Reconstrucao de trace entra no D13.3."""
        raise NotImplementedError

    def _has_required_selector(self, filters: EventQueryFilters) -> bool:
        return bool(
            filters.account_id
            or filters.window_id
            or filters.job_id
            or filters.publish_id
            or filters.op_key
            or filters.event_type
            or filters.event_type_prefix
        )
