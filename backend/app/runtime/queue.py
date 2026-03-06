from __future__ import annotations

from dataclasses import replace
from threading import Lock

from app.runtime.models import DistributedTask, TaskStatus


class InMemoryTaskQueue:
    """Fila local e thread-safe para validar execucao distribuida v1.0."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._tasks: dict[str, DistributedTask] = {}
        self._order: list[str] = []

    def enqueue(self, task: DistributedTask) -> DistributedTask:
        with self._lock:
            existing = self._tasks.get(task.task_id)
            if existing is not None:
                return existing
            self._tasks[task.task_id] = task
            self._order.append(task.task_id)
            return task

    def claim_next(self, worker_id: str) -> DistributedTask | None:
        with self._lock:
            for task_id in self._order:
                current = self._tasks[task_id]
                if current.status != TaskStatus.PENDING:
                    continue
                updated = replace(
                    current,
                    status=TaskStatus.RUNNING,
                    attempt_count=current.attempt_count + 1,
                    worker_id=worker_id,
                    last_error=None,
                )
                self._tasks[task_id] = updated
                return updated
        return None

    def update(
        self,
        task_id: str,
        *,
        status: TaskStatus,
        worker_id: str | None = None,
        last_error: str | None = None,
    ) -> DistributedTask:
        with self._lock:
            current = self._tasks[task_id]
            updated = replace(
                current,
                status=status,
                worker_id=worker_id or current.worker_id,
                last_error=last_error,
            )
            self._tasks[task_id] = updated
            return updated

    def requeue(self, task_id: str, *, last_error: str | None = None) -> DistributedTask:
        with self._lock:
            current = self._tasks[task_id]
            updated = replace(
                current,
                status=TaskStatus.PENDING,
                last_error=last_error,
            )
            self._tasks[task_id] = updated
            return updated

    def get(self, task_id: str) -> DistributedTask:
        with self._lock:
            return self._tasks[task_id]

    def pending_count(self) -> int:
        with self._lock:
            return sum(1 for task in self._tasks.values() if task.status == TaskStatus.PENDING)
