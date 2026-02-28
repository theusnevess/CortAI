from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MaestroJob:
    """Representa a execução de um job linear do Maestro em runtime."""

    id: str
    input_ref: str
    status: str = "queued"
    step: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    step_durations_ms: dict[str, int] = field(default_factory=dict)


@dataclass
class MaestroRunResult:
    """Retorno do orquestrador com o job e o estado final compartilhado."""

    job: MaestroJob
    state: dict[str, Any] = field(default_factory=dict)
