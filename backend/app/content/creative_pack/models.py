from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CreativePack:
    creative_pack_id: str
    account_id: str
    policy_stage: str
    theme: str
    variation_index: int
    angle: str
    title: str
    hook_candidates: list[str]
    script_skeleton: str
    hashtags: list[str]
    cta: str
    strategy_patch_id: str | None
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CreativePackGenerationResult:
    status: str
    creative_packs: list[CreativePack]
    actions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "creative_packs": [item.to_dict() for item in self.creative_packs],
            "actions": list(self.actions),
        }
