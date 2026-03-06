from __future__ import annotations

import sys
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.concurrency.idempotency import IdempotencyManager
from app.concurrency.lease import LeaseManager
from app.runtime.executor import RuntimeExecutorDeps, RuntimeTemporaryError
from app.runtime.models import DistributedTask, TaskStatus, TaskType
from app.runtime.queue import InMemoryTaskQueue
from app.runtime.worker import WorkerRunner


class FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class DistributedExecutionD20Tests(unittest.TestCase):
    def _deps(self, *, clock: FakeClock | None = None, event_sink: list[dict] | None = None):
        active_clock = clock or FakeClock()
        events = event_sink if event_sink is not None else []
        concurrency_events: list[dict] = []
        lease_manager = LeaseManager(clock=active_clock, event_sink=concurrency_events.append)
        idempotency_manager = IdempotencyManager(
            clock=active_clock,
            event_sink=concurrency_events.append,
            event_source=lambda: list(concurrency_events),
        )
        calls: list[str] = []

        def window_handler(task: DistributedTask) -> dict:
            calls.append(task.task_id)
            return {"status": "SUCCEEDED"}

        deps = RuntimeExecutorDeps(
            lease_manager=lease_manager,
            idempotency_manager=idempotency_manager,
            handlers={
                TaskType.WINDOW_AGGREGATION: window_handler,
                TaskType.WINDOW_POST_PIPELINE: window_handler,
                TaskType.EVENT_INDEX_REBUILD: window_handler,
            },
            event_sink=events.append,
            lease_ttl_s=5,
        )
        return deps, calls, active_clock, events

    def _task(self, *, task_id: str = "task-1", op_key: str = "AGG:acc:w1", payload: dict | None = None) -> DistributedTask:
        return DistributedTask(
            task_id=task_id,
            task_type=TaskType.WINDOW_AGGREGATION,
            account_id="acc_001",
            window_id="w_001",
            op_key=op_key,
            payload=payload or {"task": task_id},
            created_at="2026-03-06T00:00:00Z",
        )

    def test_um_worker_processa_task_com_sucesso(self) -> None:
        deps, calls, _, _ = self._deps()
        queue = InMemoryTaskQueue()
        queue.enqueue(self._task())
        worker = WorkerRunner.create(queue=queue, deps=deps, prefix="w")

        result = worker.run_once()

        self.assertIsNotNone(result)
        self.assertEqual(result.status, TaskStatus.SUCCEEDED)
        self.assertEqual(calls, ["task-1"])
        self.assertEqual(queue.get("task-1").status, TaskStatus.SUCCEEDED)

    def test_dois_workers_pega_mesma_task_so_um_executa(self) -> None:
        deps, calls, _, _ = self._deps()
        queue = InMemoryTaskQueue()
        queue.enqueue(self._task())
        worker_a = WorkerRunner.create(queue=queue, deps=deps, prefix="wa")
        worker_b = WorkerRunner.create(queue=queue, deps=deps, prefix="wb")
        results: list[object] = []

        def run(worker: WorkerRunner) -> None:
            results.append(worker.run_once())

        threads = [threading.Thread(target=run, args=(worker_a,)), threading.Thread(target=run, args=(worker_b,))]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(len(calls), 1)
        self.assertEqual(sum(1 for item in results if item is not None), 1)

    def test_task_duplicada_mesmo_op_key_vira_noop(self) -> None:
        deps, calls, _, _ = self._deps()
        queue = InMemoryTaskQueue()
        shared_payload = {"v": 1}
        queue.enqueue(self._task(task_id="task-1", op_key="AGG:acc:w1", payload=shared_payload))
        queue.enqueue(self._task(task_id="task-2", op_key="AGG:acc:w1", payload=shared_payload))
        worker = WorkerRunner.create(queue=queue, deps=deps, prefix="w")

        first = worker.run_once()
        second = worker.run_once()

        self.assertEqual(first.status, TaskStatus.SUCCEEDED)
        self.assertEqual(second.status, TaskStatus.NOOP)
        self.assertEqual(len(calls), 1)

    def test_falha_temporaria_faz_retry_seguro(self) -> None:
        clock = FakeClock()
        events: list[dict] = []
        concurrency_events: list[dict] = []
        lease_manager = LeaseManager(clock=clock, event_sink=concurrency_events.append)
        idempotency_manager = IdempotencyManager(
            clock=clock,
            event_sink=concurrency_events.append,
            event_source=lambda: list(concurrency_events),
        )
        attempts = {"count": 0}

        def flaky_handler(task: DistributedTask) -> dict:
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise RuntimeTemporaryError("TEMP_FAILURE")
            return {"status": "SUCCEEDED"}

        deps = RuntimeExecutorDeps(
            lease_manager=lease_manager,
            idempotency_manager=idempotency_manager,
            handlers={TaskType.WINDOW_AGGREGATION: flaky_handler},
            event_sink=events.append,
            lease_ttl_s=5,
        )
        queue = InMemoryTaskQueue()
        queue.enqueue(self._task())
        worker = WorkerRunner.create(queue=queue, deps=deps, prefix="w")

        first = worker.run_once()
        second = worker.run_once()

        self.assertEqual(first.status, TaskStatus.FAILED)
        self.assertTrue(first.retryable)
        self.assertEqual(second.status, TaskStatus.SUCCEEDED)
        self.assertEqual(queue.get("task-1").status, TaskStatus.SUCCEEDED)

    def test_lease_expirada_aborta_corretamente(self) -> None:
        deps, _, clock, _ = self._deps()

        def expiring_handler(task: DistributedTask) -> dict:
            clock.advance(10)
            return {"status": "SUCCEEDED"}

        deps.handlers[TaskType.WINDOW_AGGREGATION] = expiring_handler
        queue = InMemoryTaskQueue()
        queue.enqueue(self._task())
        worker = WorkerRunner.create(queue=queue, deps=deps, prefix="w")

        result = worker.run_once()

        self.assertEqual(result.status, TaskStatus.BLOCKED)
        self.assertEqual(result.reason_code, "LEASE_EXPIRED")
        self.assertEqual(queue.get("task-1").status, TaskStatus.BLOCKED)

    def test_observabilidade_registra_worker_id_op_key_task_id(self) -> None:
        events: list[dict] = []
        deps, _, _, events = self._deps(event_sink=events)
        queue = InMemoryTaskQueue()
        queue.enqueue(self._task())
        worker = WorkerRunner.create(queue=queue, deps=deps, prefix="worker")

        worker.run_once()

        self.assertTrue(any(event.get("task_id") == "task-1" for event in events))
        self.assertTrue(any(event.get("op_key") == "AGG:acc:w1" for event in events))
        self.assertTrue(any(str(event.get("worker_id", "")).startswith("worker:") for event in events))


if __name__ == "__main__":
    unittest.main()
