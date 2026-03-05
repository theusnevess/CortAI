from __future__ import annotations

import json
from typing import Any


class WindowMetricsInvariantError(ValueError):
    """Erro de invariante para idempotencia estrutural de window_metrics."""


def canonical_payload_hash(record: dict[str, Any]) -> str:
    canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return canonical


def decide_idempotency_action(
    *,
    existing: dict[str, Any] | None,
    candidate: dict[str, Any],
) -> str:
    if existing is None:
        return "WRITE"
    if canonical_payload_hash(existing) == canonical_payload_hash(candidate):
        return "NOOP"
    raise WindowMetricsInvariantError("ContractViolation: conflicting data for same (account_id, window_id)")

