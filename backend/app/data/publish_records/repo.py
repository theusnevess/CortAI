from __future__ import annotations

from pathlib import Path
from typing import Any

from app.data.publish_records.store_jsonl import read_all_records


def _matches_scope(item: dict[str, Any], account_id: str, platform: str) -> bool:
    return item.get("account_id") == account_id and item.get("platform") == platform


def get_by_job(
    job_id: str,
    account_id: str,
    platform: str,
    *,
    path: Path | None = None,
) -> dict[str, Any] | None:
    records = read_all_records() if path is None else read_all_records(path)
    posted = [
        item
        for item in records
        if item.get("job_id") == job_id
        and _matches_scope(item, account_id, platform)
        and item.get("status") == "posted"
    ]
    if not posted:
        return None
    return posted[-1]


def get_by_video(
    video_id: str,
    account_id: str,
    platform: str,
    *,
    path: Path | None = None,
) -> dict[str, Any] | None:
    records = read_all_records() if path is None else read_all_records(path)
    posted = [
        item
        for item in records
        if item.get("video_id") == video_id
        and _matches_scope(item, account_id, platform)
        and item.get("status") == "posted"
    ]
    if not posted:
        return None
    return posted[-1]
