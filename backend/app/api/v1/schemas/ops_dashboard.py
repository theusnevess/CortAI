from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthSummaryResponse(BaseModel):
    rollout_enabled: bool
    kill_switch_enabled: bool
    active_critical_alerts: int
    active_alerts: int
    event_query_p95_ms: float | None = None
    fallback_rate: float | None = None
    scheduler_status: str
    workers_status: str


class RolloutStatusResponse(BaseModel):
    rollout_name: str
    batch_summary: dict[str, Any] = Field(default_factory=dict)
    alerts: list[dict[str, Any]] = Field(default_factory=list)


class WindowItem(BaseModel):
    window_id: str
    account_id: str | None = None
    status: str
    scorecard: bool = False
    attribution: bool = False
    strategy_patch: bool = False
    patch_application: str | None = None


class WindowsResponse(BaseModel):
    items: list[WindowItem]


class TaskItem(BaseModel):
    task_id: str
    task_type: str | None = None
    account_id: str | None = None
    window_id: str | None = None
    op_key: str | None = None
    worker_id: str | None = None
    status: str | None = None
    attempt_count: int | None = None
    started_at: str | None = None
    ended_at: str | None = None


class TasksResponse(BaseModel):
    items: list[TaskItem]


class AlertsResponse(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
