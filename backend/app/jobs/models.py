from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class WindowPostPipelineResult:
    """Resultado consolidado do pipeline pós-janela (D10)."""

    status: str
    reason_code: str
    account_id: str
    window_id: str
    op_key: str
    blocked: bool
    scorecard_status: str
    attribution_status: str
    learning_status: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

