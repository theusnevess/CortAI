from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import textwrap
import wave
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from app.content.backgrounds.service import AssetProfile, BackgroundGenerationError, BackgroundGeneratorService
from app.content.pipeline.perceptual_correction import analyze_frame, balance_sequence
from app.content.screen_text.service import ScreenTextAdapterService, ScreenTextCue
from app.creative.contracts.creative_pack import AssetPlan
from app.creative.contracts.edit_plan import CaptionPlan, EditPlan
from PIL import Image

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MIN_VIDEO_DURATION_S = 8.0
MIN_BLOCK_DURATION_S = 2.0
STOPWORDS = {
    "THE", "THIS", "THAT", "WITH", "FROM", "THEY", "YOUR", "HAVE", "WERE", "WHAT", "WHEN",
    "EVERYONE", "THINK", "PLACE", "THERE", "ABOUT", "WOULD", "COULD", "SHOULD", "AFTER",
    "BECAUSE", "UNTIL", "INTO", "THEIR", "THERE", "AND", "BUT", "FOR", "NOT", "YOU", "WAS",
    "ARE", "WHY", "HOW", "WHO", "HAD", "HAS", "HER", "HIS", "ITS", "OUR", "OUT", "OFF",
    "IT", "ONE", "THEM", "THESE", "THOSE",
}
THEME_PROFILES = {
    "horror": {
        "label": "DARK FILE",
        "text_color": "#ff7a18",
        "glow_color": "#5b1d10",
        "keywords": {
            "ABANDONED", "BLOOD", "CURSED", "DARK", "DEAD", "EMPTY", "GHOST", "HAUNTED",
            "HEARD", "HOTEL", "INSIDE", "LIGHTS", "MIDNIGHT", "MISSING", "NOISES",
            "SCREAM", "SHADOW", "SHUTDOWN", "STRANGE", "UNKNOWN",
        },
    },
    "conspiracy": {
        "label": "HIDDEN SIGNAL",
        "text_color": "#f97316",
        "glow_color": "#3b1d0f",
        "keywords": {
            "COVERUP", "FILES", "FOUND", "LEAK", "PROOF", "SECRET", "SIGNAL", "THEORY",
            "TRUTH", "UNSEEN", "VAULT", "WARNING", "WHY",
        },
    },
    "facts": {
        "label": "FACT DROP",
        "text_color": "#ff7a18",
        "glow_color": "#3b1d0f",
        "keywords": {
            "DISCOVERED", "EXPLAINED", "FACT", "FOUND", "NEVER", "PROVEN", "RARE",
            "REAL", "SCIENCE", "STUDY", "SYSTEM", "WORLD",
        },
    },
}
DEFAULT_THEME = "facts"


class RenderTransientError(RuntimeError):
    """Falha transitoria elegivel para retry em render."""


@dataclass(frozen=True)
class RenderResponse:
    video_path: str


class RenderAdapter:
    def render_video(
        self,
        *,
        audio_path: str,
        script_text: str,
        asset_plan: AssetPlan,
        edit_plan: EditPlan | None,
        screen_blocks: list[str] | None,
        segment_durations: list[float] | None,
        render_job_id: str,
        template_id: str | None,
        aspect_ratio: str | None,
        attempt_count: int,
    ) -> RenderResponse:
        raise NotImplementedError


