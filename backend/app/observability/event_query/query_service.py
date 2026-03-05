from __future__ import annotations

import os

from app.observability.event_query.errors import (
    ForensicsBlockedByPolicyError,
    InsufficientFiltersError,
    LimitOutOfRangeError,
    TimeRangeRequiredError,
)
from app.observability.event_query.indexer import EventIndexer
from app.observability.event_query.models import (
    EventQueryFilters,
    EventQueryResult,
    PipelineTrace,
    QueryProfile,
    TraceRequest,
)


class EventQueryService:
    """Servico de consulta de eventos e trilha de pipeline."""

    def __init__(
        self,
        indexer: EventIndexer | None = None,
        *,
        forensics_enabled: bool | None = None,
        forensics_writer_allowlist: set[str] | None = None,
    ) -> None:
        self.indexer = indexer or EventIndexer()
        if forensics_enabled is None:
            forensics_enabled = os.getenv("FORENSICS_ENABLED", "").strip().lower() in {"1", "true", "yes"}
        self.forensics_enabled = forensics_enabled
        self.forensics_writer_allowlist = forensics_writer_allowlist or {"admin", "ci"}

    def get_events(
        self,
        filters: EventQueryFilters,
        limit: int = 200,
        *,
        profile: QueryProfile = QueryProfile.OPERATIONAL,
        writer_id: str | None = None,
    ) -> EventQueryResult:
        """Executa consulta deterministica por filtros com limite maximo."""
        if not filters.start_ts or not filters.end_ts:
            raise TimeRangeRequiredError()

        start_dt = filters.start_dt()
        end_dt = filters.end_dt()
        if end_dt <= start_dt:
            raise TimeRangeRequiredError()

        if limit < 1 or limit > 500:
            raise LimitOutOfRangeError()

        self._enforce_profile(profile=profile, filters=filters, writer_id=writer_id)

        if not self._has_required_selector(filters):
            raise InsufficientFiltersError()

        return self.indexer.scan(filters=filters, limit=limit)

    def get_pipeline_trace(self, request: TraceRequest, limit: int = 500) -> PipelineTrace:
        """Reconstrói trace de pipeline de forma determinística."""
        from app.observability.event_query.trace_builder import TraceBuilder

        return TraceBuilder(self).build_trace(request, limit=limit)

    def _has_required_selector(self, filters: EventQueryFilters) -> bool:
        return bool(
            filters.account_id
            or filters.window_id
            or filters.job_id
            or filters.publish_id
            or filters.op_key
            or filters.event_type
        )

    def _enforce_profile(
        self,
        *,
        profile: QueryProfile,
        filters: EventQueryFilters,
        writer_id: str | None,
    ) -> None:
        if profile != QueryProfile.FORENSICS:
            return
        if not self.forensics_enabled:
            raise ForensicsBlockedByPolicyError()
        if writer_id is None or writer_id not in self.forensics_writer_allowlist:
            raise ForensicsBlockedByPolicyError()
        if not (filters.account_id or filters.window_id):
            raise ForensicsBlockedByPolicyError()
