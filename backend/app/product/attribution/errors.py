from __future__ import annotations


class AttributionBuildError(ValueError):
    """Erro base para falhas de montagem do content attribution."""


class PublishRecordNotFoundError(AttributionBuildError):
    """Falha quando publish_id não existe no repositório canônico."""

    def __init__(self, message: str = "PUBLISH_RECORD_NOT_FOUND") -> None:
        super().__init__(message)


class AttributionMetricsMissingError(AttributionBuildError):
    """Falha quando não existem métricas reais para o publish/video."""

    def __init__(self, message: str = "ATTRIBUTION_METRICS_MISSING") -> None:
        super().__init__(message)


class AttributionWindowMissingError(AttributionBuildError):
    """Falha quando não é possível resolver ou carregar a janela."""

    def __init__(self, message: str = "ATTRIBUTION_WINDOW_MISSING") -> None:
        super().__init__(message)


class PolicyStageNotFoundError(AttributionBuildError):
    """Falha quando policy_stage não pode ser resolvido de forma confiável."""

    def __init__(self, message: str = "POLICY_STAGE_NOT_FOUND") -> None:
        super().__init__(message)

