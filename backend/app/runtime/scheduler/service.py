from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.runtime.models import DistributedTask
from app.runtime.queue import InMemoryTaskQueue
from app.runtime.scheduler.models import ScheduleKind, SchedulePlan, SchedulerTaskRequest
from app.runtime.scheduler.planner import build_schedule_plan


@dataclass(frozen=True)
class SchedulerService:
    """Planeja tasks e enfileira com idempotencia por op_key."""

    queue: InMemoryTaskQueue
    scheduler_id: str

    def plan(
        self,
        *,
        account_ids: list[str],
        schedule_kind: ScheduleKind,
        now: datetime | None = None,
    ) -> SchedulePlan:
        return build_schedule_plan(
            account_ids=account_ids,
            schedule_kind=schedule_kind,
            scheduler_id=self.scheduler_id,
            now=now,
        )

    def enqueue_plan(self, plan: SchedulePlan) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        for request in plan.tasks:
            results.append(self.enqueue_if_absent(request))
        return results

    def enqueue_if_absent(self, request: SchedulerTaskRequest) -> dict[str, str]:
        materialized_payload = self._materialize_payload(request)
        existing = self.queue.find_by_op_key(request.op_key)
        if existing is not None:
            if self._semantic_payload(existing.payload) == self._semantic_payload(materialized_payload):
                return {"status": "NOOP", "task_id": existing.task_id, "op_key": request.op_key}
            return {"status": "CONFLICT", "task_id": existing.task_id, "op_key": request.op_key}

        task = DistributedTask(
            task_id=f"task_{uuid4().hex}",
            task_type=request.task_type,
            account_id=request.account_id,
            window_id=request.window_id,
            op_key=request.op_key,
            payload=materialized_payload,
            created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        self.queue.enqueue(task)
        return {"status": "WRITTEN", "task_id": task.task_id, "op_key": request.op_key}

    def _materialize_payload(self, request: SchedulerTaskRequest) -> dict[str, str]:
        return {
            **request.payload,
            "scheduled_for": request.scheduled_for,
            "scheduler_id": self.scheduler_id,
        }

    def _semantic_payload(self, payload: dict[str, str]) -> dict[str, str]:
        normalized = dict(payload)
        normalized.pop("scheduler_id", None)
        return normalized
