from __future__ import annotations

from typing import Any


def dedup_key(record: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(record["account_id"]),
        str(record["video_id"]),
        str(record["captured_window_id"]),
    )


def same_dedup_key(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return dedup_key(a) == dedup_key(b)
