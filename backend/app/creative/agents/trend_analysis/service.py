from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.creative.agents.trend_analysis.models import TrendAnalysisInput, TrendAnalysisResult
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import TrendProfile


@dataclass
class TrendAnalysisAgentService:
    trends_dir: Path = Path("backend/data/trends")

    def load(self, data: TrendAnalysisInput) -> TrendAnalysisResult:
        try:
            return self._load(data)
        except Exception:  # noqa: BLE001
            return self._fallback_result()

    def _load(self, data: TrendAnalysisInput) -> TrendAnalysisResult:
        niche = (data.niche or "").strip().lower()
        if not niche:
            return self._fallback_result()

        trend_path = self.trends_dir / f"{niche}.json"
        if not trend_path.exists():
            return self._fallback_result()

        payload = json.loads(trend_path.read_text(encoding="utf-8"))
        trend_profile = TrendProfile(
            niche=str(payload.get("niche") or niche),
            dominant_hooks=[str(item) for item in payload.get("dominant_hooks", []) if str(item).strip()],
            avg_duration=str(payload.get("avg_duration") or "8-12"),
            pacing=str(payload.get("pacing") or "baseline"),
            visual_style=str(payload.get("visual_style") or "phase1_baseline"),
            text_style=str(payload.get("text_style") or "caption_focus"),
        )
        return TrendAnalysisResult(
            trend_profile=trend_profile,
            fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
        )

    def _fallback_result(self) -> TrendAnalysisResult:
        return TrendAnalysisResult(
            trend_profile=TrendProfile(
                niche="default",
                dominant_hooks=["question"],
                avg_duration="8-12",
                pacing="baseline",
                visual_style="phase1_baseline",
                text_style="caption_focus",
            ),
            fallback=FallbackDecision(
                used=True,
                mode=FallbackMode.SAFE_DEFAULT.value,
                reason="TREND_PROFILE_FALLBACK",
            ),
        )
