from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_WINDOW_SNAPSHOTS_PATH = Path("OUT/data/window_snapshots.jsonl")


_REQUIRED_FIELDS = {
    "account_id",
    "window_id",
    "publish_ids",
    "video_ids",
    "captured_range",
    "source_refs",
    "generated_at",
}


def _canonical_payload(record: dict[str, Any]) -> str:
    comparable = dict(record)
    # generated_at e metadado de auditoria e nao deve quebrar idempotencia.
    comparable.pop("generated_at", None)
    return json.dumps(comparable, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _validate_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(f for f in _REQUIRED_FIELDS if f not in snapshot)
    if missing:
        raise ValueError(f"SNAPSHOT_MISSING_FIELDS:{','.join(missing)}")
    if not isinstance(snapshot["account_id"], str) or not snapshot["account_id"]:
        raise ValueError("SNAPSHOT_INVALID_ACCOUNT")
    if not isinstance(snapshot["window_id"], str) or not snapshot["window_id"]:
        raise ValueError("SNAPSHOT_INVALID_WINDOW")
    return dict(snapshot)


def append_window_snapshot(
    snapshot: dict[str, Any],
    *,
    path: Path = DEFAULT_WINDOW_SNAPSHOTS_PATH,
) -> None:
    """Escreve snapshot em JSONL append-only."""
    normalized = _validate_snapshot(snapshot)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(normalized, ensure_ascii=False, sort_keys=True) + "\n")
        f.flush()


def read_all_window_snapshots(*, path: Path = DEFAULT_WINDOW_SNAPSHOTS_PATH) -> list[dict[str, Any]]:
    """Le snapshots em ordem de gravacao."""
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def get_window_snapshot(
    account_id: str,
    window_id: str,
    *,
    path: Path = DEFAULT_WINDOW_SNAPSHOTS_PATH,
) -> dict[str, Any] | None:
    """Retorna ultimo snapshot para a chave canonica (account_id, window_id)."""
    found: dict[str, Any] | None = None
    for row in read_all_window_snapshots(path=path):
        if row.get("account_id") == account_id and row.get("window_id") == window_id:
            found = row
    return found


def save_window_snapshot_if_absent(
    snapshot: dict[str, Any],
    *,
    path: Path = DEFAULT_WINDOW_SNAPSHOTS_PATH,
) -> str:
    """Salva snapshot uma unica vez; conflito estrutural gera erro explicito."""
    normalized = _validate_snapshot(snapshot)
    existing = get_window_snapshot(normalized["account_id"], normalized["window_id"], path=path)
    if existing is None:
        append_window_snapshot(normalized, path=path)
        return "WRITTEN"

    if _canonical_payload(existing) == _canonical_payload(normalized):
        return "NOOP"

    raise ValueError("SNAPSHOT_CONFLICT")
