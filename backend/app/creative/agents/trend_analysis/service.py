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
from app.creative.agents.trend_analysis.confidence_calibration import (
    TrendConfidenceCalibration,
    TrendConfidenceCalibrator,
)
from app.creative.agents.trend_analysis.downstream_utility import (
    TrendDownstreamUtilityMapper,
    TrendDownstreamUtilitySummary,
)
from app.creative.agents.trend_analysis.freshness import TrendFreshnessEvaluator, TrendValiditySummary
from app.creative.agents.trend_analysis.provenance import TrendProvenanceBuilder
from app.creative.agents.trend_analysis.shift_analysis import TrendShiftAnalyzer
from app.creative.agents.trend_analysis.source_governance import (
    TrendSourceGovernanceEvaluator,
    TrendSourceGovernanceResult,
)
from app.creative.agents.trend_analysis.trace_auditability import TrendTraceBuilder
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
    source_governance_evaluator: TrendSourceGovernanceEvaluator = field(default_factory=TrendSourceGovernanceEvaluator)
    provenance_builder: TrendProvenanceBuilder = field(default_factory=TrendProvenanceBuilder)
    freshness_evaluator: TrendFreshnessEvaluator = field(default_factory=TrendFreshnessEvaluator)
    confidence_calibrator: TrendConfidenceCalibrator = field(default_factory=TrendConfidenceCalibrator)
    shift_analyzer: TrendShiftAnalyzer = field(default_factory=TrendShiftAnalyzer)
    downstream_utility_mapper: TrendDownstreamUtilityMapper = field(default_factory=TrendDownstreamUtilityMapper)
    trace_builder: TrendTraceBuilder = field(default_factory=TrendTraceBuilder)

    def load(self, data: TrendAnalysisInput) -> TrendAnalysisResult:
        try:
            result = self._load(data)
        except Exception:  # noqa: BLE001
            result = self._fallback_result()
        return self._with_trend_trace(result)

    def _with_trend_trace(self, result: TrendAnalysisResult) -> TrendAnalysisResult:
        trend_trace = self.trace_builder.build(
            trend_profile=result.trend_profile,
            fallback=result.fallback,
            validation_summary=result.validation_summary,
            collector_trace=result.collector_trace,
        )
        result.collector_trace["trend_trace"] = trend_trace
        result.validation_summary["traceability"] = self.trace_builder.validation_summary(trend_trace=trend_trace)
        return result

    def _load(self, data: TrendAnalysisInput) -> TrendAnalysisResult:
        niche = (data.niche or "").strip().lower()
        if not niche:
            return self._fallback_result(reason="TREND_PROFILE_FALLBACK_EMPTY_NICHE", data=data)

        current_time = self._resolve_current_time(data.current_time)
        storage = self._resolve_storage_roots()
        collector_result = self._maybe_collect_creative_center(data)
        self._persist_collector_source_record(storage=storage, collector_result=collector_result, niche=niche)
        source_records, source_governance = self._load_source_records(
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
                source_governance=source_governance,
                primary_failure_reason="TREND_SOURCE_ASSEMBLY_REJECTED",
            )

        trend_path = self._resolve_trend_path(niche=niche, storage=storage)
        if trend_path is None:
            return self._fallback_result(reason="TREND_PROFILE_FALLBACK", data=data, current_time=current_time)

        payload = json.loads(trend_path.read_text(encoding="utf-8"))
        profile_governance = self._evaluate_profile_source(
            source_name=str(payload.get("trend_source") or "manual_file_legacy"),
            source_id=str(trend_path),
            source_class_hint="current_store",
            region=str(payload.get("region") or data.region or "US"),
            metadata={
                "path_kind": "current_store",
                "requested_region": data.region,
                "captured_at": str(payload.get("collected_at") or payload.get("updated_at") or ""),
                "valid_until": str(payload.get("valid_until") or ""),
                "supported_fields": self._supported_fields_from_payload(payload),
                "evidence_ids": self._payload_evidence_ids(payload),
            },
        )
        if not profile_governance.accepted_sources:
            return self._fallback_result(
                reason="TREND_PROFILE_FALLBACK",
                data=data,
                current_time=current_time,
                source_governance=profile_governance,
            )
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
            source_governance=profile_governance,
            primary_failure_reason="TREND_PROFILE_REJECTED",
        )

    def _fallback_result(
        self,
        *,
        reason: str = "TREND_PROFILE_FALLBACK",
        data: TrendAnalysisInput | None = None,
        current_time: datetime | None = None,
        source_governance: TrendSourceGovernanceResult | None = None,
    ) -> TrendAnalysisResult:
        resolved_time = current_time or self._resolve_current_time("" if data is None else data.current_time)
        region = "US" if data is None else str(data.region or "US")
        governance = source_governance or self._evaluate_safe_default_source(region=region)
        fallback_profile = TrendProfile(
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
        )
        provenance = self.provenance_builder.build(
            trend_profile=fallback_profile,
            source_governance=governance.to_dict(),
            fallback_used=True,
            fallback_reason=reason,
        )
        freshness_trace, validity = self._build_freshness_validity_trace(
            trend_profile=fallback_profile,
            source_governance=governance,
            current_time=resolved_time,
            fallback_used=True,
            fallback_reason=reason,
            cache_usage_mode="none",
            decision_trace=[],
        )
        confidence_calibration = self._build_confidence_calibration(
            trend_profile=fallback_profile,
            source_governance=governance,
            provenance=provenance.to_dict(),
            freshness=freshness_trace,
            validity=validity,
            fallback_used=True,
            fallback_reason=reason,
        )
        downstream_utility = self._build_downstream_utility(
            trend_profile=fallback_profile,
            provenance=provenance.to_dict(),
            confidence_calibration=confidence_calibration,
            validity=validity,
            fallback_used=True,
        )
        return TrendAnalysisResult(
            trend_profile=fallback_profile,
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
                "source_policy_respected": governance.policy_respected,
                "freshness_validity": self._freshness_validity_summary(validity),
                "confidence_calibration": confidence_calibration.to_dict(),
                "downstream_utility": self._downstream_utility_summary(downstream_utility),
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
                "source_governance": governance.to_dict(),
                "provenance": provenance.to_dict(),
                "freshness": freshness_trace,
                "validity": validity.to_dict(),
                "confidence_calibration": confidence_calibration.to_dict(),
                "downstream_utility": downstream_utility.to_dict(),
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
        source_governance: TrendSourceGovernanceResult,
        primary_failure_reason: str,
    ) -> TrendAnalysisResult:
        primary_validation = self.validation_service.validate(trend_profile=trend_profile, current_time=current_time)
        collector_trace["source_governance"] = source_governance.to_dict()
        collector_trace["provenance"] = self.provenance_builder.build(
            trend_profile=trend_profile,
            source_governance=source_governance.to_dict(),
            fallback_used=False,
            fallback_reason="",
        ).to_dict()
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
            freshness_trace, validity = self._build_freshness_validity_trace(
                trend_profile=trend_profile,
                source_governance=source_governance,
                current_time=current_time,
                fallback_used=False,
                fallback_reason="",
                cache_usage_mode=self._cache_usage_mode(
                    source_governance=source_governance,
                    fallback_used=False,
                ),
                decision_trace=list(collector_trace.get("decision_trace", [])),
            )
            collector_trace["freshness"] = freshness_trace
            collector_trace["validity"] = validity.to_dict()
            confidence_calibration = self._build_confidence_calibration(
                trend_profile=trend_profile,
                source_governance=source_governance,
                provenance=collector_trace["provenance"],
                freshness=freshness_trace,
                validity=validity,
                fallback_used=False,
                fallback_reason="",
            )
            collector_trace["confidence_calibration"] = confidence_calibration.to_dict()
            collector_trace["shift_analysis"] = self._detect_shift(
                storage=storage,
                trend_profile=trend_profile,
                current_time=current_time,
            )
            downstream_utility = self._build_downstream_utility(
                trend_profile=trend_profile,
                provenance=collector_trace["provenance"],
                confidence_calibration=confidence_calibration,
                validity=validity,
                fallback_used=False,
            )
            collector_trace["downstream_utility"] = downstream_utility.to_dict()
            self._persist_current_profile(storage=storage, trend_profile=trend_profile)
            self._persist_validated_cache(storage=storage, trend_profile=trend_profile)
            self._persist_snapshot(storage=storage, trend_profile=trend_profile, current_time=current_time)
            return TrendAnalysisResult(
                trend_profile=trend_profile,
                fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
                validation_summary={
                    **primary_validation.to_dict(),
                    "source_policy_respected": source_governance.policy_respected,
                    "freshness_validity": self._freshness_validity_summary(validity),
                    "confidence_calibration": confidence_calibration.to_dict(),
                    "downstream_utility": self._downstream_utility_summary(downstream_utility),
                },
                collector_trace=collector_trace,
            )

        if data.allow_cached:
            cached_result = self._load_validated_cache(storage=storage, niche=data.niche, current_time=current_time)
            if cached_result is not None:
                cached_profile, cached_validation, cached_governance = cached_result
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
                collector_trace["source_governance"] = cached_governance.to_dict()
                collector_trace["provenance"] = self.provenance_builder.build(
                    trend_profile=cached_profile,
                    source_governance=cached_governance.to_dict(),
                    fallback_used=True,
                    fallback_reason="TREND_CACHE_FALLBACK",
                ).to_dict()
                freshness_trace, validity = self._build_freshness_validity_trace(
                    trend_profile=cached_profile,
                    source_governance=cached_governance,
                    current_time=current_time,
                    fallback_used=True,
                    fallback_reason="TREND_CACHE_FALLBACK",
                    cache_usage_mode="fallback",
                    decision_trace=list(collector_trace.get("decision_trace", [])),
                )
                collector_trace["freshness"] = freshness_trace
                collector_trace["validity"] = validity.to_dict()
                confidence_calibration = self._build_confidence_calibration(
                    trend_profile=cached_profile,
                    source_governance=cached_governance,
                    provenance=collector_trace["provenance"],
                    freshness=freshness_trace,
                    validity=validity,
                    fallback_used=True,
                    fallback_reason="TREND_CACHE_FALLBACK",
                )
                collector_trace["confidence_calibration"] = confidence_calibration.to_dict()
                downstream_utility = self._build_downstream_utility(
                    trend_profile=cached_profile,
                    provenance=collector_trace["provenance"],
                    confidence_calibration=confidence_calibration,
                    validity=validity,
                    fallback_used=True,
                )
                collector_trace["downstream_utility"] = downstream_utility.to_dict()
                return TrendAnalysisResult(
                    trend_profile=cached_profile,
                    fallback=FallbackDecision(
                        used=True,
                        mode=FallbackMode.LOCAL_DEFAULT.value,
                        reason="TREND_CACHE_FALLBACK",
                    ),
                    validation_summary={
                        **cached_validation.to_dict(),
                        "source_policy_respected": cached_governance.policy_respected,
                        "freshness_validity": self._freshness_validity_summary(validity),
                        "confidence_calibration": confidence_calibration.to_dict(),
                        "downstream_utility": self._downstream_utility_summary(downstream_utility),
                    },
                    collector_trace=collector_trace,
                )

        history_result = self._load_history_fallback(storage=storage, niche=data.niche, current_time=current_time)
        if history_result is not None:
            history_profile, history_validation, history_governance = history_result
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
            collector_trace["source_governance"] = history_governance.to_dict()
            collector_trace["provenance"] = self.provenance_builder.build(
                trend_profile=history_profile,
                source_governance=history_governance.to_dict(),
                fallback_used=True,
                fallback_reason="TREND_HISTORY_FALLBACK",
            ).to_dict()
            freshness_trace, validity = self._build_freshness_validity_trace(
                trend_profile=history_profile,
                source_governance=history_governance,
                current_time=current_time,
                fallback_used=True,
                fallback_reason="TREND_HISTORY_FALLBACK",
                cache_usage_mode="none",
                decision_trace=list(collector_trace.get("decision_trace", [])),
            )
            collector_trace["freshness"] = freshness_trace
            collector_trace["validity"] = validity.to_dict()
            confidence_calibration = self._build_confidence_calibration(
                trend_profile=history_profile,
                source_governance=history_governance,
                provenance=collector_trace["provenance"],
                freshness=freshness_trace,
                validity=validity,
                fallback_used=True,
                fallback_reason="TREND_HISTORY_FALLBACK",
            )
            collector_trace["confidence_calibration"] = confidence_calibration.to_dict()
            downstream_utility = self._build_downstream_utility(
                trend_profile=history_profile,
                provenance=collector_trace["provenance"],
                confidence_calibration=confidence_calibration,
                validity=validity,
                fallback_used=True,
            )
            collector_trace["downstream_utility"] = downstream_utility.to_dict()
            return TrendAnalysisResult(
                trend_profile=history_profile,
                fallback=FallbackDecision(
                    used=True,
                    mode=FallbackMode.LOCAL_DEFAULT.value,
                    reason="TREND_HISTORY_FALLBACK",
                ),
                validation_summary={
                    **history_validation.to_dict(),
                    "source_policy_respected": history_governance.policy_respected,
                    "freshness_validity": self._freshness_validity_summary(validity),
                    "confidence_calibration": confidence_calibration.to_dict(),
                    "downstream_utility": self._downstream_utility_summary(downstream_utility),
                },
                collector_trace=collector_trace,
            )

        fallback = self._fallback_result(
            reason=primary_failure_reason,
            data=data,
            current_time=current_time,
            source_governance=source_governance,
        )
        fallback.collector_trace["decision_trace"] = list(collector_trace.get("decision_trace", []))
        fallback.collector_trace["fallback_path"] = "safe_default"
        return fallback

    def _build_freshness_validity_trace(
        self,
        *,
        trend_profile: TrendProfile,
        source_governance: TrendSourceGovernanceResult,
        current_time: datetime,
        fallback_used: bool,
        fallback_reason: str,
        cache_usage_mode: str,
        decision_trace: list[dict[str, Any]],
    ) -> tuple[dict[str, Any], TrendValiditySummary]:
        freshness_states, validity = self.freshness_evaluator.evaluate(
            trend_profile=trend_profile,
            source_governance=source_governance.to_dict(),
            current_time=current_time,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            cache_usage_mode=cache_usage_mode,
            decision_trace=decision_trace,
        )
        counts = {
            "fresh": 0,
            "aging": 0,
            "stale": 0,
            "expired": 0,
            "missing_timestamp": 0,
        }
        for state in freshness_states:
            counts[state.freshness_status] = counts.get(state.freshness_status, 0) + 1
        return {
            "sources": [state.to_dict() for state in freshness_states],
            "fresh_sources_count": counts["fresh"],
            "aging_sources_count": counts["aging"],
            "stale_sources_count": counts["stale"],
            "expired_sources_count": counts["expired"],
            "missing_timestamp_count": counts["missing_timestamp"],
        }, validity

    def _freshness_validity_summary(self, validity: TrendValiditySummary) -> dict[str, Any]:
        return {
            "validity_status": validity.validity_status,
            "profile_valid": validity.profile_valid,
            "cache_usage_mode": validity.cache_usage_mode,
            "fallback_due_to_freshness": validity.fallback_due_to_freshness,
        }

    def _build_confidence_calibration(
        self,
        *,
        trend_profile: TrendProfile,
        source_governance: TrendSourceGovernanceResult,
        provenance: dict[str, Any],
        freshness: dict[str, Any],
        validity: TrendValiditySummary,
        fallback_used: bool,
        fallback_reason: str,
    ) -> TrendConfidenceCalibration:
        return self.confidence_calibrator.calibrate(
            trend_profile=trend_profile,
            source_governance=source_governance.to_dict(),
            provenance=provenance,
            freshness=freshness,
            validity=validity.to_dict(),
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
        )

    def _build_downstream_utility(
        self,
        *,
        trend_profile: TrendProfile,
        provenance: dict[str, Any],
        confidence_calibration: TrendConfidenceCalibration,
        validity: TrendValiditySummary,
        fallback_used: bool,
    ) -> TrendDownstreamUtilitySummary:
        return self.downstream_utility_mapper.map(
            trend_profile=trend_profile,
            provenance=provenance,
            confidence_calibration=confidence_calibration.to_dict(),
            validity=validity.to_dict(),
            fallback_used=fallback_used,
        )

    def _downstream_utility_summary(self, downstream_utility: TrendDownstreamUtilitySummary) -> dict[str, Any]:
        return {
            "utility_complete": downstream_utility.utility_complete,
            "boundary_preserved": downstream_utility.boundary_statement
            == "Trend provides context only; Strategy remains the control layer.",
        }

    def _cache_usage_mode(
        self,
        *,
        source_governance: TrendSourceGovernanceResult,
        fallback_used: bool,
    ) -> str:
        if source_governance.selected_source_class == "validated_cache":
            return "fallback" if fallback_used else "primary"
        return "none"

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
    ) -> tuple[list[TrendSourceRecord], TrendSourceGovernanceResult]:
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
        usable_records = [item for item in records if self._source_record_is_usable(item=item, current_time=current_time)]
        governance = self.source_governance_evaluator.evaluate_candidates(
            candidates=[self._source_record_candidate(item) for item in usable_records],
            requested_region=region,
            selection_mode="mixed_allowed",
        )
        accepted_ids = {
            decision.source_id
            for decision in governance.accepted_sources
            if decision.governance_status in {"accepted", "fallback_allowed"}
        }
        accepted_records = [item for item in usable_records if self._source_record_id(item) in accepted_ids]
        accepted_records.sort(key=lambda item: (self._source_priority(item.source), item.source))
        return accepted_records, governance

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
            return self.shift_analyzer.analyze(
                current_profile=trend_profile,
                baseline_profile=None,
            ).to_dict()
        previous_profile, _ = baseline
        return self.shift_analyzer.analyze(
            current_profile=trend_profile,
            baseline_profile=previous_profile,
        ).to_dict()

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
    ) -> tuple[TrendProfile, TrendValidationResult, TrendSourceGovernanceResult] | None:
        validated_path = Path(storage["cache_dir"]) / "validated" / f"{niche}.json"
        return self._load_profile_candidate(
            path=validated_path,
            niche=niche,
            current_time=current_time,
            source_class_hint="validated_cache",
        )

    def _load_history_fallback(
        self,
        *,
        storage: dict[str, Path | str],
        niche: str,
        current_time: datetime,
    ) -> tuple[TrendProfile, TrendValidationResult, TrendSourceGovernanceResult] | None:
        history_dir = Path(storage["history_dir"]) / niche
        if not history_dir.exists():
            return None
        for path in sorted(history_dir.glob("*.json"), reverse=True):
            candidate = self._load_profile_candidate(
                path=path,
                niche=niche,
                current_time=current_time,
                source_class_hint="history_snapshot",
            )
            if candidate is None:
                continue
            _, validation, _ = candidate
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
            source_class_hint="current_store",
        )
        if current_candidate is not None:
            profile, validation, _ = current_candidate
            return profile, validation
        history_candidate = self._load_history_fallback(storage=storage, niche=niche, current_time=current_time)
        if history_candidate is None:
            return None
        profile, validation, _ = history_candidate
        return profile, validation

    def _load_profile_candidate(
        self,
        *,
        path: Path,
        niche: str,
        current_time: datetime,
        source_class_hint: str,
    ) -> tuple[TrendProfile, TrendValidationResult, TrendSourceGovernanceResult] | None:
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return None
        governance = self._evaluate_profile_source(
            source_name=str(payload.get("trend_source") or source_class_hint),
            source_id=str(path),
            source_class_hint=source_class_hint,
            region=str(payload.get("region") or "US"),
            metadata={
                "path_kind": source_class_hint,
                "captured_at": str(payload.get("collected_at") or payload.get("updated_at") or ""),
                "valid_until": str(payload.get("valid_until") or ""),
                "supported_fields": self._supported_fields_from_payload(payload),
                "evidence_ids": self._payload_evidence_ids(payload),
            },
        )
        if not governance.accepted_sources:
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
        return trend_profile, validation, governance

    def _source_record_candidate(self, item: TrendSourceRecord) -> dict[str, Any]:
        return {
            "source_id": self._source_record_id(item),
            "source_class": self.source_governance_evaluator.classify_source(source_name=item.source),
            "region": item.region,
            "metadata": {
                **dict(item.source_metadata),
                "captured_at": item.collected_at,
                "collected_at": item.collected_at,
                "valid_until": self._source_record_valid_until(item),
                "supported_fields": self._supported_fields_from_source_record(item),
                "evidence_ids": self._evidence_ids_from_source_record(item),
                "usable_reason": "ACCEPTED_USABLE_SOURCE_RECORD",
            },
        }

    def _source_record_id(self, item: TrendSourceRecord) -> str:
        return f"{item.source}:{item.niche}:{item.collected_at or 'undated'}"

    def _source_record_valid_until(self, item: TrendSourceRecord) -> str:
        if not str(item.collected_at or "").strip():
            return ""
        try:
            collected_at = self._resolve_current_time(item.collected_at)
        except ValueError:
            return ""
        return self._to_iso(collected_at + timedelta(days=self._source_window_days(item.source)))

    def _evaluate_profile_source(
        self,
        *,
        source_name: str,
        source_id: str,
        source_class_hint: str,
        region: str,
        metadata: dict[str, Any],
    ) -> TrendSourceGovernanceResult:
        return self.source_governance_evaluator.evaluate_candidates(
            candidates=[
                {
                    "source_id": source_id,
                    "source_class": self.source_governance_evaluator.classify_source(
                        source_name=source_name,
                        source_class_hint=source_class_hint,
                    ),
                    "region": region,
                    "metadata": metadata,
                }
            ],
            requested_region=region,
            selection_mode="single_preferred",
        )

    def _evaluate_safe_default_source(self, *, region: str) -> TrendSourceGovernanceResult:
        return self.source_governance_evaluator.evaluate_candidates(
            candidates=[
                {
                    "source_id": "safe_default",
                    "source_class": "safe_default",
                    "region": region,
                    "metadata": {
                        "fallback_only": True,
                        "captured_at": "",
                        "valid_until": "",
                        "supported_fields": [
                            "niche",
                            "region",
                            "dominant_hooks",
                            "avg_duration",
                            "pacing",
                            "visual_style",
                            "text_style",
                            "trend_source",
                            "confidence_scores",
                            "updated_at",
                            "valid_until",
                        ],
                        "evidence_ids": [],
                    },
                }
            ],
            requested_region=region,
            selection_mode="single_preferred",
        )

    def _supported_fields_from_source_record(self, item: TrendSourceRecord) -> list[str]:
        supported: list[str] = ["niche", "region", "sample_size", "evidence"]
        if item.dominant_hooks:
            supported.append("dominant_hooks")
        if str(item.avg_duration or "").strip():
            supported.append("avg_duration")
        if str(item.pacing or "").strip():
            supported.append("pacing")
        if str(item.visual_style or "").strip():
            supported.append("visual_style")
        if str(item.text_style or "").strip():
            supported.append("text_style")
        return sorted(set(supported))

    def _evidence_ids_from_source_record(self, item: TrendSourceRecord) -> list[str]:
        evidence_ids: list[str] = []
        for index, evidence in enumerate(item.evidence):
            evidence_ids.append(self._evidence_id_from_payload(evidence.to_dict(), index=index))
        return evidence_ids

    def _supported_fields_from_payload(self, payload: dict[str, Any]) -> list[str]:
        supported: list[str] = []
        for field_name in [
            "niche",
            "region",
            "dominant_hooks",
            "avg_duration",
            "pacing",
            "visual_style",
            "text_style",
            "trend_source",
            "confidence_scores",
            "updated_at",
            "valid_until",
            "sample_size",
            "evidence",
            "trend_version",
            "collector_version",
        ]:
            value = payload.get(field_name)
            if isinstance(value, str) and not value.strip():
                continue
            if isinstance(value, (list, dict)) and not value:
                continue
            if value is None:
                continue
            supported.append(field_name)
        return sorted(set(supported))

    def _payload_evidence_ids(self, payload: dict[str, Any]) -> list[str]:
        evidence_ids: list[str] = []
        for index, evidence in enumerate(list(payload.get("evidence") or [])):
            if not isinstance(evidence, dict):
                continue
            evidence_ids.append(self._evidence_id_from_payload(evidence, index=index))
        return evidence_ids

    def _evidence_id_from_payload(self, payload: dict[str, Any], *, index: int) -> str:
        reference_id = str(payload.get("reference_id") or "").strip()
        if reference_id:
            return reference_id
        source = str(payload.get("source") or "unknown")
        evidence_type = str(payload.get("evidence_type") or "unknown")
        captured_at = str(payload.get("captured_at") or "undated")
        return f"{source}:{evidence_type}:{captured_at}:{index}"

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
