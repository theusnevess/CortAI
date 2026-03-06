from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AlertRecord:
    """Alerta operacional derivado da avaliacao de SLO."""

    alert_code: str
    severity: str
    metric_name: str
    reason_code: str
    action: str
    value: float
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
