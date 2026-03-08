from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.content.templates.library import default_templates
from app.content.templates.models import ContentTemplate
from app.content.templates.repo import (
    get_template_by_id,
    list_templates as repo_list_templates,
    save_template_if_absent,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class ContentTemplateService:
    output_path: Path = Path("OUT/content/templates/templates.jsonl")

    def bootstrap_defaults(self, *, created_at: str | None = None) -> list[str]:
        timestamp = created_at or _now_iso()
        actions: list[str] = []
        for template in default_templates(created_at=timestamp):
            actions.append(save_template_if_absent(template.to_dict(), path=self.output_path))
        return actions

    def list_templates(self) -> list[dict[str, Any]]:
        return repo_list_templates(path=self.output_path)

    def get_template(self, template_id: str) -> dict[str, Any] | None:
        return get_template_by_id(template_id, path=self.output_path)

    def select_templates_by_type(self, template_type: str) -> list[dict[str, Any]]:
        rows = [row for row in self.list_templates() if row.get("template_type") == template_type]
        return sorted(rows, key=lambda item: str(item.get("template_id") or ""))

    def generate_template_variations(self, template_id: str, *, count: int = 2) -> list[dict[str, Any]]:
        template = self.get_template(template_id)
        if template is None:
            raise ValueError("CONTENT_TEMPLATE_NOT_FOUND")
        if count < 1:
            raise ValueError("CONTENT_TEMPLATE_VARIATION_COUNT_INVALID")
        variations: list[dict[str, Any]] = []
        for variation_index in range(1, count + 1):
            variations.append(
                {
                    "template_id": str(template["template_id"]),
                    "variation_index": variation_index,
                    "template_type": str(template["template_type"]),
                    "hook_pattern": f'{template["hook_pattern"]} [v{variation_index}]',
                    "body_pattern": f'{template["body_pattern"]} [v{variation_index}]',
                    "cta_pattern": str(template["cta_pattern"]),
                    "structure": list(template.get("structure") or []),
                    "tags": list(template.get("tags") or []),
                }
            )
        return variations

