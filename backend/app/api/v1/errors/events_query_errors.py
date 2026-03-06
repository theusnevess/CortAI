from __future__ import annotations

from typing import Any

from app.observability.event_query.errors import (
    CursorFiltersMismatchError,
    CursorInvalidEncodingError,
    CursorInvalidJSONError,
    CursorMissingFieldsError,
    CursorSignatureInvalidError,
    CursorUnsupportedVersionError,
    ForensicsBlockedByPolicyError,
    InsufficientFiltersError,
    LimitOutOfRangeError,
    TimeRangeInvalidError,
    TimeRangeRequiredError,
)


def map_event_query_error(exc: Exception) -> tuple[int, str, str, dict[str, Any]]:
    """Mapeia erros de dominio para payload e status HTTP canônicos."""
    if isinstance(exc, TimeRangeRequiredError):
        return (400, "TIME_RANGE_REQUIRED", "time_from and time_to are required.", {})
    if isinstance(exc, TimeRangeInvalidError):
        return (400, "TIME_RANGE_INVALID", "time_to must be greater than time_from.", {})
    if isinstance(exc, InsufficientFiltersError):
        return (400, "INSUFFICIENT_FILTERS", "At least one strong selector is required.", {})
    if isinstance(exc, LimitOutOfRangeError):
        return (400, "LIMIT_OUT_OF_RANGE", "limit must be within allowed range.", {})
    if isinstance(exc, (CursorInvalidEncodingError, CursorInvalidJSONError, CursorUnsupportedVersionError, CursorMissingFieldsError)):
        code = str(exc)
        return (400, code, "Cursor payload is invalid.", {})
    if isinstance(exc, CursorFiltersMismatchError):
        return (409, "CURSOR_FILTERS_MISMATCH", "Cursor does not match query filters.", {})
    if isinstance(exc, CursorSignatureInvalidError):
        return (401, "CURSOR_SIGNATURE_INVALID", "Cursor signature validation failed.", {})
    if isinstance(exc, ForensicsBlockedByPolicyError):
        return (403, "FORENSICS_BLOCKED_BY_POLICY", "Forensics profile is blocked by policy.", {})
    return (500, "EVENT_QUERY_INTERNAL_ERROR", "Internal event query error.", {})

