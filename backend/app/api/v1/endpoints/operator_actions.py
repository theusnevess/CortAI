from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.v1.dependencies.control_plane_auth import (
    ControlPlaneIdentity,
    require_control_plane_admin,
)
from app.api.v1.schemas.operator_actions import (
    AckAlertRequest,
    OperatorActionErrorResponse,
    OperatorActionResponse,
    PauseRolloutRequest,
    RebuildEventIndexRequest,
    RequeueTaskRequest,
    ResumeRolloutRequest,
)
from app.ops.actions.policy import OperatorActionPolicyError
from app.ops.actions.service import OperatorActionError, OperatorActionService

router = APIRouter(dependencies=[Depends(require_control_plane_admin)])


def _service() -> OperatorActionService:
    return OperatorActionService()


def _handle_action(callable_):
    try:
        return callable_().to_dict()
    except (OperatorActionPolicyError, OperatorActionError) as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message, "details": {}}},
        )


@router.post("/pause-rollout", response_model=OperatorActionResponse, responses={400: {"model": OperatorActionErrorResponse}, 409: {"model": OperatorActionErrorResponse}})
def pause_rollout(payload: PauseRolloutRequest, identity: ControlPlaneIdentity = Depends(require_control_plane_admin)):
    service = _service()
    return _handle_action(lambda: service.pause_rollout(operator_id=identity.subject, reason=payload.reason))


@router.post("/resume-rollout", response_model=OperatorActionResponse, responses={400: {"model": OperatorActionErrorResponse}, 409: {"model": OperatorActionErrorResponse}})
def resume_rollout(payload: ResumeRolloutRequest, identity: ControlPlaneIdentity = Depends(require_control_plane_admin)):
    service = _service()
    return _handle_action(lambda: service.resume_rollout(operator_id=identity.subject, reason=payload.reason))


@router.post("/requeue-task", response_model=OperatorActionResponse, responses={400: {"model": OperatorActionErrorResponse}, 409: {"model": OperatorActionErrorResponse}})
def requeue_task(payload: RequeueTaskRequest, identity: ControlPlaneIdentity = Depends(require_control_plane_admin)):
    service = _service()
    return _handle_action(
        lambda: service.requeue_task(
            operator_id=identity.subject,
            reason=payload.reason,
            task_id=payload.task_id,
            task_type=payload.task_type,
            status=payload.status,
            op_key=payload.op_key,
            account_id=payload.account_id,
            window_id=payload.window_id,
        )
    )


@router.post("/rebuild-event-index", response_model=OperatorActionResponse, responses={400: {"model": OperatorActionErrorResponse}, 409: {"model": OperatorActionErrorResponse}})
def rebuild_event_index(payload: RebuildEventIndexRequest, identity: ControlPlaneIdentity = Depends(require_control_plane_admin)):
    service = _service()
    return _handle_action(lambda: service.rebuild_event_index(operator_id=identity.subject, reason=payload.reason))


@router.post("/ack-alert", response_model=OperatorActionResponse, responses={400: {"model": OperatorActionErrorResponse}, 409: {"model": OperatorActionErrorResponse}})
def ack_alert(payload: AckAlertRequest, identity: ControlPlaneIdentity = Depends(require_control_plane_admin)):
    service = _service()
    return _handle_action(
        lambda: service.acknowledge_alert(
            operator_id=identity.subject,
            reason=payload.reason,
            alert_code=payload.alert_code,
        )
    )
