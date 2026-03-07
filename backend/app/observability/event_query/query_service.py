from __future__ import annotations

from datetime import datetime, timezone
import os

from app.observability.event_query.cursor import (
    CursorLast,
    SeekCursor,
    decode_cursor,
    encode_cursor,
    validate_cursor_filters_hash,
    validate_cursor_signature,
)
from app.observability.event_query.cursor_signing import SigningPolicy
from app.observability.event_query.errors import (
    ForensicsBlockedByPolicyError,
    InsufficientFiltersError,
    LimitOutOfRangeError,
    TimeRangeInvalidError,
    TimeRangeRequiredError,
)
from app.observability.event_query.indexer import EventIndexer
from app.observability.event_query.index_store.repo import EventIndexRepo
from app.observability.hot_store.repo import HotStoreRepo
from app.observability.event_query.models import (
    EventQueryFilters,
    EventQueryResult,
    PipelineTrace,
    QueryProfile,
    TraceRequest,
)
from app.observability.event_query.query_filters import build_filters_hash


class EventQueryService:
    """Servico de consulta de eventos e trilha de pipeline."""

    def __init__(
        self,
        indexer: EventIndexer | None = None,
        hot_store_repo: HotStoreRepo | None = None,
        index_repo: EventIndexRepo | None = None,
        *,
        forensics_enabled: bool | None = None,
        forensics_writer_allowlist: set[str] | None = None,
        cursor_signing_policy: SigningPolicy | None = None,
    ) -> None:
        self.indexer = indexer or EventIndexer()
        self.hot_store_repo = hot_store_repo
        self.index_repo = index_repo
        if forensics_enabled is None:
            forensics_enabled = os.getenv("FORENSICS_ENABLED", "").strip().lower() in {"1", "true", "yes"}
        self.forensics_enabled = forensics_enabled
        self.forensics_writer_allowlist = forensics_writer_allowlist or {"admin", "ci"}
        if cursor_signing_policy is None:
            enforcement = os.getenv("CURSOR_SIGNATURE_ENFORCEMENT", "").strip().lower() in {"1", "true", "yes"}
            secret = os.getenv("CURSOR_SIGNATURE_SECRET", "dev-secret").encode("utf-8")
            cursor_signing_policy = SigningPolicy(enabled=enforcement, secret=secret)
        self.cursor_signing_policy = cursor_signing_policy

    def get_events(
        self,
        filters: EventQueryFilters,
        limit: int = 200,
        *,
        profile: QueryProfile = QueryProfile.OPERATIONAL,
        writer_id: str | None = None,
        cursor: str | SeekCursor | None = None,
    ) -> EventQueryResult:
        """Executa consulta deterministica por filtros com seek keyset."""
        if not filters.start_ts or not filters.end_ts:
            raise TimeRangeRequiredError()

        start_dt = filters.start_dt()
        end_dt = filters.end_dt()
        if end_dt <= start_dt:
            raise TimeRangeInvalidError()

        if limit < 1 or limit > 500:
            raise LimitOutOfRangeError()

        self._enforce_profile(profile=profile, filters=filters, writer_id=writer_id)

        if not self._has_required_selector(filters):
            raise InsufficientFiltersError()

        filters_hash = build_filters_hash(filters)
        query_shape_id = "BASE"
        cursor_last: tuple[str, str] | None = None

        if cursor is not None:
            cursor_obj = decode_cursor(cursor) if isinstance(cursor, str) else cursor
            validate_cursor_signature(cursor_obj, self.cursor_signing_policy)
            validate_cursor_filters_hash(cursor_obj, filters_hash)
            cursor_last = (cursor_obj.last.ts, cursor_obj.last.event_id)
            query_shape_id = "WITH_CURSOR"

        result = self._search(filters=filters, limit=limit, cursor_last=cursor_last)

        next_cursor = None
        if result.has_more and result.items:
            last_item = result.items[-1]
            next_cursor = encode_cursor(
                SeekCursor(
                    v="1",
                    filters_hash=filters_hash,
                    last=CursorLast(ts=last_item.ts, event_id=last_item.event_id or ""),
                    issued_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                ),
                signing=self.cursor_signing_policy,
            )

        return EventQueryResult(
            items=result.items,
            stats=result.stats,
            next_cursor=next_cursor,
            has_more=result.has_more,
            query_shape_id=query_shape_id,
        )

    def _search(
        self,
        *,
        filters: EventQueryFilters,
        limit: int,
        cursor_last: tuple[str, str] | None,
    ) -> EventQueryResult:
        if self.hot_store_repo is not None:
            try:
                if self.hot_store_repo.is_available():
                    return self.hot_store_repo.search(filters, limit, cursor_last=cursor_last)
            except Exception:  # noqa: BLE001
                pass
        if self.index_repo is not None:
            try:
                if self.index_repo.is_available():
                    return self.index_repo.search(filters, limit, cursor_last=cursor_last)
            except Exception:  # noqa: BLE001
                pass
        return self.indexer.scan(filters=filters, limit=limit, cursor_last=cursor_last)

    def get_pipeline_trace(self, request: TraceRequest, limit: int = 500) -> PipelineTrace:
        """Reconstrui trace de pipeline de forma deterministica."""
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
