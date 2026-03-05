from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.concurrency.lease import LeaseHandle, LeaseManager
from app.concurrency.idempotency import IdempotencyManager
from app.jobs.models import WindowPostPipelineResult
from app.jobs.window_post_pipeline import WindowPostPipelineDeps, run_window_post_pipeline


@dataclass(frozen=True)
class WindowPipelineD12Deps:
    """Dependencias de concorrencia para hardening D12."""

    lease_manager: LeaseManager
    idempotency_manager: IdempotencyManager
    snapshot_service: Callable[..., dict[str, Any]]
    owner_id: str
    agg_payload_hash: str
    snapshot_kwargs: dict[str, Any]


def _build_skip_result(
    *,
    status: str,
    reason_code: str,
    account_id: str,
    window_id: str,
    op_key: str,
) -> WindowPostPipelineResult:
    return WindowPostPipelineResult(
        status=status,
        reason_code=reason_code,
        account_id=account_id,
        window_id=window_id,
        op_key=op_key,
        blocked=status.startswith("SKIPPED_BLOCKED") or status.startswith("BLOCKED"),
        scorecard_status="NOT_RUN",
        attribution_status="NOT_RUN",
        learning_status="NOT_RUN",
        details={},
    )


def run_window_pipeline_after_aggregation(
    *,
    account_id: str,
    window_id: str | None,
    deps: WindowPostPipelineDeps,
    window_metrics_persisted: bool,
    d12_deps: WindowPipelineD12Deps | None = None,
) -> WindowPostPipelineResult:
    """Integra D10 apos agregacao da janela com opcao de hardening D12."""
    if not window_id:
        return _build_skip_result(
            status="SKIPPED_INVALID_WINDOW",
            reason_code="WINDOW_ID_MISSING",
            account_id=account_id,
            window_id="",
            op_key=f"D10:{account_id}:",
        )

    if not window_metrics_persisted:
        return _build_skip_result(
            status="SKIPPED_WINDOW_NOT_PERSISTED",
            reason_code="WINDOW_METRICS_NOT_PERSISTED",
            account_id=account_id,
            window_id=window_id,
            op_key=f"D10:{account_id}:{window_id}",
        )

    if d12_deps is None:
        return run_window_post_pipeline(
            account_id=account_id,
            window_id=window_id,
            deps=deps,
            op_key=f"D10:{account_id}:{window_id}",
        )

    lease_key = f"LEASE_WINDOW:{account_id}:{window_id}"
    agg_op_key = f"AGG:{account_id}:{window_id}"
    d10_op_key = f"D10:{account_id}:{window_id}"

    try:
        lease_handle = d12_deps.lease_manager.acquire_lease(
            key=lease_key,
            ttl_s=120,
            owner_id=d12_deps.owner_id,
        )
    except Exception:
        return _build_skip_result(
            status="SKIPPED_BLOCKED_LEASE",
            reason_code="LEASE_DENIED",
            account_id=account_id,
            window_id=window_id,
            op_key=agg_op_key,
        )

    try:
        reserve_status = d12_deps.idempotency_manager.idempotency_check_or_reserve(
            agg_op_key,
            d12_deps.agg_payload_hash,
        )
        if reserve_status == "CONFLICT":
            return _build_skip_result(
                status="SKIPPED_BLOCKED_CONFLICT",
                reason_code="IDEMPOTENCY_CONFLICT",
                account_id=account_id,
                window_id=window_id,
                op_key=agg_op_key,
            )
        if reserve_status == "NOOP":
            return _build_skip_result(
                status="NOOP_EXECUTION",
                reason_code="IDEMPOTENCY_NOOP",
                account_id=account_id,
                window_id=window_id,
                op_key=agg_op_key,
            )

        if not d12_deps.lease_manager.is_lease_active(lease_handle):
            return _build_skip_result(
                status="SKIPPED_BLOCKED_LEASE_EXPIRED",
                reason_code="LEASE_EXPIRED",
                account_id=account_id,
                window_id=window_id,
                op_key=agg_op_key,
            )

        snapshot_result = d12_deps.snapshot_service(
            account_id=account_id,
            window_id=window_id,
            **d12_deps.snapshot_kwargs,
        )
        if snapshot_result.get("status") not in {"WRITTEN", "NOOP"}:
            return _build_skip_result(
                status="SKIPPED_BLOCKED_SNAPSHOT",
                reason_code="SNAPSHOT_MISSING",
                account_id=account_id,
                window_id=window_id,
                op_key=agg_op_key,
            )

        if not d12_deps.lease_manager.is_lease_active(lease_handle):
            return _build_skip_result(
                status="SKIPPED_BLOCKED_LEASE_EXPIRED",
                reason_code="LEASE_EXPIRED",
                account_id=account_id,
                window_id=window_id,
                op_key=agg_op_key,
            )

        result = run_window_post_pipeline(
            account_id=account_id,
            window_id=window_id,
            deps=deps,
            op_key=d10_op_key,
        )
        d12_deps.idempotency_manager.finalize_op(agg_op_key, result.status)
        return result
    finally:
        d12_deps.lease_manager.release_lease(lease_handle)
