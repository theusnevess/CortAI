from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ContentTemplate:
    template_id: str
    template_type: str
    structure: list[str]
    hook_pattern: str
    body_pattern: str
    cta_pattern: str
    tags: list[str]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

