from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import os
from pathlib import Path
import re

from app.creative.agents.asset_selection.models import AssetSelectionInput, AssetSelectionResult
from app.content.backgrounds.service import BackgroundGeneratorService
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import AssetPlan


@dataclass
class AssetSelectionAgentService:
    background_service: BackgroundGeneratorService = field(default_factory=BackgroundGeneratorService)

    def select(self, data: AssetSelectionInput) -> AssetSelectionResult:
        try:
            return self._select(data)
        except Exception:  # noqa: BLE001
            return self._fallback_result()

    def _select(self, data: AssetSelectionInput) -> AssetSelectionResult:
        theme = self._resolve_theme((data.niche or "").strip().lower())
        render_key = self._selection_key(data.niche, data.topic)
        hook_asset = self.background_service.pick_local_asset(theme=theme, render_job_id=render_key, variant="hook")
        setup_asset = self.background_service.pick_local_asset(theme=theme, render_job_id=render_key, variant="setup")
        payoff_asset = self.background_service.pick_local_asset(theme=theme, render_job_id=render_key, variant="payoff")
        if hook_asset is None or setup_asset is None or payoff_asset is None:
            return self._fallback_result()

        visual_style = data.trend_profile.visual_style or "phase1_baseline"
        motion_profile = self._motion_profile(data)
        plan = AssetPlan(
            hook_asset=str(hook_asset),
            setup_asset=str(setup_asset),
            payoff_asset=str(payoff_asset),
            visual_style=visual_style,
            motion_profile=motion_profile,
        )
        return AssetSelectionResult(
            asset_selection=plan,
            fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
        )

    def _fallback_result(self) -> AssetSelectionResult:
        fallback_theme = self._resolve_theme("default")
        render_key = "asset-selection-fallback"
        hook_asset = self.background_service.pick_local_asset(theme=fallback_theme, render_job_id=render_key, variant="hook")
        setup_asset = self.background_service.pick_local_asset(theme=fallback_theme, render_job_id=render_key, variant="setup")
        payoff_asset = self.background_service.pick_local_asset(theme=fallback_theme, render_job_id=render_key, variant="payoff")
        return AssetSelectionResult(
            asset_selection=AssetPlan(
                hook_asset=str(hook_asset or ""),
                setup_asset=str(setup_asset or ""),
                payoff_asset=str(payoff_asset or ""),
                visual_style="phase1_baseline",
                motion_profile="subtle_push_in",
            ),
            fallback=FallbackDecision(
                used=True,
                mode=FallbackMode.SAFE_DEFAULT.value,
                reason="ASSET_SELECTION_FALLBACK",
            ),
        )

    def align_first_frame(
        self,
        *,
        niche: str,
        topic: str,
        hook_text: str,
        asset_plan: AssetPlan,
    ) -> AssetPlan:
        if not self._hook_visual_alignment_enabled():
            return asset_plan

        hook_type = self._detect_hook_type(topic=topic, hook_text=hook_text)
        anchor_signal = self._detect_anchor_signal(hook_type=hook_type, hook_text=hook_text)
        if not anchor_signal:
            return asset_plan

        anchor_asset = self._resolve_anchor_asset(hook_type=hook_type, anchor_signal=anchor_signal, niche=niche)
        if anchor_asset is None:
            return asset_plan

        return AssetPlan(
            hook_asset=str(anchor_asset),
            setup_asset=asset_plan.setup_asset,
            payoff_asset=asset_plan.payoff_asset,
            visual_style=asset_plan.visual_style,
            motion_profile=asset_plan.motion_profile,
        )

    def _resolve_theme(self, niche: str) -> str:
        requested = niche or "default"
        theme_dir = self.background_service.local_assets_dir / requested
        if theme_dir.exists():
            return requested

        aliases = {
            "history": "facts",
            "ancient_history": "facts",
            "true_crime": "conspiracy",
            "crime": "conspiracy",
            "mystery": "horror",
            "default": "horror",
        }
        aliased = aliases.get(requested)
        if aliased and (self.background_service.local_assets_dir / aliased).exists():
            return aliased

        available = sorted(
            path.name
            for path in self.background_service.local_assets_dir.iterdir()
            if path.is_dir()
        )
        return available[0] if available else requested

    def _selection_key(self, niche: str, topic: str) -> str:
        material = f"{niche.strip().lower()}::{topic.strip().lower()}".encode("utf-8")
        return sha256(material).hexdigest()[:12]

    def _motion_profile(self, data: AssetSelectionInput) -> str:
        content_mode = (data.strategy_profile.content_mode or "").strip().lower()
        pacing = (data.trend_profile.pacing or "").strip().lower()
        if content_mode == "conservative":
            return "steady_hold"
        if pacing == "fast_first_3s":
            return "subtle_push_in"
        return "phase1_baseline"

    def _hook_visual_alignment_enabled(self) -> bool:
        return os.getenv("CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT", "1") != "0"

    def _hook_visual_alignment_mode(self) -> str:
        return os.getenv("CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT_MODE", "refined_experiential").strip().lower() or "refined_experiential"

    def _detect_hook_type(self, *, topic: str, hook_text: str) -> str:
        text = self._normalize_text(f"{topic} {hook_text}")
        experiential_patterns = (
            " STARTED ",
            " WENT DARK ",
            " DISPLAYED ",
            " SPOKE ",
            " REOPENED ",
            " WAS SEALED ",
            " KEPT CHANGING ",
            " FELL OUT OF SYNC ",
            " APPEARED AFTER MIDNIGHT ",
        )
        inferential_patterns = (
            " CONTAINED ",
            " DID NOT MATCH ",
            " SHOWED ",
            " CONFLICTING ",
            " UNAUTHORIZED OVERRIDE ",
        )
        inferential_signals = (
            " LOG ",
            " RECORD ",
            " FILE ",
            " ARCHIVE ",
            " TRANSCRIPT ",
            " STATEMENT ",
            " TAPE ",
            " EVIDENCE ",
            " DATE ",
            " TIMESTAMP ",
            " OVERRIDE ",
            " AUDIO ",
        )
        experiential_signals = (
            " CAMERA ",
            " BLACKOUT ",
            " GLITCH ",
            " ELEVATOR ",
            " DOOR ",
            " WARNING ",
            " SIGNAL ",
            " VOICE ",
            " INTERCOM ",
            " TUNNEL ",
            " MAP ",
            " BLUEPRINT ",
            " PLATFORM ",
            " TIMETABLE ",
            " CORRIDOR ",
            " ROOM ",
            " WING ",
        )
        if any(pattern in text for pattern in experiential_patterns):
            return "experiential"
        if any(signal in text for signal in experiential_signals):
            return "experiential"
        if any(pattern in text for pattern in inferential_patterns):
            return "inferential"
        if any(signal in text for signal in inferential_signals):
            return "inferential"
        return "experiential"

    def _detect_anchor_signal(self, *, hook_type: str, hook_text: str) -> str:
        text = self._normalize_text(hook_text)
        if hook_type == "inferential":
            if any(token in text for token in (" TRANSCRIPT ", " AUDIO ")):
                return "text_audio_mismatch"
            if any(token in text for token in (" DATE ", " TIMESTAMP ", " FUTURE ")):
                return "timestamp_focus"
            if any(token in text for token in (" ARCHIVE ", " OVERRIDE ")):
                return "archive_override"
            if any(token in text for token in (" TAPE ", " EVIDENCE ")):
                return "evidence_media"
            if any(token in text for token in (" LOG ", " RECORD ", " FILE ", " STATEMENT ")):
                return "document_log"
            return ""

        if any(token in text for token in (" CAMERA ", " BLACKOUT ", " GLITCH ")):
            return "camera_glitch"
        if any(token in text for token in (" MAP ", " BLUEPRINT ", " TIMETABLE ", " CORRIDOR ")):
            return "map_corridor"
        if any(token in text for token in (" SEALED ", " LOCKED ", " LOCKER ", " ROOM ", " WING ")):
            return "sealed_access"
        if any(token in text for token in (" ELEVATOR ", " DOOR ")):
            return "object_anomaly"
        if any(token in text for token in (" WARNING ", " SIGNAL ")):
            return "warning_display"
        if any(token in text for token in (" VOICE ", " INTERCOM ", " RECORDER ", " SPEAKER ")):
            return "active_device"
        return ""

    def _resolve_anchor_asset(self, *, hook_type: str, anchor_signal: str, niche: str) -> Path | None:
        if hook_type == "inferential":
            if anchor_signal in {
                "document_log",
                "text_audio_mismatch",
                "timestamp_focus",
                "archive_override",
                "evidence_media",
            }:
                return self._asset_path("conspiracy", "conspiracy_02.jpg")
            return None

        mode = self._hook_visual_alignment_mode()
        experiential_map = self._experiential_anchor_map(mode=mode, niche=niche)
        asset = experiential_map.get(anchor_signal)
        if asset is not None:
            return asset

        # Preserve niche-driven fallback if no explicit anchor mapping is safe.
        theme = self._resolve_theme((niche or "").strip().lower())
        return self.background_service.pick_local_asset(theme=theme, render_job_id="visual-alignment-fallback", variant="hook")

    def _asset_path(self, theme: str, filename: str) -> Path | None:
        path = self.background_service.local_assets_dir / theme / filename
        return path if path.exists() else None

    def _experiential_anchor_map(self, *, mode: str, niche: str) -> dict[str, Path | None]:
        baseline = {
            "camera_glitch": self._asset_path("horror", "horror_03.jpg"),
            "object_anomaly": self._asset_path("horror", "horror_04.jpg"),
            "warning_display": self._asset_path("horror", "horror_04.jpg"),
            "active_device": self._asset_path("horror", "horror_03.jpg"),
        }
        if mode != "refined_experiential":
            return baseline

        refined = dict(baseline)
        refined.update(
            {
                # More literal anchors where the existing library gives a better object-level cue.
                "camera_glitch": self._asset_path("facts", "facts_02.jpg"),
                "active_device": self._asset_path("facts", "facts_02.jpg"),
                "map_corridor": self._asset_path("conspiracy", "conspiracy_02.jpg"),
                "sealed_access": self._asset_path("horror", "horror_04.jpg"),
            }
        )
        if niche.strip().lower() in {"true_crime", "crime"}:
            refined["active_device"] = self._asset_path("conspiracy", "conspiracy_02.jpg")
        return refined

    def _normalize_text(self, value: str) -> str:
        text = value.upper()
        text = re.sub(r"[^A-Z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return f" {text} "
