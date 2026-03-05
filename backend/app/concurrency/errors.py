from __future__ import annotations

"""Erros canonicos para controle de concorrencia D12."""


class ConcurrencyError(RuntimeError):
    """Erro base de concorrencia."""


class LeaseDeniedError(ConcurrencyError):
    """Falha ao adquirir lease porque ja existe owner ativo."""


class LeaseExpiredError(ConcurrencyError):
    """Falha causada por lease expirada durante operacao critica."""


class IdempotencyConflictError(ConcurrencyError):
    """Mesmo op_key com payload diferente detectado."""
