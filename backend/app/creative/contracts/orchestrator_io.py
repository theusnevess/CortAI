from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.contracts.creative_pack import CreativePack


@dataclass(frozen=True)
class CreativeOrchestratorInput:
    account_id: str
    niche: str
    topic: str
    publish_slot: str
    force_refresh_trends: bool = False
    creative_pack_id: str | None = None
    experiment_assignment_id: str | None = None
    account_context_ref: str | None = None
    trend_context_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CreativeOrchestratorResult:
    creative_pack: CreativePack
    fallbacks_used: list[str] = field(default_factory=list)
    events_emitted: list[str] = field(default_factory=list)
    qc_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["creative_pack"] = self.creative_pack.to_dict()
        return payload


@dataclass(frozen=True)
class CreativeOrchestratorFailure:
    code: str
    message: str
    fallbacks_used: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
