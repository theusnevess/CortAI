from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from app.content.pipeline.service import ContentPipelineService
from app.creative.agents.account_health.models import AccountHealthInput
from app.creative.agents.account_health.service import AccountHealthAgentService
from app.creative.agents.strategy.models import StrategyInput
from app.creative.agents.strategy.service import StrategyAgentService
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.contracts.creative_pack import AssetPlan, CreativePack, StrategyProfile, TrendProfile
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput, CreativeOrchestratorResult
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
    strategy_agent: StrategyAgentService = field(default_factory=StrategyAgentService)
    script_agent: ScriptAgentService = field(default_factory=ScriptAgentService)
    voice_agent: VoiceAgentService = field(default_factory=VoiceAgentService)
    video_qc_agent: VideoQcAgentService = field(default_factory=VideoQcAgentService)
    event_emitter: CreativeEventEmitter = field(default_factory=CreativeEventEmitter)
    orchestrator_version: str = "phase2-block2"

    def build_creative_pack(self, data: CreativeOrchestratorInput) -> CreativeOrchestratorResult:
        account_health, strategy_result = self._resolve_account_context(data)
        if account_health.decision.status == "HOLD":
            raise AccountHealthHoldError("ACCOUNT_HEALTH_HOLD")

        return self._build_creative_pack_from_context(
            data=data,
            account_health=account_health,
            strategy_result=strategy_result,
        )

    def execute(self, data: CreativeOrchestratorInput) -> CreativePipelineExecution:
        try:
            account_health, strategy_result = self._resolve_account_context(data)
        except Exception:
            account_health = None
            strategy_result = None

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
                strategy=strategy_result,
            )

        result = self._build_creative_pack_from_context(
            data=data,
            account_health=account_health,
            strategy_result=strategy_result,
        )
        creative_pack = result.creative_pack
        pipeline_output = self.pipeline_service.run_pipeline(
            creative_pack_id=creative_pack.creative_pack_id,
            account_id=creative_pack.account_id,
            script_text=creative_pack.script_plan.narration_text(),
            voice_profile=creative_pack.voice_plan.voice_id,
            publish_slot=data.publish_slot,
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
            strategy=strategy_result,
        )

    def _resolve_account_context(
        self,
        data: CreativeOrchestratorInput,
    ):
        account_health = self.account_health_agent.evaluate(AccountHealthInput(account_id=data.account_id))
        strategy_result = self.strategy_agent.generate(
            StrategyInput(
                account_id=data.account_id,
                account_goal="retention",
                recent_metrics_summary={},
                health_status=account_health.decision.status,
                recommended_constraints=dict(account_health.decision.recommended_constraints),
            )
        )
        return account_health, strategy_result

    def _build_creative_pack_from_context(
        self,
        *,
        data: CreativeOrchestratorInput,
        account_health,
        strategy_result,
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

        script_result = self.script_agent.generate(
            account_id=data.account_id,
            niche=data.niche,
            topic=data.topic,
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

        voice_result = self.voice_agent.resolve(account_id=data.account_id, niche=data.niche)
        if voice_result.fallback.used:
            fallbacks.append(f"voice:{voice_result.fallback.reason}")
        self._emit(
            "CREATIVE/voice_selected",
            data={
                "account_id": data.account_id,
                "provider": voice_result.voice_plan.provider,
                "voice_id": voice_result.voice_plan.voice_id,
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
            trend_profile=TrendProfile(),
            script_plan=script_result.script_plan,
            voice_plan=voice_result.voice_plan,
            asset_plan=AssetPlan(),
            experiment_assignment=None,
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
