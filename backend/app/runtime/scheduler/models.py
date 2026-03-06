from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from app.runtime.models import TaskType


class ScheduleKind(str, Enum):
    """Tipos de schedule suportados pelo D21."""

    EVERY_72H = "EVERY_72H"
    DAILY = "DAILY"
    MANUAL = "MANUAL"


@dataclass(frozen=True)
class SchedulerTaskRequest:
    """Pedido de agendamento para uma task futura."""

    task_type: TaskType
    account_id: str
    scheduled_for: str
    window_id: str | None
    op_key: str
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["task_type"] = self.task_type.value
        return payload


@dataclass(frozen=True)
class SchedulePlan:
    """Plano deterministico produzido pelo scheduler."""

    schedule_kind: ScheduleKind
    scheduler_id: str
    generated_at: str
    tasks: list[SchedulerTaskRequest]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schedule_kind": self.schedule_kind.value,
            "scheduler_id": self.scheduler_id,
            "generated_at": self.generated_at,
            "tasks": [task.to_dict() for task in self.tasks],
        }
