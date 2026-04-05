from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
import os
import json
from pathlib import Path
from typing import Any, Callable, Protocol

from app.content.pipeline.hook_rewriter import rewrite_hook
from app.content.pipeline.models import ExecutionEnvelope, PipelineResult, RenderJob, RenderJobStatus
from app.content.pipeline.publish import PublishAdapter, PublishTransientError, StubPublishAdapter
from app.content.pipeline.render import RenderAdapter, RenderTransientError, StubRenderAdapter
from app.content.screen_text.service import ScreenTextAdapterService
from app.content.pipeline.tts import StubTtsAdapter, TtsAdapter, TtsTransientError
from app.content.pipeline.tts_router import TtsRouter
from app.creative.contracts.creative_pack import AssetPlan, VoicePlan
from app.creative.contracts.edit_plan import EditPlan
from app.runtime.asset_router import AssetRouter


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_render_job_id(*, creative_pack_id: str, account_id: str, publish_slot: str) -> str:
    """Gera chave deterministica do job de conteudo."""

    material = f"{creative_pack_id.strip()}::{account_id.strip()}::{publish_slot.strip()}".encode("utf-8")
    return f"rj_{sha256(material).hexdigest()[:16]}"


class RenderJobRepository(Protocol):
    def get_by_id(self, render_job_id: str) -> RenderJob | None:
        ...

    def save(self, job: RenderJob) -> None:
        ...


EventEmitter = Callable[[str, dict[str, Any]], None]


