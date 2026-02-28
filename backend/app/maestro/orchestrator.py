from __future__ import annotations

import inspect
import logging
import uuid
from datetime import datetime
from time import perf_counter
from typing import Any

from app.agents.adapters.audio_extractor_adapter import AudioExtractorAdapter
from app.agents.adapters.collector_adapter import CollectorAdapter
from app.agents.adapters.segment_adapter import SegmenterAdapter
from app.agents.adapters.transcriber_adapter import TranscriberAdapter
from app.maestro.models import MaestroJob, MaestroRunResult

logger = logging.getLogger(__name__)


class MaestroOrchestrator:
    """
    Orquestrador linear mínimo para validar o pipeline de agentes de ponta a ponta.

    Contrato v0.3:
    - collector deve entregar a mídia de origem para o pipeline.
    - audio_extractor suporta dois modos:
      - `raw_video_minio_path`: extrai áudio e produz `audio_local_path` +
        `audio_minio_path`
      - `audio_minio_path`: materializa `audio_local_path` sem reextrair
    - segmenter/transcriber continuam consumindo `audio_local_path`.
    - se esse contrato não for atendido, o job falha de forma explícita.
    """

    def __init__(
        self,
        collector: Any | None = None,
        audio_extractor: Any | None = None,
        segmenter: Any | None = None,
        transcriber: Any | None = None,
    ) -> None:
        """Inicializa o orquestrador com agentes injetáveis para runtime e testes."""

        self.collector = collector or CollectorAdapter()
        self.audio_extractor = audio_extractor or AudioExtractorAdapter()
        self.segmenter = segmenter or SegmenterAdapter()
        self.transcriber = transcriber or TranscriberAdapter()

    async def run(self, job_input: dict[str, Any]) -> MaestroRunResult:
        """Executa o fluxo collector -> audio_extractor -> segmenter -> transcriber."""

        input_ref = str(job_input.get("input_ref") or job_input.get("url") or "").strip()
        if not input_ref:
            raise ValueError("MissingField: job_input.input_ref")
        requested_job_id = str(job_input.get("job_id") or "").strip() or None

        job = MaestroJob(
            id=requested_job_id or str(uuid.uuid4()),
            input_ref=input_ref,
            status="running",
            started_at=datetime.utcnow(),
        )
        state: dict[str, Any] = {
            "job_id": job.id,
            "input_ref": input_ref,
            "artifacts": {},
        }
        started = perf_counter()

        try:
            await self._run_step(
                job=job,
                state=state,
                step="collector",
                agent=self.collector,
                payload={"url": input_ref},
            )

            audio_local_path = state.get("audio_local_path") or job_input.get("audio_local_path")
            audio_minio_path = state.get("audio_minio_path") or job_input.get("audio_minio_path")

            if not isinstance(audio_local_path, str) or not audio_local_path:
                if isinstance(audio_minio_path, str) and audio_minio_path:
                    await self._run_step(
                        job=job,
                        state=state,
                        step="audio_extractor",
                        agent=self.audio_extractor,
                        payload={"audio_minio_path": audio_minio_path},
                    )
                else:
                    raw_video_minio_path = (
                        state.get("raw_video_minio_path")
                        or state.get("artifacts", {}).get("raw_video_minio_path")
                    )
                    if not isinstance(raw_video_minio_path, str) or not raw_video_minio_path:
                        raise ValueError(
                            "ContractViolation: collector must provide raw_video_minio_path or "
                            "audio_minio_path to derive audio_local_path"
                        )
                    await self._run_step(
                        job=job,
                        state=state,
                        step="audio_extractor",
                        agent=self.audio_extractor,
                        payload={"raw_video_minio_path": raw_video_minio_path},
                    )

                audio_local_path = state.get("audio_local_path")
                audio_minio_path = state.get("audio_minio_path") or audio_minio_path

            if not isinstance(audio_local_path, str) or not audio_local_path:
                raise ValueError(
                    "ContractViolation: audio_extractor must provide audio_local_path"
                )

            state["audio_local_path"] = audio_local_path
            if isinstance(audio_minio_path, str) and audio_minio_path:
                state["audio_minio_path"] = audio_minio_path
            state.setdefault("artifacts", {})
            state["artifacts"]["audio_local_path"] = audio_local_path
            if isinstance(audio_minio_path, str) and audio_minio_path:
                state["artifacts"]["audio_minio_path"] = audio_minio_path

            await self._run_step(
                job=job,
                state=state,
                step="segmenter",
                agent=self.segmenter,
                payload={"audio_local_path": audio_local_path},
            )
            await self._run_step(
                job=job,
                state=state,
                step="transcriber",
                agent=self.transcriber,
                payload={
                    "audio_local_path": audio_local_path,
                    "segments": state.get("segments"),
                },
            )

            job.status = "done"
            job.step = None
            return MaestroRunResult(job=job, state=state)
        except Exception as exc:
            job.status = "failed"
            job.error = str(exc)
            logger.exception(
                "maestro_job_failed",
                extra={"job_id": job.id, "step": job.step, "input_ref": job.input_ref},
            )
            return MaestroRunResult(job=job, state=state)
        finally:
            job.finished_at = datetime.utcnow()
            job.duration_ms = int((perf_counter() - started) * 1000)
            logger.info(
                "maestro_job_finished",
                extra={
                    "job_id": job.id,
                    "status": job.status,
                    "duration_ms": job.duration_ms,
                    "input_ref": job.input_ref,
                },
            )

    async def _run_step(
        self,
        *,
        job: MaestroJob,
        state: dict[str, Any],
        step: str,
        agent: Any,
        payload: dict[str, Any],
    ) -> None:
        """Executa uma etapa e mescla o retorno no estado compartilhado do job."""

        job.step = step
        logger.info(
            "maestro_step_started",
            extra={"job_id": job.id, "step": step, "input_ref": job.input_ref},
        )
        started = perf_counter()
        result = agent.process(state, payload=payload)
        if inspect.isawaitable(result):
            result = await result
        if not isinstance(result, dict):
            raise ValueError(f"InvalidAgentReturn: {step} returned non-dict")
        # Cada etapa assume o contrato completo do estado para a etapa seguinte.
        state.clear()
        state.update(result)
        state["job_id"] = job.id
        state["input_ref"] = job.input_ref
        job.step_durations_ms[step] = int((perf_counter() - started) * 1000)
        logger.info(
            "maestro_step_finished",
            extra={
                "job_id": job.id,
                "step": step,
                "duration_ms": job.step_durations_ms[step],
            },
        )
