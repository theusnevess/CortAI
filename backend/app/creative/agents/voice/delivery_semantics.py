from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.creative.contracts.creative_pack import ScriptPlan, VoicePlan, VoiceSegmentPlan


VOICE_DELIVERY_SEMANTICS_VERSION = "voice_delivery_semantics_v2_6"


@dataclass(frozen=True)
class VoiceSegmentDeliverySemantics:
    segment_name: str
    value_present: bool
    script_role: str
    voice_role: str
    intended_effect: str
    rate_intent: str
    emphasis_intent: str
    pause_intent: str
    mapping_supported: bool
    missing_or_degraded_inputs: list[str] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "segment_name": self.segment_name,
            "value_present": self.value_present,
            "script_role": self.script_role,
            "voice_role": self.voice_role,
            "intended_effect": self.intended_effect,
            "rate_intent": self.rate_intent,
            "emphasis_intent": self.emphasis_intent,
            "pause_intent": self.pause_intent,
            "mapping_supported": self.mapping_supported,
            "missing_or_degraded_inputs": list(self.missing_or_degraded_inputs),
            "rationale": list(self.rationale),
        }


@dataclass(frozen=True)
class VoiceDeliverySemanticsResult:
    semantics_version: str
    semantics_complete: bool
    delivery_intent: dict[str, Any]
    role_sequence: list[str]
    segment_semantics: dict[str, dict[str, Any]]
    missing_or_degraded_inputs: list[str]
    boundary_statement: str
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "semantics_version": self.semantics_version,
            "semantics_complete": self.semantics_complete,
            "delivery_intent": dict(self.delivery_intent),
            "role_sequence": list(self.role_sequence),
            "segment_semantics": {key: dict(value) for key, value in self.segment_semantics.items()},
            "missing_or_degraded_inputs": list(self.missing_or_degraded_inputs),
            "boundary_statement": self.boundary_statement,
            "rationale": list(self.rationale),
        }


