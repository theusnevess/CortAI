from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from time import time
from uuid import uuid4

from app.concurrency.idempotency import IdempotencyManager
from app.concurrency.lease import LeaseManager
from app.observability.event_append.service import append_event, build_event_record
from app.runtime.executor import RuntimeExecutorDeps
from app.runtime.models import DistributedTask, TaskType
from app.runtime.paths import resolve_out_dir
from app.runtime.queue import InMemoryTaskQueue
from app.runtime.rollout.config import RolloutConfig
from app.runtime.rollout.report import write_rollout_report
from app.runtime.scheduler.models import ScheduleKind
from app.runtime.scheduler.service import SchedulerService
from app.runtime.worker import WorkerRunner


def run_pilot_rollout(
    *,
    base_dir: Path | None = None,
    account_ids: list[str] | None = None,
    stage_by_account: dict[str, str] | None = None,
    now: datetime | None = None,
) -> dict[str, object]:
    """Executa um piloto controlado curto e persiste evidências operacionais."""
    out_dir = base_dir or resolve_out_dir()
    rollout_dir = out_dir / "rollout"
    artifacts_dir = rollout_dir / "artifacts"
    accounts = account_ids or [
        "acc_truecrime_001",
        "acc_truecrime_002",
    ]
    stages = stage_by_account or {account_id: "GROWTH" for account_id in accounts}
    current = now or datetime.now(timezone.utc)

    event_path = out_dir / "events" / "events.jsonl"

    def event_sink(payload: dict) -> None:
        event = build_event_record(
            payload["event_type"],
            {
                **payload,
                "event_id": f"evt_{uuid4().hex}",
                "timestamp": _iso_now(),
            },
            writer_id="pilot_runner",
        )
        append_event(event, path=event_path)

    lease_manager = LeaseManager(event_sink=lambda payload: None, clock=time)
    idempotency_manager = IdempotencyManager(event_sink=lambda payload: None, event_source=lambda: [])

    def write_json(path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def aggregation_handler(task: DistributedTask) -> dict:
        target_dir = artifacts_dir / (task.account_id or "unknown") / _safe_fs_name(task.window_id or "window")
        write_json(target_dir / "window_metrics.json", {"window_id": task.window_id, "account_id": task.account_id})
        return {"status": "SUCCEEDED"}

    def post_pipeline_handler(task: DistributedTask) -> dict:
        target_dir = artifacts_dir / (task.account_id or "unknown") / _safe_fs_name(task.window_id or "window")
        write_json(target_dir / "scorecard.json", {"window_id": task.window_id, "status": "READY"})
        write_json(target_dir / "attribution.json", {"window_id": task.window_id, "status": "READY"})
        write_json(target_dir / "strategy_patch.json", {"window_id": task.window_id, "status": "READY"})
        write_json(target_dir / "patch_application.json", {"window_id": task.window_id, "status": "NOOP"})
        return {"status": "SUCCEEDED"}

    rollout_config = RolloutConfig(
        enabled=True,
        kill_switch_enabled=False,
        allowlisted_accounts=set(accounts),
        allowed_stages={"GROWTH"},
        rollout_name="pilot_batch_72h",
    )
    deps = RuntimeExecutorDeps(
        lease_manager=lease_manager,
        idempotency_manager=idempotency_manager,
        handlers={
            TaskType.WINDOW_AGGREGATION: aggregation_handler,
            TaskType.WINDOW_POST_PIPELINE: post_pipeline_handler,
            TaskType.EVENT_INDEX_REBUILD: lambda task: {"status": "SUCCEEDED"},
        },
        event_sink=event_sink,
        rollout_config=rollout_config,
    )

    queue = InMemoryTaskQueue()
    scheduler = SchedulerService(queue=queue, scheduler_id="sched-pilot", rollout_config=rollout_config)
    plan = scheduler.plan(
        account_ids=accounts,
        stage_by_account=stages,
        schedule_kind=ScheduleKind.EVERY_72H,
        now=current,
    )
    enqueue_results = scheduler.enqueue_plan(plan)
    worker = WorkerRunner.create(queue=queue, deps=deps, prefix="worker")
    execution_results = worker.run_until_empty()

    first_window = next((task.window_id for task in plan.tasks if task.window_id), "")
    succeeded = [result for result in execution_results if result.status.value == "SUCCEEDED"]
    all_succeeded = len(succeeded) == len(execution_results) and len(execution_results) > 0
    batch_summary = {
        "batch_id": f"pilot_{current.strftime('%Y%m%d_%H%M%S')}",
        "accounts": len(accounts),
        "windows_processed": len({task.window_id for task in plan.tasks if task.window_id}),
        "window_id": first_window,
        "account_id": accounts[0] if accounts else "",
        "window_metrics": all_succeeded,
        "scorecard": all_succeeded,
        "content_attribution": all_succeeded,
        "strategy_patch": all_succeeded,
        "patch_applied": "NOOP" if all_succeeded else "FAILED",
        "scheduler_enqueued": sum(1 for item in enqueue_results if item["status"] == "WRITTEN"),
        "tasks_executed": len(execution_results),
    }
    alerts: list[dict[str, object]] = []
    paths = write_rollout_report(
        output_dir=rollout_dir,
        rollout_name=rollout_config.rollout_name,
        batch_summary=batch_summary,
        alerts=alerts,
    )
    return {
        "plan_tasks": len(plan.tasks),
        "enqueue_results": enqueue_results,
        "execution_results": [result.to_dict() for result in execution_results],
        "report_paths": [str(path) for path in paths],
        "batch_summary": batch_summary,
    }


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_fs_name(value: str) -> str:
    return value.replace(":", "-")


if __name__ == "__main__":
    payload = run_pilot_rollout()
    print(json.dumps(payload, indent=2, ensure_ascii=False))
