from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.product.attribution.errors import AttributionConflictError
from app.product.attribution.schema import validate_content_attribution
from app.product.attribution.store_jsonl import append_attribution, read_all_attributions


def _canonical_payload(record: dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def get_by_publish_id(
    publish_id: str,
    *,
    path: Path | None = None,
) -> dict[str, Any] | None:
    rows = read_all_attributions() if path is None else read_all_attributions(path)
    found: dict[str, Any] | None = None
    for row in rows:
        if row.get("publish_id") == publish_id:
            found = row
    return found


def save_if_absent(
    attribution: dict[str, Any],
    *,
    path: Path | None = None,
) -> str:
    """Persiste attribution com idempotência por publish_id."""
    normalized = validate_content_attribution(attribution)
    publish_id = str(normalized["publish_id"])
    existing = get_by_publish_id(publish_id, path=path)
    if existing is None:
        if path is None:
            append_attribution(normalized)
        else:
            append_attribution(normalized, path=path)
        return "WRITTEN"
    if _canonical_payload(existing) == _canonical_payload(normalized):
        return "NOOP"
    raise AttributionConflictError()

