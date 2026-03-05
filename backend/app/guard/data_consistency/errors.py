from __future__ import annotations


class DataConsistencyGuardError(ValueError):
    """Erro base para o guard de consistencia."""


class ConsistencyViolationBlocked(DataConsistencyGuardError):
    """Falha dura quando existe violacao bloqueante."""

    def __init__(self, message: str = "CONSISTENCY_VIOLATION_BLOCKED") -> None:
        super().__init__(message)


class ConsistencyDependencyMissing(DataConsistencyGuardError):
    """Dependencia obrigatoria ausente para executar o guard."""

    def __init__(self, message: str = "CONSISTENCY_DEPENDENCY_MISSING") -> None:
        super().__init__(message)

