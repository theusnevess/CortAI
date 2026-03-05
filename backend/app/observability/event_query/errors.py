from __future__ import annotations


class EventQueryError(Exception):
    """Erro base da camada de query de eventos."""


class TimeRangeRequiredError(EventQueryError):
    """Falha quando o intervalo de tempo obrigatório não é informado."""

    def __init__(self) -> None:
        super().__init__("TIME_RANGE_REQUIRED")


class InsufficientFiltersError(EventQueryError):
    """Falha anti-scan quando não há seletor suficiente além do tempo."""

    def __init__(self) -> None:
        super().__init__("INSUFFICIENT_FILTERS")


class LimitOutOfRangeError(EventQueryError):
    """Falha para limites fora da faixa permitida."""

    def __init__(self) -> None:
        super().__init__("LIMIT_OUT_OF_RANGE")


class EventInvalidShapeError(EventQueryError):
    """Falha interna para linha JSON com shape de evento inválido."""

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
