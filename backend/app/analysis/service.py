from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.analysis.account_health_summary import build_account_health_summary
from app.analysis.attribution_summary import build_hook_performance_summary
from app.analysis.experiment_analysis import build_experiment_winners
from app.analysis.metrics_summary import build_pilot_metrics_summary
from app.analysis.models import (
    AccountHealthItem,
    AccountHealthSummary,
    ExperimentWinnerItem,
    ExperimentWinners,
    HookPerformanceItem,
    HookPerformanceSummary,
    PilotMetricsSummary,
)
from app.analysis.repo import AnalysisRepo
from app.attribution.store_jsonl import (
    HOOK_PERFORMANCE_PATH,
    read_all_records as read_attribution_records,
)
from app.data.publish_records.store_jsonl import (
    DEFAULT_PUBLISH_RECORDS_PATH,
    read_all_records as read_publish_records,
)
from app.experiments.store_jsonl import (
    ASSIGNMENTS_PATH,
    EXPERIMENTS_PATH,
    read_all_records as read_experiment_records,
)
from app.intelligence.store_jsonl import (
    ACCOUNT_HEALTH_PATH,
    RISK_PROFILES_PATH,
    read_all_records as read_intelligence_records,
)
from app.metrics.store_jsonl import DEFAULT_METRICS_PATH, read_all_records as read_metrics_records


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class AnalysisService:
    def __init__(
        self,
        *,
        publish_records_path: Path = DEFAULT_PUBLISH_RECORDS_PATH,
        video_metrics_path: Path = DEFAULT_METRICS_PATH,
        experiments_path: Path = EXPERIMENTS_PATH,
        assignments_path: Path = ASSIGNMENTS_PATH,
        hook_performance_path: Path = HOOK_PERFORMANCE_PATH,
        account_health_path: Path = ACCOUNT_HEALTH_PATH,
        risk_profiles_path: Path = RISK_PROFILES_PATH,
        creative_packs_path: Path = Path("OUT/content/creative_packs/creative_packs.jsonl"),
        events_path: Path = Path("OUT/events/events.jsonl"),
        analysis_dir: Path = Path("OUT/analysis"),
    ) -> None:
        self.publish_records_path = publish_records_path
        self.video_metrics_path = video_metrics_path
        self.experiments_path = experiments_path
        self.assignments_path = assignments_path
        self.hook_performance_path = hook_performance_path
        self.account_health_path = account_health_path
        self.risk_profiles_path = risk_profiles_path
        self.creative_packs_path = creative_packs_path
        self.events_path = events_path
        self.repo = AnalysisRepo(base_dir=analysis_dir)

    def generate_analysis_snapshots(self, *, generated_at: str | None = None) -> dict[str, Any]:
        timestamp = generated_at or _now_iso()
        publish_records = read_publish_records(self.publish_records_path)
        video_metrics = self._read_jsonl(self.video_metrics_path)
        experiments = read_experiment_records(self.experiments_path)
        assignments = read_experiment_records(self.assignments_path)
        hook_performance = read_attribution_records(self.hook_performance_path)
        account_health_rows = read_intelligence_records(self.account_health_path)
        risk_profiles = read_intelligence_records(self.risk_profiles_path)
        creative_packs = self._read_jsonl(self.creative_packs_path)
        safety_events = [
            row for row in self._read_jsonl(self.events_path)
            if str(row.get("event_type") or "").startswith("SAFETY/")
        ]

        metrics_summary = build_pilot_metrics_summary(
            generated_at=timestamp,
            publish_records=publish_records,
            video_metrics=video_metrics,
        )
        experiment_winners = build_experiment_winners(
            generated_at=timestamp,
            experiments=experiments,
            assignments=assignments,
            metrics=video_metrics,
        )
        hook_summary = build_hook_performance_summary(
            generated_at=timestamp,
            hook_performance=hook_performance,
            creative_packs=creative_packs,
            video_metrics=video_metrics,
        )
        account_health = build_account_health_summary(
            generated_at=timestamp,
            publish_records=publish_records,
            safety_events=safety_events,
            account_health_snapshots=account_health_rows,
            risk_profiles=risk_profiles,
        )

        metrics_model = PilotMetricsSummary(**metrics_summary)
        experiment_model = ExperimentWinners(
            generated_at=experiment_winners["generated_at"],
            experiments=[ExperimentWinnerItem(**item) for item in experiment_winners["experiments"]],
        )
        hook_model = HookPerformanceSummary(
            generated_at=hook_summary["generated_at"],
            hooks=[HookPerformanceItem(**item) for item in hook_summary["hooks"]],
        )
        health_model = AccountHealthSummary(
            generated_at=account_health["generated_at"],
            accounts=[AccountHealthItem(**item) for item in account_health["accounts"]],
        )

        paths = {
            "pilot_metrics_summary": str(self.repo.save_pilot_metrics_summary(metrics_model)),
            "experiment_winners": str(self.repo.save_experiment_winners(experiment_model)),
            "hook_performance_summary": str(self.repo.save_hook_performance_summary(hook_model)),
            "account_health_summary": str(self.repo.save_account_health_summary(health_model)),
        }
        return {
            "generated_at": timestamp,
            "paths": paths,
            "pilot_metrics_summary": metrics_model.to_dict(),
            "experiment_winners": experiment_model.to_dict(),
            "hook_performance_summary": hook_model.to_dict(),
            "account_health_summary": health_model.to_dict(),
        }

    def _read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        return rows
