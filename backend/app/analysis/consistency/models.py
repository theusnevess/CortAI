from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ConsistencyCheckResult:
    check_id: str
    status: str
    expected: int | None = None
    found: int | None = None
    missing_count: int | None = None
    details: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConsistencySummary:
    status: str
    generated_at: str
    checks_run: int
    checks_failed: int
    checks: list[ConsistencyCheckResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "generated_at": self.generated_at,
            "summary_counts": {
                "checks_run": self.checks_run,
                "checks_failed": self.checks_failed,
            },
            "checks": [item.to_dict() for item in self.checks],
        }

