from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.content.creative_pack.store_jsonl import append_pack, read_all_packs


class CreativePackConflictError(ValueError):
    pass


def _canonical_payload(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def get_by_id(creative_pack_id: str, *, path: Path | None = None) -> dict[str, Any] | None:
    rows = read_all_packs() if path is None else read_all_packs(path)
    found: dict[str, Any] | None = None
    for row in rows:
        if row.get("creative_pack_id") == creative_pack_id:
            found = row
    return found


def save_if_absent(pack: dict[str, Any], *, path: Path | None = None) -> str:
    existing = get_by_id(str(pack["creative_pack_id"]), path=path)
    if existing is None:
        if path is None:
            append_pack(pack)
        else:
            append_pack(pack, path)
        return "WRITTEN"
    if _canonical_payload(existing) == _canonical_payload(pack):
        return "NOOP"
    raise CreativePackConflictError("CREATIVE_PACK_CONFLICT")
