from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EventItemPublic(BaseModel):
    """Shape publico e redigido de evento retornado pela API."""

    event_id: str
    ts: str
    event_type: str
    severity: str | None = None
    action_taken: str | None = None
    writer_id: str | None = None
    account_id: str | None = None
    window_id: str | None = None
    job_id: str | None = None
    publish_id: str | None = None
    op_key: str | None = None
    details: dict[str, Any] | None = None


class EventsQueryResponse(BaseModel):
    """Resposta paginada canônica de consulta de eventos."""

    items: list[EventItemPublic]
    has_more: bool
    next_cursor: str | None = None
    query_shape_id: str | None = None


class ErrorBody(BaseModel):
    """Corpo de erro canônico da API."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Envelope único para respostas de erro."""

    error: ErrorBody

