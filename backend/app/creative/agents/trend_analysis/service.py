from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.creative.agents.trend_analysis.collectors import TikTokCreativeCenterCollector
from app.creative.agents.trend_analysis.models import (
    TrendAnalysisInput,
    TrendAnalysisResult,
    TrendCollectorResult,
    TrendSourceRecord,
)
from app.creative.agents.trend_analysis.validation import (
    TrendConfidenceScoringService,
    TrendValidationResult,
    TrendValidationService,
)
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import TrendEvidenceReference, TrendProfile


@dataclass
class TrendAnalysisAgentService:
    trends_dir: Path = Path("backend/data/trends")
    creative_center_collector: TikTokCreativeCenterCollector = field(default_factory=TikTokCreativeCenterCollector)
    validation_service: TrendValidationService = field(default_factory=TrendValidationService)
    confidence_service: TrendConfidenceScoringService = field(default_factory=TrendConfidenceScoringService)

    def load(self, data: TrendAnalysisInput) -> TrendAnalysisResult:
        try:
            return self._load(data)
        except Exception:  # noqa: BLE001
            return self._fallback_result()

    def _load(self, data: TrendAnalysisInput) -> TrendAnalysisResult:
        niche = (data.niche or "").strip().lower()
        if not niche:
            return self._fallback_result(reason="TREND_PROFILE_FALLBACK_EMPTY_NICHE", data=data)

        current_time = self._resolve_current_time(data.current_time)
        storage = self._resolve_storage_roots()
        collector_result = self._maybe_collect_creative_center(data)
        self._persist_collector_source_record(storage=storage, collector_result=collector_result, niche=niche)
        source_records = self._load_source_records(
            niche=niche,
            region=data.region,
            storage=storage,
            current_time=current_time,
            collector_result=collector_result,
        )
        if source_records:
            trend_profile = self._assemble_trend_profile(
                niche=niche,
                region=data.region,
                source_records=source_records,
                current_time=current_time,
            )
            return self._finalize_candidate(
                trend_profile=trend_profile,
                storage=storage,
                current_time=current_time,
                data=data,
                collector_trace={
                    "storage_mode": storage["mode"],
                    "resolved_path": str(Path(storage["current_dir"]) / f"{niche}.json"),
                    "loaded_from_cache": False,
                    "legacy_layout_used": storage["mode"] == "legacy_flat",
                    "collector_version": trend_profile.collector_version,
                    "assembly_mode": "source_assembly",
                    "source_mix": [item.source for item in source_records],
                    "source_count": len(source_records),
                    "creative_center_refresh": collector_result.to_dict() if collector_result is not None else None,
                    "decision_trace": [],
                },
                primary_failure_reason="TREND_SOURCE_ASSEMBLY_REJECTED",
            )

        trend_path = self._resolve_trend_path(niche=niche, storage=storage)
        if trend_path is None:
            return self._fallback_result(reason="TREND_PROFILE_FALLBACK", data=data, current_time=current_time)

        payload = json.loads(trend_path.read_text(encoding="utf-8"))
        trend_profile = self._build_trend_profile(
            payload=payload,
            niche=niche,
            trend_path=trend_path,
            region=data.region,
            current_time=current_time,
        )
        return self._finalize_candidate(
            trend_profile=trend_profile,
            storage=storage,
            current_time=current_time,
            data=data,
            collector_trace={
                "storage_mode": storage["mode"],
                "resolved_path": str(trend_path),
                "loaded_from_cache": False,
                "legacy_layout_used": storage["mode"] == "legacy_flat",
                "collector_version": trend_profile.collector_version,
                "assembly_mode": "profile_load",
                "source_mix": [trend_profile.trend_source],
                "source_count": 1,
                "creative_center_refresh": collector_result.to_dict() if collector_result is not None else None,
                "decision_trace": [],
            },
            primary_failure_reason="TREND_PROFILE_REJECTED",
        )

    def _fallback_result(
        self,
        *,
        reason: str = "TREND_PROFILE_FALLBACK",
        data: TrendAnalysisInput | None = None,
        current_time: datetime | None = None,
    ) -> TrendAnalysisResult:
        resolved_time = current_time or self._resolve_current_time("" if data is None else data.current_time)
        region = "US" if data is None else str(data.region or "US")
        return TrendAnalysisResult(
            trend_profile=TrendProfile(
                niche="default",
                dominant_hooks=["question"],
                avg_duration="8-12",
                pacing="baseline",
                visual_style="phase1_baseline",
                text_style="caption_focus",
                region=region,
                trend_source="safe_default",
                confidence_scores={
                    "dominant_hooks": 0.25,
                    "avg_duration": 0.25,
                    "pacing": 0.25,
                    "visual_style": 0.25,
                },
                updated_at=self._to_iso(resolved_time),
                valid_until=self._to_iso(resolved_time + timedelta(days=7)),
                sample_size=0,
                evidence=[],
            ),
            fallback=FallbackDecision(
                used=True,
                mode=FallbackMode.SAFE_DEFAULT.value,
                reason=reason,
            ),
            validation_summary={
                "status": "FALLBACK",
                "valid": True,
                "warnings": ["SAFE_DEFAULT_TREND_PROFILE"],
                "errors": [],
                "overall_confidence": 0.25,
                "freshness_state": "fresh",
            },
            collector_trace={
                "storage_mode": "fallback_only",
                "resolved_path": "",
                "loaded_from_cache": False,
                "legacy_layout_used": False,
                "collector_version": "trend-analysis-agent-v2_0",
                "assembly_mode": "fallback",
                "source_mix": [],
                "source_count": 0,
                "creative_center_refresh": None,
                "decision_trace": [],
            },
        )

    def _resolve_storage_roots(self) -> dict[str, Path | str]:
        base = self.trends_dir
        current_dir = base / "current"
        history_dir = base / "history"
        manual_curation_dir = base / "manual_curation"
        cache_dir = base / "cache"
        if current_dir.exists() or history_dir.exists() or manual_curation_dir.exists() or cache_dir.exists():
            current_dir.mkdir(parents=True, exist_ok=True)
            history_dir.mkdir(parents=True, exist_ok=True)
            manual_curation_dir.mkdir(parents=True, exist_ok=True)
            cache_dir.mkdir(parents=True, exist_ok=True)
            (cache_dir / "creative_center").mkdir(parents=True, exist_ok=True)
            (cache_dir / "internal_metrics_validation").mkdir(parents=True, exist_ok=True)
            (cache_dir / "validated").mkdir(parents=True, exist_ok=True)
            return {
                "mode": "canonical_v2",
                "base": base,
                "current_dir": current_dir,
                "history_dir": history_dir,
                "manual_curation_dir": manual_curation_dir,
                "cache_dir": cache_dir,
            }

        base.mkdir(parents=True, exist_ok=True)
        return {
            "mode": "legacy_flat",
            "base": base,
            "current_dir": base,
            "history_dir": base / "history",
            "manual_curation_dir": base / "manual_curation",
            "cache_dir": base / "cache",
        }

    def _finalize_candidate(
        self,
        *,
        trend_profile: TrendProfile,
        storage: dict[str, Path | str],
        current_time: datetime,
        data: TrendAnalysisInput,
        collector_trace: dict[str, Any],
        primary_failure_reason: str,
    ) -> TrendAnalysisResult:
        primary_validation = self.validation_service.validate(trend_profile=trend_profile, current_time=current_time)
        collector_trace["decision_trace"].append(
            {
                "candidate": "primary",
                "source": trend_profile.trend_source,
                "decision": primary_validation.decision,
                "warnings": list(primary_validation.warnings),
                "errors": list(primary_validation.errors),
            }
        )
        if primary_validation.decision in {"APPROVE", "HOLD"}:
            collector_trace["shift_analysis"] = self._detect_shift(
                storage=storage,
                trend_profile=trend_profile,
                current_time=current_time,
            )
            self._persist_current_profile(storage=storage, trend_profile=trend_profile)
            self._persist_validated_cache(storage=storage, trend_profile=trend_profile)
            self._persist_snapshot(storage=storage, trend_profile=trend_profile, current_time=current_time)
            return TrendAnalysisResult(
                trend_profile=trend_profile,
                fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
                validation_summary=primary_validation.to_dict(),
                collector_trace=collector_trace,
            )

        if data.allow_cached:
            cached_result = self._load_validated_cache(storage=storage, niche=data.niche, current_time=current_time)
            if cached_result is not None:
                cached_profile, cached_validation = cached_result
                collector_trace["decision_trace"].append(
                    {
                        "candidate": "validated_cache",
                        "source": cached_profile.trend_source,
                        "decision": cached_validation.decision,
                        "warnings": list(cached_validation.warnings),
                        "errors": list(cached_validation.errors),
                    }
                )
                collector_trace["loaded_from_cache"] = True
                collector_trace["fallback_path"] = "validated_cache"
                return TrendAnalysisResult(
                    trend_profile=cached_profile,
                    fallback=FallbackDecision(
                        used=True,
                        mode=FallbackMode.LOCAL_DEFAULT.value,
                        reason="TREND_CACHE_FALLBACK",
                    ),
                    validation_summary=cached_validation.to_dict(),
                    collector_trace=collector_trace,
                )

        history_result = self._load_history_fallback(storage=storage, niche=data.niche, current_time=current_time)
        if history_result is not None:
            history_profile, history_validation = history_result
            collector_trace["decision_trace"].append(
                {
                    "candidate": "history",
                    "source": history_profile.trend_source,
                    "decision": history_validation.decision,
                    "warnings": list(history_validation.warnings),
                    "errors": list(history_validation.errors),
                }
            )
            collector_trace["fallback_path"] = "history"
            return TrendAnalysisResult(
                trend_profile=history_profile,
                fallback=FallbackDecision(
                    used=True,
                    mode=FallbackMode.LOCAL_DEFAULT.value,
                    reason="TREND_HISTORY_FALLBACK",
                ),
                validation_summary=history_validation.to_dict(),
                collector_trace=collector_trace,
            )

        fallback = self._fallback_result(reason=primary_failure_reason, data=data, current_time=current_time)
        fallback.collector_trace["decision_trace"] = list(collector_trace.get("decision_trace", []))
        fallback.collector_trace["fallback_path"] = "safe_default"
        return fallback

    def _maybe_collect_creative_center(self, data: TrendAnalysisInput) -> TrendCollectorResult | None:
        if not data.force_refresh:
            return None
        return self.creative_center_collector.collect(data)

    def _resolve_trend_path(self, *, niche: str, storage: dict[str, Path | str]) -> Path | None:
        current_dir = Path(storage["current_dir"])
        candidate = current_dir / f"{niche}.json"
        if candidate.exists():
            return candidate
        if storage["mode"] == "legacy_flat":
            return candidate if candidate.exists() else None
        legacy_candidate = Path(storage["base"]) / f"{niche}.json"
        if legacy_candidate.exists():
            return legacy_candidate
        return None

    def _build_trend_profile(
        self,
        *,
        payload: dict[str, Any],
        niche: str,
        trend_path: Path,
        region: str,
        current_time: datetime,
    ) -> TrendProfile:
        updated_at = self._resolve_updated_at(payload=payload, trend_path=trend_path)
        trend_source = str(payload.get("trend_source") or "manual_file_legacy")
        source_window_days = 14 if trend_source in {"manual_file_legacy", "manual_curation"} else 7
        valid_until = self._resolve_valid_until(
            payload=payload,
            updated_at=updated_at,
            source_window_days=source_window_days,
        )
        evidence = self._parse_evidence(payload.get("evidence"), region=region)
        confidence_scores = self._parse_confidence_scores(payload.get("confidence_scores"))
        if not confidence_scores:
            confidence_scores = self._default_confidence_scores(
                trend_source=trend_source,
                has_evidence=bool(evidence),
                current_time=current_time,
                valid_until=valid_until,
            )
        return TrendProfile(
            niche=str(payload.get("niche") or niche),
            dominant_hooks=[str(item) for item in payload.get("dominant_hooks", []) if str(item).strip()],
            avg_duration=str(payload.get("avg_duration") or "8-12"),
            pacing=str(payload.get("pacing") or "baseline"),
            visual_style=str(payload.get("visual_style") or "phase1_baseline"),
            text_style=str(payload.get("text_style") or "caption_focus"),
            region=str(payload.get("region") or region or "US"),
            trend_source=trend_source,
            confidence_scores=confidence_scores,
            updated_at=self._to_iso(updated_at),
            valid_until=self._to_iso(valid_until),
            sample_size=max(int(payload.get("sample_size") or 0), len(evidence)),
            evidence=evidence,
            trend_version=str(payload.get("trend_version") or "2.0"),
            collector_version=str(payload.get("collector_version") or "trend-analysis-agent-v2_0"),
        )

    def _load_source_records(
        self,
        *,
        niche: str,
        region: str,
        storage: dict[str, Path | str],
        current_time: datetime,
        collector_result: TrendCollectorResult | None,
    ) -> list[TrendSourceRecord]:
        records: list[TrendSourceRecord] = []
        manual_record = self._load_source_record_file(
            path=Path(storage["manual_curation_dir"]) / f"{niche}.json",
            source="manual_curation",
            niche=niche,
            region=region,
        )
        if manual_record is not None:
            records.append(manual_record)
        creative_center_record = self._load_source_record_file(
            path=Path(storage["cache_dir"]) / "creative_center" / f"{niche}.json",
            source="creative_center",
            niche=niche,
            region=region,
        )
        if creative_center_record is not None:
            records.append(creative_center_record)
        internal_record = self._load_source_record_file(
            path=Path(storage["cache_dir"]) / "internal_metrics_validation" / f"{niche}.json",
            source="internal_metrics_validation",
            niche=niche,
            region=region,
        )
        if internal_record is not None:
            records.append(internal_record)
        if collector_result is not None and collector_result.source_record is not None:
            records = [item for item in records if item.source != "creative_center"]
            records.append(collector_result.source_record)
        records = [item for item in records if self._source_record_is_usable(item=item, current_time=current_time)]
        records.sort(key=lambda item: (self._source_priority(item.source), item.source))
        return records

    def _load_source_record_file(
        self,
        *,
        path: Path,
        source: str,
        niche: str,
        region: str,
    ) -> TrendSourceRecord | None:
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return None
        return TrendSourceRecord(
            source=source,
            niche=str(payload.get("niche") or niche),
            region=str(payload.get("region") or region or "US"),
            collected_at=str(payload.get("collected_at") or payload.get("updated_at") or ""),
            sample_size=max(int(payload.get("sample_size") or 0), len(payload.get("evidence") or [])),
            dominant_hooks=[str(item) for item in payload.get("dominant_hooks", []) if str(item).strip()],
            avg_duration=str(payload.get("avg_duration") or ""),
            pacing=str(payload.get("pacing") or ""),
            visual_style=str(payload.get("visual_style") or ""),
            text_style=str(payload.get("text_style") or ""),
            evidence=self._parse_evidence(payload.get("evidence"), region=region),
            source_metadata=dict(payload.get("source_metadata") or payload.get("metadata") or {}),
        )

    def _source_record_is_usable(self, *, item: TrendSourceRecord, current_time: datetime) -> bool:
        collected_at = self._resolve_current_time(item.collected_at)
        return current_time <= collected_at + timedelta(days=self._source_window_days(item.source))

    def _assemble_trend_profile(
        self,
        *,
        niche: str,
        region: str,
        source_records: list[TrendSourceRecord],
        current_time: datetime,
    ) -> TrendProfile:
        ordered_sources = sorted(source_records, key=lambda item: (self._source_priority(item.source), item.source))
        updated_at = max(self._resolve_current_time(item.collected_at) for item in ordered_sources if item.collected_at)
        valid_until = min(
            self._resolve_current_time(item.collected_at) + timedelta(days=self._source_window_days(item.source))
            for item in ordered_sources
            if item.collected_at
        )
        dominant_hooks = self._assemble_hooks(ordered_sources)
        evidence: list[TrendEvidenceReference] = []
        for item in ordered_sources:
            evidence.extend(item.evidence)
        trend_source = ordered_sources[0].source if len(ordered_sources) == 1 else "hybrid"
        confidence_scores = self._assembled_confidence_scores(
            source_records=ordered_sources,
            current_time=current_time,
            valid_until=valid_until,
        )
        return TrendProfile(
            niche=niche,
            dominant_hooks=dominant_hooks,
            avg_duration=self._choose_source_field(ordered_sources, "avg_duration", default="8-12"),
            pacing=self._choose_source_field(ordered_sources, "pacing", default="baseline"),
            visual_style=self._choose_source_field(ordered_sources, "visual_style", default="phase1_baseline"),
            text_style=self._choose_source_field(ordered_sources, "text_style", default="caption_focus"),
            region=region or "US",
            trend_source=trend_source,
            confidence_scores=confidence_scores,
            updated_at=self._to_iso(updated_at),
            valid_until=self._to_iso(valid_until),
            sample_size=sum(item.sample_size for item in ordered_sources),
            evidence=evidence,
            trend_version="2.0",
            collector_version="trend-analysis-agent-v2_0_phase_b",
        )

    def _persist_snapshot(
        self,
        *,
        storage: dict[str, Path | str],
        trend_profile: TrendProfile,
        current_time: datetime,
    ) -> None:
        history_dir = Path(storage["history_dir"]) / trend_profile.niche
        history_dir.mkdir(parents=True, exist_ok=True)
        snapshot_name = current_time.strftime("%Y%m%dT%H%M%SZ.json")
        snapshot_path = history_dir / snapshot_name
        if not snapshot_path.exists():
            snapshot_path.write_text(json.dumps(trend_profile.to_dict(), indent=2), encoding="utf-8")

    def _detect_shift(
        self,
        *,
        storage: dict[str, Path | str],
        trend_profile: TrendProfile,
        current_time: datetime,
    ) -> dict[str, Any]:
        baseline = self._load_previous_trend(storage=storage, niche=trend_profile.niche, current_time=current_time)
        if baseline is None:
            return {
                "shift_detected": False,
                "baseline_available": False,
                "changes": [],
            }
        previous_profile, _ = baseline
        changes: list[dict[str, object]] = []
        if previous_profile.dominant_hooks != trend_profile.dominant_hooks:
            changes.append(
                {
                    "field": "dominant_hooks",
                    "old": list(previous_profile.dominant_hooks),
                    "new": list(trend_profile.dominant_hooks),
                    "significance": "high",
                }
            )
        if previous_profile.pacing != trend_profile.pacing:
            changes.append(
                {
                    "field": "pacing",
                    "old": previous_profile.pacing,
                    "new": trend_profile.pacing,
                    "significance": "medium",
                }
            )
        if previous_profile.visual_style != trend_profile.visual_style:
            changes.append(
                {
                    "field": "visual_style",
                    "old": previous_profile.visual_style,
                    "new": trend_profile.visual_style,
                    "significance": "medium",
                }
            )
        if previous_profile.avg_duration != trend_profile.avg_duration:
            changes.append(
                {
                    "field": "avg_duration",
                    "old": previous_profile.avg_duration,
                    "new": trend_profile.avg_duration,
                    "significance": "medium",
                }
            )
        return {
            "shift_detected": bool(changes),
            "baseline_available": True,
            "changes": changes,
            "comparison_source": previous_profile.trend_source,
        }

    def _persist_current_profile(
        self,
        *,
        storage: dict[str, Path | str],
        trend_profile: TrendProfile,
    ) -> None:
        current_path = Path(storage["current_dir"]) / f"{trend_profile.niche}.json"
        current_path.parent.mkdir(parents=True, exist_ok=True)
        current_path.write_text(json.dumps(trend_profile.to_dict(), indent=2), encoding="utf-8")

    def _persist_validated_cache(
        self,
        *,
        storage: dict[str, Path | str],
        trend_profile: TrendProfile,
    ) -> None:
        validated_dir = Path(storage["cache_dir"]) / "validated"
        validated_dir.mkdir(parents=True, exist_ok=True)
        (validated_dir / f"{trend_profile.niche}.json").write_text(
            json.dumps(trend_profile.to_dict(), indent=2),
            encoding="utf-8",
        )

    def _persist_collector_source_record(
        self,
        *,
        storage: dict[str, Path | str],
        collector_result: TrendCollectorResult | None,
        niche: str,
    ) -> None:
        if collector_result is None or collector_result.source_record is None:
            return
        if collector_result.source_record.source != "creative_center":
            return
        target = Path(storage["cache_dir"]) / "creative_center" / f"{niche}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(collector_result.source_record.to_dict(), indent=2),
            encoding="utf-8",
        )

    def _load_validated_cache(
        self,
        *,
        storage: dict[str, Path | str],
        niche: str,
        current_time: datetime,
    ) -> tuple[TrendProfile, TrendValidationResult] | None:
        validated_path = Path(storage["cache_dir"]) / "validated" / f"{niche}.json"
        return self._load_profile_candidate(path=validated_path, niche=niche, current_time=current_time)

    def _load_history_fallback(
        self,
        *,
        storage: dict[str, Path | str],
        niche: str,
        current_time: datetime,
    ) -> tuple[TrendProfile, TrendValidationResult] | None:
        history_dir = Path(storage["history_dir"]) / niche
        if not history_dir.exists():
            return None
        for path in sorted(history_dir.glob("*.json"), reverse=True):
            candidate = self._load_profile_candidate(path=path, niche=niche, current_time=current_time)
            if candidate is None:
                continue
            _, validation = candidate
            if validation.decision in {"APPROVE", "HOLD"}:
                return candidate
        return None

    def _load_previous_trend(
        self,
        *,
        storage: dict[str, Path | str],
        niche: str,
        current_time: datetime,
    ) -> tuple[TrendProfile, TrendValidationResult] | None:
        current_candidate = self._load_profile_candidate(
            path=Path(storage["current_dir"]) / f"{niche}.json",
            niche=niche,
            current_time=current_time,
        )
        if current_candidate is not None:
            return current_candidate
        return self._load_history_fallback(storage=storage, niche=niche, current_time=current_time)

    def _load_profile_candidate(
        self,
        *,
        path: Path,
        niche: str,
        current_time: datetime,
    ) -> tuple[TrendProfile, TrendValidationResult] | None:
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return None
        trend_profile = self._build_trend_profile(
            payload=payload,
            niche=niche,
            trend_path=path,
            region=str(payload.get("region") or "US"),
            current_time=current_time,
        )
        validation = self.validation_service.validate(trend_profile=trend_profile, current_time=current_time)
        if validation.decision == "REJECT":
            return None
        return trend_profile, validation

    def _resolve_updated_at(self, *, payload: dict[str, Any], trend_path: Path) -> datetime:
        raw_value = str(payload.get("updated_at") or "").strip()
        if raw_value:
            return self._resolve_current_time(raw_value)
        return datetime.fromtimestamp(trend_path.stat().st_mtime, tz=timezone.utc)

    def _resolve_valid_until(
        self,
        *,
        payload: dict[str, Any],
        updated_at: datetime,
        source_window_days: int,
    ) -> datetime:
        raw_value = str(payload.get("valid_until") or "").strip()
        if raw_value:
            return self._resolve_current_time(raw_value)
        return updated_at + timedelta(days=source_window_days)

    def _parse_evidence(self, raw_items: Any, *, region: str) -> list[TrendEvidenceReference]:
        if not isinstance(raw_items, list):
            return []
        evidence: list[TrendEvidenceReference] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            evidence.append(
                TrendEvidenceReference(
                    evidence_type=str(item.get("evidence_type") or ""),
                    source=str(item.get("source") or ""),
                    reference_id=str(item.get("reference_id") or ""),
                    reference_url=str(item.get("reference_url") or ""),
                    captured_at=str(item.get("captured_at") or ""),
                    region=str(item.get("region") or region or "US"),
                    metadata=dict(item.get("metadata") or {}),
                )
            )
        return evidence

    def _parse_confidence_scores(self, raw_scores: Any) -> dict[str, float]:
        if not isinstance(raw_scores, dict):
            return {}
        parsed: dict[str, float] = {}
        for key, value in raw_scores.items():
            try:
                parsed[str(key)] = float(value)
            except (TypeError, ValueError):
                continue
        return parsed

    def _default_confidence_scores(
        self,
        *,
        trend_source: str,
        has_evidence: bool,
        current_time: datetime,
        valid_until: datetime,
    ) -> dict[str, float]:
        source_quality = self._source_quality(trend_source)
        freshness_bonus = 0.0 if current_time > valid_until else 0.1
        evidence_bonus = 0.1 if has_evidence else 0.0
        base = min(source_quality + freshness_bonus + evidence_bonus, 0.95)
        return {
            "dominant_hooks": round(base, 4),
            "avg_duration": round(base, 4),
            "pacing": round(base, 4),
            "visual_style": round(base, 4),
            "overall": round(base, 4),
        }

    def _assembled_confidence_scores(
        self,
        *,
        source_records: list[TrendSourceRecord],
        current_time: datetime,
        valid_until: datetime,
    ) -> dict[str, float]:
        max_source_quality = max(self._source_quality(item.source) for item in source_records)
        sample_size = sum(item.sample_size for item in source_records)
        sample_bonus = 0.15 if sample_size >= 20 else 0.1 if sample_size >= 10 else 0.05 if sample_size > 0 else 0.0
        source_mix_bonus = 0.1 if len(source_records) >= 2 else 0.0
        freshness_bonus = 0.1 if current_time <= valid_until else 0.0
        base = min(max_source_quality + sample_bonus + source_mix_bonus + freshness_bonus, 0.95)
        return {
            "dominant_hooks": round(base, 4),
            "avg_duration": round(base, 4),
            "pacing": round(base, 4),
            "visual_style": round(base, 4),
            "text_style": round(base, 4),
            "overall": round(base, 4),
        }

    def _assemble_hooks(self, source_records: list[TrendSourceRecord]) -> list[str]:
        scores: dict[str, float] = {}
        first_seen: dict[str, tuple[int, int]] = {}
        for source_index, record in enumerate(source_records):
            weight = self._source_hook_weight(record.source)
            for hook_index, hook in enumerate(record.dominant_hooks):
                key = hook.strip()
                if not key:
                    continue
                scores[key] = scores.get(key, 0.0) + weight - (hook_index * 0.01)
                first_seen.setdefault(key, (source_index, hook_index))
        ordered = sorted(scores, key=lambda item: (-scores[item], first_seen[item][0], first_seen[item][1], item))
        return ordered[:3]

    def _choose_source_field(self, source_records: list[TrendSourceRecord], field_name: str, *, default: str) -> str:
        for item in source_records:
            value = str(getattr(item, field_name) or "").strip()
            if value:
                return value
        return default

    def _source_window_days(self, source: str) -> int:
        return {
            "creative_center": 7,
            "manual_curation": 14,
            "internal_metrics_validation": 30,
            "cache:creative_center": 7,
            "cache:internal_metrics_validation": 30,
            "manual_file_legacy": 14,
        }.get(source, 14)

    def _source_quality(self, source: str) -> float:
        return {
            "creative_center": 0.8,
            "manual_curation": 0.7,
            "internal_metrics_validation": 0.6,
            "manual_file_legacy": 0.45,
            "safe_default": 0.25,
        }.get(source, 0.4)

    def _source_priority(self, source: str) -> int:
        return {
            "creative_center": 0,
            "manual_curation": 1,
            "internal_metrics_validation": 2,
        }.get(source, 99)

    def _source_hook_weight(self, source: str) -> float:
        return {
            "creative_center": 3.0,
            "manual_curation": 2.0,
            "internal_metrics_validation": 1.0,
        }.get(source, 1.0)

    def _resolve_current_time(self, raw_value: str) -> datetime:
        value = (raw_value or "").strip()
        if not value:
            return datetime.now(timezone.utc)
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).astimezone(timezone.utc)

    def _to_iso(self, value: datetime) -> str:
        return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