class VoiceDeliverySemanticsMapper:
    """Explains voice delivery intent without changing synthesis inputs."""

    REQUIRED_SEGMENTS: tuple[str, ...] = ("hook", "setup", "payoff")

    SEGMENT_ROLE_MAP: dict[str, dict[str, str]] = {
        "hook": {
            "script_role": "attention_capture",
            "voice_role": "open_tension",
            "intended_effect": "Create immediate attention and unresolved tension.",
        },
        "setup": {
            "script_role": "context_bridge",
            "voice_role": "controlled_progression",
            "intended_effect": "Carry context from hook toward the payoff without resolving early.",
        },
        "payoff": {
            "script_role": "resolution_or_reframe",
            "voice_role": "memorable_close",
            "intended_effect": "Land the resolution or reframe with deliberate emphasis.",
        },
    }

    def map(
        self,
        *,
        voice_plan: VoicePlan,
        script_plan: ScriptPlan | None = None,
        voice_plan_governance: dict[str, Any] | None = None,
    ) -> VoiceDeliverySemanticsResult:
        del voice_plan_governance
        segment_semantics = {
            segment_name: self._segment_semantics(
                segment_name=segment_name,
                segment=voice_plan.segments.get(segment_name),
                script_text=self._script_text(script_plan, segment_name),
            ).to_dict()
            for segment_name in self.REQUIRED_SEGMENTS
        }
        missing_or_degraded_inputs = self._collect_missing_or_degraded(segment_semantics)
        delivery_intent = self._delivery_intent(voice_plan=voice_plan)
        if not str(voice_plan.style or "").strip():
            missing_or_degraded_inputs.append("voice_plan.style_empty")
        if voice_plan.delivery_profile is None:
            missing_or_degraded_inputs.append("voice_plan.delivery_profile_missing")

        missing_or_degraded_inputs = self._unique(missing_or_degraded_inputs)
        semantics_complete = not missing_or_degraded_inputs and all(
            segment["mapping_supported"] for segment in segment_semantics.values()
        )
        rationale = [
            "Delivery semantics explain intent only; they do not synthesize audio.",
            "Hook/setup/payoff are mapped to deterministic voice roles.",
        ]
        if semantics_complete:
            rationale.append("All required voice segments have usable semantic mappings.")
        else:
            rationale.append("Some voice delivery inputs are missing or degraded: " + ", ".join(missing_or_degraded_inputs))
        return VoiceDeliverySemanticsResult(
            semantics_version=VOICE_DELIVERY_SEMANTICS_VERSION,
            semantics_complete=semantics_complete,
            delivery_intent=delivery_intent,
            role_sequence=list(self.REQUIRED_SEGMENTS),
            segment_semantics=segment_semantics,
            missing_or_degraded_inputs=missing_or_degraded_inputs,
            boundary_statement="Voice explains delivery intent only; TTS Router performs synthesis.",
            rationale=rationale,
        )

    def _delivery_intent(self, *, voice_plan: VoicePlan) -> dict[str, Any]:
        profile = voice_plan.delivery_profile
        style = str(voice_plan.style or "").strip()
        if profile is None:
            return {
                "style": style,
                "overall_mode": "",
                "overall_rate": None,
                "overall_intensity": "",
                "narrative_intent": self._style_intent(style),
                "rate_intent": "unknown",
                "intensity_intent": "unknown",
            }
        overall_rate = self._as_float(profile.overall_rate)
        return {
            "style": style,
            "overall_mode": str(profile.overall_mode or "").strip(),
            "overall_rate": overall_rate,
            "overall_intensity": str(profile.overall_intensity or "").strip(),
            "narrative_intent": self._style_intent(style),
            "rate_intent": self._rate_intent(overall_rate),
            "intensity_intent": self._intensity_intent(profile.overall_intensity),
        }

    def _segment_semantics(
        self,
        *,
        segment_name: str,
        segment: VoiceSegmentPlan | None,
        script_text: str,
    ) -> VoiceSegmentDeliverySemantics:
        role = self.SEGMENT_ROLE_MAP[segment_name]
        missing_or_degraded_inputs: list[str] = []
        rationale: list[str] = [role["intended_effect"]]
        if not script_text.strip():
            missing_or_degraded_inputs.append(f"script_plan.{segment_name}_empty")
            rationale.append(f"{segment_name} script text is empty, so semantic support is degraded.")
        if segment is None:
            missing_or_degraded_inputs.append(f"voice_plan.segments.{segment_name}_missing")
            return VoiceSegmentDeliverySemantics(
                segment_name=segment_name,
                value_present=bool(script_text.strip()),
                script_role=role["script_role"],
                voice_role=role["voice_role"],
                intended_effect=role["intended_effect"],
                rate_intent="unknown",
                emphasis_intent="unknown",
                pause_intent="unknown",
                mapping_supported=False,
                missing_or_degraded_inputs=missing_or_degraded_inputs,
                rationale=rationale,
            )
        rate = self._as_float(segment.rate)
        if rate <= 0.0:
            missing_or_degraded_inputs.append(f"voice_plan.segments.{segment_name}.rate_invalid")
        emphasis = str(segment.emphasis or "").strip()
        if not emphasis:
            missing_or_degraded_inputs.append(f"voice_plan.segments.{segment_name}.emphasis_empty")
        pause_after_ms = self._as_int(segment.pause_after_ms)
        pause_before_ms = self._as_int(segment.pause_before_ms)
        if pause_after_ms is None:
            missing_or_degraded_inputs.append(f"voice_plan.segments.{segment_name}.pause_after_ms_invalid")
            pause_after_ms = 0
        if pause_before_ms is None:
            missing_or_degraded_inputs.append(f"voice_plan.segments.{segment_name}.pause_before_ms_invalid")
            pause_before_ms = 0
        if pause_after_ms < 0:
            missing_or_degraded_inputs.append(f"voice_plan.segments.{segment_name}.pause_after_ms_negative")
        if pause_before_ms < 0:
            missing_or_degraded_inputs.append(f"voice_plan.segments.{segment_name}.pause_before_ms_negative")
        mapping_supported = not missing_or_degraded_inputs
        if mapping_supported:
            rationale.append(f"{segment_name} has usable rate, emphasis, and pause settings for its voice role.")
        return VoiceSegmentDeliverySemantics(
            segment_name=segment_name,
            value_present=bool(script_text.strip()),
            script_role=role["script_role"],
            voice_role=role["voice_role"],
            intended_effect=role["intended_effect"],
            rate_intent=self._rate_intent(rate),
            emphasis_intent=self._emphasis_intent(emphasis),
            pause_intent=self._pause_intent(
                pause_before_ms=pause_before_ms,
                pause_after_ms=pause_after_ms,
            ),
            mapping_supported=mapping_supported,
            missing_or_degraded_inputs=missing_or_degraded_inputs,
            rationale=rationale,
        )

    def _script_text(self, script_plan: ScriptPlan | None, segment_name: str) -> str:
        if script_plan is None:
            return ""
        return str(getattr(script_plan, segment_name, "") or "")

    def _style_intent(self, style: str) -> str:
        normalized = style.strip().lower()
        if normalized == "investigative":
            return "evidence_led_tension"
        if normalized == "ominous_minimal":
            return "controlled_ominous_suspense"
        if normalized == "neutral_archive":
            return "neutral_clarity"
        if normalized == "measured_dark":
            return "restrained_serious_delivery"
        if normalized == "dark_calm":
            return "calm_dark_context"
        return "general_script_delivery"

    def _rate_intent(self, rate: float) -> str:
        if rate <= 0.0:
            return "unknown"
        if rate < 0.95:
            return "slow_deliberate"
        if rate <= 1.02:
            return "measured"
        return "fast"

    def _intensity_intent(self, intensity: Any) -> str:
        normalized = str(intensity or "").strip().lower()
        if normalized == "high":
            return "heightened_tension"
        if normalized == "medium":
            return "controlled_presence"
        if normalized == "low":
            return "restrained"
        return "unknown"

    def _emphasis_intent(self, emphasis: str) -> str:
        normalized = emphasis.strip().lower()
        if normalized == "high":
            return "foregrounded"
        if normalized == "medium":
            return "balanced"
        if normalized == "low":
            return "subtle"
        return "unknown"

    def _pause_intent(self, *, pause_before_ms: int, pause_after_ms: int) -> str:
        if pause_before_ms >= 350:
            return "pre_landing_space"
        if pause_after_ms >= 300:
            return "post_tension_space"
        if pause_after_ms > 0 or pause_before_ms > 0:
            return "light_spacing"
        return "continuous"

    def _collect_missing_or_degraded(self, segment_semantics: dict[str, dict[str, Any]]) -> list[str]:
        values: list[str] = []
        for segment in segment_semantics.values():
            values.extend(segment["missing_or_degraded_inputs"])
        return self._unique(values)

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
