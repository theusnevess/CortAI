from __future__ import annotations

import os
from collections import Counter
from typing import Any


def feed_distribution_control_enabled() -> bool:
    return os.getenv("CORTAI_EXPERIMENT_FEED_DISTRIBUTION_CONTROL", "0") == "1"


def reorder_feed_candidates(
    candidates: list[dict[str, Any]],
    *,
    enabled: bool | None = None,
    max_consecutive_same_hook_type: int = 2,
    max_consecutive_same_visual_anchor: int = 2,
    diversity_window: int = 5,
) -> tuple[list[dict[str, Any]], int]:
    ordered_candidates = [dict(item) for item in candidates]
    if len(ordered_candidates) <= 1:
        return ordered_candidates, 0

    active = feed_distribution_control_enabled() if enabled is None else enabled
    if not active:
        return ordered_candidates, 0

    remaining = [(index, dict(item)) for index, item in enumerate(ordered_candidates)]
    sequence: list[dict[str, Any]] = []
    relaxation_count = 0

    while remaining:
        ranked: list[tuple[tuple[int, int, int, int], bool, int, dict[str, Any]]] = []
        for remaining_index, (original_index, candidate) in enumerate(remaining):
            hook_ok = _respects_consecutive_limit(
                sequence=sequence,
                candidate=candidate,
                key="hook_type",
                max_consecutive=max_consecutive_same_hook_type,
            )
            visual_ok = _respects_consecutive_limit(
                sequence=sequence,
                candidate=candidate,
                key="visual_anchor",
                max_consecutive=max_consecutive_same_visual_anchor,
            )
            window_ok = _respects_diversity_window(
                sequence=sequence,
                candidate=candidate,
                remaining=remaining,
                diversity_window=diversity_window,
            )
            score = (
                0 if hook_ok else 1,
                0 if visual_ok else 1,
                0 if window_ok else 1,
                original_index,
            )
            ranked.append((score, not (hook_ok and visual_ok and window_ok), remaining_index, candidate))

        ranked.sort(key=lambda item: item[0])
        _, relaxed, chosen_index, chosen = ranked[0]
        if relaxed:
            relaxation_count += 1
        sequence.append(chosen)
        remaining.pop(chosen_index)

    return sequence, relaxation_count


def summarize_feed_sequence(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    hook_types = [str(item.get("hook_type") or "") for item in candidates]
    anchors = [str(item.get("visual_anchor") or "") for item in candidates]
    semantic_patterns = [str(item.get("semantic_pattern") or "") for item in candidates]
    entities = [str(item.get("entity") or "") for item in candidates]

    return {
        "total_videos": len(candidates),
        "max_consecutive_same_hook_type": _max_consecutive(hook_types),
        "max_consecutive_same_visual_anchor": _max_consecutive(anchors),
        "hook_type_balance": dict(Counter(value for value in hook_types if value)),
        "visual_anchor_distribution": dict(Counter(value for value in anchors if value)),
        "semantic_distribution": dict(Counter(value for value in semantic_patterns if value)),
        "entity_distribution": dict(Counter(value for value in entities if value)),
        "repetition_rate": _repetition_rate(candidates),
    }


def _respects_consecutive_limit(
    *,
    sequence: list[dict[str, Any]],
    candidate: dict[str, Any],
    key: str,
    max_consecutive: int,
) -> bool:
    if max_consecutive < 1:
        return True
    candidate_value = str(candidate.get(key) or "")
    if not candidate_value:
        return True
    streak = 0
    for item in reversed(sequence):
        if str(item.get(key) or "") != candidate_value:
            break
        streak += 1
    return streak < max_consecutive


def _respects_diversity_window(
    *,
    sequence: list[dict[str, Any]],
    candidate: dict[str, Any],
    remaining: list[tuple[int, dict[str, Any]]],
    diversity_window: int,
) -> bool:
    if diversity_window < 2 or len(sequence) < diversity_window - 1:
        return True
    candidate_type = str(candidate.get("hook_type") or "")
    if candidate_type not in {"experiential", "inferential"}:
        return True

    prior_types = [str(item.get("hook_type") or "") for item in sequence[-(diversity_window - 1) :]]
    window_types = prior_types + [candidate_type]
    if {"experiential", "inferential"}.issubset(set(window_types)):
        return True

    other_type = "inferential" if candidate_type == "experiential" else "experiential"
    for _, item in remaining:
        if item is candidate:
            continue
        if str(item.get("hook_type") or "") == other_type:
            return False
    return True


def _max_consecutive(values: list[str]) -> int:
    longest = 0
    current = 0
    previous = ""
    for value in values:
        if not value:
            previous = ""
            current = 0
            continue
        if value == previous:
            current += 1
        else:
            previous = value
            current = 1
        if current > longest:
            longest = current
    return longest


def _repetition_rate(candidates: list[dict[str, Any]]) -> float:
    if len(candidates) < 2:
        return 0.0
    repeated_edges = 0
    total_edges = len(candidates) - 1
    for left, right in zip(candidates, candidates[1:]):
        same_hook = str(left.get("hook_type") or "") == str(right.get("hook_type") or "")
        same_anchor = str(left.get("visual_anchor") or "") == str(right.get("visual_anchor") or "")
        if same_hook or same_anchor:
            repeated_edges += 1
    return round(repeated_edges / total_edges, 4)
