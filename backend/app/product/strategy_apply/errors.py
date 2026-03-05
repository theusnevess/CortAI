from __future__ import annotations


class StrategyApplyError(ValueError):
    """Erro base da aplicação de strategy patch."""


class StrategyApplyWhitelistError(StrategyApplyError):
    def __init__(self, message: str = "STRATEGY_PATCH_WHITELIST_VIOLATION") -> None:
        super().__init__(message)


class StrategyApplyConflictError(StrategyApplyError):
    def __init__(self, message: str = "STRATEGY_PATCH_APPLICATION_CONFLICT") -> None:
        super().__init__(message)

