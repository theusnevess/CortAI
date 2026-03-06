from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RolloutConfig:
    """Configuração de rollout controlado do Batch-0 real."""

    enabled: bool = False
    kill_switch_enabled: bool = False
    allowlisted_accounts: set[str] = field(default_factory=set)
    allowed_stages: set[str] = field(default_factory=set)
    rollout_name: str = "pilot_batch_72h"
