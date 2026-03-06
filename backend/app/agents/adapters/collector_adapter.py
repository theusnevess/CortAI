from __future__ import annotations

import logging
import uuid
from time import perf_counter

from app.agents.collector.observability import (
    build_collector_run_facts,
    collector_observability_enabled,
    persist_collector_run_observation,
)
from app.agents.collector.service import CollectorAgent

logger = logging.getLogger(__name__)


class CollectorAdapter:
    def process(self, state: dict, payload: dict | None = None) -> dict:
        """
        Adapta o estado para o agente coletor e atualiza o estado com os dados do vídeo coletado.
        Args:   
            state (dict): O estado atual contendo informações necessárias para a coleta do vídeo.
        Returns:        
            dict: O estado atualizado com os dados do vídeo coletado.
        Raises: 
            ValueError: Se campos obrigatórios estiverem ausentes ou se o agente retornar dados inválidos.
        """
        payload = payload or state.get("_action", {}).get("payload", {})
        url = payload.get("url")
        if not isinstance(url, str) or not url:
            raise ValueError("MissingField: payload.url")

        started = perf_counter()
        result = CollectorAgent().process(url)
        duration_ms = int((perf_counter() - started) * 1000)
        if not isinstance(result, dict):
            raise ValueError("InvalidAgentReturn: CollectorAgent returned non-dict")

        self._emit_collector_run(state=state, source_ref=url, result=result, duration_ms=duration_ms)

        error = result.get("error")
        if isinstance(error, dict) and error.get("error_type"):
            error_type = error.get("error_type")
            message = error.get("message") or "Falha desconhecida no coletor"
            raise OSError(f"CollectorFailed:{error_type}:{message}")
        minio_path = result.get("minio_path")
        if not isinstance(minio_path, str) or not minio_path:
            raise OSError("CollectorFailed: minio_path inválido")

        state.setdefault("artifacts", {})
        state["artifacts"]["raw_video_minio_path"] = minio_path
        state["artifacts"]["raw_video_ready"] = True
        state["video"] = {
            "title": result.get("title"),
            "duration": result.get("duration"),
            "metadata": result.get("metadata"),
        }
        return state

    def _emit_collector_run(
        self,
        *,
        state: dict,
        source_ref: str,
        result: dict,
        duration_ms: int,
    ) -> None:
        """Emite observability leve para cada execucao do coletor."""
        if not collector_observability_enabled():
            return

        process_id = str(state.get("process_id") or state.get("job_id") or f"P_COLLECTOR_{uuid.uuid4()}")
        source_outcome_id = str(
            state.get("source_outcome_id")
            or state.get("job_id")
            or f"collector_run:{uuid.uuid4()}"
        )
        facts = build_collector_run_facts(
            source_ref=source_ref,
            result=result,
            duration_ms=duration_ms,
            job_id=state.get("job_id"),
        )

        logger.info(
            "collector_run status=%s error_type=%s http_status=%s retryable=%s duration_ms=%s source_type=%s process_id=%s job_id=%s",
            facts["status"],
            facts["error_type"],
            facts["http_status"],
            facts["retryable"],
            facts["duration_ms"],
            facts["source_type"],
            process_id,
            facts["job_id"],
        )

        try:
            persist_collector_run_observation(
                process_id=process_id,
                source_outcome_id=source_outcome_id,
                facts=facts,
            )
        except Exception as exc:
            logger.error("collector_run_emit_failed err=%s", exc)
