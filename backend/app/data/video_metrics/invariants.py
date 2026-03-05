from __future__ import annotations

from typing import Any

from app.data.schemas.video_metrics import validate_video_metrics
from app.data.video_metrics.dedup import dedup_key
from app.data.video_metrics.precedence import decide_precedence_action


class VideoMetricsInvariantError(ValueError):
    """Violacao de invariante para o contrato de ingestao de video_metrics."""


def enforce_ingestion_invariants(record: dict[str, Any]) -> dict[str, Any]:
    normalized = validate_video_metrics(record)
    key = dedup_key(normalized)
    if any(not part for part in key):
        raise VideoMetricsInvariantError("ContractViolation: invalid dedup key")
    return normalized


def decide_ingestion_action(
    *,
    new_record: dict[str, Any],
    current_best: dict[str, Any] | None,
) -> str:
    normalized = enforce_ingestion_invariants(new_record)
    if current_best is None:
        return "INSERT_NEW_KEY"
    _ = enforce_ingestion_invariants(current_best)
    return decide_precedence_action(new_record=normalized, current_best=current_best)