@dataclass(frozen=True)
class ContentPipelineOrchestrator:
    repository: RenderJobRepository
    tts_adapter: TtsAdapter | None = None
    render_adapter: RenderAdapter | None = None
    publish_adapter: PublishAdapter | None = None
    emit_event: EventEmitter | None = None
    max_attempts: int = 3

    def create_or_get_job(self, *, envelope: ExecutionEnvelope, now_iso: str | None = None) -> tuple[RenderJob, PipelineResult]:
        timestamp = now_iso or _now_iso()
        render_job_id = build_render_job_id(
            creative_pack_id=envelope.creative_pack_id,
            account_id=envelope.account_id,
            publish_slot=envelope.publish_slot,
        )
        existing = self.repository.get_by_id(render_job_id)
        if existing is not None:
            return existing, PipelineResult(
                status=RenderJobStatus.NOOP.value,
                publishable=existing.status == RenderJobStatus.READY,
                artifacts={
                    "audio": existing.audio_path or "",
                    "video": existing.video_path or "",
                },
                events_emitted=[],
                error_code=existing.error_code,
                render_job_id=existing.render_job_id,
            )

        job = RenderJob(
            render_job_id=render_job_id,
            creative_pack_id=envelope.creative_pack_id.strip(),
            account_id=envelope.account_id.strip(),
            status=RenderJobStatus.PENDING,
            attempt_count=0,
            created_at=timestamp,
            updated_at=timestamp,
            audio_path=None,
            video_path=None,
            error_code=None,
        )
        self.repository.save(job)
        return job, PipelineResult(status=job.status.value, publishable=False, render_job_id=job.render_job_id)

    def execute(
        self,
        *,
        envelope: ExecutionEnvelope,
        script_text: str,
        asset_plan: AssetPlan | None = None,
        edit_plan: EditPlan | None = None,
        voice_plan: VoicePlan | None = None,
        voice_profile: str | None = None,
        language: str | None = None,
        template_id: str | None = None,
        aspect_ratio: str | None = None,
        caption: str = "",
        hashtags: list[str] | None = None,
        now_iso: str | None = None,
        defer_publish_manifest: bool = False,
    ) -> tuple[RenderJob, PipelineResult]:
        job, initial_result = self.create_or_get_job(envelope=envelope, now_iso=now_iso)
        if initial_result.status == RenderJobStatus.NOOP.value:
            return job, initial_result

        events_emitted: list[str] = []
        tts_adapter = self.tts_adapter or StubTtsAdapter()
        render_adapter = self.render_adapter or StubRenderAdapter()
        publish_adapter = self.publish_adapter or StubPublishAdapter()
        tts_router = TtsRouter(tts_adapter=tts_adapter)
        asset_router = AssetRouter()
        screen_adapter = ScreenTextAdapterService()
        screen_blocks = screen_adapter.adapt(script_text)
        if os.getenv("CORTAI_EXPERIMENT_HOOK_REWRITE", "0") == "1":
            raw_blocks = screen_adapter._split_sentences(script_text)  # noqa: SLF001
            while len(raw_blocks) < 3:
                raw_blocks.append("")
            screen_blocks = screen_adapter.adapt_structured_blocks(
                hook=rewrite_hook(raw_blocks[0]),
                setup=raw_blocks[1],
                payoff=raw_blocks[2],
            )
        narration_text = screen_blocks.narration_text()
        resolved_voice_plan = voice_plan or self._legacy_voice_plan(voice_profile)
        resolved_asset_plan = asset_plan or self._legacy_asset_plan()
        resolved_asset_plan, visual_trace = asset_router.resolve_plan(
            asset_plan=resolved_asset_plan,
            render_job_id=job.render_job_id,
        )
        self._write_visual_trace(visual_trace=visual_trace)
        self._write_edit_trace(edit_trace={} if edit_plan is None else edit_plan.to_dict())

        try:
            job = self._update_job(job, status=RenderJobStatus.TTS_RUNNING)
            self._emit("CONTENT/tts_started", job, {"creative_pack_id": envelope.creative_pack_id}, events_emitted)
            tts_result, tts_attempts = self._retry(
                lambda attempt: tts_router.generate_audio(
                    script_text=narration_text,
                    voice_plan=resolved_voice_plan,
                    language=language,
                    render_job_id=job.render_job_id,
                    attempt_count=attempt,
                ),
                retry_on=TtsTransientError,
            )
            tts_output = tts_result.response
            tts_trace = tts_result.trace
            job = self._update_job(
                job,
                status=RenderJobStatus.TTS_DONE,
                audio_path=tts_output.audio_path,
                attempt_count=max(job.attempt_count, tts_attempts),
            )
            self._emit(
                "CONTENT/tts_completed",
                job,
                {
                    "audio_path": tts_output.audio_path,
                    "duration_s": tts_output.duration_s,
                    "provider_requested": tts_trace.provider_requested,
                    "provider_executed": tts_trace.provider_executed,
                    "voice_id_requested": tts_trace.voice_id_requested,
                    "voice_id_executed": tts_trace.voice_id_executed,
                    "style_requested": tts_trace.style_requested,
                    "fallback_used": tts_trace.fallback_used,
                    "fallback_reason": tts_trace.fallback_reason,
                    "tts_latency_s": tts_trace.latency_s,
                },
                events_emitted,
            )

            job = self._update_job(job, status=RenderJobStatus.RENDER_RUNNING)
            self._emit("CONTENT/render_started", job, {"audio_path": job.audio_path}, events_emitted)
            render_output, render_attempts = self._retry(
                lambda attempt: render_adapter.render_video(
                    audio_path=str(job.audio_path),
                    script_text=script_text,
                    asset_plan=resolved_asset_plan,
                    edit_plan=edit_plan,
                    screen_blocks=screen_blocks.as_list(),
                    segment_durations=tts_output.segment_durations,
                    render_job_id=job.render_job_id,
                    template_id=template_id,
                    aspect_ratio=aspect_ratio,
                    attempt_count=attempt,
                ),
                retry_on=RenderTransientError,
            )
            job = self._update_job(
                job,
                status=RenderJobStatus.RENDER_DONE,
                video_path=render_output.video_path,
                attempt_count=max(job.attempt_count, render_attempts),
            )
            self._emit("CONTENT/render_completed", job, {"video_path": render_output.video_path}, events_emitted)

            if defer_publish_manifest:
                return job, PipelineResult(
                    status=RenderJobStatus.RENDER_DONE.value,
                    publishable=False,
                    artifacts={
                        "audio": str(job.audio_path or ""),
                        "video": str(job.video_path or ""),
                    },
                    events_emitted=events_emitted,
                    error_code=None,
                    render_job_id=job.render_job_id,
                    tts_trace=tts_trace,
                    visual_trace=visual_trace,
                    edit_trace={} if edit_plan is None else edit_plan.to_dict(),
                )

            publish_output, publish_attempts = self._retry(
                lambda attempt: publish_adapter.create_manifest(
                    envelope=envelope,
                    video_path=str(job.video_path),
                    caption=caption,
                    hashtags=list(hashtags or []),
                    attempt_count=attempt,
                ),
                retry_on=PublishTransientError,
            )
            job = self._update_job(
                job,
                status=RenderJobStatus.READY,
                attempt_count=max(job.attempt_count, publish_attempts),
            )
            self._emit(
                "CONTENT/publish_manifest_created",
                job,
                {
                    "publish_id": publish_output.manifest.publish_id,
                    "scheduled_time": publish_output.manifest.scheduled_time,
                },
                events_emitted,
            )
            return job, PipelineResult(
                status=RenderJobStatus.READY.value,
                publishable=True,
                publish_manifest=publish_output.manifest,
                artifacts={
                    "audio": str(job.audio_path or ""),
                    "video": str(job.video_path or ""),
                },
                events_emitted=events_emitted,
                error_code=None,
                render_job_id=job.render_job_id,
                tts_trace=tts_trace,
                visual_trace=visual_trace,
                edit_trace={} if edit_plan is None else edit_plan.to_dict(),
            )
        except Exception as exc:  # noqa: BLE001
            error_code = str(exc) or exc.__class__.__name__
            job = self._update_job(job, status=RenderJobStatus.FAILED, error_code=error_code)
            self._emit("CONTENT/pipeline_failed", job, {"error_code": error_code}, events_emitted)
            return job, PipelineResult(
                status=RenderJobStatus.FAILED.value,
                publishable=False,
                artifacts={
                    "audio": str(job.audio_path or ""),
                    "video": str(job.video_path or ""),
                },
                events_emitted=events_emitted,
                error_code=error_code,
                render_job_id=job.render_job_id,
            )

    def finalize_publish(
        self,
        *,
        render_job_id: str,
        envelope: ExecutionEnvelope,
        caption: str = "",
        hashtags: list[str] | None = None,
    ) -> tuple[RenderJob, PipelineResult]:
        job = self.repository.get_by_id(render_job_id)
        if job is None:
            raise ValueError("RENDER_JOB_NOT_FOUND")
        if not job.video_path:
            raise ValueError("RENDER_VIDEO_MISSING")

        publish_adapter = self.publish_adapter or StubPublishAdapter()
        events_emitted: list[str] = []
        publish_output, publish_attempts = self._retry(
            lambda attempt: publish_adapter.create_manifest(
                envelope=envelope,
                video_path=str(job.video_path),
                caption=caption,
                hashtags=list(hashtags or []),
                attempt_count=attempt,
            ),
            retry_on=PublishTransientError,
        )
        job = self._update_job(job, status=RenderJobStatus.READY, attempt_count=max(job.attempt_count, publish_attempts))
        self._emit(
            "CONTENT/publish_manifest_created",
            job,
            {
                "publish_id": publish_output.manifest.publish_id,
                "scheduled_time": publish_output.manifest.scheduled_time,
            },
            events_emitted,
        )
        return job, PipelineResult(
            status=RenderJobStatus.READY.value,
            publishable=True,
            publish_manifest=publish_output.manifest,
            artifacts={
                "audio": str(job.audio_path or ""),
                "video": str(job.video_path or ""),
            },
            events_emitted=events_emitted,
            error_code=None,
            render_job_id=job.render_job_id,
        )

    def mark_governance_outcome(self, *, render_job_id: str, decision: str) -> tuple[RenderJob, PipelineResult]:
        job = self.repository.get_by_id(render_job_id)
        if job is None:
            raise ValueError("RENDER_JOB_NOT_FOUND")
        status = RenderJobStatus.HOLD if decision == "HOLD" else RenderJobStatus.REJECT
        job = self._update_job(job, status=status)
        return job, PipelineResult(
            status=decision,
            publishable=False,
            artifacts={
                "audio": str(job.audio_path or ""),
                "video": str(job.video_path or ""),
            },
            events_emitted=[],
            error_code=None,
            render_job_id=job.render_job_id,
        )

    def _retry(self, func: Callable[[int], Any], *, retry_on: type[Exception]) -> tuple[Any, int]:
        last_exc: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return func(attempt), attempt
            except retry_on as exc:
                last_exc = exc
                if attempt >= self.max_attempts:
                    raise
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("UNREACHABLE_RETRY_STATE")

    def _update_job(self, job: RenderJob, **changes: Any) -> RenderJob:
        updated = replace(job, updated_at=_now_iso(), **changes)
        self.repository.save(updated)
        return updated

    def _emit(self, event_type: str, job: RenderJob, details: dict[str, Any], events_emitted: list[str]) -> None:
        events_emitted.append(event_type)
        if self.emit_event is None:
            return
        payload = {
            "render_job_id": job.render_job_id,
            "creative_pack_id": job.creative_pack_id,
            "account_id": job.account_id,
            "status": job.status.value,
            "attempt_count": job.attempt_count,
            "job_id": job.render_job_id,
            "ts": _now_iso(),
            **details,
        }
        self.emit_event(event_type, payload)

    def _legacy_voice_plan(self, voice_profile: str | None) -> VoicePlan:
        mode = os.getenv("CORTAI_TTS_MODE", "piper").lower()
        provider = mode if mode in {"piper", "openai", "edge", "pyttsx3"} else "piper"
        resolved_voice = voice_profile or os.getenv("CORTAI_PIPER_MODEL", "")
        return VoicePlan(provider=provider, voice_id=resolved_voice, style="legacy_voice_profile")

    def _legacy_asset_plan(self) -> AssetPlan:
        return AssetPlan(
            hook_asset="",
            setup_asset="",
            payoff_asset="",
            visual_style="phase1_baseline",
            motion_profile="phase1_baseline",
        )

    def _write_visual_trace(self, *, visual_trace: dict[str, Any]) -> None:
        target = Path("OUT/audit/asset_agent_runtime/visual_trace.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(visual_trace, indent=2), encoding="utf-8")

    def _write_edit_trace(self, *, edit_trace: dict[str, Any]) -> None:
        target = Path("OUT/audit/editor_agent_runtime/edit_trace.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(edit_trace, indent=2), encoding="utf-8")
