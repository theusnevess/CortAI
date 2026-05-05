from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.runtime.models import TaskType
from app.runtime.queue import InMemoryTaskQueue
from app.runtime.scheduler.models import ScheduleKind, SchedulerTaskRequest
from app.runtime.scheduler.service import SchedulerService


class DistributedSchedulerD21Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.queue = InMemoryTaskQueue()
        self.scheduler = SchedulerService(queue=self.queue, scheduler_id="sched-1")
        self.now = datetime(2026, 3, 6, 12, 0, 0, tzinfo=timezone.utc)

    def test_gera_task_correta_para_janela_72h(self) -> None:
        plan = self.scheduler.plan(
            account_ids=["acc_001"],
            schedule_kind=ScheduleKind.EVERY_72H,
            now=self.now,
        )

        self.assertEqual(len(plan.tasks), 2)
        self.assertEqual(plan.tasks[0].task_type, TaskType.WINDOW_AGGREGATION)
        self.assertEqual(plan.tasks[1].task_type, TaskType.WINDOW_POST_PIPELINE)
        self.assertIn("w_2026-03-03T12:00:00Z_2026-03-06T12:00:00Z", plan.tasks[0].window_id)

    def test_nao_duplica_task_ja_agendada(self) -> None:
        plan = self.scheduler.plan(
            account_ids=["acc_001"],
            schedule_kind=ScheduleKind.EVERY_72H,
            now=self.now,
        )
        first = self.scheduler.enqueue_plan(plan)
        second = self.scheduler.enqueue_plan(plan)

        self.assertTrue(all(item["status"] == "WRITTEN" for item in first))
        self.assertTrue(all(item["status"] == "NOOP" for item in second))

    def test_restart_do_scheduler_nao_duplica(self) -> None:
        plan = self.scheduler.plan(
            account_ids=["acc_001"],
            schedule_kind=ScheduleKind.EVERY_72H,
            now=self.now,
        )
        self.scheduler.enqueue_plan(plan)

        restarted = SchedulerService(queue=self.queue, scheduler_id="sched-1-restarted")
        second = restarted.enqueue_plan(plan)
        self.assertTrue(all(item["status"] == "NOOP" for item in second))

    def test_multiplas_contas_geram_filas_independentes(self) -> None:
        plan = self.scheduler.plan(
            account_ids=["acc_001", "acc_002", "acc_003"],
            schedule_kind=ScheduleKind.EVERY_72H,
            now=self.now,
        )

        self.assertEqual(len(plan.tasks), 6)
        account_ids = {task.account_id for task in plan.tasks}
        self.assertEqual(account_ids, {"acc_001", "acc_002", "acc_003"})

    def test_integracao_com_queue_respeita_op_key(self) -> None:
        request = SchedulerTaskRequest(
            task_type=TaskType.WINDOW_AGGREGATION,
            account_id="acc_001",
            scheduled_for="2026-03-06T12:00:00Z",
            window_id="w_001",
            op_key="AGG:acc_001:w_001",
            payload={"window_id": "w_001"},
        )
        first = self.scheduler.enqueue_if_absent(request)
        conflict = self.scheduler.enqueue_if_absent(
            SchedulerTaskRequest(
                task_type=TaskType.WINDOW_AGGREGATION,
                account_id="acc_001",
                scheduled_for="2026-03-06T12:00:00Z",
                window_id="w_001",
                op_key="AGG:acc_001:w_001",
                payload={"window_id": "w_001", "different": True},
            )
        )

        self.assertEqual(first["status"], "WRITTEN")
        self.assertEqual(conflict["status"], "CONFLICT")

    def test_scheduled_for_e_window_id_corretos(self) -> None:
        plan = self.scheduler.plan(
            account_ids=["acc_001"],
            schedule_kind=ScheduleKind.DAILY,
            now=self.now,
        )

        self.assertEqual(len(plan.tasks), 1)
        self.assertEqual(plan.tasks[0].scheduled_for, "2026-03-06T12:00:00Z")
        self.assertIsNone(plan.tasks[0].window_id)


if __name__ == "__main__":
    unittest.main()
