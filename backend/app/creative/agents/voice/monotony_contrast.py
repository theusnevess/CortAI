from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.creative.contracts.creative_pack import VoicePlan


VOICE_MONOTONY_CONTRAST_VERSION = "voice_monotony_contrast_v2_6"


@dataclass(frozen=True)
class VoiceMonotonyContrastAnalysis:
    analysis_version: str
    analysis_complete: bool
    monotony_risk_level: str
    contrast_level: str
    rate_variation: float
    emphasis_variation: bool
    pause_variation_ms: int
    segment_role_alignment: bool
    reason_codes: list[str] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)
    missing_or_degraded_inputs: list[str] = field(default_factory=list)
    boundary_statement: str = "Voice monotony analysis is audit-only; TTS Router performs synthesis."

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_version": self.analysis_version,
            "analysis_complete": self.analysis_complete,
            "monotony_risk_level": self.monotony_risk_level,
            "contrast_level": self.contrast_level,
            "rate_variation": self.rate_variation,
            "emphasis_variation": self.emphasis_variation,
            "pause_variation_ms": self.pause_variation_ms,
            "segment_role_alignment": self.segment_role_alignment,
            "reason_codes": list(self.reason_codes),
            "rationale": list(self.rationale),
            "missing_or_degraded_inputs": list(self.missing_or_degraded_inputs),
            "boundary_statement": self.boundary_statement,
        }


