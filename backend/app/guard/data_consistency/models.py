from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Violation:
    check_id: str
    reason_code: str
    severity: str
    action: str
    status: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GuardResult:
    ok: bool
    blocked: bool
    reason_code: str
    violations: list[Violation]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blocked": self.blocked,
            "reason_code": self.reason_code,
            "violations": [violation.to_dict() for violation in self.violations],
        }

