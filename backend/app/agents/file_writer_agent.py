import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

AGENT_OUTPUT_DIR = Path("storage/agent_output")


def _pipeline_status_from_reason(termination_reason: str) -> str:
    """
    Normaliza o status do pipeline a partir da razao de termino.
    Args:
        termination_reason (str): Razao de termino do pipeline.
    Returns:
        str: Status canonico do pipeline.
    """
    if termination_reason == "video_failed":
        return "failed"
    if termination_reason == "pipeline_complete":
        return "completed"
    return "truncated"


def write_manifest(state: Dict[str, Any], payload: Dict[str, Any] | None = None) -> Path:
    """
    Gera um manifest deterministico do pipeline em formato JSON.
    O arquivo e idempotente por decision_id.
    Args:
        state (Dict[str, Any]): Estado atual do processo.
        payload (Dict[str, Any] | None): Payload da acao (pode conter decision_id e reason).
    Returns:
        Path: Caminho do manifest criado.
    """
    payload = payload or {}
    action_meta = state.get("_action", {}) if isinstance(state, dict) else {}
    decision_id = payload.get("decision_id") or action_meta.get("decision_id")
    process_id = payload.get("process_id") or action_meta.get("process_id") or state.get("process_id")
    termination_reason = payload.get("reason") or (state.get("artifacts") or {}).get("termination_reason")
    pipeline_status = _pipeline_status_from_reason(str(termination_reason or ""))

    artifacts = state.get("artifacts") or {}
    raw_video_path = artifacts.get("raw_video_minio_path")
    audio_local_path = artifacts.get("audio_local_path")
    segments = state.get("segments") if isinstance(state.get("segments"), list) else []
    transcriptions = (
        state.get("transcriptions") if isinstance(state.get("transcriptions"), list) else []
    )

    AGENT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not isinstance(decision_id, str) or not decision_id:
        raise ValueError("MissingField: decision_id")

    manifest_path = AGENT_OUTPUT_DIR / f"{decision_id}.json"
    manifest = {
        "process_id": process_id,
        "decision_id": decision_id,
        "pipeline_status": pipeline_status,
        "termination_reason": termination_reason,
        "segments_count": len(segments),
        "transcriptions_count": len(transcriptions),
        "artifact_paths": {
            "manifest_path": str(manifest_path),
        },
        "artifacts": {
            "raw_video_minio_path": raw_video_path,
            "audio_local_path": audio_local_path,
        },
        "created_at": datetime.utcnow().isoformat(),
    }
    # Idempotente por decision_id: sobrescreve o mesmo manifest de forma deterministica.
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=True)
    return manifest_path
