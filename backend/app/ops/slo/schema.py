from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SLOThreshold:
    """Regra congelada para um SLI monitorado."""

    metric_name: str
    description: str
    direction: str
    target: float
    warn_threshold: float
    critical_threshold: float
    budget: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SLOMetricResult:
    """Resultado da avaliacao de uma metrica unica."""

    metric_name: str
    value: float
    status: str
    severity: str
    reason_code: str
    threshold: SLOThreshold
    budget_consumed_ratio: float | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["threshold"] = self.threshold.to_dict()
        return payload


@dataclass(frozen=True)
class SLOEvaluationResult:
    """Resultado consolidado da avaliacao de SLOs."""

    overall_status: str
    metrics: list[SLOMetricResult] = field(default_factory=list)
    missing_metrics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "metrics": [metric.to_dict() for metric in self.metrics],
            "missing_metrics": list(self.missing_metrics),
        }
