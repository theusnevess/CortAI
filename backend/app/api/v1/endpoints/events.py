from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.api.v1.errors.events_query_errors import map_event_query_error
from app.api.v1.schemas.events_query import ErrorResponse, EventsQueryResponse
from app.observability.event_query.errors import InsufficientFiltersError, LimitOutOfRangeError, TimeRangeRequiredError
from app.observability.event_query.indexer import EventIndexer
from app.observability.event_query.index_store.repo import EventIndexRepo
from app.observability.event_query.models import EventQueryFilters, EventRecord, QueryProfile
from app.observability.event_query.query_service import EventQueryService

router = APIRouter()


def _build_service() -> EventQueryService:
    base_dir = Path(os.getenv("EVENT_QUERY_BASE_DIR", "OUT"))
    indexer = EventIndexer(base_dir=base_dir)
    index_repo = EventIndexRepo(base_dir / "index" / "event_index.sqlite3")
    return EventQueryService(indexer=indexer, index_repo=index_repo)


def _has_strong_selector(filters: EventQueryFilters) -> bool:
    return bool(
        filters.account_id
        or filters.window_id
        or filters.job_id
        or filters.publish_id
        or filters.op_key
    )


def _to_public_item(record: EventRecord) -> dict:
    return {
        "event_id": record.event_id,
        "ts": record.ts,
        "event_type": record.event_type,
        "severity": record.severity,
        "action_taken": record.action_taken,
        "writer_id": record.writer_id,
        "account_id": record.account_id,
        "window_id": record.window_id,
        "job_id": record.job_id,
        "publish_id": record.publish_id,
        "op_key": record.op_key,
        "details": record.details,
    }


@router.get("", response_model=EventsQueryResponse, responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
def get_events(
    time_from: str | None = Query(None),
    time_to: str | None = Query(None),
    limit: int = Query(50),
    event_type_prefix: str | None = Query(None),
    account_id: str | None = Query(None),
    window_id: str | None = Query(None),
    job_id: str | None = Query(None),
    publish_id: str | None = Query(None),
    op_key: str | None = Query(None),
    severity: str | None = Query(None),
    action_taken: str | None = Query(None),
    cursor: str | None = Query(None),
):
    """Endpoint operacional de consulta de eventos com cursor keyset."""
    service = _build_service()
    try:
        if limit < 1 or limit > 200:
            raise LimitOutOfRangeError()
        if not time_from or not time_to:
            raise TimeRangeRequiredError()

        filters = EventQueryFilters(
            start_ts=time_from,
            end_ts=time_to,
            event_type_prefix=event_type_prefix,
            account_id=account_id,
            window_id=window_id,
            job_id=job_id,
            publish_id=publish_id,
            op_key=op_key,
            severity=severity,
            action_taken=action_taken,
        )

        if not _has_strong_selector(filters):
            raise InsufficientFiltersError()

        result = service.get_events(
            filters=filters,
            limit=limit,
            profile=QueryProfile.OPERATIONAL,
            cursor=cursor,
        )

        return {
            "items": [_to_public_item(item) for item in result.items],
            "has_more": result.has_more,
            "next_cursor": result.next_cursor,
            "query_shape_id": result.query_shape_id,
        }
    except Exception as exc:  # noqa: BLE001
        status, code, message, details = map_event_query_error(exc)
        return JSONResponse(
            status_code=status,
            content={
                "error": {
                    "code": code,
                    "message": message,
                    "details": details,
                }
            },
        )

