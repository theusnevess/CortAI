from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class CaptionPlan:
    style_id: str = "documentary_readable"
    max_words_per_block: int = 5
    emphasis_words: list[str] = field(default_factory=list)
    emphasis_strength: str = "medium"
    emphasis_style: str = "highlight_pulse"
    emphasis_timing_points: list[float] = field(default_factory=list)
    placement: str = "lower_third"
    font_family: str = "DejaVu Sans"
    font_size_mode: str = "large_mobile"
    text_color: str = "#FFF4E8"
    outline_color: str = "#120A08"
    outline_width: int = 6
    shadow: str = "soft"
    pacing_mode: str = "segment_split"
    segment_caption_blocks: dict[str, list[str]] = field(default_factory=dict)
    timing_alignment_mode: str = "voice_segment_locked"
    uppercase_mode: str = "emphasis_only"
    safe_margin_profile: str = "mobile_safe"
    caption_animation_mode: str = "progressive_word_reveal"
    emphasis_animation_mode: str = "scale_pulse"
    reveal_profile: str = "staggered_words"
    key_word_emphasis_rules: dict[str, str] = field(default_factory=dict)
    segment_caption_animation_profile: dict[str, str] = field(default_factory=dict)
    caption_behavior_profile: str = "immersive_readable"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CaptionPlan":
        return cls(**payload)


@dataclass(frozen=True)
class MusicPlan:
    track_type: str = "investigative_pulse"
    mood: str = "tense"
    intensity_curve: str = "rise_to_payoff"
    track_path_or_id: str = "preset:investigative_pulse"
    volume_hook: float = 0.14
    volume_setup: float = 0.11
    volume_payoff: float = 0.18
    ducking_enabled: bool = True
    ducking_level_db: float = -16.0
    fade_in_ms: int = 180
    fade_out_ms: int = 260
    segment_music_profile: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MusicPlan":
        return cls(**payload)


@dataclass(frozen=True)
class TransitionPlan:
    hook_to_setup_type: str = "crossfade"
    hook_to_setup_duration_ms: int = 180
    setup_to_payoff_type: str = "crossfade"
    setup_to_payoff_duration_ms: int = 200
    allow_hard_cut: bool = True
    allow_crossfade: bool = True
    allow_fade_to_black: bool = True
    transition_profile: str = "clean_story"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TransitionPlan":
        return cls(**payload)


@dataclass(frozen=True)
class MotionPlan:
    hook_motion_type: str = "subtle_push"
    setup_motion_type: str = "pan_right"
    payoff_motion_type: str = "slow_zoom_in"
    hook_motion_params: dict[str, float | str] = field(default_factory=dict)
    setup_motion_params: dict[str, float | str] = field(default_factory=dict)
    payoff_motion_params: dict[str, float | str] = field(default_factory=dict)
    scale_start: float = 1.04
    scale_end: float = 1.16
    pan_direction: str = "right"
    pan_distance: float = 0.08
    parallax_enabled: bool = False
    motion_intensity: str = "subtle"
    motion_style: str = "investigative_focus"
    motion_intent: str = "narrative_attention"
    reveal_motion_profile: str = "push_reveal"
    observation_motion_profile: str = "observational_drift"
    payoff_emphasis_motion_profile: str = "restrained_impact"
    motion_behavior_profile: str = "story_led_subtle"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MotionPlan":
        return cls(**payload)


@dataclass(frozen=True)
class ColorPlan:
    grade_preset: str = "neutral_investigative"
    contrast_level: float = 1.05
    saturation_level: float = 0.84
    temperature_shift: float = -0.02
    vignette_enabled: bool = True
    vignette_intensity: float = 0.18
    grain_enabled: bool = True
    grain_level: float = 7.0
    shadow_tone: str = "cool"
    highlight_tone: str = "neutral"
    atmosphere_profile: str = "immersive_lowkey"
    polish_intensity: str = "medium"
    texture_overlay_mode: str = "grain_only"
    light_falloff_profile: str = "soft_edge"
    atmosphere_behavior_profile: str = "contextual_cinematic"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ColorPlan":
        return cls(**payload)


@dataclass(frozen=True)
class TimingPlan:
    hook_duration_s: float = 2.7
    setup_duration_s: float = 3.0
    payoff_duration_s: float = 3.3
    total_duration_s: float = 9.0
    cut_points: list[float] = field(default_factory=list)
    voice_sync_points: list[float] = field(default_factory=list)
    caption_sync_points: list[float] = field(default_factory=list)
    transition_windows: list[dict[str, float | str]] = field(default_factory=list)
    emphasis_sync_points: list[float] = field(default_factory=list)
    micro_timing_adjustments: dict[str, float] = field(default_factory=dict)
    segment_landing_profile: str = "hook_snap_setup_hold_payoff_land"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TimingPlan":
        return cls(**payload)


@dataclass(frozen=True)
class EditorRuntimeConstraints:
    deterministic_seed: str = ""
    allow_music_fallback: bool = True
    allow_caption_fallback: bool = True
    allow_transition_fallback: bool = True
    allow_motion_fallback: bool = True
    safe_render_mode: str = "graceful"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EditorRuntimeConstraints":
        return cls(**payload)


@dataclass(frozen=True)
class EditPlan:
    caption_plan: CaptionPlan = field(default_factory=CaptionPlan)
    music_plan: MusicPlan = field(default_factory=MusicPlan)
    transition_plan: TransitionPlan = field(default_factory=TransitionPlan)
    motion_plan: MotionPlan = field(default_factory=MotionPlan)
    color_plan: ColorPlan = field(default_factory=ColorPlan)
    timing_plan: TimingPlan = field(default_factory=TimingPlan)
    editor_runtime_constraints: EditorRuntimeConstraints = field(default_factory=EditorRuntimeConstraints)
    generated_at: str = ""
    editor_version: str = "editor-agent-v1"
    rationale: str = ""
    editor_style_profile: str = "baseline_expressive"

    def to_dict(self) -> dict[str, Any]:
        return {
            "caption_plan": self.caption_plan.to_dict(),
            "music_plan": self.music_plan.to_dict(),
            "transition_plan": self.transition_plan.to_dict(),
            "motion_plan": self.motion_plan.to_dict(),
            "color_plan": self.color_plan.to_dict(),
            "timing_plan": self.timing_plan.to_dict(),
            "editor_runtime_constraints": self.editor_runtime_constraints.to_dict(),
            "generated_at": self.generated_at,
            "editor_version": self.editor_version,
            "rationale": self.rationale,
            "editor_style_profile": self.editor_style_profile,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EditPlan":
        return cls(
            caption_plan=CaptionPlan.from_dict(dict(payload.get("caption_plan") or {})),
            music_plan=MusicPlan.from_dict(dict(payload.get("music_plan") or {})),
            transition_plan=TransitionPlan.from_dict(dict(payload.get("transition_plan") or {})),
            motion_plan=MotionPlan.from_dict(dict(payload.get("motion_plan") or {})),
            color_plan=ColorPlan.from_dict(dict(payload.get("color_plan") or {})),
            timing_plan=TimingPlan.from_dict(dict(payload.get("timing_plan") or {})),
            editor_runtime_constraints=EditorRuntimeConstraints.from_dict(
                dict(payload.get("editor_runtime_constraints") or {})
            ),
            generated_at=str(payload.get("generated_at") or ""),
            editor_version=str(payload.get("editor_version") or "editor-agent-v1"),
            rationale=str(payload.get("rationale") or ""),
            editor_style_profile=str(payload.get("editor_style_profile") or "baseline_expressive"),
        )
