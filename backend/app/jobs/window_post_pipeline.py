from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.jobs.models import WindowPostPipelineResult


class GuardService(Protocol):
    def __call__(self, *, account_id: str, window_id: str) -> dict[str, Any]:
        ...


class ScorecardService(Protocol):
    def __call__(self, *, account_id: str, window_id: str) -> dict[str, Any]:
        ...


class AttributionService(Protocol):
    def __call__(self, *, account_id: str, window_id: str) -> dict[str, Any]:
        ...


class StrategyLearningService(Protocol):
    def __call__(self, *, account_id: str, window_id: str) -> dict[str, Any]:
        ...


class ExecutionRepo(Protocol):
    def has_op(self, op_key: str) -> bool:
        ...

    def mark_op(self, op_key: str) -> None:
        ...


@dataclass(frozen=True)
class WindowPostPipelineDeps:
    """Dependências injetáveis para o D10."""

    guard_service: GuardService
    scorecard_service: ScorecardService
    attribution_service: AttributionService
    strategy_learning_service: StrategyLearningService
    execution_repo: ExecutionRepo | None = None


def _error_code_from_exception(exc: Exception) -> str:
    message = str(exc).strip()
    if message:
        return message
    return exc.__class__.__name__


def run_window_post_pipeline(
    *,
    account_id: str,
    window_id: str,
    deps: WindowPostPipelineDeps,
    op_key: str | None = None,
) -> WindowPostPipelineResult:
    """Executa wiring mínimo D10 com guard obrigatório."""
    effective_op_key = op_key or f"D10:{account_id}:{window_id}"

    if deps.execution_repo is not None and deps.execution_repo.has_op(effective_op_key):
        return WindowPostPipelineResult(
            status="NOOP_EXECUTION",
            reason_code="OP_KEY_ALREADY_DONE",
            account_id=account_id,
            window_id=window_id,
            op_key=effective_op_key,
            blocked=False,
            scorecard_status="NOT_RUN",
            attribution_status="NOT_RUN",
            learning_status="NOT_RUN",
            details={},
        )

    guard_result = deps.guard_service(account_id=account_id, window_id=window_id)
    if bool(guard_result.get("blocked")):
        if deps.execution_repo is not None:
            deps.execution_repo.mark_op(effective_op_key)
        return WindowPostPipelineResult(
            status="SKIPPED_BLOCKED",
            reason_code="CONSISTENCY_VIOLATION_BLOCKED",
            account_id=account_id,
            window_id=window_id,
            op_key=effective_op_key,
            blocked=True,
            scorecard_status="NOT_RUN",
            attribution_status="NOT_RUN",
            learning_status="NOT_RUN",
            details={"guard_result": guard_result},
        )

    try:
        scorecard_result = deps.scorecard_service(account_id=account_id, window_id=window_id)
    except Exception as exc:  # noqa: BLE001 - erro controlado para retorno de pipeline.
        return WindowPostPipelineResult(
            status="FAILED_SCORECARD",
            reason_code=_error_code_from_exception(exc),
            account_id=account_id,
            window_id=window_id,
            op_key=effective_op_key,
            blocked=False,
            scorecard_status="ERROR",
            attribution_status="NOT_RUN",
            learning_status="NOT_RUN",
            details={},
        )

    scorecard_status = str(scorecard_result.get("status", "WRITTEN"))
    if scorecard_status in {"SKIPPED", "NOT_GENERATED"}:
        if deps.execution_repo is not None:
            deps.execution_repo.mark_op(effective_op_key)
        return WindowPostPipelineResult(
            status="SKIPPED_SCORECARD",
            reason_code="SCORECARD_NOT_GENERATED",
            account_id=account_id,
            window_id=window_id,
            op_key=effective_op_key,
            blocked=False,
            scorecard_status=scorecard_status,
            attribution_status="NOT_RUN",
            learning_status="NOT_RUN",
            details={"scorecard_result": scorecard_result},
        )

    try:
        attribution_result = deps.attribution_service(account_id=account_id, window_id=window_id)
    except Exception as exc:  # noqa: BLE001 - erro controlado para retorno de pipeline.
        reason_code = _error_code_from_exception(exc)
        if reason_code == "ATTRIBUTION_METRICS_MISSING":
            if deps.execution_repo is not None:
                deps.execution_repo.mark_op(effective_op_key)
            return WindowPostPipelineResult(
                status="SKIPPED_ATTRIBUTION_MISSING",
                reason_code="ATTRIBUTION_METRICS_MISSING",
                account_id=account_id,
                window_id=window_id,
                op_key=effective_op_key,
                blocked=False,
                scorecard_status=scorecard_status,
                attribution_status="SKIPPED",
                learning_status="NOT_RUN",
                details={},
            )
        return WindowPostPipelineResult(
            status="FAILED_ATTRIBUTION",
            reason_code=reason_code,
            account_id=account_id,
            window_id=window_id,
            op_key=effective_op_key,
            blocked=False,
            scorecard_status=scorecard_status,
            attribution_status="ERROR",
            learning_status="NOT_RUN",
            details={},
        )

    attribution_status = str(attribution_result.get("status", "WRITTEN"))

    try:
        learning_result = deps.strategy_learning_service(account_id=account_id, window_id=window_id)
    except Exception as exc:  # noqa: BLE001 - erro controlado para retorno de pipeline.
        return WindowPostPipelineResult(
            status="FAILED_LEARNING",
            reason_code=_error_code_from_exception(exc),
            account_id=account_id,
            window_id=window_id,
            op_key=effective_op_key,
            blocked=False,
            scorecard_status=scorecard_status,
            attribution_status=attribution_status,
            learning_status="ERROR",
            details={},
        )

    learning_status = str(learning_result.get("status", "WRITTEN"))
    final_status = "FINISHED"
    final_reason = "PIPELINE_OK"
    if learning_status == "CONFLICT":
        final_status = "FINISHED_CONFLICT"
        final_reason = "STRATEGY_PATCH_CONFLICT"

    if deps.execution_repo is not None:
        deps.execution_repo.mark_op(effective_op_key)

    return WindowPostPipelineResult(
        status=final_status,
        reason_code=final_reason,
        account_id=account_id,
        window_id=window_id,
        op_key=effective_op_key,
        blocked=False,
        scorecard_status=scorecard_status,
        attribution_status=attribution_status,
        learning_status=learning_status,
        details={
            "scorecard_result": scorecard_result,
            "attribution_result": attribution_result,
            "learning_result": learning_result,
        },
    )

