from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BaseOperatorActionRequest(BaseModel):
    operator_id: str
    reason: str


class PauseRolloutRequest(BaseOperatorActionRequest):
    pass


class ResumeRolloutRequest(BaseOperatorActionRequest):
    pass


class RequeueTaskRequest(BaseOperatorActionRequest):
    task_id: str
    task_type: str
    status: str
    op_key: str
    account_id: str | None = None
    window_id: str | None = None


class RebuildEventIndexRequest(BaseOperatorActionRequest):
    pass


class AckAlertRequest(BaseOperatorActionRequest):
    alert_code: str


class OperatorActionResponse(BaseModel):
    action_type: str
    status: str
    reason_code: str
    target_id: str
    details: dict[str, Any] = Field(default_factory=dict)


class OperatorActionErrorResponse(BaseModel):
    error: dict[str, Any]
