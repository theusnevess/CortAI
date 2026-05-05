from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.creative.contracts.creative_pack import VoicePlan, VoiceSegmentPlan


VOICE_SEGMENT_TIMING_VERSION = "voice_segment_timing_v2_6"


@dataclass(frozen=True)
class VoiceSegmentTimingAssessment:
    segment_name: str
    present: bool
    rate: float | None
    rate_status: str
    emphasis: str
    emphasis_status: str
    pause_before_ms: int | None
    pause_after_ms: int | None
    pause_status: str
    timing_role: str
    timing_valid: bool
    degraded_fields: list[str] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "segment_name": self.segment_name,
            "present": self.present,
            "rate": self.rate,
            "rate_status": self.rate_status,
            "emphasis": self.emphasis,
            "emphasis_status": self.emphasis_status,
            "pause_before_ms": self.pause_before_ms,
            "pause_after_ms": self.pause_after_ms,
            "pause_status": self.pause_status,
            "timing_role": self.timing_role,
            "timing_valid": self.timing_valid,
            "degraded_fields": list(self.degraded_fields),
            "rationale": list(self.rationale),
        }


@dataclass(frozen=True)
class VoiceTimingContrastSummary:
    contrast_detected: bool
    contrast_level: str
    hook_setup_rate_delta: float | None
    setup_payoff_rate_delta: float | None
    hook_has_attention_pause: bool
    payoff_has_landing_pause: bool
    expected_contrast_present: bool
    degraded_fields: list[str] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contrast_detected": self.contrast_detected,
            "contrast_level": self.contrast_level,
            "hook_setup_rate_delta": self.hook_setup_rate_delta,
            "setup_payoff_rate_delta": self.setup_payoff_rate_delta,
            "hook_has_attention_pause": self.hook_has_attention_pause,
            "payoff_has_landing_pause": self.payoff_has_landing_pause,
            "expected_contrast_present": self.expected_contrast_present,
            "degraded_fields": list(self.degraded_fields),
            "rationale": list(self.rationale),
        }


@dataclass(frozen=True)
class VoiceSegmentTimingResult:
    timing_version: str
    timing_complete: bool
    segment_timing: dict[str, dict[str, Any]]
    timing_contrast: dict[str, Any]
    missing_or_degraded_inputs: list[str]
    boundary_statement: str
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timing_version": self.timing_version,
            "timing_complete": self.timing_complete,
            "segment_timing": {key: dict(value) for key, value in self.segment_timing.items()},
            "timing_contrast": dict(self.timing_contrast),
            "missing_or_degraded_inputs": list(self.missing_or_degraded_inputs),
            "boundary_statement": self.boundary_statement,
            "rationale": list(self.rationale),
        }


