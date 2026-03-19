from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from app.content.pipeline.service import ContentPipelineService
from app.creative.agents.learning.models import LearningAgentInput
from app.creative.agents.learning.service import LearningAgentService
from app.creative.agents.asset_selection.models import AssetSelectionInput
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.agents.account_health.models import AccountHealthInput
from app.creative.agents.account_health.service import AccountHealthAgentService
from app.creative.agents.strategy.models import StrategyInput
from app.creative.agents.strategy.service import StrategyAgentService
from app.creative.agents.trend_analysis.models import TrendAnalysisInput
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.script.models import ScriptAgentInput
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.contracts.creative_pack import CreativePack, ExperimentAssignment
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
    strategy_agent: StrategyAgentService = field(default_factory=StrategyAgentService)
    experiment_capability: ExperimentCapabilityService = field(default_factory=ExperimentCapabilityService)
    asset_selection_agent: AssetSelectionAgentService = field(default_factory=AssetSelectionAgentService)
    script_agent: ScriptAgentService = field(default_factory=ScriptAgentService)
    voice_agent: VoiceAgentService = field(default_factory=VoiceAgentService)
    video_qc_agent: VideoQcAgentService = field(default_factory=VideoQcAgentService)
    event_emitter: CreativeEventEmitter = field(default_factory=CreativeEventEmitter)
    orchestrator_version: str = "phase2-block4"

    def build_creative_pack(self, data: CreativeOrchestratorInput) -> CreativeOrchestratorResult:
        account_health, trend_result, learning_result, strategy_result, experiment_result, asset_selection_result = self._resolve_account_context(data)
        if account_health.decision.status == "HOLD":
            raise AccountHealthHoldError("ACCOUNT_HEALTH_HOLD")

        return self._build_creative_pack_from_context(
            data=data,
            account_health=account_health,
            trend_result=trend_result,
            learning_result=learning_result,
            strategy_result=strategy_result,
            experiment_result=experiment_result,
            asset_selection_result=asset_selection_result,
        )

    def execute(self, data: CreativeOrchestratorInput) -> CreativePipelineExecution:
        try:
            account_health, trend_result, learning_result, strategy_result, experiment_result, asset_selection_result = self._resolve_account_context(data)
        except Exception:
            account_health = None
            trend_result = None
            learning_result = None
            strategy_result = None
            experiment_result = None
            asset_selection_result = None

        if account_health is not None and account_health.decision.status == "HOLD":
            self.event_emitter.emit(
                "CREATIVE/account_health_hold",
                {
                    "account_id": data.account_id,
                    "status": account_health.decision.status,
                    "reasons": list(account_health.decision.reasons),
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
                strategy=strategy_result,
                experiment=experiment_result,
                asset_selection=asset_selection_result,
            )

        result = self._build_creative_pack_from_context(
            data=data,
            account_health=account_health,
            trend_result=trend_result,
            learning_result=learning_result,
            strategy_result=strategy_result,
            experiment_result=experiment_result,
            asset_selection_result=asset_selection_result,
        )
        creative_pack = result.creative_pack
        pipeline_output = self.pipeline_service.run_pipeline(
            creative_pack_id=creative_pack.creative_pack_id,
            account_id=creative_pack.account_id,
            script_text=creative_pack.script_plan.narration_text(),
            voice_plan=creative_pack.voice_plan,
            voice_profile=creative_pack.voice_plan.voice_id,
            publish_slot=data.publish_slot,
            experiment_variant=creative_pack.experiment_plan.variant_id,
        )
        qc_result = self.video_qc_agent.evaluate(
            render_job_id=str(pipeline_output["result"].get("render_job_id") or ""),
            artifacts=pipeline_output["result"].get("artifacts", {}),
            base_dir=self._base_dir_from_artifacts(pipeline_output["result"].get("artifacts", {})),
        )
        qc_event = "CREATIVE/video_qc_approved" if qc_result.status == "APPROVE" else "CREATIVE/video_qc_rejected"
        self.event_emitter.emit(
            qc_event,
            {
                "account_id": creative_pack.account_id,
                "creative_pack_id": creative_pack.creative_pack_id,
                "job_id": pipeline_output["result"].get("render_job_id"),
                "status": qc_result.status,
                "reasons": list(qc_result.reasons),
                "ts": _now_iso(),
            },
        )
        return CreativePipelineExecution(
            creative_pack=creative_pack,
            pipeline_output=pipeline_output,
            video_qc=qc_result,
            account_health=account_health,
            trend_analysis=trend_result,
            learning=learning_result,
            strategy=strategy_result,
            experiment=experiment_result,
            asset_selection=asset_selection_result,
        )

    def _resolve_account_context(
        self,
        data: CreativeOrchestratorInput,
    ):
        account_health = self.account_health_agent.evaluate(AccountHealthInput(account_id=data.account_id))
        trend_result = self.trend_analysis_agent.load(TrendAnalysisInput(niche=data.niche))
        learning_result = self.learning_agent.generate(
            LearningAgentInput(
                account_id=data.account_id,
            )
        )
        strategy_result = self.strategy_agent.generate(
            StrategyInput(
                account_id=data.account_id,
                account_goal="retention",
                recent_metrics_summary=dict(learning_result.learning_insights.signal_summary),
                health_status=account_health.decision.status,
                recommended_constraints=dict(account_health.decision.recommended_constraints),
            )
        )
        experiment_result = self.experiment_capability.generate(
            ExperimentCapabilityInput(
                account_id=data.account_id,
                niche=data.niche,
                topic=data.topic,
                publish_slot=data.publish_slot,
                learning_insights=learning_result.learning_insights,
            )
        )
        asset_selection_result = self.asset_selection_agent.select(
            AssetSelectionInput(
                niche=data.niche,
                topic=data.topic,
                strategy_profile=strategy_result.strategy_profile,
                trend_profile=trend_result.trend_profile,
            )
        )
        return account_health, trend_result, learning_result, strategy_result, experiment_result, asset_selection_result

    def _build_creative_pack_from_context(
        self,
        *,
        data: CreativeOrchestratorInput,
        account_health,
        trend_result,
        learning_result,
        strategy_result,
        experiment_result,
        asset_selection_result,
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
                },
                events=events,
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
                "fallback_used": asset_selection_result.fallback.used,
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
            learning_insights=learning_result.learning_insights,
            experiment_plan=experiment_result.experiment_plan,
            experiment_assignment=None if experiment_result is None else ExperimentAssignment(
                experiment_id=experiment_result.experiment_plan.experiment_id,
                variant_id=experiment_result.experiment_plan.variant_id,
            ),
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


class AccountHealthHoldError(RuntimeError):
    """Execution was intentionally stopped by account health policy."""
