from __future__ import annotations


class StrategyLearningError(ValueError):
    """Erro base da camada de strategy learning."""


class StrategyScorecardMissingError(StrategyLearningError):
    def __init__(self, message: str = "SL_SCORECARD_MISSING") -> None:
        super().__init__(message)


class StrategyWindowMetricsMissingError(StrategyLearningError):
    def __init__(self, message: str = "SL_WINDOW_METRICS_MISSING") -> None:
        super().__init__(message)


class StrategyAttributionEmptyError(StrategyLearningError):
    def __init__(self, message: str = "SL_ATTRIBUTION_EMPTY") -> None:
        super().__init__(message)


class StrategyPatchConflictError(StrategyLearningError):
    def __init__(self, message: str = "STRATEGY_PATCH_CONFLICT") -> None:
        super().__init__(message)

