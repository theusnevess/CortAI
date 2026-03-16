from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class VideoQcInput:
    render_job_id: str
    video_path: str
    audio_path: str
    metadata_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VideoQcDecision:
    status: Literal["APPROVE", "REJECT"]
    reasons: list[str] = field(default_factory=list)
    checked_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VideoQcResult:
    status: Literal["APPROVE", "REJECT"]
    reasons: list[str] = field(default_factory=list)
    checked_at: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
