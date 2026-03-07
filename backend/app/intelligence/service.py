from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.data.publish_records.store_jsonl import read_all_records as read_publish_records
from app.data.video_metrics.store_jsonl import read_all_records as read_video_metrics
from app.intelligence.models import PlatformIntelligenceBundle
from app.intelligence.pacing_analysis import analyze_account_health, analyze_pacing, analyze_risk_profile
from app.intelligence.repo import save_if_absent
from app.intelligence.store_jsonl import (
    ACCOUNT_HEALTH_PATH,
    PACING_PROFILES_PATH,
    PUBLISH_WINDOWS_PATH,
    RISK_PROFILES_PATH,
    read_all_records,
)
from app.intelligence.window_analysis import analyze_publish_windows


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class PlatformIntelligenceService:
    def __init__(
        self,
        *,
        publish_records_path: Path = Path("OUT/data/publish_records/publish_records.jsonl"),
        video_metrics_path: Path = Path("OUT/data/video_metrics/video_metrics.jsonl"),
        events_path: Path = Path("OUT/events/events.jsonl"),
        intelligence_dir: Path = Path("OUT/intelligence"),
    ) -> None:
        self.publish_records_path = publish_records_path
        self.video_metrics_path = video_metrics_path
        self.events_path = events_path
        self.intelligence_dir = intelligence_dir

    def analyze_account(self, *, account_id: str, generated_at: str | None = None) -> PlatformIntelligenceBundle:
        timestamp = generated_at or _now_iso()
        publish_records = [row for row in read_publish_records(self.publish_records_path) if row.get("account_id") == account_id]
        metrics = [row for row in read_video_metrics(self.video_metrics_path) if row.get("account_id") == account_id]
        safety_events = [
            row
            for row in read_all_records(self.events_path)
            if row.get("account_id") == account_id and str(row.get("event_type") or "").startswith("SAFETY/")
        ]

        publish_window = analyze_publish_windows(
            account_id=account_id,
            publish_records=publish_records,
            video_metrics=metrics,
            generated_at=timestamp,
        )
        risk_profile = analyze_risk_profile(account_id=account_id, safety_events=safety_events, generated_at=timestamp)
        pacing = analyze_pacing(
            account_id=account_id,
            publish_records=publish_records,
            safety_events=safety_events,
            generated_at=timestamp,
        )
        account_health = analyze_account_health(
            account_id=account_id,
            publish_records=publish_records,
            video_metrics=metrics,
            risk_profile=risk_profile,
            generated_at=timestamp,
        )

        actions = {
            "publish_window": save_if_absent(
                publish_window.to_dict(),
                key_field="recommendation_id",
                path=self.intelligence_dir / PUBLISH_WINDOWS_PATH.name,
            ),
            "pacing": save_if_absent(
                pacing.to_dict(),
                key_field="recommendation_id",
                path=self.intelligence_dir / PACING_PROFILES_PATH.name,
            ),
            "risk_profile": save_if_absent(
                risk_profile.to_dict(),
                key_field="profile_id",
                path=self.intelligence_dir / RISK_PROFILES_PATH.name,
            ),
            "account_health": save_if_absent(
                account_health.to_dict(),
                key_field="snapshot_id",
                path=self.intelligence_dir / ACCOUNT_HEALTH_PATH.name,
            ),
        }
        return PlatformIntelligenceBundle(
            publish_window=publish_window,
            pacing=pacing,
            risk_profile=risk_profile,
            account_health=account_health,
            actions=actions,
        )
