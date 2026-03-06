from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path

from app.runtime.paths import resolve_out_dir


@dataclass(frozen=True)
class RolloutConfig:
    """Configuração de rollout controlado do Batch-0 real."""

    enabled: bool = False
    kill_switch_enabled: bool = False
    allowlisted_accounts: set[str] = field(default_factory=set)
    allowed_stages: set[str] = field(default_factory=set)
    rollout_name: str = "pilot_batch_72h"


def apply_runtime_rollout_overrides(config: RolloutConfig, *, base_dir: Path | None = None) -> RolloutConfig:
    """Aplica override operacional persistido sem relaxar a policy base."""
    path = (base_dir or resolve_out_dir()) / "ops" / "operator_control.json"
    if not path.exists():
        return config
    payload = json.loads(path.read_text(encoding="utf-8"))
    return replace(
        config,
        enabled=bool(payload.get("rollout_enabled", config.enabled)),
        kill_switch_enabled=bool(payload.get("kill_switch_enabled", config.kill_switch_enabled)),
    )
