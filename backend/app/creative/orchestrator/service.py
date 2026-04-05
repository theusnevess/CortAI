from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from app.content.pipeline.service import ContentPipelineService
from app.data.publish_records.store_jsonl import read_all_records as read_publish_records
from app.metrics.store_jsonl import read_all_records as read_metrics
from app.creative.agents.learning.models import LearningAgentInput
from app.creative.agents.learning.service import LearningAgentService
from app.creative.agents.novelty.models import NoveltyInput
from app.creative.agents.novelty.service import NoveltyEngineService
from app.creative.agents.asset_selection.models import AssetSelectionInput, AssetSelectionResult
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.agents.editor.models import EditorAgentInput
from app.creative.agents.editor.service import EditorAgentService
from app.creative.agents.account_health.models import AccountHealthInput
from app.creative.agents.account_health.service import AccountHealthAgentService
from app.creative.agents.strategy.models import StrategyInput
from app.creative.agents.strategy.service import StrategyAgentService
from app.creative.agents.trend_analysis.models import TrendAnalysisInput
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.script.models import ScriptAgentInput
from app.creative.agents.video_qc.models import VideoQcInput
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import CreativePack
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput, CreativeOrchestratorResult
from app.creative.experiments.models import ExperimentCapabilityInput
from app.creative.experiments.service import ExperimentCapabilityService
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.models import CreativePipelineExecution


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_creative_pack_id(*, account_id: str, niche: str, topic: str, publish_slot: str) -> str:
    material = f"{account_id.strip()}::{niche.strip()}::{topic.strip()}::{publish_slot.strip()}".encode("utf-8")
    return f"cp_{sha256(material).hexdigest()[:16]}"


