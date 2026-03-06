from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderCallResult:
    """Resultado bruto de uma chamada a provider com metadata de retry."""

    provider: str
    endpoint: str
    payload: dict[str, Any]
    latency_ms: float
    retry_count: int
    external_id: str | None = None
    request_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NormalizedVideoMetrics:
    """Shape normalizado para ingestao de video_metrics."""

    record: dict[str, Any]


@dataclass(frozen=True)
class NormalizedPublishRecord:
    """Shape normalizado para ingestao de publish_record."""

    record: dict[str, Any]


@dataclass(frozen=True)
class IntegrationSyncResult:
    """Resultado consolidado de sincronizacao externa."""

    status: str
    provider: str
    entity: str
    record: dict[str, Any]
    retry_count: int
    latency_ms: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
