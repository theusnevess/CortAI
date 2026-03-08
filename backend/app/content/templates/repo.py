from __future__ import annotations

import json
from pathlib import Path

from app.content.templates.store_jsonl import append_template, read_all_templates


class ContentTemplateConflictError(ValueError):
    pass


def _canonical_payload(record: dict) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def list_templates(*, path: Path | None = None) -> list[dict]:
    rows = read_all_templates() if path is None else read_all_templates(path)
    return sorted(rows, key=lambda item: (str(item.get("template_type") or ""), str(item.get("template_id") or "")))


def get_template_by_id(template_id: str, *, path: Path | None = None) -> dict | None:
    found: dict | None = None
    for row in list_templates(path=path):
        if row.get("template_id") == template_id:
            found = row
    return found


def save_template_if_absent(template: dict, *, path: Path | None = None) -> str:
    existing = get_template_by_id(str(template["template_id"]), path=path)
    if existing is None:
        if path is None:
            append_template(template)
        else:
            append_template(template, path)
        return "WRITTEN"
    if _canonical_payload(existing) == _canonical_payload(template):
        return "NOOP"
    raise ContentTemplateConflictError("CONTENT_TEMPLATE_CONFLICT")

