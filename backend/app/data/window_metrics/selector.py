from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.data.publish_records.store_jsonl import read_all_records


def _parse_iso8601_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("ContractViolation: invalid ISO8601 value")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("ContractViolation: invalid ISO8601 value") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def build_window_id(window_start: str, window_end: str) -> str:
    """Monta o identificador canônico da janela."""
    return f"w_{window_start}_{window_end}"


def select_window_video_ids(
    account_id: str,
    window_start: str,
    window_end: str,
    *,
    path: Path | None = None,
) -> list[str]:
    """Seleciona video_ids publicados na janela para uma conta."""
    start_dt = _parse_iso8601_utc(window_start)
    end_dt = _parse_iso8601_utc(window_end)
    if end_dt <= start_dt:
        raise ValueError("ContractViolation: window_end must be greater than window_start")

    records = read_all_records() if path is None else read_all_records(path)
    selected: list[tuple[datetime, str]] = []

    for item in records:
        if item.get("account_id") != account_id:
            continue
        if item.get("status") != "posted":
            continue
        video_id = item.get("video_id")
        if not isinstance(video_id, str) or not video_id.strip():
            continue
        published_at = item.get("published_at")
        if not isinstance(published_at, str):
            continue
        published_at_dt = _parse_iso8601_utc(published_at)
        if start_dt <= published_at_dt < end_dt:
            selected.append((published_at_dt, video_id.strip()))

    # Ordenacao deterministica: primeiro por data de publicacao, depois por video_id.
    selected.sort(key=lambda row: (row[0], row[1]))
    return [video_id for _, video_id in selected]