class VoiceMonotonyContrastAnalyzer:
    """Classifies voice monotony risk from planned timing only."""

    REQUIRED_SEGMENTS: tuple[str, ...] = ("hook", "setup", "payoff")
    EXPECTED_VOICE_ROLES: dict[str, str] = {
        "hook": "open_tension",
        "setup": "controlled_progression",
        "payoff": "memorable_close",
    }

    def analyze(
        self,
        *,
        voice_plan: VoicePlan,
        segment_timing: dict[str, Any] | None = None,
        delivery_semantics: dict[str, Any] | None = None,
    ) -> VoiceMonotonyContrastAnalysis:
        timing_by_segment = self._timing_by_segment(
            voice_plan=voice_plan,
            segment_timing=segment_timing,
        )
        missing_or_degraded_inputs = self._collect_missing_or_degraded(
            timing_by_segment=timing_by_segment,
            segment_timing=segment_timing,
            delivery_semantics=delivery_semantics,
        )
        rates = [timing_by_segment[name]["rate"] for name in self.REQUIRED_SEGMENTS if timing_by_segment[name]["rate"] > 0.0]
        rate_variation = round(max(rates) - min(rates), 2) if len(rates) == len(self.REQUIRED_SEGMENTS) else 0.0
        emphases = [
            timing_by_segment[name]["emphasis"]
            for name in self.REQUIRED_SEGMENTS
            if timing_by_segment[name]["emphasis"]
        ]
        emphasis_variation = len(set(emphases)) > 1
        pause_totals = [
            timing_by_segment[name]["pause_total_ms"]
            for name in self.REQUIRED_SEGMENTS
            if timing_by_segment[name]["pause_total_ms"] is not None
        ]
        pause_variation_ms = int(max(pause_totals) - min(pause_totals)) if len(pause_totals) == len(self.REQUIRED_SEGMENTS) else 0
        segment_role_alignment = self._segment_role_alignment(
            timing_by_segment=timing_by_segment,
            delivery_semantics=delivery_semantics,
        )
        contrast_score = self._contrast_score(
            rate_variation=rate_variation,
            emphasis_variation=emphasis_variation,
            pause_variation_ms=pause_variation_ms,
            segment_role_alignment=segment_role_alignment,
            timing_by_segment=timing_by_segment,
        )
        contrast_level = self._contrast_level(contrast_score)
        monotony_risk_level = self._monotony_risk_level(
            contrast_level=contrast_level,
            segment_role_alignment=segment_role_alignment,
            missing_or_degraded_inputs=missing_or_degraded_inputs,
        )
        reason_codes = self._reason_codes(
            rate_variation=rate_variation,
            emphasis_variation=emphasis_variation,
            pause_variation_ms=pause_variation_ms,
            segment_role_alignment=segment_role_alignment,
            contrast_level=contrast_level,
            monotony_risk_level=monotony_risk_level,
            missing_or_degraded_inputs=missing_or_degraded_inputs,
        )
        rationale = self._rationale(
            rate_variation=rate_variation,
            emphasis_variation=emphasis_variation,
            pause_variation_ms=pause_variation_ms,
            segment_role_alignment=segment_role_alignment,
            contrast_level=contrast_level,
            monotony_risk_level=monotony_risk_level,
            reason_codes=reason_codes,
        )
        return VoiceMonotonyContrastAnalysis(
            analysis_version=VOICE_MONOTONY_CONTRAST_VERSION,
            analysis_complete=not missing_or_degraded_inputs,
            monotony_risk_level=monotony_risk_level,
            contrast_level=contrast_level,
            rate_variation=rate_variation,
            emphasis_variation=emphasis_variation,
            pause_variation_ms=pause_variation_ms,
            segment_role_alignment=segment_role_alignment,
            reason_codes=reason_codes,
            rationale=rationale,
            missing_or_degraded_inputs=missing_or_degraded_inputs,
        )

    def _timing_by_segment(
        self,
        *,
        voice_plan: VoicePlan,
        segment_timing: dict[str, Any] | None,
    ) -> dict[str, dict[str, Any]]:
        trace_segments = (segment_timing or {}).get("segment_timing", {})
        output: dict[str, dict[str, Any]] = {}
        for segment_name in self.REQUIRED_SEGMENTS:
            trace_segment = trace_segments.get(segment_name, {})
            voice_segment = voice_plan.segments.get(segment_name)
            rate = self._as_float(trace_segment.get("rate") if trace_segment else getattr(voice_segment, "rate", 0.0))
            emphasis = str(trace_segment.get("emphasis") if trace_segment else getattr(voice_segment, "emphasis", "") or "").strip().lower()
            pause_before = self._as_int(
                trace_segment.get("pause_before_ms") if trace_segment else getattr(voice_segment, "pause_before_ms", None)
            )
            pause_after = self._as_int(
                trace_segment.get("pause_after_ms") if trace_segment else getattr(voice_segment, "pause_after_ms", None)
            )
            present = bool(trace_segment.get("present", voice_segment is not None))
            pause_total = None
            if pause_before is not None and pause_after is not None:
                pause_total = pause_before + pause_after
            output[segment_name] = {
                "present": present,
                "rate": rate,
                "emphasis": emphasis,
                "pause_before_ms": pause_before,
                "pause_after_ms": pause_after,
                "pause_total_ms": pause_total,
                "degraded_fields": list(trace_segment.get("degraded_fields", [])),
            }
        return output

    def _collect_missing_or_degraded(
        self,
        *,
        timing_by_segment: dict[str, dict[str, Any]],
        segment_timing: dict[str, Any] | None,
        delivery_semantics: dict[str, Any] | None,
    ) -> list[str]:
        values: list[str] = []
        for segment_name, segment in timing_by_segment.items():
            if not segment["present"]:
                values.append(f"voice_plan.segments.{segment_name}_missing")
            if segment["rate"] <= 0.0:
                values.append(f"voice_plan.segments.{segment_name}.rate_invalid")
            if not segment["emphasis"]:
                values.append(f"voice_plan.segments.{segment_name}.emphasis_empty")
            if segment["pause_before_ms"] is None:
                values.append(f"voice_plan.segments.{segment_name}.pause_before_ms_invalid")
            if segment["pause_after_ms"] is None:
                values.append(f"voice_plan.segments.{segment_name}.pause_after_ms_invalid")
            values.extend(segment["degraded_fields"])
        values.extend((segment_timing or {}).get("missing_or_degraded_inputs", []))
        values.extend((delivery_semantics or {}).get("missing_or_degraded_inputs", []))
        return self._unique(values)

    def _segment_role_alignment(
        self,
        *,
        timing_by_segment: dict[str, dict[str, Any]],
        delivery_semantics: dict[str, Any] | None,
    ) -> bool:
        if not all(timing_by_segment[name]["present"] for name in self.REQUIRED_SEGMENTS):
            return False
        if delivery_semantics:
            semantic_segments = delivery_semantics.get("segment_semantics", {})
            for segment_name, expected_role in self.EXPECTED_VOICE_ROLES.items():
                if semantic_segments.get(segment_name, {}).get("voice_role") != expected_role:
                    return False
        hook = timing_by_segment["hook"]
        setup = timing_by_segment["setup"]
        payoff = timing_by_segment["payoff"]
        hook_distinct = (
            hook["emphasis"] != setup["emphasis"]
            or abs(hook["rate"] - setup["rate"]) >= 0.02
            or self._pause_delta(hook, setup) >= 100
            or (hook["pause_after_ms"] or 0) >= 300
        )
        payoff_distinct = (
            payoff["emphasis"] != setup["emphasis"]
            or abs(payoff["rate"] - setup["rate"]) >= 0.02
            or self._pause_delta(payoff, setup) >= 100
            or (payoff["pause_before_ms"] or 0) >= 350
        )
        return hook_distinct and payoff_distinct

    def _contrast_score(
        self,
        *,
        rate_variation: float,
        emphasis_variation: bool,
        pause_variation_ms: int,
        segment_role_alignment: bool,
        timing_by_segment: dict[str, dict[str, Any]],
    ) -> int:
        score = 0
        if rate_variation >= 0.06:
            score += 2
        elif rate_variation >= 0.02:
            score += 1
        if emphasis_variation:
            score += 1
        if pause_variation_ms >= 250:
            score += 2
        elif pause_variation_ms >= 100:
            score += 1
        if segment_role_alignment:
            score += 1
        if (timing_by_segment["hook"]["pause_after_ms"] or 0) >= 300:
            score += 1
        if (timing_by_segment["payoff"]["pause_before_ms"] or 0) >= 350:
            score += 1
        return score

    def _contrast_level(self, score: int) -> str:
        if score >= 6:
            return "high"
        if score >= 3:
            return "medium"
        return "low"

    def _monotony_risk_level(
        self,
        *,
        contrast_level: str,
        segment_role_alignment: bool,
        missing_or_degraded_inputs: list[str],
    ) -> str:
        if missing_or_degraded_inputs and contrast_level == "low":
            return "high"
        if contrast_level == "high" and segment_role_alignment and not missing_or_degraded_inputs:
            return "low"
        if contrast_level == "low" or not segment_role_alignment:
            return "high"
        return "medium"

    def _reason_codes(
        self,
        *,
        rate_variation: float,
        emphasis_variation: bool,
        pause_variation_ms: int,
        segment_role_alignment: bool,
        contrast_level: str,
        monotony_risk_level: str,
        missing_or_degraded_inputs: list[str],
    ) -> list[str]:
        codes: list[str] = []
        if missing_or_degraded_inputs:
            codes.append("MONOTONY_ANALYSIS_DEGRADED_INPUT")
        if rate_variation < 0.02:
            codes.append("LOW_RATE_VARIATION")
        else:
            codes.append("RATE_VARIATION_PRESENT")
        if not emphasis_variation:
            codes.append("NO_EMPHASIS_VARIATION")
        else:
            codes.append("EMPHASIS_VARIATION_PRESENT")
        if pause_variation_ms < 100:
            codes.append("LOW_PAUSE_VARIATION")
        else:
            codes.append("PAUSE_VARIATION_PRESENT")
        if not segment_role_alignment:
            codes.append("SEGMENT_ROLE_ALIGNMENT_WEAK")
        else:
            codes.append("SEGMENT_ROLE_ALIGNMENT_PRESENT")
        if contrast_level == "high":
            codes.append("STRONG_CONTRAST_DETECTED")
        elif contrast_level == "medium":
            codes.append("PARTIAL_CONTRAST_DETECTED")
        else:
            codes.append("LOW_CONTRAST_DETECTED")
        if monotony_risk_level == "high":
            codes.append("HIGH_MONOTONY_RISK")
        elif monotony_risk_level == "medium":
            codes.append("MEDIUM_MONOTONY_RISK")
        else:
            codes.append("LOW_MONOTONY_RISK")
        return codes

    def _rationale(
        self,
        *,
        rate_variation: float,
        emphasis_variation: bool,
        pause_variation_ms: int,
        segment_role_alignment: bool,
        contrast_level: str,
        monotony_risk_level: str,
        reason_codes: list[str],
    ) -> list[str]:
        return [
            "Monotony analysis compares planned hook/setup/payoff timing only; it does not inspect synthesized audio.",
            f"Rate variation is {rate_variation}; emphasis variation present is {emphasis_variation}; pause variation is {pause_variation_ms}ms.",
            f"Segment role alignment is {segment_role_alignment}; contrast level is {contrast_level}; monotony risk is {monotony_risk_level}.",
            "Reason codes: " + ", ".join(reason_codes),
        ]

    def _pause_delta(self, first: dict[str, Any], second: dict[str, Any]) -> int:
        first_total = first["pause_total_ms"] or 0
        second_total = second["pause_total_ms"] or 0
        return abs(first_total - second_total)

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
