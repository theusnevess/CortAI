from __future__ import annotations

from app.jobs.models import WindowPostPipelineResult
from app.jobs.window_post_pipeline import WindowPostPipelineDeps, run_window_post_pipeline


def run_window_pipeline_after_aggregation(
    *,
    account_id: str,
    window_id: str | None,
    deps: WindowPostPipelineDeps,
    window_metrics_persisted: bool,
) -> WindowPostPipelineResult:
    """Integra o D10 após agregação da janela com guard obrigatório."""
    if not window_id:
        return WindowPostPipelineResult(
            status="SKIPPED_INVALID_WINDOW",
            reason_code="WINDOW_ID_MISSING",
            account_id=account_id,
            window_id="",
            op_key=f"D10:{account_id}:",
            blocked=False,
            scorecard_status="NOT_RUN",
            attribution_status="NOT_RUN",
            learning_status="NOT_RUN",
            details={},
        )

    if not window_metrics_persisted:
        return WindowPostPipelineResult(
            status="SKIPPED_WINDOW_NOT_PERSISTED",
            reason_code="WINDOW_METRICS_NOT_PERSISTED",
            account_id=account_id,
            window_id=window_id,
            op_key=f"D10:{account_id}:{window_id}",
            blocked=False,
            scorecard_status="NOT_RUN",
            attribution_status="NOT_RUN",
            learning_status="NOT_RUN",
            details={},
        )

    return run_window_post_pipeline(
        account_id=account_id,
        window_id=window_id,
        deps=deps,
        op_key=f"D10:{account_id}:{window_id}",
    )

