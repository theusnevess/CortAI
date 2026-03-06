from __future__ import annotations

from dataclasses import dataclass

from app.runtime.models import DistributedTask
from app.runtime.rollout.config import RolloutConfig


@dataclass(frozen=True)
class RolloutDecision:
    """Resultado determinístico da avaliação da policy de rollout."""

    allowed: bool
    reason_code: str


def evaluate_rollout_account(
    *,
    account_id: str,
    policy_stage: str | None,
    config: RolloutConfig,
) -> RolloutDecision:
    if not config.enabled:
        return RolloutDecision(False, "ROLLOUT_DISABLED")
    if config.kill_switch_enabled:
        return RolloutDecision(False, "ROLL_OUT_KILL_SWITCH")
    if config.allowlisted_accounts and account_id not in config.allowlisted_accounts:
        return RolloutDecision(False, "ROLLOUT_ACCOUNT_NOT_ALLOWED")
    normalized_stage = (policy_stage or "").strip().upper()
    if config.allowed_stages and normalized_stage not in config.allowed_stages:
        return RolloutDecision(False, "ROLLOUT_STAGE_NOT_ALLOWED")
    return RolloutDecision(True, "ROLLOUT_ALLOWED")


def evaluate_rollout_task(task: DistributedTask, *, config: RolloutConfig) -> RolloutDecision:
    policy_stage = str(task.payload.get("policy_stage") or "")
    return evaluate_rollout_account(
        account_id=str(task.account_id or ""),
        policy_stage=policy_stage,
        config=config,
    )
