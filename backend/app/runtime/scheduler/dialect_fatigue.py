from __future__ import annotations

import os
from collections import Counter
from typing import Any


def dialect_fatigue_control_enabled() -> bool:
    return os.getenv("CORTAI_EXPERIMENT_DIALECT_FATIGUE_CONTROL", "0") == "1"


def reorder_by_hook_type(
    candidates: list[dict[str, Any]],
    *,
    enabled: bool | None = None,
    ideal_max_consecutive: int = 2,
    tolerated_max_consecutive: int = 3,
    diversity_window: int = 5,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ordered = [dict(item) for item in candidates]
    active = dialect_fatigue_control_enabled() if enabled is None else enabled
    if not active or len(ordered) <= 1:
        return ordered, {"dialect_control_relaxed": False, "reason": ""}

    remaining = [(index, dict(item)) for index, item in enumerate(ordered)]
    sequence: list[dict[str, Any]] = []
    relaxed = False
    reason = ""

    while remaining:
        ranked: list[tuple[tuple[int, int, int, int], int, dict[str, Any]]] = []
        for remaining_index, (original_index, candidate) in enumerate(remaining):
            ideal_ok = _respects_consecutive_limit(
                sequence=sequence,
                candidate=candidate,
                max_consecutive=ideal_max_consecutive,
            )
            tolerated_ok = _respects_consecutive_limit(
                sequence=sequence,
                candidate=candidate,
                max_consecutive=tolerated_max_consecutive,
            )
            window_ok = _respects_window_balance(
                sequence=sequence,
                candidate=candidate,
                remaining=remaining,
                diversity_window=diversity_window,
            )
            score = (
                0 if ideal_ok else 1,
                0 if tolerated_ok else 1,
                0 if window_ok else 1,
                original_index,
            )
            ranked.append((score, remaining_index, candidate))

        ranked.sort(key=lambda item: item[0])
        best_score, chosen_index, chosen = ranked[0]
        if best_score[0] > 0 or best_score[1] > 0 or best_score[2] > 0:
            relaxed = True
            if best_score[1] > 0:
                reason = "insufficient_hook_type_diversity"
            elif best_score[0] > 0:
                reason = "narrow_hook_type_pool"
            elif best_score[2] > 0:
                reason = "window_balance_unavailable"
        sequence.append(chosen)
        remaining.pop(chosen_index)

    available_types = {str(item.get("hook_type") or "") for item in ordered if str(item.get("hook_type") or "") in {"experiential", "inferential"}}
    if len(available_types) < 2:
        return sequence, {"dialect_control_relaxed": True, "reason": "insufficient_hook_type_diversity"}

    return sequence, {"dialect_control_relaxed": relaxed, "reason": reason}


def summarize_dialect_sequence(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    hook_types = [str(item.get("hook_type") or "") for item in candidates if str(item.get("hook_type") or "")]
    return {
        "total_videos": len(candidates),
        "max_consecutive_same_hook_type": _max_consecutive(hook_types),
        "dominant_hook_type_share": round(max(Counter(hook_types).values()) / len(hook_types), 4) if hook_types else 0.0,
        "window_hook_type_balance": _window_balance_ratio(hook_types, window=5),
        "dialect_fatigue_rate": _dialect_fatigue_rate(hook_types),
        "hook_type_balance": dict(Counter(hook_types)),
    }


def _respects_consecutive_limit(
    *,
    sequence: list[dict[str, Any]],
    candidate: dict[str, Any],
    max_consecutive: int,
) -> bool:
    if max_consecutive < 1:
        return True
    candidate_type = str(candidate.get("hook_type") or "")
    if candidate_type not in {"experiential", "inferential"}:
        return True
    streak = 0
    for item in reversed(sequence):
        if str(item.get("hook_type") or "") != candidate_type:
            break
        streak += 1
    return streak < max_consecutive


def _respects_window_balance(
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
    window_types = [str(item.get("hook_type") or "") for item in sequence[-(diversity_window - 1) :]] + [candidate_type]
    if {"experiential", "inferential"}.issubset(set(window_types)):
        return True
    other_type = "inferential" if candidate_type == "experiential" else "experiential"
    return any(str(item.get("hook_type") or "") == other_type for _, item in remaining if item is not candidate)


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


def _window_balance_ratio(values: list[str], *, window: int) -> float:
    if len(values) < window:
        return 1.0 if {"experiential", "inferential"}.issubset(set(values)) else 0.0
    total = 0
    good = 0
    for idx in range(len(values) - window + 1):
        total += 1
        subset = set(values[idx : idx + window])
        if {"experiential", "inferential"}.issubset(subset):
            good += 1
    return round(good / total, 4) if total else 0.0


def _dialect_fatigue_rate(values: list[str]) -> float:
    if len(values) < 2:
        return 0.0
    same_edges = sum(1 for left, right in zip(values, values[1:]) if left == right)
    return round(same_edges / (len(values) - 1), 4)
