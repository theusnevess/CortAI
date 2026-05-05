from __future__ import annotations

import os
from collections import Counter
from typing import Any


def feed_candidate_composition_enabled() -> bool:
    return os.getenv("CORTAI_EXPERIMENT_FEED_CANDIDATE_COMPOSITION", "0") == "1"


def compose_feed_candidates(
    candidates: list[dict[str, Any]],
    *,
    target_size: int | None = None,
    enabled: bool | None = None,
    max_dominant_visual_anchor_share: float = 0.6,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ordered_candidates = [dict(item) for item in candidates]
    active = feed_candidate_composition_enabled() if enabled is None else enabled
    requested_size = len(ordered_candidates) if target_size is None else max(0, min(target_size, len(ordered_candidates)))
    if not active or requested_size >= len(ordered_candidates):
        return ordered_candidates[:requested_size], {
            "composition_relaxed": requested_size >= len(ordered_candidates),
            "reason": "insufficient_candidate_diversity" if requested_size >= len(ordered_candidates) else "disabled",
        }

    selected: list[dict[str, Any]] = []
    remaining = [(index, dict(item)) for index, item in enumerate(ordered_candidates)]
    relaxation = {"composition_relaxed": False, "reason": ""}

    while remaining and len(selected) < requested_size:
        ranked: list[tuple[tuple[int, int, int, int], int, dict[str, Any]]] = []
        selected_hook_types = {str(item.get("hook_type") or "") for item in selected if str(item.get("hook_type") or "")}
        available_hook_types = {
            str(item.get("hook_type") or "")
            for _, item in remaining
            if str(item.get("hook_type") or "") in {"experiential", "inferential"}
        }
        missing_hook_types = {"experiential", "inferential"} - selected_hook_types
        missing_hook_types &= available_hook_types

        for remaining_index, (original_index, candidate) in enumerate(remaining):
            candidate_hook_type = str(candidate.get("hook_type") or "")
            candidate_anchor = str(candidate.get("visual_anchor") or "")
            selected_metrics = summarize_candidate_pool(selected)
            candidate_metrics = summarize_candidate_pool(selected + [candidate])

            hook_priority = 0
            if missing_hook_types:
                hook_priority = 0 if candidate_hook_type in missing_hook_types else 1

            visual_priority = 0
            dominant_visual_share = float(candidate_metrics["dominant_visual_anchor_share"])
            if len(selected) >= 2 and dominant_visual_share > max_dominant_visual_anchor_share:
                visual_priority = 1

            score = (
                hook_priority,
                visual_priority,
                selected_metrics["visual_anchor_distribution"].get(candidate_anchor, 0),
                original_index,
            )
            ranked.append((score, remaining_index, candidate))

        ranked.sort(key=lambda item: item[0])
        best_score, chosen_index, chosen = ranked[0]
        if best_score[0] > 0 or best_score[1] > 0:
            relaxation["composition_relaxed"] = True
            if best_score[0] > 0 and missing_hook_types:
                relaxation["reason"] = "insufficient_hook_type_diversity"
            elif best_score[1] > 0:
                relaxation["reason"] = "insufficient_visual_anchor_diversity"
        selected.append(chosen)
        remaining.pop(chosen_index)

    if len(selected) < requested_size:
        relaxation["composition_relaxed"] = True
        relaxation["reason"] = "insufficient_candidate_diversity"
    elif not relaxation["composition_relaxed"]:
        source_metrics = summarize_candidate_pool(ordered_candidates)
        if len(source_metrics["hook_type_balance"]) < 2:
            relaxation["composition_relaxed"] = True
            relaxation["reason"] = "insufficient_hook_type_diversity"
        elif len(source_metrics["visual_anchor_distribution"]) < 2:
            relaxation["composition_relaxed"] = True
            relaxation["reason"] = "insufficient_visual_anchor_diversity"

    return selected, relaxation


def summarize_candidate_pool(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    hook_types = [str(item.get("hook_type") or "") for item in candidates if str(item.get("hook_type") or "")]
    anchors = [str(item.get("visual_anchor") or "") for item in candidates if str(item.get("visual_anchor") or "")]
    hook_counter = Counter(hook_types)
    anchor_counter = Counter(anchors)
    total = len(candidates)

    dominant_hook_type_share = 0.0
    dominant_visual_anchor_share = 0.0
    if total > 0 and hook_counter:
        dominant_hook_type_share = round(max(hook_counter.values()) / total, 4)
    if total > 0 and anchor_counter:
        dominant_visual_anchor_share = round(max(anchor_counter.values()) / total, 4)

    return {
        "total_candidates": total,
        "hook_type_balance": dict(hook_counter),
        "visual_anchor_distribution": dict(anchor_counter),
        "dominant_hook_type_share": dominant_hook_type_share,
        "dominant_visual_anchor_share": dominant_visual_anchor_share,
    }