class StubRenderAdapter(RenderAdapter):
    """Dark-story renderer with background-first composition and progressive reveal."""

    def __init__(self, *, base_dir: Path = Path("OUT/content")) -> None:
        self.base_dir = base_dir
        self.screen_text_adapter = ScreenTextAdapterService()
        self.background_service = BackgroundGeneratorService(base_dir=self.base_dir / "backgrounds")

    def render_video(
        self,
        *,
        audio_path: str,
        script_text: str,
        asset_plan: AssetPlan,
        edit_plan: EditPlan | None,
        screen_blocks: list[str] | None,
        segment_durations: list[float] | None,
        render_job_id: str,
        template_id: str | None,
        aspect_ratio: str | None,
        attempt_count: int,
    ) -> RenderResponse:
        source_audio = Path(audio_path)
        if not source_audio.exists():
            raise ValueError("RENDER_AUDIO_MISSING")
        cleaned_script = script_text.strip()
        if not cleaned_script:
            raise ValueError("RENDER_SCRIPT_MISSING")
        if not asset_plan.hook_asset or not asset_plan.setup_asset or not asset_plan.payoff_asset:
            raise ValueError("RENDER_ASSET_PLAN_INCOMPLETE")

        video_path = self.base_dir / "video" / f"{render_job_id}.mp4"
        metadata_dir = self.base_dir / "metadata"
        metadata_path = metadata_dir / f"{render_job_id}.json"
        text_path = metadata_dir / f"{render_job_id}.txt"
        subtitle_path = metadata_dir / f"{render_job_id}.ass"
        video_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_dir.mkdir(parents=True, exist_ok=True)

        duration_s = self._audio_duration(source_audio)
        theme = self._infer_theme(cleaned_script)
        effective_edit_plan = edit_plan or self._fallback_edit_plan(
            script_text=cleaned_script,
            theme=theme,
            segment_durations=segment_durations,
        )
        if screen_blocks:
            screen_text_blocks = self.screen_text_adapter.adapt(cleaned_script)
            screen_text_blocks = type(screen_text_blocks)(
                hook_text=screen_blocks[0] if len(screen_blocks) > 0 else "",
                setup_text=screen_blocks[1] if len(screen_blocks) > 1 else "",
                payoff_text=screen_blocks[2] if len(screen_blocks) > 2 else "",
            )
        else:
            screen_text_blocks = self.screen_text_adapter.adapt(cleaned_script)
        blocks = list(screen_text_blocks.as_list())
        timings = self._build_timings(
            duration_s,
            len(blocks),
            segment_durations=segment_durations,
            edit_plan=effective_edit_plan,
        )
        subtitle_cues = self._build_caption_cues(
            caption_plan=effective_edit_plan.caption_plan,
            segment_texts={
                "hook": screen_text_blocks.hook_text,
                "setup": screen_text_blocks.setup_text,
                "payoff": screen_text_blocks.payoff_text,
            },
            timings=timings,
        )
        self._write_ass_subtitles(
            subtitle_path=subtitle_path,
            cues=subtitle_cues,
            width=self._resolve_dimensions(aspect_ratio)[0],
            height=self._resolve_dimensions(aspect_ratio)[1],
            caption_plan=effective_edit_plan.caption_plan,
        )
        corrected_dir = metadata_dir / "corrected_frames"
        corrected_dir.mkdir(parents=True, exist_ok=True)
        corrected_paths, corrected_profiles = self._prepare_corrected_backgrounds(
            asset_plan=asset_plan,
            corrected_dir=corrected_dir,
            render_job_id=render_job_id,
        )
        hook_background_path = corrected_paths["hook"]
        setup_background_path = corrected_paths["setup"]
        payoff_background_path = corrected_paths["payoff"]
        highlights = [self._highlight_word(block, theme=theme) for block in blocks]
        hook_profile = corrected_profiles["hook"]
        setup_profile = corrected_profiles["setup"]
        payoff_profile = corrected_profiles["payoff"]

        text_path.write_text(cleaned_script, encoding="utf-8")
        render_mode = self._render_video_file(
            audio_path=source_audio,
            timings=timings,
            theme=theme,
            highlights=highlights,
            subtitle_path=subtitle_path,
            edit_plan=effective_edit_plan,
            hook_profile=hook_profile,
            setup_profile=setup_profile,
            payoff_profile=payoff_profile,
            hook_background_path=Path(hook_background_path) if hook_background_path else None,
            setup_background_path=Path(setup_background_path) if setup_background_path else None,
            payoff_background_path=Path(payoff_background_path) if payoff_background_path else None,
            video_path=video_path,
            aspect_ratio=aspect_ratio,
        )
        metadata_path.write_text(
            json.dumps(
                {
                    "render_job_id": render_job_id,
                    "audio_path": audio_path,
                    "template_id": template_id,
                    "aspect_ratio": aspect_ratio,
                    "attempt_count": attempt_count,
                    "render_mode": render_mode,
                    "duration_s": duration_s,
                    "render_duration_s": max(duration_s, MIN_VIDEO_DURATION_S),
                    "text_path": str(text_path),
                    "blocks": blocks,
                    "highlights": highlights,
                    "timings": timings,
                    "theme": theme,
                    "asset_plan": asset_plan.to_dict(),
                    "edit_plan": effective_edit_plan.to_dict(),
                    "subtitle_path": str(subtitle_path),
                    "subtitle_cues": [
                        {
                            "text": cue.text,
                            "start": cue.start,
                            "end": cue.end,
                            "style_role": cue.style_role,
                        }
                        for cue in subtitle_cues
                    ],
                    "music_plan": effective_edit_plan.music_plan.to_dict(),
                    "transition_plan": effective_edit_plan.transition_plan.to_dict(),
                    "motion_plan": effective_edit_plan.motion_plan.to_dict(),
                    "color_plan": effective_edit_plan.color_plan.to_dict(),
                    "timing_plan": effective_edit_plan.timing_plan.to_dict(),
                    "hook_background_path": hook_background_path,
                    "setup_background_path": setup_background_path,
                    "payoff_background_path": payoff_background_path,
                    "hook_background_mean_luma": None if hook_profile is None else round(hook_profile.mean_luma, 2),
                    "setup_background_mean_luma": None if setup_profile is None else round(setup_profile.mean_luma, 2),
                    "payoff_background_mean_luma": None if payoff_profile is None else round(payoff_profile.mean_luma, 2),
                    "hook_background_contrast": None if hook_profile is None else round(hook_profile.contrast, 2),
                    "setup_background_contrast": None if setup_profile is None else round(setup_profile.contrast, 2),
                    "payoff_background_contrast": None if payoff_profile is None else round(payoff_profile.contrast, 2),
                },
                ensure_ascii=True,
                indent=2,
            ),
            encoding="utf-8",
        )
        return RenderResponse(video_path=str(video_path))

    def _render_video_file(
        self,
        *,
        audio_path: Path,
        timings: list[tuple[float, float]],
        theme: str,
        highlights: list[str],
        subtitle_path: Path,
        edit_plan: EditPlan,
        hook_profile: AssetProfile | None,
        setup_profile: AssetProfile | None,
        payoff_profile: AssetProfile | None,
        hook_background_path: Path | None,
        setup_background_path: Path | None,
        payoff_background_path: Path | None,
        video_path: Path,
        aspect_ratio: str | None,
    ) -> str:
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            self._run_ffmpeg(
                ffmpeg_cmd=[ffmpeg_path],
                audio_path=str(audio_path),
                timings=timings,
                theme=theme,
                highlights=highlights,
                subtitle_path=str(subtitle_path),
                edit_plan=edit_plan,
                hook_profile=hook_profile,
                setup_profile=setup_profile,
                payoff_profile=payoff_profile,
                hook_background_path=str(hook_background_path) if hook_background_path else None,
                setup_background_path=str(setup_background_path) if setup_background_path else None,
                payoff_background_path=str(payoff_background_path) if payoff_background_path else None,
                video_path=str(video_path),
                aspect_ratio=aspect_ratio,
            )
            return "local_ffmpeg"

        repo_root = Path(__file__).resolve().parents[4]
        try:
            audio_rel = audio_path.resolve().relative_to(repo_root)
            subtitle_rel = subtitle_path.resolve().relative_to(repo_root)
            hook_background_rel = None if hook_background_path is None else hook_background_path.resolve().relative_to(repo_root)
            setup_background_rel = None if setup_background_path is None else setup_background_path.resolve().relative_to(repo_root)
            payoff_background_rel = None if payoff_background_path is None else payoff_background_path.resolve().relative_to(repo_root)
            video_rel = video_path.resolve().relative_to(repo_root)
        except ValueError:
            video_path.write_bytes(b"FAKE_MP4_PLACEHOLDER")
            return "placeholder"

        docker_path = shutil.which("docker")
        if not docker_path:
            video_path.write_bytes(b"FAKE_MP4_PLACEHOLDER")
            return "placeholder"

        workspace = repo_root.resolve().as_posix()
        container_audio = str(PurePosixPath("/workspace").joinpath(*audio_rel.parts))
        container_subtitle = str(PurePosixPath("/workspace").joinpath(*subtitle_rel.parts))
        container_hook_background = (
            None if hook_background_rel is None else str(PurePosixPath("/workspace").joinpath(*hook_background_rel.parts))
        )
        container_setup_background = (
            None if setup_background_rel is None else str(PurePosixPath("/workspace").joinpath(*setup_background_rel.parts))
        )
        container_payoff_background = (
            None if payoff_background_rel is None else str(PurePosixPath("/workspace").joinpath(*payoff_background_rel.parts))
        )
        container_video = str(PurePosixPath("/workspace").joinpath(*video_rel.parts))
        self._run_ffmpeg(
            ffmpeg_cmd=[
                docker_path,
                "run",
                "--rm",
                "--entrypoint",
                "ffmpeg",
                "-v",
                f"{workspace}:/workspace",
                "-w",
                "/workspace",
                os.getenv("CORTAI_FFMPEG_IMAGE", "cortai10-api"),
            ],
            audio_path=container_audio,
            timings=timings,
            theme=theme,
            highlights=highlights,
            subtitle_path=container_subtitle,
            edit_plan=edit_plan,
            hook_profile=hook_profile,
            setup_profile=setup_profile,
            payoff_profile=payoff_profile,
            hook_background_path=container_hook_background,
            setup_background_path=container_setup_background,
            payoff_background_path=container_payoff_background,
            video_path=container_video,
            aspect_ratio=aspect_ratio,
        )
        return "docker_ffmpeg"

    def _run_ffmpeg(
        self,
        *,
        ffmpeg_cmd: list[str],
        audio_path: str,
        timings: list[tuple[float, float]],
        theme: str,
        highlights: list[str],
        subtitle_path: str,
        edit_plan: EditPlan,
        hook_profile: AssetProfile | None,
        setup_profile: AssetProfile | None,
        payoff_profile: AssetProfile | None,
        hook_background_path: str | None,
        setup_background_path: str | None,
        payoff_background_path: str | None,
        video_path: str,
        aspect_ratio: str | None,
    ) -> None:
        width, height = self._resolve_dimensions(aspect_ratio)
        filter_chain = self._build_filter_chain(
            width=width,
            height=height,
            timings=timings,
            theme=theme,
            highlights=highlights,
            subtitle_path=subtitle_path,
            edit_plan=edit_plan,
            hook_profile=hook_profile,
            setup_profile=setup_profile,
            payoff_profile=payoff_profile,
        )
        music_filter_chain = self._build_music_filter_chain(edit_plan=edit_plan, timings=timings)
        if hook_background_path and setup_background_path and payoff_background_path:
            input_source = [
                *ffmpeg_cmd,
                "-y",
                "-loop",
                "1",
                "-i",
                hook_background_path,
                "-loop",
                "1",
                "-i",
                setup_background_path,
                "-loop",
                "1",
                "-i",
                payoff_background_path,
                "-i",
                audio_path,
                "-f",
                "lavfi",
                "-t",
                f"{max(3.0, timings[-1][1]):.2f}",
                "-i",
                "anoisesrc=color=brown:amplitude=0.03",
                "-f",
                "lavfi",
                "-t",
                f"{max(3.0, timings[-1][1]):.2f}",
                "-i",
                "sine=frequency=62:sample_rate=44100:beep_factor=0",
            ]
        else:
            input_source = [
                *ffmpeg_cmd,
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c=#05070d:s={width}x{height}:r=30",
                "-f",
                "lavfi",
                "-i",
                f"color=c=#05070d:s={width}x{height}:r=30",
                "-f",
                "lavfi",
                "-i",
                f"color=c=#05070d:s={width}x{height}:r=30",
                "-i",
                audio_path,
                "-f",
                "lavfi",
                "-t",
                f"{max(3.0, timings[-1][1]):.2f}",
                "-i",
                "anoisesrc=color=brown:amplitude=0.03",
                "-f",
                "lavfi",
                "-t",
                f"{max(3.0, timings[-1][1]):.2f}",
                "-i",
                "sine=frequency=62:sample_rate=44100:beep_factor=0",
            ]
        cmd = [
            *input_source,
            "-filter_complex",
            f"{filter_chain};"
            "[3:a]volume=12dB,loudnorm=I=-16:LRA=11:TP=-1.5[voice];"
            f"{music_filter_chain}",
            "-map",
            "[vout]",
            "-map",
            "[aout]",
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-b:a",
            "256k",
            video_path,
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except subprocess.CalledProcessError as exc:
            raise RenderTransientError(exc.stderr.strip() or "RENDER_FFMPEG_FAILED") from exc

    def _build_filter_chain(
        self,
        *,
        width: int,
        height: int,
        timings: list[tuple[float, float]],
        theme: str,
        highlights: list[str],
        subtitle_path: str,
        edit_plan: EditPlan,
        hook_profile: AssetProfile | None,
        setup_profile: AssetProfile | None,
        payoff_profile: AssetProfile | None,
    ) -> str:
        del highlights
        escaped_subtitle_path = self._escape_filter_value(subtitle_path)
        transition_plan = edit_plan.transition_plan
        color_plan = edit_plan.color_plan
        motion_plan = edit_plan.motion_plan
        style_profile = str(edit_plan.editor_style_profile or "").lower()
        first_cut = max(0.0, timings[1][0] - (transition_plan.hook_to_setup_duration_ms / 1000.0)) if len(timings) > 1 else 0.0
        second_cut = max(0.0, timings[2][0] - (transition_plan.setup_to_payoff_duration_ms / 1000.0)) if len(timings) > 2 else first_cut
        first_impact_end = min(timings[0][1], 1.35 if "pressure_hold" not in style_profile else 1.50)
        hook_brightness = self._block_brightness_adjustment(hook_profile, target=78.0, max_boost=0.09)
        setup_brightness = self._block_brightness_adjustment(setup_profile, target=76.0, max_boost=0.06)
        payoff_brightness = self._block_brightness_adjustment(payoff_profile, target=84.0, max_boost=0.16)
        payoff_contrast = 1.12 if (payoff_profile and payoff_profile.mean_luma < 60) else 1.08
        bg_chain = ";".join(
            [
                self._segment_motion_filter(
                    input_index=0,
                    output_label="bg0",
                    motion_type=motion_plan.hook_motion_type,
                    params=dict(motion_plan.hook_motion_params),
                    width=width,
                    height=height,
                    scale_start=motion_plan.scale_start,
                    scale_end=motion_plan.scale_end,
                ),
                self._segment_motion_filter(
                    input_index=1,
                    output_label="bg1",
                    motion_type=motion_plan.setup_motion_type,
                    params=dict(motion_plan.setup_motion_params),
                    width=width,
                    height=height,
                    scale_start=motion_plan.scale_start,
                    scale_end=max(motion_plan.scale_start + 0.04, motion_plan.scale_end - 0.03),
                ),
                self._segment_motion_filter(
                    input_index=2,
                    output_label="bg2",
                    motion_type=motion_plan.payoff_motion_type,
                    params=dict(motion_plan.payoff_motion_params),
                    width=width,
                    height=height,
                    scale_start=max(1.06, motion_plan.scale_start),
                    scale_end=max(1.18, motion_plan.scale_end),
                ),
                f"[bg0][bg1]xfade=transition={self._xfade_name(transition_plan.hook_to_setup_type)}:duration={transition_plan.hook_to_setup_duration_ms / 1000.0:.2f}:offset={first_cut:.2f}[v01]",
                f"[v01][bg2]xfade=transition={self._xfade_name(transition_plan.setup_to_payoff_type)}:duration={transition_plan.setup_to_payoff_duration_ms / 1000.0:.2f}:offset={second_cut:.2f}[vbase]",
            ]
        )
        filters = [
            bg_chain,
            *self._color_filter_chain(color_plan=color_plan, theme=theme),
            f"drawbox=x=0:y=0:w={width}:h={height}:color=black@0.05:t=fill",
            f"drawbox=x=0:y=0:w={width}:h=230:color=black@0.12:t=fill:enable='between(t,0.00,{timings[0][1]:.2f})'",
            f"drawbox=x=0:y=0:w={width}:h=200:color=black@0.08:t=fill:enable='between(t,{timings[1][0]:.2f},{timings[1][1]:.2f})'" if len(timings) > 1 else "",
            f"drawbox=x=0:y=0:w={width}:h=250:color=black@0.14:t=fill:enable='between(t,{timings[2][0]:.2f},{timings[2][1]:.2f})'" if len(timings) > 2 else "",
            f"drawbox=x=0:y={height - 620}:w={width}:h=620:color=black@0.17:t=fill:enable='between(t,0.00,{timings[0][1]:.2f})'",
            f"drawbox=x=0:y={height - 620}:w={width}:h=620:color=black@0.15:t=fill:enable='between(t,{timings[1][0]:.2f},{timings[1][1]:.2f})'" if len(timings) > 1 else "",
            f"drawbox=x=0:y={height - 660}:w={width}:h=660:color=black@0.22:t=fill:enable='between(t,{timings[2][0]:.2f},{timings[2][1]:.2f})'" if len(timings) > 2 else "",
            "unsharp=5:5:0.55:5:5:0.0",
            f"eq=brightness={hook_brightness:.3f}:contrast=1.08:saturation=0.90:enable='between(t,0.00,{timings[0][1]:.2f})'",
            f"eq=contrast=1.12:brightness={hook_brightness + 0.01:.3f}:saturation=0.94:enable='between(t,0.00,{first_impact_end:.2f})'",
            f"unsharp=5:5:0.72:5:5:0.0:enable='between(t,0.00,{first_impact_end:.2f})'",
            f"eq=brightness={setup_brightness:.3f}:contrast=1.03:saturation=0.86:enable='between(t,{timings[1][0]:.2f},{timings[1][1]:.2f})'" if len(timings) > 1 else "",
            f"subtitles='{escaped_subtitle_path}':fontsdir='/usr/share/fonts/truetype/dejavu'",
        ]
        filters = [item for item in filters if item]

        if len(timings) >= 3:
            final_start, final_end = timings[2]
            filters.extend(
                [
                    f"eq=contrast={payoff_contrast:.2f}:brightness={payoff_brightness:.3f}:saturation=0.88:enable='between(t,{final_start:.2f},{final_end:.2f})'",
                    f"colorbalance=rs=0.02:gs=0.005:bs=-0.01:enable='between(t,{final_start:.2f},{final_end:.2f})'",
                    f"unsharp=5:5:0.70:5:5:0.0:enable='between(t,{max(final_start, final_end - 1.1):.2f},{final_end:.2f})'",
                    f"eq=contrast=1.14:brightness={payoff_brightness + 0.01:.3f}:saturation=0.92:enable='between(t,{max(final_start, final_end - 0.85):.2f},{final_end:.2f})'",
                    f"drawbox=x=0:y={height - 700}:w={width}:h=700:color=black@0.26:t=fill:enable='between(t,{max(final_start, final_end - 0.95):.2f},{final_end:.2f})'",
                ]
            )

        return ",".join(filters) + "[vout]"

    def _escape_filter_value(self, value: str) -> str:
        escaped = value.replace("\\", "/")
        escaped = escaped.replace(":", r"\:")
        escaped = escaped.replace("'", r"\'")
        escaped = escaped.replace(",", r"\,")
        return escaped

    def _normalize_block(self, block: str, *, role: str) -> str:
        compact = self._ascii_safe_text(" ".join(block.split()))
        width = 17 if role == "hook" else 18
        max_lines = 3
        return self._fit_text(compact, width=width, max_lines=max_lines)

    def _write_unix_text(self, path: Path, text: str) -> None:
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)

    def _ascii_safe_text(self, value: str) -> str:
        normalized = (
            value.replace("\u2014", " ")
            .replace("\u2013", " ")
            .replace("\u2018", "'")
            .replace("\u2019", "'")
            .replace("\u201c", '"')
            .replace("\u201d", '"')
            .replace("\u2026", "...")
        )
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        normalized = re.sub(r"\s*-\s*", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _fit_text(self, value: str, *, width: int, max_lines: int) -> str:
        words = value.split()
        if not words:
            return ""

        wrapped = self._wrap_words(words, width=width)
        if len(wrapped) <= max_lines:
            return "\n".join(wrapped)

        shortened = self._semantic_shorten(words, width=width, max_lines=max_lines)
        wrapped = textwrap.wrap(shortened, width=width, break_long_words=False, break_on_hyphens=False)
        return "\n".join(wrapped[:max_lines])

    def _semantic_shorten(self, words: list[str], *, width: int, max_lines: int) -> str:
        kept = self._trim_low_value_words(words, width=width, max_lines=max_lines)
        wrapped = self._wrap_words(kept, width=width)
        if len(wrapped) <= max_lines:
            return " ".join(kept)

        tail_keep = self._tail_keep_count(kept)
        while len(kept) > max(3, tail_keep + 1):
            removable = self._best_removal_index(kept, preserve_tail=tail_keep)
            if removable is None:
                break
            kept = kept[:removable] + kept[removable + 1 :]
            wrapped = self._wrap_words(kept, width=width)
            if len(wrapped) <= max_lines:
                return " ".join(kept)

        return " ".join(kept)

    def _trim_low_value_words(self, words: list[str], *, width: int, max_lines: int) -> list[str]:
        kept = list(words)
        tail_keep = self._tail_keep_count(kept)
        while len(kept) > max(3, tail_keep + 1):
            wrapped = self._wrap_words(kept, width=width)
            if len(wrapped) <= max_lines:
                return kept
            removable = self._best_removal_index(kept, preserve_tail=tail_keep)
            if removable is None:
                break
            kept = kept[:removable] + kept[removable + 1 :]
        return kept

    def _best_removal_index(self, words: list[str], *, preserve_tail: int) -> int | None:
        cutoff = max(0, len(words) - preserve_tail)
        candidates: list[tuple[int, int]] = []
        for index, word in enumerate(words[:cutoff]):
            token = re.sub(r"[^A-Z0-9']+", "", word.upper())
            if not token:
                continue
            score = self._removal_priority(token=token, index=index, total=len(words))
            candidates.append((score, index))
        if not candidates:
            return None
        candidates.sort(reverse=True)
        return candidates[0][1]

    def _removal_priority(self, *, token: str, index: int, total: int) -> int:
        score = 0
        if token in STOPWORDS:
            score += 100
        if len(token) <= 3:
            score += 35
        if token in {"THEN", "JUST", "STILL", "VERY", "ALMOST", "EVERY", "SINGLE"}:
            score += 28
        if token.isdigit():
            score += 10
        if index < max(1, total // 2):
            score += 12
        return score

    def _tail_keep_count(self, words: list[str]) -> int:
        if len(words) >= 6:
            return 2
        return 1

    def _wrap_words(self, words: list[str], *, width: int) -> list[str]:
        return textwrap.wrap(" ".join(words), width=width, break_long_words=False, break_on_hyphens=False)

    def _highlight_word(self, block: str, *, theme: str) -> str:
        tokens = re.findall(r"[A-Z']+", block.upper())
        if not tokens:
            return "WATCH"
        profile = THEME_PROFILES.get(theme, THEME_PROFILES[DEFAULT_THEME])
        theme_keywords = profile["keywords"]
        weighted: list[tuple[int, str]] = []
        for index, token in enumerate(tokens):
            if token in STOPWORDS:
                continue
            score = len(token)
            if token in theme_keywords:
                score += 12
            if index == 0:
                score += 2
            if token.endswith(("ED", "ING")):
                score += 3
            weighted.append((score, token))
        if not weighted:
            weighted = [(len(token), token) for token in tokens if len(token) >= 3]
        if not weighted:
            return "WATCH"
        weighted.sort(key=lambda item: (item[0], len(item[1])), reverse=True)
        return weighted[0][1]

    def _infer_theme(self, script_text: str) -> str:
        tokens = set(re.findall(r"[A-Z']+", script_text.upper()))
        best_theme = DEFAULT_THEME
        best_score = -1
        for theme, profile in THEME_PROFILES.items():
            score = len(tokens & profile["keywords"])
            if score > best_score:
                best_theme = theme
                best_score = score
        return best_theme

    def _build_timings(
        self,
        duration_s: float,
        block_count: int,
        *,
        segment_durations: list[float] | None = None,
        edit_plan: EditPlan | None = None,
    ) -> list[tuple[float, float]]:
        effective = max(duration_s, MIN_VIDEO_DURATION_S)
        spoken_duration = max(duration_s, 0.0)
        if block_count <= 0:
            return []

        if segment_durations and len(segment_durations) == block_count:
            total = sum(max(0.0, item) for item in segment_durations)
            if total > 0:
                timings: list[tuple[float, float]] = []
                cursor = 0.0
                for index, raw_duration in enumerate(segment_durations):
                    duration = max(MIN_BLOCK_DURATION_S, raw_duration)
                    proposed_end = round(cursor + duration, 2)
                    if index == block_count - 1:
                        end = round(max(proposed_end, spoken_duration), 2)
                    else:
                        end = proposed_end
                    timings.append((round(cursor, 2), round(end, 2)))
                    cursor = end
                if timings[-1][1] < round(spoken_duration, 2):
                    timings[-1] = (timings[-1][0], round(spoken_duration, 2))
                return timings

        if edit_plan is not None:
            planned = [
                max(MIN_BLOCK_DURATION_S, float(edit_plan.timing_plan.hook_duration_s or MIN_BLOCK_DURATION_S)),
                max(MIN_BLOCK_DURATION_S, float(edit_plan.timing_plan.setup_duration_s or MIN_BLOCK_DURATION_S)),
                max(MIN_BLOCK_DURATION_S, float(edit_plan.timing_plan.payoff_duration_s or MIN_BLOCK_DURATION_S)),
            ][:block_count]
            total = sum(planned)
            if total > 0:
                timings: list[tuple[float, float]] = []
                cursor = 0.0
                for index, raw in enumerate(planned):
                    scaled = (raw / total) * effective
                    end = effective if index == block_count - 1 else round(cursor + scaled, 2)
                    timings.append((round(cursor, 2), round(end, 2)))
                    cursor = end
                return timings

        if block_count == 1:
            return [(0.0, round(effective, 2))]

        if block_count == 2:
            ratios = [0.44, 0.56]
        else:
            ratios = [0.30, 0.33, 0.37]

        timings: list[tuple[float, float]] = []
        start = 0.0
        for index, ratio in enumerate(ratios[:block_count]):
            block_duration = effective * ratio
            end = effective if index == block_count - 1 else round(start + block_duration, 2)
            timings.append((round(start, 2), round(end, 2)))
            start = end

        if block_count > 1:
            normalized: list[tuple[float, float]] = []
            cursor = 0.0
            for index, (start, end) in enumerate(timings):
                duration = end - start
                if index != block_count - 1:
                    duration = max(duration, MIN_BLOCK_DURATION_S)
                normalized_end = effective if index == block_count - 1 else round(cursor + duration, 2)
                normalized.append((round(cursor, 2), round(normalized_end, 2)))
                cursor = normalized_end
            if normalized[-1][1] < effective:
                normalized[-1] = (normalized[-1][0], round(effective, 2))
            timings = normalized
        return timings

    def _write_ass_subtitles(
        self,
        *,
        subtitle_path: Path,
        cues: list[ScreenTextCue],
        width: int,
        height: int,
        caption_plan: CaptionPlan,
    ) -> None:
        subtitle_path.parent.mkdir(parents=True, exist_ok=True)
        script = self._build_ass_document(cues=cues, width=width, height=height, caption_plan=caption_plan)
        subtitle_path.write_text(script, encoding="utf-8", newline="\n")

    def _build_ass_document(self, *, cues: list[ScreenTextCue], width: int, height: int, caption_plan: CaptionPlan) -> str:
        styles = "\n".join(
            [
                self._ass_style_line(
                    name="HookStyle",
                    font_family=caption_plan.font_family,
                    primary_color=caption_plan.text_color,
                    secondary_color="#FF8A2A",
                    outline_color=caption_plan.outline_color,
                    outline_width=caption_plan.outline_width,
                    fontsize=58 if caption_plan.font_size_mode == "large_mobile" else 48,
                    bold=-1,
                    alignment=2,
                    margin_l=92,
                    margin_r=92,
                    margin_v=self._caption_margin_v(caption_plan),
                    line_spacing=8,
                ),
                self._ass_style_line(
                    name="BodyStyle",
                    font_family=caption_plan.font_family,
                    primary_color=caption_plan.text_color,
                    secondary_color="#F3B16C",
                    outline_color=caption_plan.outline_color,
                    outline_width=caption_plan.outline_width,
                    fontsize=48 if caption_plan.font_size_mode == "large_mobile" else 40,
                    bold=-1,
                    alignment=2,
                    margin_l=96,
                    margin_r=96,
                    margin_v=self._caption_margin_v(caption_plan),
                    line_spacing=8,
                ),
                self._ass_style_line(
                    name="PayoffStyle",
                    font_family=caption_plan.font_family,
                    primary_color=caption_plan.text_color,
                    secondary_color="#FF7A18",
                    outline_color=caption_plan.outline_color,
                    outline_width=caption_plan.outline_width,
                    fontsize=54 if caption_plan.font_size_mode == "large_mobile" else 44,
                    bold=-1,
                    alignment=2,
                    margin_l=96,
                    margin_r=96,
                    margin_v=self._caption_margin_v(caption_plan),
                    line_spacing=8,
                ),
            ]
        )
        events = []
        for cue in cues:
            style_name = {
                "hook": "HookStyle",
                "setup": "BodyStyle",
                "payoff": "PayoffStyle",
            }[cue.style_role]
            events.append(
                "Dialogue: 0,"
                f"{self._ass_time(cue.start)},{self._ass_time(cue.end)},{style_name},,0,0,0,,"
                f"{self._caption_event_tags(cue, caption_plan=caption_plan)}{self._render_caption_text(cue, caption_plan=caption_plan)}"
            )
        return (
            "[Script Info]\n"
            "ScriptType: v4.00+\n"
            f"PlayResX: {width}\n"
            f"PlayResY: {height}\n"
            "WrapStyle: 2\n"
            "ScaledBorderAndShadow: yes\n\n"
            "[V4+ Styles]\n"
            "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,"
            "ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
            f"{styles}\n\n"
            "[Events]\n"
            "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"
            + "\n".join(events)
            + "\n"
        )

    def _ass_style_line(
        self,
        *,
        name: str,
        font_family: str,
        primary_color: str,
        secondary_color: str,
        outline_color: str,
        outline_width: int,
        fontsize: int,
        bold: int,
        alignment: int,
        margin_l: int,
        margin_r: int,
        margin_v: int,
        line_spacing: int,
    ) -> str:
        return (
            f"Style: {name},{font_family},{fontsize},{self._ass_color(primary_color)},{self._ass_color(secondary_color)},{self._ass_color(outline_color)},&H5A000000,"
            f"{bold},0,0,0,100,100,{line_spacing},0,1,{outline_width},0,{alignment},{margin_l},{margin_r},{margin_v},1"
        )

    def _ass_color(self, value: str) -> str:
        normalized = value.strip().lstrip("#")
        if len(normalized) != 6:
            normalized = "FFF4E8"
        rr = normalized[0:2]
        gg = normalized[2:4]
        bb = normalized[4:6]
        return f"&H00{bb}{gg}{rr}"

    def _caption_margin_v(self, caption_plan: CaptionPlan) -> int:
        if caption_plan.placement == "center":
            return 620
        return 220 if caption_plan.safe_margin_profile == "mobile_safe" else 190

    def _apply_caption_emphasis(self, text: str, *, caption_plan: CaptionPlan) -> str:
        rendered = text
        for token in caption_plan.emphasis_words:
            rendered = re.sub(rf"\b{re.escape(token)}\b", token.upper(), rendered, flags=re.IGNORECASE)
        return rendered

    def _caption_event_tags(self, cue: ScreenTextCue, *, caption_plan: CaptionPlan) -> str:
        strength = str(caption_plan.emphasis_strength or "medium").lower()
        role_profile = str(caption_plan.segment_caption_animation_profile.get(cue.style_role, "")).lower()
        hook_scale = "104" if strength == "high" else "102"
        payoff_scale = "108" if strength == "high" else "105"
        if cue.style_role == "hook":
            fade_out = "125" if "hold" in role_profile else "110"
            settle_scale = "101" if "bite" in role_profile else "100"
            return (
                rf"{{\fad(45,{fade_out})\blur0.40\bord7\fscx80\fscy80"
                + rf"\t(0,110,\fscx{hook_scale}\fscy{hook_scale})"
                + rf"\t(110,220,\fscx{settle_scale}\fscy{settle_scale})"
                + r"\move(540,1742,540,1674,0,155)}"
            )
        if cue.style_role == "payoff":
            first_scale = "110" if "surge" in role_profile else payoff_scale
            settle_scale = "103" if "hold" in role_profile else "102"
            return (
                r"{\fad(35,135)\blur0.35\bord7\fscx82\fscy82"
                + rf"\t(0,150,\fscx{first_scale}\fscy{first_scale})"
                + rf"\t(150,260,\fscx{settle_scale}\fscy{settle_scale})"
                + r"\move(540,1734,540,1662,0,190)}"
            )
        if "linger" in role_profile:
            return r"{\fad(60,105)\blur0.50\bord6\fscx91\fscy91\t(0,110,\fscx100\fscy100)\move(540,1726,540,1692,0,120)}"
        if "drift" in role_profile:
            return r"{\fad(52,92)\blur0.42\bord6\fscx89\fscy89\t(0,95,\fscx100\fscy100)\move(540,1726,540,1684,0,118)}"
        return r"{\fad(55,95)\blur0.45\bord6\fscx90\fscy90\t(0,105,\fscx100\fscy100)\move(540,1724,540,1688,0,115)}"

    def _render_caption_text(self, cue: ScreenTextCue, *, caption_plan: CaptionPlan) -> str:
        emphasized = self._apply_caption_emphasis(cue.text, caption_plan=caption_plan)
        duration_cs = max(10, int(round((cue.end - cue.start) * 100)))
        lines = [line for line in emphasized.splitlines() if line.strip()]
        if not lines:
            return ""

        words = [word for line in lines for word in line.split()]
        if not words:
            return self._ass_escape_text(emphasized)

        weighted_words: list[tuple[str, int]] = []
        for word in words:
            weighted_words.append((word, self._caption_word_weight(word, cue=cue, caption_plan=caption_plan)))
        total_weight = max(1, sum(weight for _, weight in weighted_words))
        base_slot = max(7, self._caption_base_slot(duration_cs=duration_cs, cue=cue, caption_plan=caption_plan, total_weight=total_weight))
        pieces: list[str] = []
        weighted_index = 0
        for line_index, line in enumerate(lines):
            line_words = line.split()
            for word_index, word in enumerate(line_words):
                escaped_word = self._ass_escape_text(word)
                _, weight = weighted_words[weighted_index]
                weighted_index += 1
                slot = max(7, int(round(base_slot * weight)))
                emphasis_open, emphasis_close = self._caption_word_tags(word, cue=cue, caption_plan=caption_plan)
                pieces.append(r"{\kf" + str(slot) + "}" + emphasis_open + escaped_word + emphasis_close)
                if word_index != len(line_words) - 1:
                    pieces.append(" ")
            if line_index != len(lines) - 1:
                pieces.append(r"\N")
        return "".join(pieces)

    def _caption_word_weight(self, word: str, *, cue: ScreenTextCue, caption_plan: CaptionPlan) -> int:
        normalized = re.sub(r"[^A-Z0-9']+", "", word.upper())
        if not normalized:
            return 1
        rule = str(caption_plan.key_word_emphasis_rules.get(normalized, "")).lower()
        weight = 1
        if rule == "strong":
            weight = 3
        elif rule == "medium":
            weight = 2
        if cue.style_role == "hook" and rule:
            weight += 1
        if cue.style_role == "payoff" and (rule or normalized == self._terminal_keyword(cue.text)):
            weight += 2
        return min(weight, 5)

    def _caption_word_tags(self, word: str, *, cue: ScreenTextCue, caption_plan: CaptionPlan) -> tuple[str, str]:
        normalized = re.sub(r"[^A-Z0-9']+", "", word.upper())
        if not normalized:
            return "", ""
        rule = str(caption_plan.key_word_emphasis_rules.get(normalized, "")).lower()
        terminal_keyword = self._terminal_keyword(cue.text)
        is_terminal_payoff = cue.style_role == "payoff" and normalized == terminal_keyword
        if not rule and not is_terminal_payoff:
            return "", ""
        if is_terminal_payoff:
            return (
                r"{\1c&H1E73FF&\bord8\blur0.25\fscx122\fscy122\t(0,130,\fscx110\fscy110)}",
                r"{\r}",
            )
        if cue.style_role == "hook" and rule == "strong":
            return (
                r"{\1c&H1E73FF&\bord8\blur0.30\fscx118\fscy118\t(0,100,\fscx107\fscy107)}",
                r"{\r}",
            )
        if cue.style_role == "payoff" and rule:
            return (
                r"{\1c&H4CA8F3&\bord7\blur0.4\fscx110\fscy110\t(0,110,\fscx104\fscy104)}",
                r"{\r}",
            )
        return (
            r"{\1c&H6CB1F3&\bord7\blur0.45\fscx108\fscy108\t(0,90,\fscx103\fscy103)}",
            r"{\r}",
        )

    def _caption_base_slot(self, *, duration_cs: int, cue: ScreenTextCue, caption_plan: CaptionPlan, total_weight: int) -> int:
        role_profile = str(caption_plan.segment_caption_animation_profile.get(cue.style_role, "")).lower()
        divisor = total_weight
        if cue.style_role == "hook":
            divisor = max(1, total_weight - 1)
        if cue.style_role == "payoff":
            divisor = max(1, total_weight - 1)
        base_slot = duration_cs // divisor
        if "hold" in role_profile:
            base_slot += 2
        elif "bite" in role_profile:
            base_slot = max(7, base_slot - 1)
        elif "drift" in role_profile:
            base_slot += 1
        return base_slot

    def _terminal_keyword(self, text: str) -> str:
        candidates = [
            token
            for token in re.findall(r"[A-Z0-9']+", text.upper())
            if len(token) >= 5 and token not in STOPWORDS
        ]
        return candidates[-1] if candidates else ""

    def _fallback_edit_plan(
        self,
        *,
        script_text: str,
        theme: str,
        segment_durations: list[float] | None,
    ) -> EditPlan:
        hook, setup, payoff = self.screen_text_adapter.adapt(script_text).as_list()
        blocks = {
            "hook": [hook] if hook else [],
            "setup": [setup] if setup else [],
            "payoff": [payoff] if payoff else [],
        }
        total = max(MIN_VIDEO_DURATION_S, sum(segment_durations or [2.7, 3.0, 3.3]))
        return EditPlan(
            caption_plan=CaptionPlan(segment_caption_blocks=blocks),
            generated_at="",
            rationale=f"fallback_edit_plan:{theme}",
            timing_plan=EditPlan().timing_plan if not segment_durations else EditPlan().timing_plan.__class__(
                hook_duration_s=segment_durations[0],
                setup_duration_s=segment_durations[1] if len(segment_durations) > 1 else 3.0,
                payoff_duration_s=segment_durations[2] if len(segment_durations) > 2 else 3.3,
                total_duration_s=total,
                cut_points=[segment_durations[0], segment_durations[0] + (segment_durations[1] if len(segment_durations) > 1 else 3.0)],
                voice_sync_points=[0.0, segment_durations[0], segment_durations[0] + (segment_durations[1] if len(segment_durations) > 1 else 3.0), total],
                caption_sync_points=[0.0, segment_durations[0], segment_durations[0] + (segment_durations[1] if len(segment_durations) > 1 else 3.0), total],
                transition_windows=[],
            ),
        )

    def _build_caption_cues(
        self,
        *,
        caption_plan: CaptionPlan,
        segment_texts: dict[str, str],
        timings: list[tuple[float, float]],
    ) -> list[ScreenTextCue]:
        roles = ["hook", "setup", "payoff"]
        cues: list[ScreenTextCue] = []
        for index, role in enumerate(roles[: len(timings)]):
            start, end = timings[index]
            blocks = list(caption_plan.segment_caption_blocks.get(role) or [])
            if not blocks:
                fallback = self._normalize_block(segment_texts.get(role, ""), role=role)
                blocks = [fallback] if fallback else []
            if not blocks:
                continue
            span = max(0.3, end - start)
            weights = self._segment_block_weights(role=role, block_count=len(blocks))
            total_weight = max(1.0, sum(weights))
            cursor = start
            for block_index, block in enumerate(blocks):
                block_span = span * (weights[block_index] / total_weight)
                cue_start = round(cursor, 2)
                cue_end = round(end if block_index == len(blocks) - 1 else cursor + block_span, 2)
                cursor = cue_end
                cues.append(
                    ScreenTextCue(
                        text=self._normalize_block(block, role=role),
                        start=cue_start,
                        end=cue_end,
                        style_role=role,
                    )
                )
        return cues

    def _segment_block_weights(self, *, role: str, block_count: int) -> list[float]:
        if block_count <= 1:
            return [1.0]
        if role == "hook":
            return [0.78] + [1.0] * (block_count - 1)
        if role == "payoff":
            return [1.0] * (block_count - 1) + [1.28]
        return [1.0] * block_count

    def _build_music_filter_chain(self, *, edit_plan: EditPlan, timings: list[tuple[float, float]]) -> str:
        profile = self._music_profile(edit_plan.music_plan.track_type)
        total_end = max(3.0, timings[-1][1])
        hook_end = timings[0][1]
        setup_end = timings[1][1] if len(timings) > 1 else total_end
        fade_in = edit_plan.music_plan.fade_in_ms / 1000.0
        fade_out = edit_plan.music_plan.fade_out_ms / 1000.0
        fade_out_start = max(0.0, total_end - fade_out)
        duck_volume = max(0.08, min(1.0, 10 ** (edit_plan.music_plan.ducking_level_db / 20.0)))
        return (
            f"[4:a]highpass=f={profile['noise_highpass']},lowpass=f={profile['noise_lowpass']},volume={profile['noise_volume']:.2f}[noise];"
            f"[5:a]lowpass=f={profile['tone_lowpass']},highpass=f={profile['tone_highpass']},asetrate=44100*{profile['tone_ratio']:.5f},aresample=44100,volume={profile['tone_volume']:.2f}[tone];"
            "[noise][tone]amix=inputs=2:weights='1 0.8':normalize=0[musicbase];"
            f"[musicbase]volume='if(lt(t,{hook_end:.2f}),{edit_plan.music_plan.volume_hook:.3f},if(lt(t,{setup_end:.2f}),{edit_plan.music_plan.volume_setup:.3f},{edit_plan.music_plan.volume_payoff:.3f}))':eval=frame,"
            f"afade=t=in:st=0:d={fade_in:.2f},afade=t=out:st={fade_out_start:.2f}:d={fade_out:.2f}[musiclvl];"
            + (
                f"[musiclvl]volume={duck_volume:.3f}[musicduck];"
                "[voice][musicduck]amix=inputs=2:weights='1 1':normalize=0[aout]"
                if edit_plan.music_plan.ducking_enabled
                else "[voice][musiclvl]amix=inputs=2:weights='1 0.8':normalize=0[aout]"
            )
        )

    def _music_profile(self, track_type: str) -> dict[str, float]:
        profiles = {
            "investigative_pulse": {"noise_highpass": 35, "noise_lowpass": 1400, "noise_volume": 0.22, "tone_lowpass": 220, "tone_highpass": 40, "tone_ratio": 0.92, "tone_volume": 0.11},
            "horror_low_drone": {"noise_highpass": 25, "noise_lowpass": 1100, "noise_volume": 0.26, "tone_lowpass": 120, "tone_highpass": 20, "tone_ratio": 0.74, "tone_volume": 0.15},
            "device_alert_tense": {"noise_highpass": 60, "noise_lowpass": 2400, "noise_volume": 0.18, "tone_lowpass": 500, "tone_highpass": 120, "tone_ratio": 1.24, "tone_volume": 0.09},
            "documentary_bed": {"noise_highpass": 40, "noise_lowpass": 1600, "noise_volume": 0.15, "tone_lowpass": 260, "tone_highpass": 50, "tone_ratio": 1.05, "tone_volume": 0.08},
        }
        return profiles.get(track_type, profiles["investigative_pulse"])

    def _segment_motion_filter(
        self,
        *,
        input_index: int,
        output_label: str,
        motion_type: str,
        params: dict[str, float | str],
        width: int,
        height: int,
        scale_start: float,
        scale_end: float,
    ) -> str:
        scale_delta = float(params.get("scale_delta", max(0.04, scale_end - scale_start)))
        local_scale_end = max(scale_start, scale_start + scale_delta)
        step = max(0.0007, scale_delta / 90.0)
        scale_expr = f"min({local_scale_end:.2f},{scale_start:.2f}+on*{step:.4f})"
        if motion_type in {"slow_zoom_out", "subtle_pull"}:
            local_scale_start = max(local_scale_end, scale_end)
            local_scale_end = max(scale_start, local_scale_start - scale_delta)
            scale_expr = f"max({local_scale_end:.2f},{local_scale_start:.2f}-on*{step:.4f})"
        if motion_type == "static":
            scale_expr = f"{scale_start:.2f}"
        pan_distance = float(params.get("pan_distance", 0.06))
        if motion_type == "pan_left":
            x_expr = f"iw*{0.20 + pan_distance:.2f}-on*0.18"
            y_expr = "ih*0.08"
        elif motion_type == "pan_up":
            x_expr = "iw*0.10"
            y_expr = f"ih*{0.18 + pan_distance:.2f}-on*0.16"
        elif motion_type == "pan_down":
            x_expr = "iw*0.10"
            y_expr = f"ih*0.02+on*0.16"
        elif motion_type == "pan_right":
            x_expr = "iw*0.04+on*0.18"
            y_expr = "ih*0.08"
        else:
            x_expr = "iw*0.08+on*0.10"
            y_expr = "ih*0.05+on*0.08"
        return (
            f"[{input_index}:v]scale={width * 2}:{height * 2}:force_original_aspect_ratio=increase,"
            f"zoompan=z='{scale_expr}':x='{x_expr}':y='{y_expr}':d=1:s={width}x{height}:fps=25[{output_label}]"
        )

    def _xfade_name(self, transition_type: str) -> str:
        mapping = {
            "hard_cut": "fade",
            "crossfade": "fade",
            "fade_to_black": "fadeblack",
            "smooth_wipe": "wipeleft",
        }
        return mapping.get(transition_type, "fade")

    def _color_filter_chain(self, *, color_plan, theme: str) -> list[str]:
        preset = str(color_plan.grade_preset)
        preset_filters = {
            "documentary_dark": [
                "[vbase]eq=contrast=1.10:brightness=-0.06:saturation=0.76",
                "curves=master='0/0 0.28/0.18 0.68/0.72 1/1'",
                "colorbalance=rs=0.01:gs=0.00:bs=-0.01",
            ],
            "institutional_cold": [
                "[vbase]eq=contrast=1.11:brightness=-0.05:saturation=0.74",
                "curves=master='0/0 0.30/0.20 0.70/0.75 1/1'",
                "colorbalance=rs=-0.02:gs=0.00:bs=0.04",
            ],
            "horror_lowkey": [
                "[vbase]eq=contrast=1.14:brightness=-0.08:saturation=0.68",
                "curves=master='0/0 0.32/0.16 0.72/0.76 1/1'",
                "colorbalance=rs=0.03:gs=-0.02:bs=0.04",
            ],
            "neutral_investigative": [
                "[vbase]eq=contrast=1.08:brightness=-0.04:saturation=0.82",
                "curves=master='0/0 0.30/0.22 0.70/0.76 1/1'",
            ],
            "device_alert_tense": [
                "[vbase]eq=contrast=1.13:brightness=-0.06:saturation=0.72",
                "curves=master='0/0 0.30/0.18 0.68/0.74 1/1'",
                "colorbalance=rs=0.03:gs=-0.01:bs=0.03",
            ],
        }
        filters = list(preset_filters.get(preset, preset_filters["neutral_investigative"]))
        filters.append(f"eq=contrast={float(color_plan.contrast_level):.2f}:brightness={float(color_plan.temperature_shift) / 3.0:.3f}:saturation={float(color_plan.saturation_level):.2f}")
        if color_plan.grain_enabled:
            filters.append(f"noise=alls={int(float(color_plan.grain_level) * 1.4)}:allf=t")
        if color_plan.vignette_enabled:
            filters.append(f"vignette=PI/{max(2.4, 6.2 - (float(color_plan.vignette_intensity) * 12.0)):.2f}")
        if str(color_plan.atmosphere_profile) in {"immersive_lowkey", "signal_pressure", "institutional_tension"}:
            filters.append("curves=all='0/0 0.20/0.14 0.52/0.58 1/1'")
        if theme == "facts":
            filters.append("gblur=sigma=0.12")
        return filters

    def _ass_escape_text(self, text: str) -> str:
        lines = []
        for raw_line in text.splitlines() or [text]:
            sanitized_line = self._ascii_safe_text(raw_line)
            sanitized_line = sanitized_line.replace("\\", r"\\")
            sanitized_line = sanitized_line.replace("{", "(").replace("}", ")")
            if sanitized_line:
                lines.append(sanitized_line)
        sanitized = r"\N".join(lines)
        return sanitized

    def _ass_time(self, seconds: float) -> str:
        total_cs = int(round(max(0.0, seconds) * 100))
        hours, rem = divmod(total_cs, 360000)
        minutes, rem = divmod(rem, 6000)
        secs, cs = divmod(rem, 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"

    def _generate_background(self, *, script_text: str, theme: str, render_job_id: str, variant: str) -> str | None:
        local_asset = self.background_service.pick_local_asset(theme=theme, render_job_id=render_job_id, variant=variant)
        if local_asset is not None:
            return str(local_asset)
        try:
            return self.background_service.generate(script_text=script_text, theme=theme, render_job_id=render_job_id)
        except BackgroundGenerationError:
            return None

    def _describe_background(self, path: str | None) -> AssetProfile | None:
        if not path:
            return None
        candidate = Path(path)
        if not candidate.exists():
            return None
        try:
            return self.background_service.describe_asset(candidate)
        except Exception:  # noqa: BLE001
            return None

    def _prepare_corrected_backgrounds(
        self,
        *,
        asset_plan: AssetPlan,
        corrected_dir: Path,
        render_job_id: str,
    ) -> tuple[dict[str, str], dict[str, AssetProfile]]:
        segment_names = ("hook", "setup", "payoff")
        source_paths = {
            "hook": Path(asset_plan.hook_asset),
            "setup": Path(asset_plan.setup_asset),
            "payoff": Path(asset_plan.payoff_asset),
        }
        opened = [Image.open(source_paths[name]).convert("RGB") for name in segment_names]
        try:
            corrected_images = balance_sequence(opened)
        finally:
            for image in opened:
                image.close()

        corrected_paths: dict[str, str] = {}
        corrected_profiles: dict[str, AssetProfile] = {}
        for name, image in zip(segment_names, corrected_images, strict=True):
            target = corrected_dir / f"{render_job_id}_{name}.jpg"
            image.save(target, format="JPEG", quality=95, optimize=True)
            image.close()
            with Image.open(target) as corrected_image:
                profile = analyze_frame(corrected_image.convert("RGB"))
            corrected_profiles[name] = AssetProfile(
                path=target,
                mean_luma=profile.mean_luminance,
                contrast=profile.contrast,
            )
            corrected_paths[name] = str(target)
        return corrected_paths, corrected_profiles

    def _block_brightness_adjustment(self, profile: AssetProfile | None, *, target: float, max_boost: float) -> float:
        if profile is None:
            return 0.04
        if profile.mean_luma >= target:
            return 0.02
        gap = target - profile.mean_luma
        boost = min(max_boost, 0.02 + (gap / 255.0) * 0.30)
        return round(boost, 3)

    def _resolve_dimensions(self, aspect_ratio: str | None) -> tuple[int, int]:
        if aspect_ratio == "16:9":
            return (1280, 720)
        return (1080, 1920)

    def _audio_duration(self, audio_path: Path) -> float:
        if audio_path.suffix.lower() == ".wav":
            with wave.open(str(audio_path), "rb") as reader:
                frame_rate = reader.getframerate() or 1
                frame_count = reader.getnframes()
                return round(frame_count / frame_rate, 2)
        return self._probe_duration(audio_path)

    def _probe_duration(self, audio_path: Path) -> float:
        ffprobe_path = shutil.which("ffprobe")
        if ffprobe_path:
            return self._run_ffprobe([ffprobe_path], str(audio_path))

        repo_root = Path(__file__).resolve().parents[4]
        try:
            audio_rel = audio_path.resolve().relative_to(repo_root)
        except ValueError as exc:
            raise RenderTransientError("RENDER_DURATION_PROBE_FAILED") from exc

        docker_path = shutil.which("docker")
        if not docker_path:
            raise RenderTransientError("RENDER_DURATION_PROBE_FAILED")

        workspace = repo_root.resolve().as_posix()
        container_audio = str(PurePosixPath("/workspace").joinpath(*audio_rel.parts))
        return self._run_ffprobe(
            [
                docker_path,
                "run",
                "--rm",
                "--entrypoint",
                "ffprobe",
                "-v",
                f"{workspace}:/workspace",
                "-w",
                "/workspace",
                os.getenv("CORTAI_FFMPEG_IMAGE", "cortai10-api"),
            ],
            container_audio,
        )

    def _run_ffprobe(self, command: list[str], audio_path: str) -> float:
        cmd = [
            *command,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ]
        try:
            output = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return round(float(output.stdout.strip()), 2)
        except Exception as exc:  # noqa: BLE001
            raise RenderTransientError("RENDER_DURATION_PROBE_FAILED") from exc