class VoiceSegmentTimingAnalyzer:
    """Audits segment timing and pause shape without changing voice synthesis."""

    REQUIRED_SEGMENTS: tuple[str, ...] = ("hook", "setup", "payoff")
    TIMING_ROLES: dict[str, str] = {
        "hook": "attention_open",
        "setup": "context_progression",
        "payoff": "landing_close",
    }

    def analyze(
        self,
        *,
        voice_plan: VoicePlan,
        delivery_semantics: dict[str, Any] | None = None,
    ) -> VoiceSegmentTimingResult:
        del delivery_semantics
        segment_timing = {
            segment_name: self._segment_assessment(
                segment_name=segment_name,
                segment=voice_plan.segments.get(segment_name),
            ).to_dict()
            for segment_name in self.REQUIRED_SEGMENTS
        }
        timing_contrast = self._contrast(segment_timing).to_dict()
        missing_or_degraded_inputs = self._collect_missing_or_degraded(segment_timing, timing_contrast)
        timing_complete = (
            not missing_or_degraded_inputs
            and all(segment["timing_valid"] for segment in segment_timing.values())
            and bool(timing_contrast["expected_contrast_present"])
        )
        rationale = [
            "Segment timing audits rate, emphasis, and pauses only; it does not synthesize or modify audio.",
            "Timing contrast is a deterministic comparison of hook/setup/payoff delivery shape.",
        ]
        if timing_complete:
            rationale.append("All required segments have valid timing fields and expected hook/setup/payoff contrast.")
        else:
            rationale.append("Timing analysis found missing or degraded timing inputs: " + ", ".join(missing_or_degraded_inputs))
        return VoiceSegmentTimingResult(
            timing_version=VOICE_SEGMENT_TIMING_VERSION,
            timing_complete=timing_complete,
            segment_timing=segment_timing,
            timing_contrast=timing_contrast,
            missing_or_degraded_inputs=missing_or_degraded_inputs,
            boundary_statement="Voice timing analysis is audit-only; TTS Router performs synthesis.",
            rationale=rationale,
        )

    def _segment_assessment(
        self,
        *,
        segment_name: str,
        segment: VoiceSegmentPlan | None,
    ) -> VoiceSegmentTimingAssessment:
        if segment is None:
            return VoiceSegmentTimingAssessment(
                segment_name=segment_name,
                present=False,
                rate=None,
                rate_status="missing",
                emphasis="",
                emphasis_status="missing",
                pause_before_ms=None,
                pause_after_ms=None,
                pause_status="missing",
                timing_role=self.TIMING_ROLES[segment_name],
                timing_valid=False,
                degraded_fields=[f"voice_plan.segments.{segment_name}_missing"],
                rationale=[f"{segment_name} timing cannot be assessed because the segment is missing."],
            )
        degraded_fields: list[str] = []
        rate = self._as_float(segment.rate)
        rate_status = self._rate_status(rate)
        if rate_status == "invalid":
            degraded_fields.append(f"voice_plan.segments.{segment_name}.rate_invalid")
        emphasis = str(segment.emphasis or "").strip()
        emphasis_status = self._emphasis_status(emphasis)
        if emphasis_status == "missing":
            degraded_fields.append(f"voice_plan.segments.{segment_name}.emphasis_empty")
        pause_before_ms = self._as_int(segment.pause_before_ms)
        pause_after_ms = self._as_int(segment.pause_after_ms)
        pause_status = self._pause_status(
            segment_name=segment_name,
            pause_before_ms=pause_before_ms,
            pause_after_ms=pause_after_ms,
        )
        if pause_before_ms is None:
            degraded_fields.append(f"voice_plan.segments.{segment_name}.pause_before_ms_invalid")
            pause_before_ms = 0
        if pause_after_ms is None:
            degraded_fields.append(f"voice_plan.segments.{segment_name}.pause_after_ms_invalid")
            pause_after_ms = 0
        if pause_before_ms < 0:
            degraded_fields.append(f"voice_plan.segments.{segment_name}.pause_before_ms_negative")
        if pause_after_ms < 0:
            degraded_fields.append(f"voice_plan.segments.{segment_name}.pause_after_ms_negative")
        timing_valid = not degraded_fields
        rationale = [
            f"{segment_name} timing role is {self.TIMING_ROLES[segment_name]}.",
            f"Rate is classified as {rate_status}; emphasis is classified as {emphasis_status}; pauses are classified as {pause_status}.",
        ]
        if degraded_fields:
            rationale.append("Segment timing has degraded fields: " + ", ".join(degraded_fields))
        return VoiceSegmentTimingAssessment(
            segment_name=segment_name,
            present=True,
            rate=rate,
            rate_status=rate_status,
            emphasis=emphasis,
            emphasis_status=emphasis_status,
            pause_before_ms=pause_before_ms,
            pause_after_ms=pause_after_ms,
            pause_status=pause_status,
            timing_role=self.TIMING_ROLES[segment_name],
            timing_valid=timing_valid,
            degraded_fields=degraded_fields,
            rationale=rationale,
        )

    def _contrast(self, segment_timing: dict[str, dict[str, Any]]) -> VoiceTimingContrastSummary:
        hook = segment_timing["hook"]
        setup = segment_timing["setup"]
        payoff = segment_timing["payoff"]
        rates_available = all(segment["rate"] is not None and segment["rate"] > 0.0 for segment in (hook, setup, payoff))
        hook_setup_delta = self._rounded_delta(hook["rate"], setup["rate"]) if rates_available else None
        setup_payoff_delta = self._rounded_delta(setup["rate"], payoff["rate"]) if rates_available else None
        hook_has_attention_pause = bool((hook["pause_after_ms"] or 0) >= 300)
        payoff_has_landing_pause = bool((payoff["pause_before_ms"] or 0) >= 350)
        emphasis_contrast = hook["emphasis_status"] == "high" and payoff["emphasis_status"] == "high"
        rate_contrast = bool(
            hook_setup_delta is not None
            and setup_payoff_delta is not None
            and abs(hook_setup_delta) >= 0.02
            and abs(setup_payoff_delta) >= 0.02
        )
        contrast_detected = hook_has_attention_pause or payoff_has_landing_pause or emphasis_contrast or rate_contrast
        expected_contrast_present = hook_has_attention_pause and payoff_has_landing_pause and emphasis_contrast
        contrast_level = self._contrast_level(
            rate_contrast=rate_contrast,
            hook_has_attention_pause=hook_has_attention_pause,
            payoff_has_landing_pause=payoff_has_landing_pause,
            emphasis_contrast=emphasis_contrast,
        )
        degraded_fields: list[str] = []
        if not rates_available:
            degraded_fields.append("voice_plan.segments.rate_contrast_unavailable")
        if not hook_has_attention_pause:
            degraded_fields.append("voice_plan.segments.hook.attention_pause_weak")
        if not payoff_has_landing_pause:
            degraded_fields.append("voice_plan.segments.payoff.landing_pause_weak")
        rationale = [
            "Contrast compares current hook/setup/payoff timing shape only.",
            f"Hook attention pause present: {hook_has_attention_pause}. Payoff landing pause present: {payoff_has_landing_pause}.",
        ]
        if rate_contrast:
            rationale.append("Rate contrast exists between hook/setup/payoff.")
        else:
            rationale.append("Rate contrast is weak or unavailable.")
        return VoiceTimingContrastSummary(
            contrast_detected=contrast_detected,
            contrast_level=contrast_level,
            hook_setup_rate_delta=hook_setup_delta,
            setup_payoff_rate_delta=setup_payoff_delta,
            hook_has_attention_pause=hook_has_attention_pause,
            payoff_has_landing_pause=payoff_has_landing_pause,
            expected_contrast_present=expected_contrast_present,
            degraded_fields=degraded_fields,
            rationale=rationale,
        )

    def _rate_status(self, rate: float) -> str:
        if rate <= 0.0:
            return "invalid"
        if rate < 0.95:
            return "slow"
        if rate <= 1.02:
            return "measured"
        return "fast"

    def _emphasis_status(self, emphasis: str) -> str:
        normalized = emphasis.strip().lower()
        if not normalized:
            return "missing"
        if normalized in {"low", "medium", "high"}:
            return normalized
        return "custom"

    def _pause_status(self, *, segment_name: str, pause_before_ms: int | None, pause_after_ms: int | None) -> str:
        if pause_before_ms is None or pause_after_ms is None:
            return "invalid"
        if pause_before_ms < 0 or pause_after_ms < 0:
            return "invalid"
        if segment_name == "hook" and pause_after_ms >= 300:
            return "attention_pause"
        if segment_name == "payoff" and pause_before_ms >= 350:
            return "landing_pause"
        if pause_before_ms > 0 or pause_after_ms > 0:
            return "light_pause"
        return "continuous"

    def _contrast_level(
        self,
        *,
        rate_contrast: bool,
        hook_has_attention_pause: bool,
        payoff_has_landing_pause: bool,
        emphasis_contrast: bool,
    ) -> str:
        score = sum([rate_contrast, hook_has_attention_pause, payoff_has_landing_pause, emphasis_contrast])
        if score >= 4:
            return "high"
        if score >= 2:
            return "medium"
        if score == 1:
            return "low"
        return "none"

    def _collect_missing_or_degraded(
        self,
        segment_timing: dict[str, dict[str, Any]],
        timing_contrast: dict[str, Any],
    ) -> list[str]:
        values: list[str] = []
        for segment in segment_timing.values():
            values.extend(segment["degraded_fields"])
        values.extend(timing_contrast["degraded_fields"])
        return self._unique(values)

    def _rounded_delta(self, first: Any, second: Any) -> float:
        return round(float(first) - float(second), 2)

    def _as_float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _as_int(self, value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _unique(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        output: list[str] = []
        for value in values:
            if not value or value in seen:
                continue
            seen.add(value)
            output.append(value)
        return output
