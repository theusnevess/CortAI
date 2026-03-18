from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.content.pipeline.models import ExecutionEnvelope, PipelineResult, RenderJob
from app.content.pipeline.orchestrator import ContentPipelineOrchestrator
from app.content.pipeline.publish import PublishAdapter, StubPublishAdapter
from app.content.pipeline.render import RenderAdapter, StubRenderAdapter
from app.content.pipeline.tts import StubTtsAdapter, TtsAdapter
from app.creative.contracts.creative_pack import VoicePlan
from app.observability.event_append.service import append_event, build_event_record


@dataclass
class InMemoryRenderJobRepository:
    jobs: dict[str, RenderJob] = field(default_factory=dict)

    def get_by_id(self, render_job_id: str) -> RenderJob | None:
        return self.jobs.get(render_job_id)

    def save(self, job: RenderJob) -> None:
        self.jobs[job.render_job_id] = job


@dataclass
class ContentPipelineService:
    repository: InMemoryRenderJobRepository = field(default_factory=InMemoryRenderJobRepository)
    tts_adapter: TtsAdapter = field(default_factory=StubTtsAdapter)
    render_adapter: RenderAdapter = field(default_factory=StubRenderAdapter)
    publish_adapter: PublishAdapter = field(default_factory=StubPublishAdapter)
    event_path: Path = Path("OUT/events/events.jsonl")

    def execute(
        self,
        envelope: ExecutionEnvelope,
        *,
        script_text: str,
        voice_plan: VoicePlan | None = None,
        voice_profile: str | None = None,
        language: str | None = None,
        template_id: str | None = None,
        aspect_ratio: str | None = None,
        caption: str = "",
        hashtags: list[str] | None = None,
    ) -> dict[str, object]:
        orchestrator = ContentPipelineOrchestrator(
            repository=self.repository,
            tts_adapter=self.tts_adapter,
            render_adapter=self.render_adapter,
            publish_adapter=self.publish_adapter,
            emit_event=self._emit_event,
        )
        job, result = orchestrator.execute(
            envelope=envelope,
            script_text=script_text,
            voice_plan=voice_plan,
            voice_profile=voice_profile,
            language=language,
            template_id=template_id,
            aspect_ratio=aspect_ratio,
            caption=caption,
            hashtags=hashtags,
        )
        return {
            "job": job.to_dict(),
            "result": result.to_dict(),
        }

    def run_pipeline(
        self,
        *,
        creative_pack_id: str,
        account_id: str,
        script_text: str,
        voice_plan: VoicePlan | None = None,
        voice_profile: str | None = None,
        language: str | None = None,
        template_id: str | None = None,
        aspect_ratio: str | None = None,
        publish_slot: str = "",
        experiment_variant: str | None = None,
        caption: str = "",
        hashtags: list[str] | None = None,
    ) -> dict[str, object]:
        envelope = ExecutionEnvelope(
            job_id="",
            account_id=account_id,
            creative_pack_id=creative_pack_id,
            publish_slot=publish_slot or "1970-01-01T00:00:00Z",
            experiment_variant=experiment_variant,
        )
        return self.execute(
            envelope,
            script_text=script_text,
            voice_plan=voice_plan,
            voice_profile=voice_profile,
            language=language,
            template_id=template_id,
            aspect_ratio=aspect_ratio,
            caption=caption,
            hashtags=hashtags,
        )

    def _emit_event(self, event_type: str, payload: dict[str, object]) -> None:
        event = build_event_record(event_type, dict(payload), writer_id="content_pipeline")
        append_event(event, path=self.event_path)
