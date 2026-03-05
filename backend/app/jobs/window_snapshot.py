from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.data.window_snapshots.store_jsonl import (
    DEFAULT_WINDOW_SNAPSHOTS_PATH,
    save_window_snapshot_if_absent,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_window_snapshot(
    *,
    account_id: str,
    window_id: str,
    publish_ids: list[str],
    video_ids: list[str],
    captured_range: dict[str, str],
    source_refs: dict[str, str],
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Monta snapshot imutavel da janela para proteger execucao D10."""
    return {
        "account_id": account_id,
        "window_id": window_id,
        "publish_ids": sorted(set(publish_ids)),
        "video_ids": sorted(set(video_ids)),
        "captured_range": dict(captured_range),
        "source_refs": dict(source_refs),
        "generated_at": generated_at or _utc_now_iso(),
    }


def ensure_window_snapshot(
    *,
    account_id: str,
    window_id: str,
    publish_ids: list[str],
    video_ids: list[str],
    captured_range: dict[str, str],
    source_refs: dict[str, str],
    path: Path = DEFAULT_WINDOW_SNAPSHOTS_PATH,
) -> dict[str, Any]:
    """Cria snapshot uma unica vez e retorna status WRITTEN ou NOOP."""
    snapshot = build_window_snapshot(
        account_id=account_id,
        window_id=window_id,
        publish_ids=publish_ids,
        video_ids=video_ids,
        captured_range=captured_range,
        source_refs=source_refs,
    )
    status = save_window_snapshot_if_absent(snapshot, path=path)
    return {"status": status, "snapshot": snapshot}
