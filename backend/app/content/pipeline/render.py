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
from app.content.screen_text.service import ScreenTextAdapterService, ScreenTextCue

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

        video_path = self.base_dir / "video" / f"{render_job_id}.mp4"
        metadata_dir = self.base_dir / "metadata"
        metadata_path = metadata_dir / f"{render_job_id}.json"
        text_path = metadata_dir / f"{render_job_id}.txt"
        subtitle_path = metadata_dir / f"{render_job_id}.ass"
        video_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_dir.mkdir(parents=True, exist_ok=True)

        duration_s = self._audio_duration(source_audio)
        theme = self._infer_theme(cleaned_script)
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
        timings = self._build_timings(duration_s, len(blocks), segment_durations=segment_durations)
        subtitle_cues = [
            ScreenTextCue(
                text=self._normalize_block(cue.text, role=cue.style_role),
                start=cue.start,
                end=cue.end,
                style_role=cue.style_role,
            )
            for cue in screen_text_blocks.timed_cues(timings)
        ]
        self._write_ass_subtitles(subtitle_path=subtitle_path, cues=subtitle_cues, width=self._resolve_dimensions(aspect_ratio)[0], height=self._resolve_dimensions(aspect_ratio)[1])
        hook_background_path = self._generate_background(
            script_text=cleaned_script,
            theme=theme,
            render_job_id=render_job_id,
            variant="hook",
        )
        setup_background_path = self._generate_background(
            script_text=cleaned_script,
            theme=theme,
            render_job_id=render_job_id,
            variant="setup",
        )
        payoff_background_path = self._generate_background(
            script_text=cleaned_script,
            theme=theme,
            render_job_id=render_job_id,
            variant="payoff",
        )
        highlights = [self._highlight_word(block, theme=theme) for block in blocks]
        hook_profile = self._describe_background(hook_background_path)
        setup_profile = self._describe_background(setup_background_path)
        payoff_profile = self._describe_background(payoff_background_path)

        text_path.write_text(cleaned_script, encoding="utf-8")
        render_mode = self._render_video_file(
            audio_path=source_audio,
            timings=timings,
            theme=theme,
            highlights=highlights,
            subtitle_path=subtitle_path,
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
                    "hook_background_path": hook_background_path,
                    "setup_background_path": setup_background_path,
                    "payoff_background_path": payoff_background_path,
                    "hook_background_mean_luma": None if hook_profile is None else round(hook_profile.mean_luma, 2),
                    "setup_background_mean_luma": None if setup_profile is None else round(setup_profile.mean_luma, 2),
                    "payoff_background_mean_luma": None if payoff_profile is None else round(payoff_profile.mean_luma, 2),
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
            hook_profile=hook_profile,
            setup_profile=setup_profile,
            payoff_profile=payoff_profile,
        )
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
            "[4:a]highpass=f=35,lowpass=f=1500,volume=0.36[noise];"
            "[5:a]lowpass=f=180,volume=0.10[drone];"
            "[noise][drone]amix=inputs=2:weights='1 0.8':normalize=0[amb];"
            "[voice][amb]amix=inputs=2:weights='1 0.72':normalize=0[aout]",
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
        hook_profile: AssetProfile | None,
        setup_profile: AssetProfile | None,
        payoff_profile: AssetProfile | None,
    ) -> str:
        del highlights
        escaped_subtitle_path = self._escape_filter_value(subtitle_path)
        first_cut = max(0.0, timings[1][0] - 0.20) if len(timings) > 1 else 0.0
        second_cut = max(0.0, timings[2][0] - 0.20) if len(timings) > 2 else first_cut
        hook_brightness = self._block_brightness_adjustment(hook_profile, target=78.0, max_boost=0.09)
        setup_brightness = self._block_brightness_adjustment(setup_profile, target=76.0, max_boost=0.06)
        payoff_brightness = self._block_brightness_adjustment(payoff_profile, target=84.0, max_boost=0.16)
        payoff_contrast = 1.12 if (payoff_profile and payoff_profile.mean_luma < 60) else 1.08
        bg_chain = (
            "[0:v]scale="
            f"{width * 2}:{height * 2}:force_original_aspect_ratio=increase,"
            "zoompan="
            "z='min(1.22,1.08+on*0.0013)':"
            "x='iw*0.05+on*0.24':"
            "y='ih*0.03+on*0.12':"
            f"d=1:s={width}x{height}:fps=25[bg0];"
            "[1:v]scale="
            f"{width * 2}:{height * 2}:force_original_aspect_ratio=increase,"
            "zoompan="
            "z='min(1.28,1.16+on*0.0011)':"
            "x='iw*0.12+on*0.22':"
            "y='ih*0.07+on*0.12':"
            f"d=1:s={width}x{height}:fps=25[bg1];"
            "[2:v]scale="
            f"{width * 2}:{height * 2}:force_original_aspect_ratio=increase,"
            "zoompan="
            "z='min(1.40,1.28+on*0.0012)':"
            "x='iw*0.22+on*0.24':"
            "y='ih*0.13+on*0.14':"
            f"d=1:s={width}x{height}:fps=25[bg2];"
            f"[bg0][bg1]xfade=transition=fade:duration=0.20:offset={first_cut:.2f}[v01];"
            f"[v01][bg2]xfade=transition=fade:duration=0.20:offset={second_cut:.2f}[vbase]"
        )
        filters = [
            bg_chain,
            "[vbase]eq=contrast=1.04:brightness=-0.03:saturation=0.78",
            "gblur=sigma=0.25",
            "noise=alls=9:allf=t",
            "eq=contrast=1.06:brightness=-0.02:saturation=0.80",
            "vignette=PI/5",
            f"drawbox=x=0:y={height - 500}:w={width}:h=500:color=black@0.10:t=fill",
            f"eq=brightness={hook_brightness:.3f}:contrast=1.05:enable='between(t,0.00,{timings[0][1]:.2f})'",
            f"eq=brightness={setup_brightness:.3f}:contrast=1.03:enable='between(t,{timings[1][0]:.2f},{timings[1][1]:.2f})'" if len(timings) > 1 else "",
            f"subtitles='{escaped_subtitle_path}':fontsdir='/usr/share/fonts/truetype/dejavu'",
        ]
        filters = [item for item in filters if item]

        if len(timings) >= 3:
            final_start, final_end = timings[2]
            filters.extend(
                [
                    f"eq=contrast={payoff_contrast:.2f}:brightness={payoff_brightness:.3f}:saturation=0.88:enable='between(t,{final_start:.2f},{final_end:.2f})'",
                    f"colorbalance=rs=0.02:gs=0.005:bs=-0.01:enable='between(t,{final_start:.2f},{final_end:.2f})'",
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

    def _write_ass_subtitles(self, *, subtitle_path: Path, cues: list[ScreenTextCue], width: int, height: int) -> None:
        subtitle_path.parent.mkdir(parents=True, exist_ok=True)
        script = self._build_ass_document(cues=cues, width=width, height=height)
        subtitle_path.write_text(script, encoding="utf-8", newline="\n")

    def _build_ass_document(self, *, cues: list[ScreenTextCue], width: int, height: int) -> str:
        styles = "\n".join(
            [
                self._ass_style_line(
                    name="HookStyle",
                    fontsize=40,
                    bold=-1,
                    alignment=1,
                    margin_l=132,
                    margin_r=132,
                    margin_v=380,
                    line_spacing=4,
                ),
                self._ass_style_line(
                    name="BodyStyle",
                    fontsize=34,
                    bold=-1,
                    alignment=1,
                    margin_l=128,
                    margin_r=128,
                    margin_v=380,
                    line_spacing=4,
                ),
                self._ass_style_line(
                    name="PayoffStyle",
                    fontsize=36,
                    bold=-1,
                    alignment=1,
                    margin_l=128,
                    margin_r=128,
                    margin_v=380,
                    line_spacing=4,
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
            ass_text = self._ass_escape_text(cue.text)
            events.append(
                "Dialogue: 0,"
                f"{self._ass_time(cue.start)},{self._ass_time(cue.end)},{style_name},,0,0,0,,"
                f"{{\\fad(120,120)}}{ass_text}"
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
        fontsize: int,
        bold: int,
        alignment: int,
        margin_l: int,
        margin_r: int,
        margin_v: int,
        line_spacing: int,
    ) -> str:
        return (
            f"Style: {name},DejaVu Sans,{fontsize},&H00187AFF,&H00187AFF,&H00061702,&H64000000,"
            f"{bold},0,0,0,100,100,{line_spacing},0,1,6,2,{alignment},{margin_l},{margin_r},{margin_v},1"
        )

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
