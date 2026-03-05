from __future__ import annotations

from pathlib import Path
from typing import Any

from app.data.window_metrics.repo import get_by_key as get_window_metrics_by_key
from app.guard.data_consistency.errors import ConsistencyViolationBlocked
from app.guard.data_consistency.guard import run_data_consistency_guard
from app.product.scorecard.generator import generate_real_batch_scorecard
from app.product.scorecard.repo import save_scorecard


def generate_scorecard_for_window(
    *,
    account_id: str,
    window_id: str,
    generated_at: str,
    deps: dict[str, Any],
    scorecard_path: Path | None = None,
) -> dict[str, Any]:
    """Executa guard + geração do scorecard com persistência idempotente."""
    guard_result = run_data_consistency_guard(account_id, window_id, deps)
    if guard_result.blocked:
        raise ConsistencyViolationBlocked()

    window_metrics_path = deps.get("window_metrics_path")
    window_metrics = get_window_metrics_by_key(
        account_id,
        window_id,
        path=Path(window_metrics_path) if window_metrics_path is not None else None,
    )
    if window_metrics is None:
        raise ValueError("ContractViolation: window_metrics not found")

    scorecard = generate_real_batch_scorecard(window_metrics=window_metrics, generated_at=generated_at)
    write_action = save_scorecard(scorecard, path=scorecard_path)
    return {"scorecard": scorecard, "write_action": write_action}

