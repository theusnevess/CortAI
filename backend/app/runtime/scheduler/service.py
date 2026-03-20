from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.runtime.models import DistributedTask
from app.runtime.queue import InMemoryTaskQueue
from app.runtime.rollout.config import RolloutConfig
from app.runtime.rollout.policy import evaluate_rollout_account
from app.runtime.scheduler.candidate_universe import expand_candidate_universe
from app.runtime.scheduler.feed_composition import compose_feed_candidates
from app.runtime.scheduler.feed_distribution import reorder_feed_candidates
from app.runtime.scheduler.models import ScheduleKind, SchedulePlan, SchedulerTaskRequest
from app.runtime.scheduler.planner import build_schedule_plan


@dataclass(frozen=True)
class SchedulerService:
    """Planeja tasks e enfileira com idempotencia por op_key."""

    queue: InMemoryTaskQueue
    scheduler_id: str
    rollout_config: RolloutConfig | None = None

    def plan(
        self,
        *,
        account_ids: list[str],
        schedule_kind: ScheduleKind,
        now: datetime | None = None,
        stage_by_account: dict[str, str] | None = None,
    ) -> SchedulePlan:
        eligible_accounts = account_ids
        if self.rollout_config is not None:
            eligible_accounts = [
                account_id
                for account_id in account_ids
                if evaluate_rollout_account(
                    account_id=account_id,
                    policy_stage=(stage_by_account or {}).get(account_id),
                    config=self.rollout_config,
                ).allowed
            ]
        return build_schedule_plan(
            account_ids=eligible_accounts,
            schedule_kind=schedule_kind,
            scheduler_id=self.scheduler_id,
            now=now,
            stage_by_account=stage_by_account,
        )

    def enqueue_plan(self, plan: SchedulePlan) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        for request in plan.tasks:
            results.append(self.enqueue_if_absent(request))
        return results

    def enqueue_if_absent(self, request: SchedulerTaskRequest) -> dict[str, str]:
        if self.rollout_config is not None:
            decision = evaluate_rollout_account(
                account_id=request.account_id,
                policy_stage=str(request.payload.get("policy_stage") or ""),
                config=self.rollout_config,
            )
            if not decision.allowed:
                return {"status": "BLOCKED", "task_id": "", "op_key": request.op_key, "reason_code": decision.reason_code}
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

    def reorder_feed_candidates(self, candidates: list[dict[str, object]]) -> tuple[list[dict[str, object]], int]:
        return reorder_feed_candidates(candidates)

    def compose_feed_candidates(
        self,
        candidates: list[dict[str, object]],
        *,
        target_size: int | None = None,
    ) -> tuple[list[dict[str, object]], dict[str, object]]:
        return compose_feed_candidates(candidates, target_size=target_size)

    def expand_candidate_universe(self, candidates: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, object]]:
        return expand_candidate_universe(candidates)

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
