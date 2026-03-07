from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.attribution.duration_analysis import build_duration_analysis, build_pattern_performance, infer_pattern_key
from app.attribution.hook_analysis import build_hook_performance
from app.attribution.repo import save_if_absent
from app.attribution.store_jsonl import (
    DURATION_ANALYSIS_PATH,
    HOOK_PERFORMANCE_PATH,
    PATTERN_PERFORMANCE_PATH,
    STRUCTURE_PERFORMANCE_PATH,
    read_all_records,
)
from app.attribution.structure_analysis import build_structure_key, build_structure_performance
from app.data.publish_records.store_jsonl import read_all_records as read_publish_records
from app.data.video_metrics.store_jsonl import read_all_records as read_video_metrics
from app.experiments.store_jsonl import ASSIGNMENTS_PATH, read_all_records as read_experiment_records


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class AdvancedAttributionService:
    def __init__(
        self,
        *,
        publish_records_path: Path = Path("OUT/data/publish_records/publish_records.jsonl"),
        video_metrics_path: Path = Path("OUT/data/video_metrics/video_metrics.jsonl"),
        creative_packs_path: Path = Path("OUT/content/creative_packs/creative_packs.jsonl"),
        assignments_path: Path = Path("OUT/experiments/assignments.jsonl"),
        attribution_dir: Path = Path("OUT/attribution"),
    ) -> None:
        self.publish_records_path = publish_records_path
        self.video_metrics_path = video_metrics_path
        self.creative_packs_path = creative_packs_path
        self.assignments_path = assignments_path
        self.attribution_dir = attribution_dir

    def analyze_account(self, *, account_id: str, generated_at: str | None = None) -> dict[str, Any]:
        timestamp = generated_at or _now_iso()
        publish_rows = [row for row in read_publish_records(self.publish_records_path) if row.get("account_id") == account_id]
        metrics_rows = [row for row in read_video_metrics(self.video_metrics_path) if row.get("account_id") == account_id]
        creative_rows = [row for row in read_all_records(self.creative_packs_path) if row.get("account_id") == account_id]
        assignment_rows = read_experiment_records(self.assignments_path)

        metrics_by_video = {str(row.get("video_id") or row.get("external_video_id") or ""): row for row in metrics_rows}
        creative_by_id = {str(row.get("creative_pack_id") or ""): row for row in creative_rows}
        assignments_by_subject = {str(row.get("subject_key") or ""): row for row in assignment_rows}

        hook_items: list[dict[str, Any]] = []
        structure_items: list[dict[str, Any]] = []
        duration_items: list[dict[str, Any]] = []
        pattern_items: list[dict[str, Any]] = []
        actions = {"hook": [], "structure": [], "duration": [], "pattern": []}

        for publish in publish_rows:
            metadata = publish.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}
            creative_pack_id = str(metadata.get("creative_pack_id") or "")
            creative_pack = creative_by_id.get(creative_pack_id, {})
            metric = metrics_by_video.get(str(publish.get("video_id") or ""), {})
            views = int(metric.get("views") or 0)
            completion_rate = float(metric.get("completion_rate") or 0.0)
            watch_3s_rate = float(metric.get("retention_3s") or 0.0)
            hook_key = self._resolve_hook_key(creative_pack)
            structure_key = build_structure_key(str(creative_pack.get("script_skeleton") or ""))
            experiment_variant = self._resolve_experiment_variant(
                assignments_by_subject=assignments_by_subject,
                creative_pack_id=creative_pack_id,
                publish=publish,
            )
            duration_s = self._resolve_duration_s(metadata)
            title = str(creative_pack.get("title") or "")
            pattern_key = infer_pattern_key(hook_key=hook_key, structure_key=structure_key, title=title)

            hook = build_hook_performance(
                account_id=account_id,
                publish_id=str(publish.get("publish_id") or ""),
                creative_pack_id=creative_pack_id,
                hook_key=hook_key,
                views=views,
                completion_rate=completion_rate,
                watch_3s_rate=watch_3s_rate,
                experiment_variant=experiment_variant,
                generated_at=timestamp,
            )
            structure = build_structure_performance(
                account_id=account_id,
                publish_id=str(publish.get("publish_id") or ""),
                creative_pack_id=creative_pack_id,
                structure_key=structure_key,
                views=views,
                completion_rate=completion_rate,
                experiment_variant=experiment_variant,
                generated_at=timestamp,
            )
            duration = build_duration_analysis(
                account_id=account_id,
                publish_id=str(publish.get("publish_id") or ""),
                creative_pack_id=creative_pack_id,
                duration_s=duration_s,
                completion_rate=completion_rate,
                generated_at=timestamp,
            )
            pattern = build_pattern_performance(
                account_id=account_id,
                publish_id=str(publish.get("publish_id") or ""),
                creative_pack_id=creative_pack_id,
                pattern_key=pattern_key,
                views=views,
                completion_rate=completion_rate,
                experiment_variant=experiment_variant,
                generated_at=timestamp,
            )

            actions["hook"].append(
                save_if_absent(
                    hook.to_dict(),
                    key_field="hook_performance_id",
                    path=self.attribution_dir / HOOK_PERFORMANCE_PATH.name,
                )
            )
            actions["structure"].append(
                save_if_absent(
                    structure.to_dict(),
                    key_field="structure_performance_id",
                    path=self.attribution_dir / STRUCTURE_PERFORMANCE_PATH.name,
                )
            )
            actions["duration"].append(
                save_if_absent(
                    duration.to_dict(),
                    key_field="duration_analysis_id",
                    path=self.attribution_dir / DURATION_ANALYSIS_PATH.name,
                )
            )
            actions["pattern"].append(
                save_if_absent(
                    pattern.to_dict(),
                    key_field="pattern_performance_id",
                    path=self.attribution_dir / PATTERN_PERFORMANCE_PATH.name,
                )
            )
            hook_items.append(hook.to_dict())
            structure_items.append(structure.to_dict())
            duration_items.append(duration.to_dict())
            pattern_items.append(pattern.to_dict())

        return {
            "hook_performance": hook_items,
            "structure_performance": structure_items,
            "duration_analysis": duration_items,
            "pattern_performance": pattern_items,
            "actions": actions,
        }

    def _resolve_hook_key(self, creative_pack: dict[str, Any]) -> str:
        hooks = creative_pack.get("hook_candidates")
        if isinstance(hooks, list) and hooks:
            return str(hooks[0])
        return "UNKNOWN_HOOK"

    def _resolve_duration_s(self, metadata: dict[str, Any]) -> int:
        for key in ("duration_s", "effective_duration_s"):
            value = metadata.get(key)
            try:
                parsed = int(value)
            except (TypeError, ValueError):
                continue
            return max(parsed, 0)
        return 0

    def _resolve_experiment_variant(
        self,
        *,
        assignments_by_subject: dict[str, dict[str, Any]],
        creative_pack_id: str,
        publish: dict[str, Any],
    ) -> str | None:
        for subject_key in (
            creative_pack_id,
            f"{publish.get('account_id') or ''}|{publish.get('window_id') or ''}",
            str(publish.get("publish_id") or ""),
        ):
            row = assignments_by_subject.get(subject_key)
            if row is not None:
                return str(row.get("variant") or "") or None
        return None
