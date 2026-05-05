from __future__ import annotations

import os
import re
from collections import Counter
from typing import Any


def candidate_universe_expansion_enabled() -> bool:
    return os.getenv("CORTAI_EXPERIMENT_CANDIDATE_UNIVERSE_EXPANSION", "1") != "0"


def expand_candidate_universe(
    candidates: list[dict[str, Any]],
    *,
    enabled: bool | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    active = candidate_universe_expansion_enabled() if enabled is None else enabled
    expanded: list[dict[str, Any]] = []
    inferential_expansions = 0
    document_subtypes = Counter()

    for item in candidates:
        candidate = dict(item)
        if not active:
            expanded.append(candidate)
            continue

        original_hook_type = str(candidate.get("hook_type") or "")
        original_anchor = str(candidate.get("visual_anchor") or "")
        hook_text = str(candidate.get("hook_text") or "")

        if original_hook_type != "inferential" and _eligible_for_inferential_supply(hook_text):
            candidate["hook_type"] = "inferential"
            inferential_expansions += 1

        candidate["visual_anchor_family"] = original_anchor
        candidate["expansion_applied"] = False
        candidate["expansion_reason"] = "no_valid_expansion"

        if original_anchor == "document":
            subtype = _document_subtype(hook_text)
            if subtype != "document":
                candidate["visual_anchor"] = subtype
                candidate["expansion_applied"] = True
                candidate["expansion_reason"] = "document_subtype_expanded"
                document_subtypes[subtype] += 1
            else:
                document_subtypes["document"] += 1
        elif candidate.get("hook_type") == "inferential" and original_hook_type != "inferential":
            candidate["expansion_applied"] = True
            candidate["expansion_reason"] = "inferential_supply_expanded"

        expanded.append(candidate)

    expansion_note = {
        "expansion_applied": inferential_expansions > 0 or bool(document_subtypes),
        "inferential_expansions": inferential_expansions,
        "document_subtype_distribution": dict(document_subtypes),
        "reason": "expansion_applied" if inferential_expansions > 0 or bool(document_subtypes) else "no_valid_expansion",
    }
    return expanded, expansion_note


def summarize_expanded_pool(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    hook_types = Counter(str(item.get("hook_type") or "") for item in candidates if str(item.get("hook_type") or ""))
    anchors = Counter(str(item.get("visual_anchor") or "") for item in candidates if str(item.get("visual_anchor") or ""))
    document_subtypes = Counter(
        str(item.get("visual_anchor") or "")
        for item in candidates
        if str(item.get("visual_anchor_family") or item.get("visual_anchor") or "") == "document"
    )
    total = len(candidates)
    inferential_count = hook_types.get("inferential", 0)

    dominant_hook_type_share = round(max(hook_types.values()) / total, 4) if total and hook_types else 0.0
    dominant_visual_anchor_share = round(max(anchors.values()) / total, 4) if total and anchors else 0.0

    return {
        "total_candidates": total,
        "inferential_supply_rate": round(inferential_count / total, 4) if total else 0.0,
        "hook_type_balance": dict(hook_types),
        "dominant_hook_type_share": dominant_hook_type_share,
        "dominant_visual_anchor_share": dominant_visual_anchor_share,
        "document_subtype_distribution": dict(document_subtypes),
        "visual_anchor_distribution": dict(anchors),
    }


def _eligible_for_inferential_supply(hook_text: str) -> bool:
    text = _normalize(hook_text)
    inferential_objects = (
        " LOG ",
        " RECORD ",
        " TRANSCRIPT ",
        " ARCHIVE ",
        " FILE ",
        " STATEMENT ",
        " TAPE ",
        " LEDGER ",
        " TIMETABLE ",
        " BLUEPRINT ",
        " MAP ",
        " PAGE ",
    )
    inferential_markers = (
        " MISSING ",
        " CHANGED ",
        " CONFLICTING ",
        " CONTRADICTION ",
        " DID NOT MATCH ",
        " FUTURE ",
        " DATE ",
        " TIMESTAMP ",
        " OVERRIDE ",
        " UNAUTHORIZED ",
        " DIFFERENT ",
        " KEPT CHANGING ",
        " CONTAINED ",
        " SHOWED ",
    )
    has_object = any(token in text for token in inferential_objects)
    has_marker = any(token in text for token in inferential_markers)
    return has_object and has_marker


def _document_subtype(hook_text: str) -> str:
    text = _normalize(hook_text)
    if any(token in text for token in (" TRANSCRIPT ", " STATEMENT ")):
        return "transcript_sheet"
    if any(token in text for token in (" DATE ", " TIMESTAMP ", " FUTURE ")):
        return "timestamp_closeup"
    if any(token in text for token in (" ARCHIVE ", " OVERRIDE ", " SERVER ", " LOG ")):
        return "terminal_log"
    if any(token in text for token in (" EVIDENCE ", " TAPE ")):
        return "evidence_board"
    if any(token in text for token in (" REDACTED ", " SEALED CALL ")):
        return "document_redacted"
    if any(token in text for token in (" LEDGER ", " RECORD ", " FILE ", " PAGE ")):
        return "document_printed"
    if any(token in text for token in (" CONFLICTING ", " MISSING ", " CHANGED ", " CONTRADICTION ")):
        return "document_annotated"
    return "document"


def _normalize(value: str) -> str:
    text = value.upper()
    text = re.sub(r"[^A-Z0-9\\s]", " ", text)
    text = re.sub(r"\\s+", " ", text).strip()
    return f" {text} "
