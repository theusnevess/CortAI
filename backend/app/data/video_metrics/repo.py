from __future__ import annotations

from pathlib import Path
from typing import Any

from app.data.video_metrics.precedence import compare_sources
from app.data.video_metrics.store_jsonl import read_all_records


def _is_same_key(
    item: dict[str, Any],
    *,
    account_id: str,
    video_id: str,
    captured_window_id: str,
) -> bool:
    return (
        item.get("account_id") == account_id
        and item.get("video_id") == video_id
        and item.get("captured_window_id") == captured_window_id
    )


def _choose_best(current: dict[str, Any] | None, candidate: dict[str, Any]) -> dict[str, Any]:
    if current is None:
        return candidate
    comparison = compare_sources(str(candidate["source_kind"]), str(current["source_kind"]))
    if comparison > 0:
        return candidate
    if comparison < 0:
        return current

    current_ts = str(current.get("ingested_at") or "")
    candidate_ts = str(candidate.get("ingested_at") or "")
    if candidate_ts >= current_ts:
        return candidate
    return current


def get_best(
    account_id: str,
    video_id: str,
    captured_window_id: str,
    *,
    path: Path | None = None,
) -> dict[str, Any] | None:
    records = read_all_records() if path is None else read_all_records(path)
    best: dict[str, Any] | None = None
    for item in records:
        if _is_same_key(
            item,
            account_id=account_id,
            video_id=video_id,
            captured_window_id=captured_window_id,
        ):
            best = _choose_best(best, item)
    return best


def list_for_window(
    account_id: str,
    captured_window_id: str,
    *,
    path: Path | None = None,
) -> list[dict[str, Any]]:
    records = read_all_records() if path is None else read_all_records(path)
    by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in records:
        if item.get("account_id") != account_id or item.get("captured_window_id") != captured_window_id:
            continue
        key = (
            str(item["account_id"]),
            str(item["video_id"]),
            str(item["captured_window_id"]),
        )
        by_key[key] = _choose_best(by_key.get(key), item)
    return list(by_key.values())
