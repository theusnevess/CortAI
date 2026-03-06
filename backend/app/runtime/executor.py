from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from socket import gethostname
from typing import Any, Callable

from app.concurrency.errors import LeaseDeniedError
from app.concurrency.idempotency import IdempotencyManager, payload_hash
from app.concurrency.lease import LeaseManager
from app.runtime.models import DistributedTask, TaskStatus, TaskType
from app.runtime.rollout.config import RolloutConfig
from app.runtime.rollout.policy import evaluate_rollout_task


class RuntimeTemporaryError(RuntimeError):
    """Falha temporaria que permite retry controlado."""


TaskHandler = Callable[[DistributedTask], Any]
EventSink = Callable[[dict[str, Any]], None]


@dataclass(frozen=True)
class RuntimeExecutorDeps:
    """Dependencias do executor distribuido do D20."""

    lease_manager: LeaseManager
    idempotency_manager: IdempotencyManager
    handlers: dict[TaskType, TaskHandler]
    event_sink: EventSink | None = None
    lease_ttl_s: int = 120
    rollout_config: RolloutConfig | None = None


@dataclass(frozen=True)
class TaskExecutionResult:
    """Resultado consolidado de execucao de uma task."""

    task_id: str
    status: TaskStatus
    reason_code: str
    worker_id: str
    op_key: str
    retryable: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


def execute_task(task: DistributedTask, *, deps: RuntimeExecutorDeps, worker_id: str) -> TaskExecutionResult:
    """Executa uma task com lease, idempotencia e observabilidade minima."""
    handler = deps.handlers[task.task_type]
    lease_key = _lease_key_for(task)
    if deps.rollout_config is not None:
        decision = evaluate_rollout_task(task, config=deps.rollout_config)
        if not decision.allowed:
            return _finish(
                deps,
                task=task,
                worker_id=worker_id,
                status=TaskStatus.BLOCKED,
                reason_code=decision.reason_code,
            )
    _emit_event(
        deps,
        event_type="RUNTIME/task_started",
        task=task,
        worker_id=worker_id,
        reason_code="TASK_STARTED",
    )

    try:
        lease_handle = deps.lease_manager.acquire_lease(lease_key, deps.lease_ttl_s, worker_id)
    except LeaseDeniedError:
        return _finish(
            deps,
            task=task,
            worker_id=worker_id,
            status=TaskStatus.BLOCKED,
            reason_code="LEASE_DENIED",
        )

    try:
        reserve_status = deps.idempotency_manager.idempotency_check_or_reserve(
            task.op_key,
            payload_hash(task.payload),
        )
        if reserve_status == "NOOP":
            if task.attempt_count > 1:
                reserve_status = "WRITTEN"
            else:
                deps.idempotency_manager.finalize_op(task.op_key, TaskStatus.NOOP.value)
                return _finish(
                    deps,
                    task=task,
                    worker_id=worker_id,
                    status=TaskStatus.NOOP,
                    reason_code="IDEMPOTENCY_NOOP",
                )
        if reserve_status == "CONFLICT":
            return _finish(
                deps,
                task=task,
                worker_id=worker_id,
                status=TaskStatus.BLOCKED,
                reason_code="IDEMPOTENCY_CONFLICT",
            )

        result = handler(task)
        if not deps.lease_manager.is_lease_active(lease_handle):
            return _finish(
                deps,
                task=task,
                worker_id=worker_id,
                status=TaskStatus.BLOCKED,
                reason_code="LEASE_EXPIRED",
            )

        final_status = _map_handler_status(result)
        deps.idempotency_manager.finalize_op(task.op_key, final_status.value)
        return _finish(
            deps,
            task=task,
            worker_id=worker_id,
            status=final_status,
            reason_code="TASK_SUCCEEDED" if final_status == TaskStatus.SUCCEEDED else final_status.value,
        )
    except RuntimeTemporaryError as exc:
        return _finish(
            deps,
            task=task,
            worker_id=worker_id,
            status=TaskStatus.FAILED,
            reason_code=str(exc) or "TEMPORARY_FAILURE",
            retryable=task.attempt_count < task.max_attempts,
        )
    except Exception as exc:  # noqa: BLE001
        return _finish(
            deps,
            task=task,
            worker_id=worker_id,
            status=TaskStatus.FAILED,
            reason_code=str(exc) or exc.__class__.__name__,
            retryable=False,
        )
    finally:
        if "lease_handle" in locals():
            deps.lease_manager.release_lease(lease_handle)


def build_worker_id(prefix: str = "worker") -> str:
    """Gera identidade observavel para o worker atual."""
    return f"{prefix}:{gethostname()}:{os.getpid()}"


def _map_handler_status(result: Any) -> TaskStatus:
    if isinstance(result, dict):
        status = str(result.get("status", "SUCCEEDED")).upper()
        if status in TaskStatus.__members__:
            return TaskStatus[status]
    return TaskStatus.SUCCEEDED


def _lease_key_for(task: DistributedTask) -> str:
    if task.window_id and task.account_id:
        return f"LEASE_WINDOW:{task.account_id}:{task.window_id}"
    if task.account_id:
        return f"LEASE_ACCOUNT:{task.account_id}"
    return f"LEASE_TASK:{task.task_id}"


def _finish(
    deps: RuntimeExecutorDeps,
    *,
    task: DistributedTask,
    worker_id: str,
    status: TaskStatus,
    reason_code: str,
    retryable: bool = False,
) -> TaskExecutionResult:
    _emit_event(
        deps,
        event_type="RUNTIME/task_finished",
        task=task,
        worker_id=worker_id,
        reason_code=reason_code,
        status=status.value,
        retryable=retryable,
    )
    return TaskExecutionResult(
        task_id=task.task_id,
        status=status,
        reason_code=reason_code,
        worker_id=worker_id,
        op_key=task.op_key,
        retryable=retryable,
    )


def _emit_event(
    deps: RuntimeExecutorDeps,
    *,
    event_type: str,
    task: DistributedTask,
    worker_id: str,
    reason_code: str,
    status: str | None = None,
    retryable: bool | None = None,
) -> None:
    if deps.event_sink is None:
        return
    payload = {
        "event_type": event_type,
        "reason_code": reason_code,
        "task_id": task.task_id,
        "task_type": task.task_type.value,
        "account_id": task.account_id,
        "window_id": task.window_id,
        "op_key": task.op_key,
        "worker_id": worker_id,
        "pid": os.getpid(),
        "hostname": gethostname(),
    }
    if status is not None:
        payload["status"] = status
    if retryable is not None:
        payload["retryable"] = retryable
    deps.event_sink(payload)
