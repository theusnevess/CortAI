from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil


@dataclass(frozen=True)
class LatencySummary:
    """Resumo de latencia em milissegundos para uma operacao."""

    count: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    max_ms: float
    avg_ms: float

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


def _percentile(sorted_values: list[float], fraction: float) -> float:
    if not sorted_values:
        return 0.0
    index = max(0, ceil(len(sorted_values) * fraction) - 1)
    return round(sorted_values[index], 3)


def summarize_latencies(durations_ms: list[float]) -> LatencySummary:
    """Consolida p50/p95/p99 a partir de duracoes em milissegundos."""
    if not durations_ms:
        return LatencySummary(count=0, p50_ms=0.0, p95_ms=0.0, p99_ms=0.0, max_ms=0.0, avg_ms=0.0)

    values = sorted(round(value, 3) for value in durations_ms)
    return LatencySummary(
        count=len(values),
        p50_ms=_percentile(values, 0.50),
        p95_ms=_percentile(values, 0.95),
        p99_ms=_percentile(values, 0.99),
        max_ms=round(values[-1], 3),
        avg_ms=round(sum(values) / len(values), 3),
    )
