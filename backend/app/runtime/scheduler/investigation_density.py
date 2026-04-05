from __future__ import annotations

import os
import math
from collections import Counter
from typing import Any


def investigation_dialect_density_enabled() -> bool:
    return os.getenv("CORTAI_EXPERIMENT_INVESTIGATION_DIALECT_DENSITY", "0") == "1"


def reorder_investigation_stream_by_density(
    candidates: list[dict[str, Any]],
    *,
    enabled: bool | None = None,
    target_stream_id: str = "investigation_stream",
    window_size: int = 5,
    preferred_inferential_streak: int = 2,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ordered = [dict(item) for item in candidates]
    active = investigation_dialect_density_enabled() if enabled is None else enabled
    if not active or len(ordered) <= 1:
        return ordered, {"density_control_relaxed": False, "reason": ""}
    if any(str(item.get("stream_id") or "") != target_stream_id for item in ordered):
        return ordered, {"density_control_relaxed": True, "reason": "non_target_stream"}

    remaining = [(index, dict(item)) for index, item in enumerate(ordered)]
    sequence: list[dict[str, Any]] = []
    relaxed = False
    reason = ""
    total_positions = len(ordered)
    total_experiential = sum(
        1 for item in ordered if str(item.get("hook_type") or "") == "experiential"
    )
    experiential_targets = [
        max(1, round((index + 1) * (total_positions + 1) / (total_experiential + 1)))
        for index in range(total_experiential)
    ]

    while remaining:
        current_position = len(sequence) + 1
        experiential_used = sum(
            1 for item in sequence if str(item.get("hook_type") or "") == "experiential"
        )
        next_experiential_target = (
            experiential_targets[experiential_used]
            if experiential_used < len(experiential_targets)
            else math.inf
        )
        ranked: list[tuple[tuple[int, int, int, int], int, dict[str, Any]]] = []
        for remaining_index, (original_index, candidate) in enumerate(remaining):
            candidate_type = str(candidate.get("hook_type") or "")
            inferential_break_needed = _inferential_break_needed(
                sequence=sequence,
                preferred_streak=preferred_inferential_streak,
            )
            breaks_inferential_block = inferential_break_needed and candidate_type == "experiential"
            window_ok = _respects_experiential_window_density(
                sequence=sequence,
                candidate_type=candidate_type,
                remaining=remaining,
                window_size=window_size,
            )
            requires_experiential_now = _requires_experiential_now(
                sequence=sequence,
                candidate_type=candidate_type,
                remaining=remaining,
                window_size=window_size,
            )
            target_due = (
                candidate_type == "experiential" and current_position >= next_experiential_target
            )
            score = (
                0 if requires_experiential_now else 1,
                0 if target_due else 1,
                0 if breaks_inferential_block else 1,
                0 if window_ok else 1,
                original_index,
            )
            ranked.append((score, remaining_index, candidate))

        ranked.sort(key=lambda item: item[0])
        best_score, chosen_index, chosen = ranked[0]
        if best_score[0] > 0:
            relaxed = True
            reason = "insufficient_experiential_supply_in_window"
        sequence.append(chosen)
        remaining.pop(chosen_index)

    return sequence, {"density_control_relaxed": relaxed, "reason": reason}


def summarize_investigation_density(candidates: list[dict[str, Any]], *, window_size: int = 5) -> dict[str, Any]:
    hook_types = [str(item.get("hook_type") or "") for item in candidates if str(item.get("hook_type") or "")]
    windows = _window_summaries(hook_types, window_size=window_size)
    return {
        "total_videos": len(candidates),
        "max_consecutive_same_hook_type": _max_consecutive(hook_types),
        "window_hook_type_balance": round(
            sum(1 for row in windows if row["has_experiential"]) / len(windows), 4
        )
        if windows
        else 0.0,
        "windows_with_at_least_one_experiential": round(
            sum(1 for row in windows if row["has_experiential"]) / len(windows), 4
        )
        if windows
        else 0.0,
        "dialect_fatigue_rate": _dialect_fatigue_rate(hook_types),
        "hook_type_balance": dict(Counter(hook_types)),
    }


def _inferential_break_needed(
    *,
    sequence: list[dict[str, Any]],
    preferred_streak: int,
) -> bool:
    streak = 0
    for item in reversed(sequence):
        if str(item.get("hook_type") or "") != "inferential":
            break
        streak += 1
    return streak >= preferred_streak


def _respects_experiential_window_density(
    *,
    sequence: list[dict[str, Any]],
    candidate_type: str,
    remaining: list[tuple[int, dict[str, Any]]],
    window_size: int,
) -> bool:
    if len(sequence) < window_size - 1:
        return True
    window_types = [str(item.get("hook_type") or "") for item in sequence[-(window_size - 1) :]]
    prospective = window_types + [candidate_type]
    if "experiential" in prospective:
        return True
    return any(str(item.get("hook_type") or "") == "experiential" for _, item in remaining)


def _requires_experiential_now(
    *,
    sequence: list[dict[str, Any]],
    candidate_type: str,
    remaining: list[tuple[int, dict[str, Any]]],
    window_size: int,
) -> bool:
    if len(sequence) < window_size - 1:
        return False
    recent = [str(item.get("hook_type") or "") for item in sequence[-(window_size - 1) :]]
    if "experiential" in recent:
        return False
    experiential_remaining = any(
        str(item.get("hook_type") or "") == "experiential" for _, item in remaining
    )
    return experiential_remaining and candidate_type == "experiential"


def _window_summaries(values: list[str], *, window_size: int) -> list[dict[str, Any]]:
    if len(values) < window_size:
        return []
    rows: list[dict[str, Any]] = []
    for index in range(len(values) - window_size + 1):
        subset = values[index : index + window_size]
        rows.append(
            {
                "start": index + 1,
                "end": index + window_size,
                "has_experiential": "experiential" in subset,
                "has_inferential": "inferential" in subset,
            }
        )
    return rows


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


def _dialect_fatigue_rate(values: list[str]) -> float:
    if len(values) < 2:
        return 0.0
    same_edges = sum(1 for left, right in zip(values, values[1:]) if left == right)
    return round(same_edges / (len(values) - 1), 4)
