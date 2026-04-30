from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class VideoQcInput:
    render_job_id: str
    video_path: str
    audio_path: str
    metadata_path: str | None = None
    script_text: str = ""
    tts_trace: dict[str, Any] = field(default_factory=dict)
    visual_trace: dict[str, Any] = field(default_factory=dict)
    edit_trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VideoQcDecision:
    status: Literal["APPROVE", "HOLD", "REJECT"]
    publishable: bool = False
    hard_failures: list[str] = field(default_factory=list)
    soft_failures: list[str] = field(default_factory=list)
    product_vetoes: list[str] = field(default_factory=list)
    score_summary: dict[str, float] = field(default_factory=dict)
    product_signals: dict[str, Any] = field(default_factory=dict)
    decision_trace: dict[str, Any] = field(default_factory=dict)
    checked_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VideoQcResult:
    decision: VideoQcDecision
    status: Literal["APPROVE", "HOLD", "REJECT"]
    reasons: list[str] = field(default_factory=list)
    checked_at: str = ""
    publishable: bool = False
    details: dict[str, Any] = field(default_factory=dict)
    qc_input_governance: dict[str, Any] = field(default_factory=dict)
    qc_evidence_scoring: dict[str, Any] = field(default_factory=dict)
    decision_semantics: dict[str, Any] = field(default_factory=dict)
    qc_trace: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    confidence_level: str = ""
    confidence_components: dict[str, float] = field(default_factory=dict)
    confidence_rationale: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
