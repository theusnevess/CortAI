from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.concurrency.idempotency import IdempotencyManager
from app.concurrency.lease import LeaseManager
from app.runtime.executor import RuntimeExecutorDeps
from app.runtime.models import DistributedTask, TaskType
from app.runtime.queue import InMemoryTaskQueue
from app.runtime.rollout.config import RolloutConfig
from app.runtime.rollout.report import write_rollout_report
from app.runtime.scheduler.models import ScheduleKind
from app.runtime.scheduler.service import SchedulerService
from app.runtime.worker import WorkerRunner


class FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now


class RealBatchRolloutD23Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.rollout_config = RolloutConfig(
            enabled=True,
            kill_switch_enabled=False,
            allowlisted_accounts={"acc_truecrime_001"},
            allowed_stages={"GROWTH"},
            rollout_name="pilot_batch_72h",
        )
        self.now = datetime(2026, 3, 6, 12, 0, 0, tzinfo=timezone.utc)

    def _deps(self, *, artifacts_dir: Path | None = None, rollout_config: RolloutConfig | None = None):
        events: list[dict] = []
        concurrency_events: list[dict] = []
        clock = FakeClock()
        lease_manager = LeaseManager(clock=clock, event_sink=concurrency_events.append)
        idempotency_manager = IdempotencyManager(
            clock=clock,
            event_sink=concurrency_events.append,
            event_source=lambda: list(concurrency_events),
        )

        def write_json(path: Path, payload: dict) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

        def window_aggregation_handler(task: DistributedTask) -> dict:
            if artifacts_dir is not None:
                write_json(artifacts_dir / "window_metrics.json", {"window_id": task.window_id, "account_id": task.account_id})
            return {"status": "SUCCEEDED"}

        def window_post_handler(task: DistributedTask) -> dict:
            if artifacts_dir is not None:
                write_json(artifacts_dir / "scorecard.json", {"window_id": task.window_id})
                write_json(artifacts_dir / "attribution.json", {"window_id": task.window_id})
                write_json(artifacts_dir / "strategy_patch.json", {"window_id": task.window_id})
                write_json(artifacts_dir / "patch_application.json", {"window_id": task.window_id, "status": "NOOP"})
            return {"status": "SUCCEEDED"}

        return RuntimeExecutorDeps(
            lease_manager=lease_manager,
            idempotency_manager=idempotency_manager,
            handlers={
                TaskType.WINDOW_AGGREGATION: window_aggregation_handler,
                TaskType.WINDOW_POST_PIPELINE: window_post_handler,
                TaskType.EVENT_INDEX_REBUILD: lambda task: {"status": "SUCCEEDED"},
            },
            event_sink=events.append,
            rollout_config=rollout_config or self.rollout_config,
        )

    def test_conta_allowlisted_roda_normalmente(self) -> None:
        queue = InMemoryTaskQueue()
        scheduler = SchedulerService(queue=queue, scheduler_id="sched-1", rollout_config=self.rollout_config)

        plan = scheduler.plan(
            account_ids=["acc_truecrime_001"],
            stage_by_account={"acc_truecrime_001": "GROWTH"},
            schedule_kind=ScheduleKind.EVERY_72H,
            now=self.now,
        )
        result = scheduler.enqueue_plan(plan)

        self.assertEqual(len(plan.tasks), 2)
        self.assertTrue(all(item["status"] == "WRITTEN" for item in result))

    def test_conta_fora_da_allowlist_nao_agenda_task(self) -> None:
        queue = InMemoryTaskQueue()
        scheduler = SchedulerService(queue=queue, scheduler_id="sched-1", rollout_config=self.rollout_config)

        plan = scheduler.plan(
            account_ids=["acc_other_001"],
            stage_by_account={"acc_other_001": "GROWTH"},
            schedule_kind=ScheduleKind.EVERY_72H,
            now=self.now,
        )

        self.assertEqual(plan.tasks, [])
        self.assertEqual(queue.pending_count(), 0)

    def test_rollout_desabilitado_bloqueia_scheduler(self) -> None:
        config = RolloutConfig(enabled=False, allowlisted_accounts={"acc_truecrime_001"}, allowed_stages={"GROWTH"})
        queue = InMemoryTaskQueue()
        scheduler = SchedulerService(queue=queue, scheduler_id="sched-1", rollout_config=config)

        plan = scheduler.plan(
            account_ids=["acc_truecrime_001"],
            stage_by_account={"acc_truecrime_001": "GROWTH"},
            schedule_kind=ScheduleKind.EVERY_72H,
            now=self.now,
        )

        self.assertEqual(plan.tasks, [])

    def test_kill_switch_impede_novas_execucoes(self) -> None:
        config = RolloutConfig(
            enabled=True,
            kill_switch_enabled=True,
            allowlisted_accounts={"acc_truecrime_001"},
            allowed_stages={"GROWTH"},
        )
        queue = InMemoryTaskQueue()
        task = DistributedTask(
            task_id="task_1",
            task_type=TaskType.WINDOW_AGGREGATION,
            account_id="acc_truecrime_001",
            window_id="w_001",
            op_key="AGG:acc_truecrime_001:w_001",
            payload={"policy_stage": "GROWTH"},
            created_at="2026-03-06T12:00:00Z",
        )
        queue.enqueue(task)
        worker = WorkerRunner.create(queue=queue, deps=self._deps(rollout_config=config), prefix="worker")

        result = worker.run_once()

        self.assertIsNotNone(result)
        self.assertEqual(result.reason_code, "ROLL_OUT_KILL_SWITCH")

    def test_worker_respeita_rollout_policy(self) -> None:
        queue = InMemoryTaskQueue()
        task = DistributedTask(
            task_id="task_1",
            task_type=TaskType.WINDOW_AGGREGATION,
            account_id="acc_other_001",
            window_id="w_001",
            op_key="AGG:acc_other_001:w_001",
            payload={"policy_stage": "GROWTH"},
            created_at="2026-03-06T12:00:00Z",
        )
        queue.enqueue(task)
        worker = WorkerRunner.create(queue=queue, deps=self._deps(), prefix="worker")

        result = worker.run_once()

        self.assertIsNotNone(result)
        self.assertEqual(result.reason_code, "ROLLOUT_ACCOUNT_NOT_ALLOWED")

    def test_batch_real_72h_produz_artifacts_esperados(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir) / "OUT" / "rollout" / "artifacts"
            queue = InMemoryTaskQueue()
            scheduler = SchedulerService(queue=queue, scheduler_id="sched-1", rollout_config=self.rollout_config)
            plan = scheduler.plan(
                account_ids=["acc_truecrime_001"],
                stage_by_account={"acc_truecrime_001": "GROWTH"},
                schedule_kind=ScheduleKind.EVERY_72H,
                now=self.now,
            )
            scheduler.enqueue_plan(plan)
            worker = WorkerRunner.create(queue=queue, deps=self._deps(artifacts_dir=artifacts_dir), prefix="worker")
            results = worker.run_until_empty()

            self.assertEqual(len(results), 2)
            self.assertTrue((artifacts_dir / "window_metrics.json").exists())
            self.assertTrue((artifacts_dir / "scorecard.json").exists())
            self.assertTrue((artifacts_dir / "attribution.json").exists())
            self.assertTrue((artifacts_dir / "strategy_patch.json").exists())

            report_paths = write_rollout_report(
                output_dir=Path(tmp_dir) / "OUT" / "rollout",
                rollout_name="pilot_batch_72h",
                batch_summary={
                    "window_metrics": True,
                    "scorecard": True,
                    "content_attribution": True,
                    "strategy_patch": True,
                    "patch_applied": "NOOP",
                },
                alerts=[],
            )
            for path in report_paths:
                self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
