from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.analysis.consistency.checker import run_consistency_checks
from app.analysis.consistency.models import ConsistencySummary
from app.analysis.consistency.store_json import save_consistency_json, save_consistency_markdown
from app.attribution.store_jsonl import DEFAULT_ATTRIBUTION_DIR, read_all_records as read_attribution_records
from app.content.creative_pack.store_jsonl import DEFAULT_CREATIVE_PACKS_PATH, read_all_packs
from app.data.publish_records.store_jsonl import DEFAULT_PUBLISH_RECORDS_PATH, read_all_records as read_publish_records
from app.experiments.store_jsonl import (
    ASSIGNMENTS_PATH,
    EXPERIMENTS_PATH,
    RESULTS_PATH,
    read_all_records as read_experiment_records,
)
from app.intelligence.store_jsonl import ACCOUNT_HEALTH_PATH, RISK_PROFILES_PATH, read_all_records as read_intelligence_records
from app.metrics.store_jsonl import DEFAULT_METRICS_PATH, read_all_records as read_metrics_records


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_safety_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            event_type = str(item.get("event_type") or "")
            if event_type.startswith("SAFETY/"):
                rows.append(item)
    return rows


@dataclass
class DataConsistencyCheckerService:
    publish_records_path: Path = DEFAULT_PUBLISH_RECORDS_PATH
    video_metrics_path: Path = DEFAULT_METRICS_PATH
    experiments_path: Path = EXPERIMENTS_PATH
    assignments_path: Path = ASSIGNMENTS_PATH
    results_path: Path = RESULTS_PATH
    creative_packs_path: Path = DEFAULT_CREATIVE_PACKS_PATH
    hook_performance_path: Path = DEFAULT_ATTRIBUTION_DIR / "hook_performance.jsonl"
    account_health_path: Path = ACCOUNT_HEALTH_PATH
    risk_profiles_path: Path = RISK_PROFILES_PATH
    safety_events_path: Path = Path("OUT/events/events.jsonl")
    analysis_dir: Path = Path("OUT/analysis")

    def generate_consistency_report(self, *, generated_at: str | None = None) -> ConsistencySummary:
        timestamp = generated_at or _now_iso()
        summary = run_consistency_checks(
            generated_at=timestamp,
            analysis_dir=self.analysis_dir,
            publish_records=read_publish_records(self.publish_records_path),
            video_metrics=read_metrics_records(self.video_metrics_path),
            experiments=read_experiment_records(self.experiments_path),
            assignments=read_experiment_records(self.assignments_path),
            results=read_experiment_records(self.results_path),
            creative_packs=read_all_packs(self.creative_packs_path),
            hook_performance=read_attribution_records(self.hook_performance_path),
            safety_events=_read_safety_events(self.safety_events_path),
            account_health=read_intelligence_records(self.account_health_path),
            risk_profiles=read_intelligence_records(self.risk_profiles_path),
        )
        save_consistency_json(summary, self.analysis_dir / "consistency_check.json")
        save_consistency_markdown(summary, self.analysis_dir / "consistency_check.md")
        return summary

