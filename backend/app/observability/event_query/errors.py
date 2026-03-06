from __future__ import annotations

"""Erros canonicos da camada de event query e forensics."""


class EventQueryError(Exception):
    """Erro base da camada de query de eventos."""


class TimeRangeRequiredError(EventQueryError):
    """Falha quando o intervalo de tempo obrigatorio nao e informado."""

    def __init__(self) -> None:
        super().__init__("TIME_RANGE_REQUIRED")


class InsufficientFiltersError(EventQueryError):
    """Falha anti-scan quando nao ha seletor suficiente alem do tempo."""

    def __init__(self) -> None:
        super().__init__("INSUFFICIENT_FILTERS")


class LimitOutOfRangeError(EventQueryError):
    """Falha para limites fora da faixa permitida."""

    def __init__(self) -> None:
        super().__init__("LIMIT_OUT_OF_RANGE")


class EventInvalidShapeError(EventQueryError):
    """Falha interna para linha JSON com shape de evento invalido."""

    def __init__(self) -> None:
        super().__init__("EVENT_INVALID_SHAPE")


EVENT_INVALID_JSONL_LINE = "EVENT_INVALID_JSONL_LINE"
EVENT_INVALID_SHAPE = "EVENT_INVALID_SHAPE"


class TraceRequestInvalidError(EventQueryError):
    """Falha de validacao de seletor para pipeline trace."""

    def __init__(self) -> None:
        super().__init__("TRACE_REQUEST_INVALID")


class ForensicsBlockedByPolicyError(EventQueryError):
    """Falha quando consulta forense nao atende policy de seguranca."""

    def __init__(self) -> None:
        super().__init__("FORENSICS_BLOCKED_BY_POLICY")


class CursorInvalidEncodingError(EventQueryError):
    """Falha quando o cursor nao e base64url valido."""

    def __init__(self) -> None:
        super().__init__("CURSOR_INVALID_ENCODING")


class CursorInvalidJSONError(EventQueryError):
    """Falha quando o payload do cursor nao e JSON valido."""

    def __init__(self) -> None:
        super().__init__("CURSOR_INVALID_JSON")


class CursorUnsupportedVersionError(EventQueryError):
    """Falha para versao de cursor nao suportada."""

    def __init__(self) -> None:
        super().__init__("CURSOR_UNSUPPORTED_VERSION")


class CursorMissingFieldsError(EventQueryError):
    """Falha quando campos obrigatorios do cursor nao existem."""

    def __init__(self) -> None:
        super().__init__("CURSOR_MISSING_FIELDS")


class CursorFiltersMismatchError(EventQueryError):
    """Falha quando o hash de filtros diverge da consulta atual."""

    def __init__(self) -> None:
        super().__init__("CURSOR_FILTERS_MISMATCH")


class CursorSignatureInvalidError(EventQueryError):
    """Falha quando assinatura do cursor e invalida."""

    def __init__(self) -> None:
        super().__init__("CURSOR_SIGNATURE_INVALID")
