from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class StrategyPatchApplyResult:
    """Resultado consolidado da aplicação de patch no registry."""

    status: str
    reason_code: str
    account_id: str
    window_id: str
    policy_stage: str
    patch_id: str
    event_type: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

