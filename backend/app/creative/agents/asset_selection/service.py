from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path

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
