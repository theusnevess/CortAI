from __future__ import annotations

from typing import Any

SOURCE_PRECEDENCE = {
    "PLATFORM_ANALYTICS": 3,
    "SCRAPED_ANALYTICS": 2,
    "MANUAL_ENTRY": 1,
}


class VideoMetricsPrecedenceError(ValueError):
    """Raised when precedence cannot be resolved."""


def source_rank(source_kind: str) -> int:
    if source_kind not in SOURCE_PRECEDENCE:
        raise VideoMetricsPrecedenceError("ContractViolation: invalid source_kind for precedence")
    return SOURCE_PRECEDENCE[source_kind]


def compare_sources(new_source_kind: str, current_source_kind: str) -> int:
    """
    Returns:
    - 1 when new source is better
    - 0 when equal
    - -1 when worse
    """
    new_rank = source_rank(new_source_kind)
    current_rank = source_rank(current_source_kind)
    if new_rank > current_rank:
        return 1
    if new_rank < current_rank:
        return -1
    return 0


def decide_precedence_action(
    *,
    new_record: dict[str, Any],
    current_best: dict[str, Any] | None,
) -> str:
    if current_best is None:
        return "INSERT_NEW_KEY"
    comparison = compare_sources(str(new_record["source_kind"]), str(current_best["source_kind"]))
    if comparison > 0:
        return "UPDATE_BEST_HIGHER_SOURCE"
    if comparison < 0:
        return "NOOP_WORSE_SOURCE"
    return "NOOP_SAME_SOURCE"
