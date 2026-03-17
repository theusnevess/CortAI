from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.creative.agents.learning.models import LearningAgentInput, LearningAgentResult
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import LearningInsights


@dataclass
class LearningAgentService:
    default_publish_records_path: Path = Path("OUT/data/publish_records/publish_records.jsonl")
    default_video_metrics_path: Path = Path("OUT/metrics/video_metrics.jsonl")
    default_analysis_dir: Path = Path("OUT/analysis")
    default_output_path: Path | None = None

    def generate(self, data: LearningAgentInput) -> LearningAgentResult:
        try:
            return self._generate(data)
        except Exception:  # noqa: BLE001
            result = self._fallback_result()
            self._persist(result.learning_insights, data.output_path or self.default_output_path)
            return result

    def _generate(self, data: LearningAgentInput) -> LearningAgentResult:
        publish_rows = self._read_jsonl(data.publish_records_path or self.default_publish_records_path)
        metric_rows = self._read_jsonl(data.video_metrics_path or self.default_video_metrics_path)
        analysis_dir = data.analysis_dir or self.default_analysis_dir
        hook_summary = self._read_json(analysis_dir / "hook_performance_summary.json")

        account_publish_rows = [row for row in publish_rows if str(row.get("account_id") or "") == data.account_id]
        account_metric_rows = [row for row in metric_rows if str(row.get("account_id") or "") == data.account_id]

        if not account_publish_rows and not account_metric_rows and not hook_summary:
            result = self._fallback_result()
            self._persist(result.learning_insights, data.output_path or self.default_output_path)
            return result

        recommended_hook = self._resolve_hook_type(hook_summary)
        average_duration = self._average_numeric(account_metric_rows, ("duration_s", "render_duration_s", "video_duration_s"))
        average_completion = self._average_numeric(account_metric_rows, ("completion_rate", "completion", "retention_rate"))
        average_views = self._average_numeric(account_metric_rows, ("views", "view_count"))

        target_duration_range = self._duration_bucket(average_duration)
        preferred_visual_style = "dark_backgrounds" if average_completion >= 0.4 else "phase1_baseline"
        preferred_voice_style = "calm_dark" if average_views >= 150 else "phase1_baseline"
        saturation_signal = "elevated" if len(account_publish_rows) >= 5 else "baseline"
        recommendations = [
            f"prefer_hook_type:{recommended_hook}",
            f"target_duration_range:{target_duration_range}",
        ]
        if preferred_visual_style != "phase1_baseline":
            recommendations.append(f"prefer_visual_style:{preferred_visual_style}")
        if saturation_signal != "baseline":
            recommendations.append("reduce_format_repetition")

        insights = LearningInsights(
            recommended_hook_type=recommended_hook,
            target_duration_range=target_duration_range,
            preferred_visual_style=preferred_visual_style,
            preferred_voice_style=preferred_voice_style,
            saturation_signal=saturation_signal,
            recommendations=recommendations,
            signal_summary={
                "publish_count": len(account_publish_rows),
                "metrics_count": len(account_metric_rows),
                "avg_views": average_views,
                "avg_completion_rate": average_completion,
                "avg_duration_s": average_duration,
            },
        )
        result = LearningAgentResult(
            learning_insights=insights,
            fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
        )
        self._persist(insights, data.output_path or self.default_output_path)
        return result

    def _fallback_result(self) -> LearningAgentResult:
        return LearningAgentResult(
            learning_insights=LearningInsights(
                recommended_hook_type="question",
                target_duration_range="8-12s",
                preferred_visual_style="phase1_baseline",
                preferred_voice_style="phase1_baseline",
                saturation_signal="baseline",
                recommendations=["fallback_default"],
                signal_summary={"publish_count": 0, "metrics_count": 0},
            ),
            fallback=FallbackDecision(
                used=True,
                mode=FallbackMode.SAFE_DEFAULT.value,
                reason="LEARNING_INSIGHTS_FALLBACK",
            ),
        )

    def _read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if not text:
                continue
            rows.append(json.loads(text))
        return rows

    def _read_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _resolve_hook_type(self, hook_summary: dict[str, Any]) -> str:
        hooks = hook_summary.get("hooks")
        if isinstance(hooks, list) and hooks:
            first = hooks[0]
            if isinstance(first, dict):
                for key in ("hook_style", "hook", "label", "pattern"):
                    value = str(first.get(key) or "").strip()
                    if value:
                        return value
        return "question"

    def _average_numeric(self, rows: list[dict[str, Any]], keys: tuple[str, ...]) -> float:
        values: list[float] = []
        for row in rows:
            for key in keys:
                value = row.get(key)
                if isinstance(value, (int, float)):
                    values.append(float(value))
                    break
        if not values:
            return 0.0
        return round(sum(values) / len(values), 4)

    def _duration_bucket(self, average_duration: float) -> str:
        if average_duration <= 0:
            return "8-12s"
        if average_duration <= 12:
            return "8-12s"
        if average_duration <= 45:
            return "35-45s"
        return "45-60s"

    def _persist(self, insights: LearningInsights, output_path: Path | None) -> None:
        if output_path is None:
            return
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(insights.to_dict(), indent=2), encoding="utf-8")
