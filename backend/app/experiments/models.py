from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

ALLOWED_SCOPES = {"CREATIVE_PACK", "HOOK_STYLE", "PACING_PROFILE", "PUBLISH_WINDOW"}
ALLOWED_STATUSES = {"DRAFT", "ACTIVE", "PAUSED", "ARCHIVED"}
ALLOWED_VARIANTS = {"A", "B"}


@dataclass(frozen=True)
class Experiment:
    experiment_id: str
    name: str
    scope: str
    variant_a: dict[str, Any]
    variant_b: dict[str, Any]
    status: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExperimentAssignment:
    assignment_id: str
    experiment_id: str
    subject_key: str
    variant: str
    assigned_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExperimentResult:
    result_id: str
    experiment_id: str
    subject_key: str
    variant: str
    window_id: str
    metrics: dict[str, Any]
    recorded_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
