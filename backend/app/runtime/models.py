from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class TaskType(str, Enum):
    """Tipos de task suportados pelo runtime distribuido v1.0."""

    WINDOW_AGGREGATION = "WINDOW_AGGREGATION"
    WINDOW_POST_PIPELINE = "WINDOW_POST_PIPELINE"
    EVENT_INDEX_REBUILD = "EVENT_INDEX_REBUILD"


class TaskStatus(str, Enum):
    """Estados canonicos de uma task distribuida."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    NOOP = "NOOP"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class DistributedTask:
    """Representa uma unidade de trabalho distribuida."""

    task_id: str
    task_type: TaskType
    account_id: str | None
    window_id: str | None
    op_key: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    status: TaskStatus = TaskStatus.PENDING
    attempt_count: int = 0
    max_attempts: int = 3
    worker_id: str | None = None
    last_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["task_type"] = self.task_type.value
        payload["status"] = self.status.value
        return payload
