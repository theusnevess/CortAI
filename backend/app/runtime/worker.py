from __future__ import annotations

from dataclasses import dataclass

from app.runtime.executor import RuntimeExecutorDeps, TaskExecutionResult, build_worker_id, execute_task
from app.runtime.models import TaskStatus
from app.runtime.queue import InMemoryTaskQueue


@dataclass
class WorkerRunner:
    """Worker local para consumir tasks da fila distribuida v1.0."""

    queue: InMemoryTaskQueue
    deps: RuntimeExecutorDeps
    worker_id: str

    @classmethod
    def create(cls, *, queue: InMemoryTaskQueue, deps: RuntimeExecutorDeps, prefix: str = "worker") -> "WorkerRunner":
        return cls(queue=queue, deps=deps, worker_id=build_worker_id(prefix))

    def run_once(self) -> TaskExecutionResult | None:
        task = self.queue.claim_next(self.worker_id)
        if task is None:
            return None

        result = execute_task(task, deps=self.deps, worker_id=self.worker_id)
        if result.status in {TaskStatus.SUCCEEDED, TaskStatus.NOOP, TaskStatus.BLOCKED}:
            self.queue.update(
                task.task_id,
                status=result.status,
                worker_id=self.worker_id,
                last_error=None if result.status != TaskStatus.BLOCKED else result.reason_code,
            )
            return result

        current = self.queue.get(task.task_id)
        if result.retryable and current.attempt_count < current.max_attempts:
            self.queue.requeue(task.task_id, last_error=result.reason_code)
        else:
            self.queue.update(
                task.task_id,
                status=TaskStatus.FAILED,
                worker_id=self.worker_id,
                last_error=result.reason_code,
            )
        return result

    def run_until_empty(self, max_iterations: int = 1000) -> list[TaskExecutionResult]:
        results: list[TaskExecutionResult] = []
        for _ in range(max_iterations):
            result = self.run_once()
            if result is None:
                break
            results.append(result)
        return results
