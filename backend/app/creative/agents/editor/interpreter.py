from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import re

from app.content.screen_text.service import ScreenTextAdapterService
from app.creative.contracts.creative_pack import AssetPlan, ScriptPlan, StrategyProfile, TrendProfile, VoicePlan
from app.creative.contracts.edit_plan import (
    CaptionPlan,
    ColorPlan,
    EditPlan,
    EditorRuntimeConstraints,
    MotionPlan,
    MusicPlan,
    TimingPlan,
    TransitionPlan,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class EditorInterpreter:
    screen_text_adapter: ScreenTextAdapterService = ScreenTextAdapterService()

    def interpret(
        self,
        *,
        niche: str,
        topic: str,
        script_plan: ScriptPlan,
        voice_plan: VoicePlan,
        asset_plan: AssetPlan,
        strategy_profile: StrategyProfile | None = None,
        trend_profile: TrendProfile | None = None,
    ) -> EditPlan:
        segment_texts = {
            "hook": script_plan.hook,
            "setup": script_plan.setup,
            "payoff": script_plan.payoff,
        }
        caption_blocks = {
            name: self._caption_blocks(text=value, max_words=self._max_words_per_block(niche=niche))
            for name, value in segment_texts.items()
        }
        emphasis_words = self._emphasis_words(segment_texts)
        variation_profile = self._variation_profile(topic=topic, script_plan=script_plan)
        timing_plan = self._timing_plan(script_plan=script_plan, voice_plan=voice_plan, variation_profile=variation_profile)
        mood = self._resolve_mood(niche=niche, topic=topic, asset_plan=asset_plan, trend_profile=trend_profile)
        style_profile = self._editor_style_profile(
            niche=niche,
            mood=mood,
            trend_profile=trend_profile,
            variation_profile=variation_profile,
        )
        caption_behavior = self._caption_behavior_profile(niche=niche, mood=mood, variation_profile=variation_profile)
        motion_behavior = self._motion_behavior_profile(niche=niche, asset_plan=asset_plan, variation_profile=variation_profile)
        atmosphere_behavior = self._atmosphere_behavior_profile(
            niche=niche,
            mood=mood,
            asset_plan=asset_plan,
            variation_profile=variation_profile,
        )
        strategy_variant = self._strategy_editor_variant(strategy_profile=strategy_profile)
        caption_animation_profile = self._segment_caption_animation_profile(
            script_plan=script_plan,
            variation_profile=variation_profile,
        )
        motion_types = self._motion_types(
            script_plan=script_plan,
            asset_plan=asset_plan,
            variation_profile=variation_profile,
            strategy_profile=strategy_profile,
        )
        atmosphere_profile = self._atmosphere_profile(niche=niche, mood=mood, asset_plan=asset_plan)
        transition_durations = self._transition_durations(niche=niche, strategy_profile=strategy_profile)
        return EditPlan(
            caption_plan=CaptionPlan(
                style_id=self._caption_style_id(niche=niche),
                max_words_per_block=self._max_words_per_block(niche=niche),
                emphasis_words=emphasis_words,
                emphasis_strength="high" if niche in {"horror", "true_crime", "conspiracy"} else "medium",
                emphasis_style="highlight_pulse",
                emphasis_timing_points=timing_plan.emphasis_sync_points,
                placement="lower_third",
                font_family="DejaVu Sans",
                font_size_mode="large_mobile",
                text_color="#FFF4E8" if niche != "facts" else "#FFF7E5",
                outline_color="#120A08",
                outline_width=6,
                shadow="soft",
                pacing_mode="segment_split",
                segment_caption_blocks=caption_blocks,
                timing_alignment_mode="voice_segment_locked",
                uppercase_mode="emphasis_only",
                safe_margin_profile="mobile_safe",
                caption_animation_mode="progressive_word_reveal",
                emphasis_animation_mode="scale_pulse",
                reveal_profile="staggered_words",
                key_word_emphasis_rules={word: ("strong" if index < 2 else "medium") for index, word in enumerate(emphasis_words)},
                segment_caption_animation_profile=caption_animation_profile,
                caption_behavior_profile=f"{caption_behavior}__{strategy_variant}",
            ),
            music_plan=MusicPlan(
                track_type=self._track_type(niche=niche, mood=mood),
                mood=mood,
                intensity_curve="rise_to_payoff",
                track_path_or_id=f"preset:{self._track_type(niche=niche, mood=mood)}",
                volume_hook=0.16 if niche in {"horror", "true_crime"} else 0.13,
                volume_setup=0.12,
                volume_payoff=0.2 if niche in {"horror", "true_crime"} else 0.16,
                ducking_enabled=True,
                ducking_level_db=-16.0,
                fade_in_ms=180,
                fade_out_ms=280,
                segment_music_profile={
                    "hook": "attention",
                    "setup": "sustain",
                    "payoff": "culminate",
                },
            ),
            transition_plan=TransitionPlan(
                hook_to_setup_type="crossfade" if niche != "facts" else "hard_cut",
                hook_to_setup_duration_ms=transition_durations["hook_to_setup_duration_ms"],
                setup_to_payoff_type="crossfade",
                setup_to_payoff_duration_ms=transition_durations["setup_to_payoff_duration_ms"],
                allow_hard_cut=True,
                allow_crossfade=True,
                allow_fade_to_black=True,
                transition_profile="clean_story",
            ),
            motion_plan=MotionPlan(
                hook_motion_type=motion_types["hook"],
                setup_motion_type=motion_types["setup"],
                payoff_motion_type=motion_types["payoff"],
                hook_motion_params=self._hook_motion_params(variation_profile=variation_profile, strategy_profile=strategy_profile),
                setup_motion_params=self._setup_motion_params(variation_profile=variation_profile, strategy_profile=strategy_profile),
                payoff_motion_params=self._payoff_motion_params(variation_profile=variation_profile, strategy_profile=strategy_profile),
                scale_start=1.04,
                scale_end=1.16,
                pan_direction="right",
                pan_distance=0.08,
                parallax_enabled=False,
                motion_intensity="subtle",
                motion_style="investigative_focus",
                motion_intent="narrative_attention",
                reveal_motion_profile="push_reveal",
                observation_motion_profile="observational_drift",
                payoff_emphasis_motion_profile="restrained_impact",
                motion_behavior_profile=f"{motion_behavior}__{strategy_variant}",
            ),
            color_plan=ColorPlan(
                grade_preset=self._grade_preset(niche=niche, asset_plan=asset_plan),
                contrast_level=1.05 if niche == "facts" else 1.08,
                saturation_level=0.82 if niche in {"horror", "true_crime"} else 0.9,
                temperature_shift=-0.03 if niche in {"horror", "true_crime"} else -0.01,
                vignette_enabled=True,
                vignette_intensity=0.18,
                grain_enabled=True,
                grain_level=8.0 if niche in {"horror", "true_crime"} else 5.0,
                shadow_tone="cool",
                highlight_tone="amber" if niche == "true_crime" else "neutral",
                atmosphere_profile=atmosphere_profile,
                polish_intensity="high" if niche in {"horror", "true_crime", "conspiracy"} else "medium",
                texture_overlay_mode="grain_only",
                light_falloff_profile="soft_edge",
                atmosphere_behavior_profile=f"{atmosphere_behavior}__{strategy_variant}",
            ),
            timing_plan=timing_plan,
            editor_runtime_constraints=EditorRuntimeConstraints(
                deterministic_seed=self._deterministic_seed(topic=topic, script_plan=script_plan),
                allow_music_fallback=True,
                allow_caption_fallback=True,
                allow_transition_fallback=True,
                allow_motion_fallback=True,
                safe_render_mode="graceful",
            ),
            generated_at=_now_iso(),
            editor_version="editor-agent-v2_2",
            rationale=(
                f"Built for {niche} with {mood} mood, segment-locked expressive captions, "
                f"{self._track_type(niche=niche, mood=mood)} music bed, "
                f"{self._grade_preset(niche=niche, asset_plan=asset_plan)} grade, "
                f"{motion_behavior} motion behavior, and {caption_behavior} caption behavior."
            ),
            editor_style_profile=f"{style_profile}__{strategy_variant}",
        )

    def _caption_blocks(self, text: str, *, max_words: int) -> list[str]:
        adapted = self.screen_text_adapter._light_adapt_block(text, role="setup")  # noqa: SLF001
        tokens = adapted.split()
        if not tokens:
            return []
        blocks: list[str] = []
        cursor = 0
        while cursor < len(tokens):
            blocks.append(" ".join(tokens[cursor: cursor + max_words]))
            cursor += max_words
        return blocks[:3]

    def _emphasis_words(self, segment_texts: dict[str, str]) -> list[str]:
        counts: dict[str, int] = {}
        for value in segment_texts.values():
            for token in re.findall(r"[A-Za-z0-9']+", value.lower()):
                if len(token) < 5:
                    continue
                if token in {"there", "where", "could", "would", "after", "still"}:
                    continue
                counts[token] = counts.get(token, 0) + 1
        ranked = sorted(counts.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))
        return [token.upper() for token, _ in ranked[:5]]

    def _timing_plan(self, *, script_plan: ScriptPlan, voice_plan: VoicePlan, variation_profile: str) -> TimingPlan:
        hook_dur = self._estimate_duration(script_plan.hook, voice_plan, role="hook")
        setup_dur = self._estimate_duration(script_plan.setup, voice_plan, role="setup")
        payoff_dur = self._estimate_duration(script_plan.payoff, voice_plan, role="payoff")
        total = round(hook_dur + setup_dur + payoff_dur, 2)
        cut_points = [round(hook_dur, 2), round(hook_dur + setup_dur, 2)]
        voice_sync = [0.0, round(hook_dur, 2), round(hook_dur + setup_dur, 2), total]
        hook_in_ms, setup_hold_ms, payoff_land_ms = self._micro_timing_adjustments(variation_profile)
        return TimingPlan(
            hook_duration_s=hook_dur,
            setup_duration_s=setup_dur,
            payoff_duration_s=payoff_dur,
            total_duration_s=total,
            cut_points=cut_points,
            voice_sync_points=voice_sync,
            caption_sync_points=list(voice_sync),
            emphasis_sync_points=[
                round(max(0.12, hook_dur * 0.38), 2),
                round(max(hook_dur + 0.18, hook_dur + (setup_dur * 0.44)), 2),
                round(max(hook_dur + setup_dur + 0.18, total - max(0.42, payoff_dur * 0.28)), 2),
            ],
            micro_timing_adjustments={
                "hook_in_ms": hook_in_ms,
                "setup_hold_ms": setup_hold_ms,
                "payoff_land_ms": payoff_land_ms,
            },
            segment_landing_profile="hook_snap_setup_hold_payoff_land",
            transition_windows=[
                {"from": "hook", "to": "setup", "start": max(0.0, cut_points[0] - 0.22), "end": cut_points[0]},
                {"from": "setup", "to": "payoff", "start": max(cut_points[0], cut_points[1] - 0.24), "end": cut_points[1]},
            ],
        )

    def _estimate_duration(self, text: str, voice_plan: VoicePlan, *, role: str) -> float:
        words = max(1, len(text.split()))
        base_rate = max(0.75, voice_plan.delivery_profile.overall_rate)
        role_rate = voice_plan.segments.get(role).rate if role in voice_plan.segments else base_rate
        words_per_second = max(2.0, 2.9 * role_rate)
        pause = 0.18
        if role == "hook":
            pause += 0.22
        elif role == "payoff":
            pause += 0.26
        estimate = (words / words_per_second) + pause
        return round(max(2.1, min(4.8, estimate)), 2)

    def _max_words_per_block(self, *, niche: str) -> int:
        return 4 if niche in {"horror", "true_crime"} else 5

    def _caption_style_id(self, *, niche: str) -> str:
        if niche == "true_crime":
            return "investigative_readable"
        if niche == "horror":
            return "lowkey_impact"
        return "documentary_readable"

    def _editor_style_profile(
        self,
        *,
        niche: str,
        mood: str,
        trend_profile: TrendProfile | None,
        variation_profile: str,
    ) -> str:
        if trend_profile and trend_profile.visual_style:
            base = trend_profile.visual_style.lower().replace(" ", "_")
            return f"trend_conditioned_{base}__{variation_profile}"
        if niche == "horror":
            return f"immersive_dread__{variation_profile}"
        if niche == "true_crime":
            return f"evidence_pressure__{variation_profile}"
        if "device" in mood:
            return f"signal_alert__{variation_profile}"
        return f"measured_story__{variation_profile}"

    def _caption_behavior_profile(self, *, niche: str, mood: str, variation_profile: str) -> str:
        if niche == "horror":
            return f"hypnotic_lowkey__{variation_profile}"
        if niche == "true_crime":
            return f"forensic_emphasis__{variation_profile}"
        if "device" in mood:
            return f"signal_ping__{variation_profile}"
        return f"immersive_readable__{variation_profile}"

    def _motion_behavior_profile(self, *, niche: str, asset_plan: AssetPlan, variation_profile: str) -> str:
        if asset_plan.visual_anchor in {"warning_display", "monitor_screen", "device"}:
            return f"tension_device_hold__{variation_profile}"
        if niche == "horror":
            return f"creeping_reveal__{variation_profile}"
        if niche == "true_crime":
            return f"observational_pressure__{variation_profile}"
        return f"measured_focus__{variation_profile}"

    def _atmosphere_behavior_profile(self, *, niche: str, mood: str, asset_plan: AssetPlan, variation_profile: str) -> str:
        if asset_plan.visual_anchor in {"warning_display", "monitor_screen"}:
            return f"electrical_tension__{variation_profile}"
        if niche == "horror":
            return f"lowkey_dread__{variation_profile}"
        if niche == "true_crime":
            return f"institutional_pressure__{variation_profile}"
        if "device" in mood:
            return f"signal_tension__{variation_profile}"
        return f"neutral_story__{variation_profile}"

    def _segment_caption_animation_profile(self, *, script_plan: ScriptPlan, variation_profile: str) -> dict[str, str]:
        setup_profile = "measured_reveal" if self._setup_is_observational(script_plan.setup) else "steady_reveal"
        if variation_profile == "pressure_hold":
            return {"hook": "snap_reveal_hold", "setup": f"{setup_profile}_linger", "payoff": "impact_land_hold"}
        if variation_profile == "measured_surge":
            return {"hook": "snap_reveal_bite", "setup": f"{setup_profile}_drift", "payoff": "impact_land_surge"}
        return {"hook": "snap_reveal", "setup": setup_profile, "payoff": "impact_land"}

    def _motion_types(
        self,
        *,
        script_plan: ScriptPlan,
        asset_plan: AssetPlan,
        variation_profile: str,
        strategy_profile: StrategyProfile | None,
    ) -> dict[str, str]:
        if strategy_profile is not None and strategy_profile.content_mode == "conservative":
            return {
                "hook": "slow_zoom_in",
                "setup": "steady_hold",
                "payoff": "subtle_pull",
            }
        if asset_plan.visual_anchor in {"warning_display", "monitor_screen", "device"}:
            setup_motion = "pan_down" if variation_profile == "pressure_hold" else "pan_right"
            return {
                "hook": "slow_zoom_in",
                "setup": setup_motion,
                "payoff": "subtle_pull",
            }
        if asset_plan.visual_anchor in {"sealed_access", "door"}:
            setup_motion = "pan_up" if variation_profile == "measured_surge" else "pan_left"
            return {
                "hook": "subtle_push",
                "setup": setup_motion,
                "payoff": "slow_zoom_in",
            }
        if any(token in script_plan.payoff.lower() for token in {"revealed", "found", "inside", "behind", "beneath"}):
            payoff_motion = "subtle_pull"
        else:
            payoff_motion = "slow_zoom_in"
        if self._setup_is_observational(script_plan.setup):
            setup_motion = "pan_right" if variation_profile != "pressure_hold" else "pan_down"
        else:
            setup_motion = "pan_left" if variation_profile != "measured_surge" else "pan_up"
        hook_motion = "slow_zoom_in" if variation_profile == "measured_surge" else "subtle_push"
        return {"hook": hook_motion, "setup": setup_motion, "payoff": payoff_motion}

    def _strategy_editor_variant(self, *, strategy_profile: StrategyProfile | None) -> str:
        if strategy_profile is None:
            return "baseline"
        if strategy_profile.content_mode == "conservative":
            return "conservative_hold"
        if strategy_profile.variation_policy == "medium":
            return "variation_push"
        if strategy_profile.target_duration_range.startswith("8-10"):
            return "tight_cut"
        return "baseline"

    def _transition_durations(self, *, niche: str, strategy_profile: StrategyProfile | None) -> dict[str, int]:
        hook_to_setup = 160 if niche == "facts" else 220
        setup_to_payoff = 200 if niche == "facts" else 240
        if strategy_profile is None:
            return {
                "hook_to_setup_duration_ms": hook_to_setup,
                "setup_to_payoff_duration_ms": setup_to_payoff,
            }
        if strategy_profile.content_mode == "conservative":
            return {
                "hook_to_setup_duration_ms": hook_to_setup + 60,
                "setup_to_payoff_duration_ms": setup_to_payoff + 60,
            }
        if strategy_profile.variation_policy == "medium":
            return {
                "hook_to_setup_duration_ms": max(120, hook_to_setup - 30),
                "setup_to_payoff_duration_ms": setup_to_payoff + 20,
            }
        if strategy_profile.target_duration_range.startswith("8-10"):
            return {
                "hook_to_setup_duration_ms": max(120, hook_to_setup - 20),
                "setup_to_payoff_duration_ms": max(160, setup_to_payoff - 10),
            }
        return {
            "hook_to_setup_duration_ms": hook_to_setup,
            "setup_to_payoff_duration_ms": setup_to_payoff,
        }

    def _atmosphere_profile(self, *, niche: str, mood: str, asset_plan: AssetPlan) -> str:
        if asset_plan.visual_anchor in {"warning_display", "monitor_screen"}:
            return "electrical_tension"
        if niche == "horror":
            return "immersive_lowkey"
        if niche == "true_crime":
            return "institutional_pressure"
        if "device" in mood:
            return "signal_alert"
        return "measured_documentary"

    def _track_type(self, *, niche: str, mood: str) -> str:
        if niche == "horror":
            return "horror_low_drone"
        if "device" in mood or "signal" in mood:
            return "device_alert_tense"
        if niche == "true_crime":
            return "investigative_pulse"
        return "documentary_bed"

    def _grade_preset(self, *, niche: str, asset_plan: AssetPlan) -> str:
        if niche == "horror":
            return "horror_lowkey"
        if asset_plan.visual_anchor in {"warning_display", "monitor_screen"}:
            return "device_alert_tense"
        if niche == "true_crime":
            return "institutional_cold"
        return "neutral_investigative"

    def _resolve_mood(
        self,
        *,
        niche: str,
        topic: str,
        asset_plan: AssetPlan,
        trend_profile: TrendProfile | None,
    ) -> str:
        material = " ".join(
            part for part in (niche, topic, asset_plan.semantic_pattern, asset_plan.visual_anchor, trend_profile.visual_style if trend_profile else "") if part
        ).lower()
        if any(token in material for token in {"warning", "signal", "device", "monitor"}):
            return "device_alert_tense"
        if niche == "horror":
            return "lowkey_dread"
        if niche == "true_crime":
            return "investigative_tension"
        return "measured_investigation"

    def _setup_is_observational(self, text: str) -> bool:
        lowered = text.lower()
        return any(token in lowered for token in {"showed", "revealed", "drift", "records", "evidence", "timestamp"})

    def _deterministic_seed(self, *, topic: str, script_plan: ScriptPlan) -> str:
        material = f"{topic.strip().lower()}::{script_plan.hook.strip().lower()}::{script_plan.setup.strip().lower()}::{script_plan.payoff.strip().lower()}"
        digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
        return str(int(digest[:10], 16) % 10_000_000)

    def _variation_profile(self, *, topic: str, script_plan: ScriptPlan) -> str:
        material = f"{topic.strip().lower()}::{script_plan.hook.strip().lower()}::{script_plan.payoff.strip().lower()}"
        bucket = int(hashlib.sha256(material.encode("utf-8")).hexdigest()[:8], 16) % 3
        return ("clean_snap", "measured_surge", "pressure_hold")[bucket]

    def _micro_timing_adjustments(self, variation_profile: str) -> tuple[float, float, float]:
        if variation_profile == "measured_surge":
            return (-105.0, 110.0, 205.0)
        if variation_profile == "pressure_hold":
            return (-95.0, 140.0, 225.0)
        return (-82.0, 120.0, 190.0)

    def _hook_motion_params(self, *, variation_profile: str, strategy_profile: StrategyProfile | None) -> dict[str, float]:
        if strategy_profile is not None and strategy_profile.content_mode == "conservative":
            return {"scale_delta": 0.09, "pan_distance": 0.01}
        if variation_profile == "measured_surge":
            return {"scale_delta": 0.14, "pan_distance": 0.02}
        if variation_profile == "pressure_hold":
            return {"scale_delta": 0.11, "pan_distance": 0.03}
        return {"scale_delta": 0.12, "pan_distance": 0.03}

    def _setup_motion_params(self, *, variation_profile: str, strategy_profile: StrategyProfile | None) -> dict[str, float]:
        if strategy_profile is not None and strategy_profile.content_mode == "conservative":
            return {"scale_delta": 0.03, "pan_distance": 0.03}
        if strategy_profile is not None and strategy_profile.variation_policy == "medium":
            return {"scale_delta": 0.07, "pan_distance": 0.1}
        if variation_profile == "measured_surge":
            return {"scale_delta": 0.04, "pan_distance": 0.08}
        if variation_profile == "pressure_hold":
            return {"scale_delta": 0.06, "pan_distance": 0.06}
        return {"scale_delta": 0.05, "pan_distance": 0.07}

    def _payoff_motion_params(self, *, variation_profile: str, strategy_profile: StrategyProfile | None) -> dict[str, float]:
        if strategy_profile is not None and strategy_profile.content_mode == "conservative":
            return {"scale_delta": 0.1, "pan_distance": 0.02}
        if strategy_profile is not None and strategy_profile.variation_policy == "medium":
            return {"scale_delta": 0.18, "pan_distance": 0.05}
        if variation_profile == "measured_surge":
            return {"scale_delta": 0.16, "pan_distance": 0.03}
        if variation_profile == "pressure_hold":
            return {"scale_delta": 0.17, "pan_distance": 0.04}
        return {"scale_delta": 0.15, "pan_distance": 0.04}