@dataclass
class CreativeOrchestratorService:
    pipeline_service: ContentPipelineService = field(default_factory=ContentPipelineService)
    account_health_agent: AccountHealthAgentService = field(default_factory=AccountHealthAgentService)
    trend_analysis_agent: TrendAnalysisAgentService = field(default_factory=TrendAnalysisAgentService)
    learning_agent: LearningAgentService = field(default_factory=LearningAgentService)
    novelty_agent: NoveltyEngineService = field(default_factory=NoveltyEngineService)
    strategy_agent: StrategyAgentService = field(default_factory=StrategyAgentService)
    experiment_capability: ExperimentCapabilityService = field(default_factory=ExperimentCapabilityService)
    asset_selection_agent: AssetSelectionAgentService = field(default_factory=AssetSelectionAgentService)
    editor_agent: EditorAgentService = field(default_factory=EditorAgentService)
    script_agent: ScriptAgentService = field(default_factory=ScriptAgentService)
    voice_agent: VoiceAgentService = field(default_factory=VoiceAgentService)
    video_qc_agent: VideoQcAgentService = field(default_factory=VideoQcAgentService)
    event_emitter: CreativeEventEmitter = field(default_factory=CreativeEventEmitter)
    orchestrator_version: str = "phase2-block4"

    def build_creative_pack(self, data: CreativeOrchestratorInput) -> CreativeOrchestratorResult:
        account_health, trend_result, learning_result, novelty_result, strategy_result, experiment_result = self._resolve_account_context(data)
        if account_health.decision.status == "HOLD":
            raise AccountHealthHoldError("ACCOUNT_HEALTH_HOLD")

        return self._build_creative_pack_from_context(
            data=data,
            account_health=account_health,
            trend_result=trend_result,
            learning_result=learning_result,
            novelty_result=novelty_result,
            strategy_result=strategy_result,
            experiment_result=experiment_result,
        )

    def execute(self, data: CreativeOrchestratorInput) -> CreativePipelineExecution:
        try:
            account_health, trend_result, learning_result, novelty_result, strategy_result, experiment_result = self._resolve_account_context(data)
        except Exception:
            account_health = None
            trend_result = None
            learning_result = None
            novelty_result = None
            strategy_result = None
            experiment_result = None

        if account_health is not None and account_health.decision.status == "HOLD":
            self.event_emitter.emit(
                "CREATIVE/account_health_hold",
                {
                    "account_id": data.account_id,
                    "status": account_health.decision.status,
                    "reasons": list(account_health.decision.reasons),
                    "recommended_constraints": dict(account_health.decision.recommended_constraints),
                    "input_summary": dict(account_health.input_summary),
                    "decision_trace": dict(account_health.decision_trace),
                    "fallback_used": account_health.fallback.used,
                    "fallback_reason": account_health.fallback.reason,
                    "ts": _now_iso(),
                },
            )
            return CreativePipelineExecution(
                creative_pack=None,
                pipeline_output={"result": {"status": "HOLD", "render_job_id": None, "artifacts": {}}},
                video_qc=None,
                account_health=account_health,
                trend_analysis=trend_result,
                learning=learning_result,
                novelty=novelty_result,
                strategy=strategy_result,
                experiment=experiment_result,
                asset_selection=None,
            )

        result = self._build_creative_pack_from_context(
            data=data,
            account_health=account_health,
            trend_result=trend_result,
            learning_result=learning_result,
            novelty_result=novelty_result,
            strategy_result=strategy_result,
            experiment_result=experiment_result,
        )
        creative_pack = result.creative_pack
        pipeline_output = self.pipeline_service.run_pipeline(
            creative_pack_id=creative_pack.creative_pack_id,
            account_id=creative_pack.account_id,
            script_text=creative_pack.script_plan.narration_text(),
            asset_plan=creative_pack.asset_plan,
            edit_plan=creative_pack.edit_plan,
            voice_plan=creative_pack.voice_plan,
            voice_profile=creative_pack.voice_plan.voice_id,
            publish_slot=data.publish_slot,
            experiment_variant=creative_pack.experiment_plan.variant_id,
            defer_publish_manifest=True,
        )
        qc_result = self.video_qc_agent.evaluate(
            qc_input=VideoQcInput(
                render_job_id=str(pipeline_output["result"].get("render_job_id") or ""),
                video_path=str(pipeline_output["result"].get("artifacts", {}).get("video") or ""),
                audio_path=str(pipeline_output["result"].get("artifacts", {}).get("audio") or ""),
                metadata_path=str(
                    self._base_dir_from_artifacts(pipeline_output["result"].get("artifacts", {}))
                    / "metadata"
                    / f"{pipeline_output['result'].get('render_job_id')}.json"
                ),
                script_text=creative_pack.script_plan.narration_text(),
                tts_trace=dict(pipeline_output["result"].get("tts_trace") or {}),
                visual_trace=dict(pipeline_output["result"].get("visual_trace") or {}),
                edit_trace=dict(pipeline_output["result"].get("edit_trace") or {}),
            )
        )
        pipeline_output = self._apply_qc_governance(
            creative_pack=creative_pack,
            pipeline_output=pipeline_output,
            qc_result=qc_result,
            publish_slot=data.publish_slot,
        )
        experiment_result_payload, experiment_result_action = self.experiment_capability.record_runtime_result(
            result=experiment_result,
            window_id=str(data.publish_slot or pipeline_output["result"].get("render_job_id") or ""),
            metrics=self._build_experiment_result_metrics(
                pipeline_output=pipeline_output,
                qc_result=qc_result,
            ),
            recorded_at=_now_iso(),
        )
        if experiment_result_payload is not None:
            self.event_emitter.emit(
                "CREATIVE/experiment_result_recorded",
                {
                    "account_id": creative_pack.account_id,
                    "creative_pack_id": creative_pack.creative_pack_id,
                    "assignment_id": (
                        None
                        if experiment_result.experiment_assignment is None
                        else experiment_result.experiment_assignment.assignment_id
                    ),
                    "experiment_id": experiment_result_payload.get("experiment_id"),
                    "result_id": experiment_result_payload.get("result_id"),
                    "window_id": experiment_result_payload.get("window_id"),
                    "action": experiment_result_action,
                    "decision_trace": dict(experiment_result.decision_trace),
                    "experiment_trace": dict(experiment_result.experiment_trace),
                    "ts": _now_iso(),
                },
            )
        experiment_result = self._with_recorded_experiment_result(
            experiment_result=experiment_result,
            experiment_result_payload=experiment_result_payload,
            experiment_result_action=experiment_result_action,
            window_id=str(data.publish_slot or pipeline_output["result"].get("render_job_id") or ""),
        )
        qc_event = {
            "APPROVE": "CREATIVE/video_qc_approved",
            "HOLD": "CREATIVE/video_qc_hold",
            "REJECT": "CREATIVE/video_qc_rejected",
        }[qc_result.status]
        self.event_emitter.emit(
            qc_event,
            {
                "account_id": creative_pack.account_id,
                "creative_pack_id": creative_pack.creative_pack_id,
                "job_id": pipeline_output["result"].get("render_job_id"),
                "status": qc_result.status,
                "reasons": list(qc_result.reasons),
                "publishable": qc_result.publishable,
                "ts": _now_iso(),
            },
        )
        if qc_result.status == "APPROVE":
            self.novelty_agent.register_approved_execution(
                account_id=creative_pack.account_id,
                execution_payload={
                    "creative_pack": creative_pack.to_dict(),
                    "video_qc": qc_result.to_dict(),
                },
            )
        return CreativePipelineExecution(
            creative_pack=creative_pack,
            pipeline_output=pipeline_output,
            video_qc=qc_result,
            account_health=account_health,
            trend_analysis=trend_result,
            learning=learning_result,
            novelty=novelty_result,
            strategy=strategy_result,
            experiment=experiment_result,
            asset_selection=AssetSelectionResult(
                asset_selection=creative_pack.asset_plan,
                fallback=FallbackDecision(
                    used=any(item.startswith("asset_selection:") for item in result.fallbacks_used),
                    mode=FallbackMode.LOCAL_DEFAULT.value if any(item.startswith("asset_selection:") for item in result.fallbacks_used) else FallbackMode.NONE.value,
                    reason=next(
                        (item.split(":", 1)[1] for item in result.fallbacks_used if item.startswith("asset_selection:")),
                        "",
                    ),
                ),
            ),
        )

    def _build_experiment_result_metrics(
        self,
        *,
        pipeline_output: dict[str, object],
        qc_result,
    ) -> dict[str, Any]:
        decision = qc_result.decision
        score_summary = dict(decision.score_summary or {})
        product_signals = dict(decision.product_signals or {})
        details = dict(qc_result.details or {})
        return {
            "qc_status": qc_result.status,
            "publishable": qc_result.publishable,
            "overall_score": self._as_float(score_summary.get("overall_score")),
            "product_quality": self._as_float(score_summary.get("product_quality")),
            "hook_quality": self._as_float(product_signals.get("hook_quality")),
            "payoff_quality": self._as_float(product_signals.get("payoff_quality")),
            "render_status": str(pipeline_output["result"].get("status") or ""),
            "video_duration_s": self._as_float(details.get("render_duration_s")),
            "has_audio": bool(details.get("has_audio")),
        }

    def _with_recorded_experiment_result(
        self,
        *,
        experiment_result,
        experiment_result_payload: dict[str, Any] | None,
        experiment_result_action: str,
        window_id: str,
    ):
        trace = dict(experiment_result.experiment_trace or {})
        trace["result_recorded"] = experiment_result_payload is not None
        trace["result_action"] = experiment_result_action
        trace["result_window_id"] = window_id
        trace["result_id"] = None if experiment_result_payload is None else experiment_result_payload.get("result_id")
        trace["result_metrics_summary"] = (
            {}
            if experiment_result_payload is None
            else dict(experiment_result_payload.get("metrics") or {})
        )
        return type(experiment_result)(
            experiment_plan=experiment_result.experiment_plan,
            experiment_assignment=experiment_result.experiment_assignment,
            fallback=experiment_result.fallback,
            experiment_result=experiment_result_payload,
            decision_trace=dict(experiment_result.decision_trace or {}),
            experiment_trace=trace,
        )

    def _resolve_account_context(
        self,
        data: CreativeOrchestratorInput,
    ):
        account_health = self.account_health_agent.evaluate(self._build_account_health_input(data))
        trend_result = self.trend_analysis_agent.load(
            TrendAnalysisInput(
                niche=data.niche,
                account_id=data.account_id,
                region="US",
                force_refresh=data.force_refresh_trends,
            )
        )
        learning_result = self.learning_agent.generate(
            LearningAgentInput(
                account_id=data.account_id,
            )
        )
        novelty_result = self.novelty_agent.generate(
            NoveltyInput(account_id=data.account_id)
        )
        strategy_result = self.strategy_agent.generate(
            StrategyInput(
                account_id=data.account_id,
                account_goal="retention",
                recent_metrics_summary=dict(learning_result.learning_insights.signal_summary),
                health_status=account_health.decision.status,
                recommended_constraints=dict(account_health.decision.recommended_constraints),
                trend_profile=trend_result.trend_profile,
                novelty_pressure_profile=novelty_result.novelty_pressure_profile,
                learning_policy=learning_result.learning_policy,
                pattern_findings_summary=learning_result.pattern_findings_summary,
            )
        )
        experiment_result = self.experiment_capability.generate(
            ExperimentCapabilityInput(
                account_id=data.account_id,
                niche=data.niche,
                topic=data.topic,
                publish_slot=data.publish_slot,
                learning_insights=learning_result.learning_insights,
                account_health_status=account_health.decision.status,
                novelty_pressure_level=novelty_result.novelty_pressure_profile.pressure_level,
                recent_hold_or_reject_rate=self._as_float(
                    learning_result.learning_insights.signal_summary.get("recent_hold_or_reject_rate")
                ),
                recent_avg_overall_score=self._as_float(
                    learning_result.learning_insights.signal_summary.get("avg_overall_score")
                ),
            )
        )
        return account_health, trend_result, learning_result, novelty_result, strategy_result, experiment_result

    def _build_account_health_input(self, data: CreativeOrchestratorInput) -> AccountHealthInput:
        runtime_root = self._runtime_root()
        account_id = str(data.account_id or "")
        publish_rows = [
            row
            for row in read_publish_records(runtime_root / "data" / "publish_records" / "publish_records.jsonl")
            if str(row.get("account_id") or "") == account_id
        ]
        metric_rows = [
            row
            for row in read_metrics(runtime_root / "metrics" / "video_metrics.jsonl")
            if str(row.get("account_id") or "") == account_id
        ]
        execution_rows = self._read_execution_history(runtime_root=runtime_root, account_id=account_id)
        return AccountHealthInput(
            account_id=account_id,
            recent_publish_count=len(publish_rows[-10:]),
            recent_format_repetition_ratio=self._derive_format_repetition_ratio(execution_rows),
            recent_views_drop_ratio=self._derive_views_drop_ratio(metric_rows),
            recent_low_performance_streak=self._derive_low_performance_streak(execution_rows),
        )

    def _build_creative_pack_from_context(
        self,
        *,
        data: CreativeOrchestratorInput,
        account_health,
        trend_result,
        learning_result,
        novelty_result,
        strategy_result,
        experiment_result,
    ) -> CreativeOrchestratorResult:
        events: list[str] = []
        fallbacks: list[str] = []
        self._emit("CREATIVE/orchestrator_started", data=data.to_dict(), events=events)
        if account_health.fallback.used:
            fallbacks.append(f"account_health:{account_health.fallback.reason}")
        self._emit(
            f"CREATIVE/account_health_{account_health.decision.status.lower()}",
            data={
                "account_id": data.account_id,
                "status": account_health.decision.status,
                "reasons": list(account_health.decision.reasons),
                "recommended_constraints": dict(account_health.decision.recommended_constraints),
                "input_summary": dict(account_health.input_summary),
                "decision_trace": dict(account_health.decision_trace),
                "fallback_used": account_health.fallback.used,
                "fallback_reason": account_health.fallback.reason,
            },
            events=events,
        )
        if strategy_result.fallback.used:
            fallbacks.append(f"strategy:{strategy_result.fallback.reason}")
        if trend_result.fallback.used:
            fallbacks.append(f"trend:{trend_result.fallback.reason}")
            self._emit(
                "CREATIVE/trend_profile_fallback",
                data={
                    "account_id": data.account_id,
                    "niche": data.niche,
                    "fallback_used": True,
                    "fallback_reason": trend_result.fallback.reason,
                    "fallback_path": (trend_result.collector_trace or {}).get("fallback_path", "safe_default"),
                    "trend_source": trend_result.trend_profile.trend_source,
                    "source_mix": list((trend_result.collector_trace or {}).get("source_mix") or []),
                    "validation_status": (trend_result.validation_summary or {}).get("status", ""),
                    "overall_confidence": (trend_result.validation_summary or {}).get("overall_confidence"),
                    "freshness_state": (trend_result.validation_summary or {}).get("freshness_state", ""),
                    "pacing": trend_result.trend_profile.pacing,
                    "visual_style": trend_result.trend_profile.visual_style,
                },
                events=events,
            )
        else:
            self._emit(
                "CREATIVE/trend_profile_loaded",
                data={
                    "account_id": data.account_id,
                    "niche": trend_result.trend_profile.niche,
                    "visual_style": trend_result.trend_profile.visual_style,
                    "fallback_used": False,
                    "trend_source": trend_result.trend_profile.trend_source,
                    "source_mix": list((trend_result.collector_trace or {}).get("source_mix") or []),
                    "validation_status": (trend_result.validation_summary or {}).get("status", ""),
                    "overall_confidence": (trend_result.validation_summary or {}).get("overall_confidence"),
                    "freshness_state": (trend_result.validation_summary or {}).get("freshness_state", ""),
                    "pacing": trend_result.trend_profile.pacing,
                },
                events=events,
            )
        trend_refresh = None
        if trend_result.collector_trace:
            trend_refresh = trend_result.collector_trace.get("creative_center_refresh")
        if isinstance(trend_refresh, dict):
            self._emit(
                "CREATIVE/trend_collection_started",
                data={
                    "account_id": data.account_id,
                    "niche": data.niche,
                    "source": "creative_center",
                },
                events=events,
            )
            refresh_trace = dict(trend_refresh.get("trace") or {})
            refresh_status = str(refresh_trace.get("status") or "").upper()
            refresh_event = "CREATIVE/trend_collection_completed"
            if any(token in refresh_status for token in {"FAILED", "ERROR"}):
                refresh_event = "CREATIVE/trend_collection_failed"
            self._emit(
                refresh_event,
                data={
                    "account_id": data.account_id,
                    "niche": data.niche,
                    "source": refresh_trace.get("source", "creative_center"),
                    "collector_version": refresh_trace.get("collector_version", ""),
                    "status": refresh_trace.get("status", ""),
                    "region_requested": refresh_trace.get("region_requested", ""),
                    "region_effective": refresh_trace.get("region_effective", ""),
                    "region_filter_applied": refresh_trace.get("region_filter_applied"),
                    "hashtags_count": refresh_trace.get("hashtags_count", 0),
                    "songs_count": refresh_trace.get("songs_count", 0),
                    "error": refresh_trace.get("error", ""),
                },
                events=events,
            )
        shift_analysis = dict((trend_result.collector_trace or {}).get("shift_analysis") or {})
        if bool(shift_analysis.get("shift_detected")):
            self._emit(
                "CREATIVE/trend_shift_detected",
                data={
                    "account_id": data.account_id,
                    "niche": data.niche,
                    "trend_source": trend_result.trend_profile.trend_source,
                    "changes": list(shift_analysis.get("changes") or []),
                    "comparison_source": shift_analysis.get("comparison_source", ""),
                },
                events=events,
            )
        for decision_item in list((trend_result.collector_trace or {}).get("decision_trace") or []):
            if str(decision_item.get("candidate") or "") == "primary" and str(decision_item.get("decision") or "").upper() == "REJECT":
                self._emit(
                    "CREATIVE/trend_validation_rejected",
                    data={
                        "account_id": data.account_id,
                        "niche": data.niche,
                        "status": "REJECT",
                        "candidate": "primary",
                        "trend_source": str(decision_item.get("source") or ""),
                        "warnings": list(decision_item.get("warnings") or []),
                        "errors": list(decision_item.get("errors") or []),
                        "fallback_path": (trend_result.collector_trace or {}).get("fallback_path", ""),
                        "recovered_by_fallback": bool(trend_result.fallback.used),
                    },
                    events=events,
                )
        validation_status = str((trend_result.validation_summary or {}).get("status") or "").upper()
        if validation_status in {"APPROVE", "HOLD", "REJECT"}:
            validation_event = {
                "APPROVE": "CREATIVE/trend_validation_approved",
                "HOLD": "CREATIVE/trend_validation_hold",
                "REJECT": "CREATIVE/trend_validation_rejected",
            }[validation_status]
            self._emit(
                validation_event,
                data={
                    "account_id": data.account_id,
                    "niche": data.niche,
                    "status": validation_status,
                    "trend_source": trend_result.trend_profile.trend_source,
                    "source_mix": list((trend_result.collector_trace or {}).get("source_mix") or []),
                    "overall_confidence": trend_result.validation_summary.get("overall_confidence"),
                    "freshness_state": trend_result.validation_summary.get("freshness_state", ""),
                    "warnings": list(trend_result.validation_summary.get("warnings") or []),
                    "errors": list(trend_result.validation_summary.get("errors") or []),
                    "fallback_path": (trend_result.collector_trace or {}).get("fallback_path", ""),
                    "collector_version": trend_result.trend_profile.collector_version,
                    "trend_version": trend_result.trend_profile.trend_version,
                },
                events=events,
            )
        if learning_result.fallback.used:
            fallbacks.append(f"learning:{learning_result.fallback.reason}")
            self._emit(
                "CREATIVE/learning_insights_fallback",
                data={
                    "account_id": data.account_id,
                    "fallback_used": True,
                },
                events=events,
            )
        else:
            self._emit(
                "CREATIVE/learning_insights_generated",
                data={
                    "account_id": data.account_id,
                    "recommended_hook_type": learning_result.learning_insights.recommended_hook_type,
                    "target_duration_range": learning_result.learning_insights.target_duration_range,
                    "fallback_used": False,
                },
                events=events,
            )
        self._emit(
            "CREATIVE/strategy_profile_generated",
            data={
                "account_id": data.account_id,
                "goal": strategy_result.strategy_profile.goal,
                "content_mode": strategy_result.strategy_profile.content_mode,
                "hook_aggressiveness": strategy_result.strategy_profile.hook_aggressiveness,
                "target_duration_range": strategy_result.strategy_profile.target_duration_range,
                "variation_policy": strategy_result.strategy_profile.variation_policy,
                "health_status": account_health.decision.status,
                "fallback_used": strategy_result.fallback.used,
            },
            events=events,
        )
        if experiment_result.fallback.used:
            fallbacks.append(f"experiment:{experiment_result.fallback.reason}")
            self._emit(
                "CREATIVE/experiment_plan_fallback",
                data={
                    "account_id": data.account_id,
                    "fallback_used": True,
                    "decision_trace": dict(experiment_result.decision_trace),
                    "experiment_trace": dict(experiment_result.experiment_trace),
                },
                events=events,
            )
        else:
            self._emit(
                "CREATIVE/experiment_plan_generated",
                data={
                    "account_id": data.account_id,
                    "experiment_id": experiment_result.experiment_plan.experiment_id,
                    "variant_id": experiment_result.experiment_plan.variant_id,
                    "variant_type": experiment_result.experiment_plan.variant_type,
                    "fallback_used": False,
                    "decision_trace": dict(experiment_result.decision_trace),
                    "experiment_trace": dict(experiment_result.experiment_trace),
                },
                events=events,
            )
            if experiment_result.experiment_assignment is not None:
                self._emit(
                    "CREATIVE/experiment_assignment_recorded",
                    data={
                        "account_id": data.account_id,
                        "assignment_id": experiment_result.experiment_assignment.assignment_id,
                        "experiment_id": experiment_result.experiment_assignment.experiment_id,
                        "subject_key": experiment_result.experiment_assignment.subject_key,
                        "variant_id": experiment_result.experiment_assignment.variant_id,
                        "assigned_at": experiment_result.experiment_assignment.assigned_at,
                        "decision_trace": dict(experiment_result.decision_trace),
                    },
                    events=events,
                )
        script_result = self.script_agent.generate(
            ScriptAgentInput(
                account_id=data.account_id,
                niche=data.niche,
                topic=data.topic,
                account_health_status=account_health.decision.status,
                strategy_profile=strategy_result.strategy_profile,
                trend_profile=trend_result.trend_profile,
                learning_insights=learning_result.learning_insights,
                experiment_plan=experiment_result.experiment_plan,
            )
        )
        if script_result.fallback.used:
            fallbacks.append(f"script:{script_result.fallback.reason}")
        self._emit(
            "CREATIVE/script_generated",
            data={
                "account_id": data.account_id,
                "creative_pack_id": data.creative_pack_id or "",
                "generation_mode": script_result.script_plan.generation_mode,
                "fallback_used": script_result.fallback.used,
            },
            events=events,
        )

        voice_result = self.voice_agent.resolve(
            account_id=data.account_id,
            niche=data.niche,
            script_plan=script_result.script_plan,
            strategy_profile=strategy_result.strategy_profile,
        )
        if voice_result.fallback.used:
            fallbacks.append(f"voice:{voice_result.fallback.reason}")
        self._emit(
            "CREATIVE/voice_selected",
            data={
                "account_id": data.account_id,
                "provider": voice_result.voice_plan.provider,
                "voice_id": voice_result.voice_plan.voice_id,
                "style": voice_result.voice_plan.style,
                "fallback_used": voice_result.fallback.used,
            },
            events=events,
        )

        asset_selection_result = self.asset_selection_agent.select(
            AssetSelectionInput(
                niche=data.niche,
                topic=data.topic,
                strategy_profile=strategy_result.strategy_profile,
                trend_profile=trend_result.trend_profile,
                script_plan=script_result.script_plan,
            )
        )
        if asset_selection_result.fallback.used:
            fallbacks.append(f"asset_selection:{asset_selection_result.fallback.reason}")
            self._emit(
                "CREATIVE/asset_selection_fallback",
                data={
                    "account_id": data.account_id,
                    "niche": data.niche,
                    "fallback_used": True,
                },
                events=events,
            )
        self._emit(
            "CREATIVE/asset_selection_generated",
            data={
                "account_id": data.account_id,
                "hook_asset": asset_selection_result.asset_selection.hook_asset,
                "setup_asset": asset_selection_result.asset_selection.setup_asset,
                "payoff_asset": asset_selection_result.asset_selection.payoff_asset,
                "visual_style": asset_selection_result.asset_selection.visual_style,
                "visual_anchor": asset_selection_result.asset_selection.visual_anchor,
                "semantic_pattern": asset_selection_result.asset_selection.semantic_pattern,
                "fallback_used": asset_selection_result.fallback.used,
            },
            events=events,
        )

        aligned_asset_plan = self.asset_selection_agent.align_first_frame(
            niche=data.niche,
            topic=data.topic,
            hook_text=script_result.script_plan.hook,
            asset_plan=asset_selection_result.asset_selection,
        )
        if aligned_asset_plan.hook_asset != asset_selection_result.asset_selection.hook_asset:
            self._emit(
                "CREATIVE/hook_visual_alignment_applied",
                data={
                    "account_id": data.account_id,
                    "hook_asset_before": asset_selection_result.asset_selection.hook_asset,
                    "hook_asset_after": aligned_asset_plan.hook_asset,
                },
                events=events,
            )

        editor_result = self.editor_agent.plan(
            EditorAgentInput(
                account_id=data.account_id,
                niche=data.niche,
                topic=data.topic,
                script_plan=script_result.script_plan,
                voice_plan=voice_result.voice_plan,
                asset_plan=aligned_asset_plan,
                strategy_profile=strategy_result.strategy_profile,
                trend_profile=trend_result.trend_profile,
            )
        )
        if editor_result.fallback.used:
            fallbacks.append(f"editor:{editor_result.fallback.reason}")
        self._emit(
            "CREATIVE/editor_plan_generated",
            data={
                "account_id": data.account_id,
                "editor_version": editor_result.edit_plan.editor_version,
                "caption_style_id": editor_result.edit_plan.caption_plan.style_id,
                "music_track_type": editor_result.edit_plan.music_plan.track_type,
                "grade_preset": editor_result.edit_plan.color_plan.grade_preset,
                "fallback_used": editor_result.fallback.used,
            },
            events=events,
        )

        creative_pack = CreativePack(
            creative_pack_id=data.creative_pack_id or _build_creative_pack_id(
                account_id=data.account_id,
                niche=data.niche,
                topic=data.topic,
                publish_slot=data.publish_slot,
            ),
            account_id=data.account_id,
            niche=data.niche,
            topic=data.topic,
            strategy_profile=strategy_result.strategy_profile,
            trend_profile=trend_result.trend_profile,
            script_plan=script_result.script_plan,
            voice_plan=voice_result.voice_plan,
            asset_plan=aligned_asset_plan,
            edit_plan=editor_result.edit_plan,
            learning_insights=learning_result.learning_insights,
            learning_policy=learning_result.learning_policy,
            pattern_findings_summary=list(learning_result.pattern_findings_summary),
            experiment_plan=experiment_result.experiment_plan,
            experiment_assignment=None if experiment_result is None else experiment_result.experiment_assignment,
            account_health_status=account_health.decision.status,
            recommended_constraints=dict(account_health.decision.recommended_constraints),
            generated_at=_now_iso(),
            orchestrator_version=self.orchestrator_version,
        )
        self._emit(
            "CREATIVE/orchestrator_completed",
            data={
                "account_id": data.account_id,
                "creative_pack_id": creative_pack.creative_pack_id,
                "fallbacks_used": fallbacks,
            },
            events=events,
        )
        return CreativeOrchestratorResult(
            creative_pack=creative_pack,
            fallbacks_used=fallbacks,
            events_emitted=events,
            qc_required=True,
        )

    def _emit(self, event_type: str, *, data: dict[str, object], events: list[str]) -> None:
        events.append(event_type)
        payload = dict(data)
        payload.setdefault("ts", _now_iso())
        self.event_emitter.emit(event_type, payload)

    def _base_dir_from_artifacts(self, artifacts: object) -> Path:
        if not isinstance(artifacts, dict):
            return Path("OUT/content")
        video_path = artifacts.get("video")
        if not isinstance(video_path, str) or not video_path:
            return Path("OUT/content")
        video = Path(video_path)
        try:
            return video.parents[1]
        except IndexError:
            return Path("OUT/content")

    def _runtime_root(self) -> Path:
        event_path = Path(self.event_emitter.event_path)
        try:
            return event_path.parents[1]
        except IndexError:
            return Path("OUT")

    def _read_execution_history(self, *, runtime_root: Path, account_id: str) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        if not runtime_root.exists():
            return rows
        for path in sorted(runtime_root.rglob("execution_outputs.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            creative_pack = payload.get("creative_pack") if isinstance(payload, dict) else None
            if not isinstance(creative_pack, dict):
                continue
            if str(creative_pack.get("account_id") or "") != account_id:
                continue
            video_qc = payload.get("video_qc") if isinstance(payload.get("video_qc"), dict) else {}
            decision = video_qc.get("decision") if isinstance(video_qc.get("decision"), dict) else {}
            score_summary = decision.get("score_summary") if isinstance(decision.get("score_summary"), dict) else {}
            learning_insights = creative_pack.get("learning_insights") if isinstance(creative_pack.get("learning_insights"), dict) else {}
            signal_summary = learning_insights.get("signal_summary") if isinstance(learning_insights.get("signal_summary"), dict) else {}
            asset_plan = creative_pack.get("asset_plan") if isinstance(creative_pack.get("asset_plan"), dict) else {}
            payoff_asset = str(asset_plan.get("payoff_asset") or "")
            payoff_family = Path(payoff_asset).parent.name if payoff_asset else ""
            rows.append(
                {
                    "source_path": str(path),
                    "generated_at": str(creative_pack.get("generated_at") or ""),
                    "qc_status": str(video_qc.get("status") or decision.get("status") or ""),
                    "overall_score": self._as_float(score_summary.get("overall_score")),
                    "payoff_family": payoff_family,
                    "learning_recent_hold_or_reject_rate": self._as_float(signal_summary.get("recent_hold_or_reject_rate")),
                    "learning_avg_overall_score": self._as_float(signal_summary.get("avg_overall_score")),
                }
            )
        rows.sort(key=lambda item: str(item.get("generated_at") or item.get("source_path") or ""))
        return rows[-20:]

    def _derive_views_drop_ratio(self, metric_rows: list[dict[str, object]]) -> float:
        recent = metric_rows[-6:]
        if len(recent) < 4:
            return 0.0
        values = [self._as_float(row.get("views") or row.get("view_count")) for row in recent]
        midpoint = len(values) // 2
        previous = values[:midpoint]
        latest = values[midpoint:]
        previous_avg = sum(previous) / len(previous) if previous else 0.0
        latest_avg = sum(latest) / len(latest) if latest else 0.0
        if previous_avg <= 0 or latest_avg >= previous_avg:
            return 0.0
        return round((previous_avg - latest_avg) / previous_avg, 4)

    def _derive_low_performance_streak(self, execution_rows: list[dict[str, object]]) -> int:
        streak = 0
        for row in reversed(execution_rows[-8:]):
            qc_status = str(row.get("qc_status") or "").upper()
            overall_score = self._as_float(row.get("overall_score"))
            learning_bad_cluster = self._as_float(row.get("learning_recent_hold_or_reject_rate")) >= 0.4
            learning_low_score = 0.0 < self._as_float(row.get("learning_avg_overall_score")) < 0.78
            if qc_status in {"HOLD", "REJECT"} or (0.0 < overall_score < 0.82) or learning_bad_cluster or learning_low_score:
                streak += 1
                continue
            break
        return streak

    def _derive_format_repetition_ratio(self, execution_rows: list[dict[str, object]]) -> float:
        recent = execution_rows[-5:]
        if len(recent) < 3:
            return 0.0
        counts: dict[str, int] = {}
        for row in recent:
            family = str(row.get("payoff_family") or "")
            if not family:
                continue
            counts[family] = counts.get(family, 0) + 1
        if not counts:
            return 0.0
        dominant = max(counts.values())
        return round(dominant / len(recent), 4)

    def _as_float(self, value: object) -> float:
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def _apply_qc_governance(
        self,
        *,
        creative_pack: CreativePack,
        pipeline_output: dict[str, object],
        qc_result,
        publish_slot: str,
    ) -> dict[str, object]:
        render_job_id = str(pipeline_output["result"].get("render_job_id") or "")
        if qc_result.status == "APPROVE":
            finalized = self.pipeline_service.finalize_publish(
                creative_pack_id=creative_pack.creative_pack_id,
                account_id=creative_pack.account_id,
                render_job_id=render_job_id,
                publish_slot=publish_slot,
                experiment_variant=creative_pack.experiment_plan.variant_id,
            )
            finalized["result"]["tts_trace"] = pipeline_output["result"].get("tts_trace")
            finalized["result"]["visual_trace"] = pipeline_output["result"].get("visual_trace")
            finalized["result"]["edit_trace"] = pipeline_output["result"].get("edit_trace")
            return finalized

        non_publishable = self.pipeline_service.mark_non_publishable(
            render_job_id=render_job_id,
            decision=qc_result.status,
        )
        non_publishable["result"]["artifacts"] = dict(pipeline_output["result"].get("artifacts") or {})
        non_publishable["result"]["tts_trace"] = pipeline_output["result"].get("tts_trace")
        non_publishable["result"]["visual_trace"] = pipeline_output["result"].get("visual_trace")
        non_publishable["result"]["edit_trace"] = pipeline_output["result"].get("edit_trace")
        non_publishable["result"]["publish_manifest"] = None
        return non_publishable


class AccountHealthHoldError(RuntimeError):
    """Execution was intentionally stopped by account health policy."""
