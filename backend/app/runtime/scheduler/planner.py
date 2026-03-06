from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.runtime.models import TaskType
from app.runtime.scheduler.models import ScheduleKind, SchedulePlan, SchedulerTaskRequest


def build_schedule_plan(
    *,
    account_ids: list[str],
    schedule_kind: ScheduleKind,
    scheduler_id: str,
    now: datetime | None = None,
    stage_by_account: dict[str, str] | None = None,
) -> SchedulePlan:
    """Gera plano deterministico de tasks para a janela do scheduler."""
    current = _ensure_utc(now or datetime.now(timezone.utc))
    tasks: list[SchedulerTaskRequest] = []

    for account_id in account_ids:
        policy_stage = (stage_by_account or {}).get(account_id, "")
        if schedule_kind == ScheduleKind.EVERY_72H:
            window_start = current - timedelta(hours=72)
            window_id = _window_id(window_start, current)
            scheduled_for = current.isoformat().replace("+00:00", "Z")
            tasks.extend(
                [
                    SchedulerTaskRequest(
                        task_type=TaskType.WINDOW_AGGREGATION,
                        account_id=account_id,
                        scheduled_for=scheduled_for,
                        window_id=window_id,
                        op_key=f"AGG:{account_id}:{window_id}",
                        payload={
                            "window_start": window_start.isoformat().replace("+00:00", "Z"),
                            "window_end": scheduled_for,
                            "policy_stage": policy_stage,
                        },
                    ),
                    SchedulerTaskRequest(
                        task_type=TaskType.WINDOW_POST_PIPELINE,
                        account_id=account_id,
                        scheduled_for=scheduled_for,
                        window_id=window_id,
                        op_key=f"D10:{account_id}:{window_id}",
                        payload={"window_id": window_id, "policy_stage": policy_stage},
                    ),
                ]
            )
            continue

        if schedule_kind == ScheduleKind.DAILY:
            scheduled_for = current.isoformat().replace("+00:00", "Z")
            tasks.append(
                SchedulerTaskRequest(
                    task_type=TaskType.EVENT_INDEX_REBUILD,
                    account_id=account_id,
                    scheduled_for=scheduled_for,
                    window_id=None,
                    op_key=f"IDX_REBUILD:{account_id}:{current.date().isoformat()}",
                    payload={"date": current.date().isoformat(), "policy_stage": policy_stage},
                )
            )
            continue

        scheduled_for = current.isoformat().replace("+00:00", "Z")
        tasks.append(
            SchedulerTaskRequest(
                task_type=TaskType.WINDOW_POST_PIPELINE,
                account_id=account_id,
                scheduled_for=scheduled_for,
                window_id=None,
                op_key=f"MANUAL:{account_id}:{scheduled_for}",
                payload={"manual": True, "policy_stage": policy_stage},
            )
        )

    return SchedulePlan(
        schedule_kind=schedule_kind,
        scheduler_id=scheduler_id,
        generated_at=current.isoformat().replace("+00:00", "Z"),
        tasks=tasks,
    )


def _window_id(start: datetime, end: datetime) -> str:
    return f"w_{start.isoformat().replace('+00:00', 'Z')}_{end.isoformat().replace('+00:00', 'Z')}"


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
