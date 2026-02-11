import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_ARTIFACT_DIR = Path(os.getenv("ARTIFACT_OUTPUT_DIR", "storage/agent_output"))


class ArtifactNotFound(RuntimeError):
    pass


class ArtifactInvalid(RuntimeError):
    pass


@dataclass(frozen=True)
class ArtifactManifest:
    """
    Wrapper leve (sem heuristica). So garante acesso tipado e validacao.
    """

    process_id: str
    decision_id: str
    pipeline_status: str
    termination_reason: Optional[str]
    artifacts: Dict[str, Any]
    segments_count: int
    transcriptions_count: int
    artifact_paths: Dict[str, Any]
    created_at: str
    raw: Dict[str, Any]

    @property
    def manifest_path(self) -> Optional[str]:
        ap = self.raw.get("artifact_paths") or {}
        return ap.get("manifest_path")

    @property
    def raw_video_minio_path(self) -> Optional[str]:
        return (self.raw.get("artifacts") or {}).get("raw_video_minio_path")

    @property
    def audio_local_path(self) -> Optional[str]:
        return (self.raw.get("artifacts") or {}).get("audio_local_path")


def _require_str(obj: Dict[str, Any], key: str) -> str:
    v = obj.get(key)
    if not isinstance(v, str) or not v.strip():
        raise ArtifactInvalid(f"manifest invalido: campo '{key}' ausente ou nao-string")
    return v


def _require_int(obj: Dict[str, Any], key: str) -> int:
    v = obj.get(key)
    if isinstance(v, bool) or not isinstance(v, int):
        raise ArtifactInvalid(f"manifest invalido: campo '{key}' ausente ou nao-int")
    return v


def _require_dict(obj: Dict[str, Any], key: str) -> Dict[str, Any]:
    v = obj.get(key)
    if not isinstance(v, dict):
        raise ArtifactInvalid(f"manifest invalido: campo '{key}' ausente ou nao-dict")
    return v


def _validate_manifest_shape(m: Dict[str, Any]) -> None:
    _require_str(m, "process_id")
    _require_str(m, "decision_id")
    _require_str(m, "pipeline_status")

    tr = m.get("termination_reason")
    if tr is not None and (not isinstance(tr, str) or not tr.strip()):
        raise ArtifactInvalid("manifest invalido: termination_reason deve ser str ou null")

    _require_dict(m, "artifacts")
    _require_int(m, "segments_count")
    _require_int(m, "transcriptions_count")
    _require_dict(m, "artifact_paths")
    _require_str(m, "created_at")

    try:
        datetime.fromisoformat(m["created_at"].replace("Z", "+00:00"))
    except Exception as e:
        raise ArtifactInvalid("manifest invalido: created_at nao e ISO datetime") from e


def _manifest_path_for_decision(decision_id: str, artifact_dir: Path) -> Path:
    return artifact_dir / f"{decision_id}.json"


def _build_manifest(raw: Dict[str, Any]) -> ArtifactManifest:
    _validate_manifest_shape(raw)
    return ArtifactManifest(
        process_id=raw["process_id"],
        decision_id=raw["decision_id"],
        pipeline_status=raw["pipeline_status"],
        termination_reason=raw.get("termination_reason"),
        artifacts=raw.get("artifacts") or {},
        segments_count=raw["segments_count"],
        transcriptions_count=raw["transcriptions_count"],
        artifact_paths=raw.get("artifact_paths") or {},
        created_at=raw["created_at"],
        raw=raw,
    )


def load_manifest(decision_id: str, artifact_dir: Optional[Path] = None) -> ArtifactManifest:
    """
    Le o manifest canonico <decision_id>.json.
    - Sem heuristica
    - Valida schema fixo
    - Erra explicitamente se nao existir / invalido
    """
    if not isinstance(decision_id, str) or not decision_id.strip():
        raise ArtifactInvalid("decision_id invalido")

    base = artifact_dir or DEFAULT_ARTIFACT_DIR
    path = _manifest_path_for_decision(decision_id, base)

    if not path.exists():
        raise ArtifactNotFound(f"manifest nao encontrado: {path}")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise ArtifactInvalid(f"manifest invalido (json parse): {e}") from e

    if not isinstance(raw, dict):
        raise ArtifactInvalid("manifest invalido: raiz nao e dict")

    return _build_manifest(raw)


def load_manifest_by_path(
    manifest_path: str, artifact_dir: Optional[Path] = None
) -> ArtifactManifest:
    """
    Variante objetiva: carrega pelo path explicito (ex.: artifacts.manifest_path).
    Ainda valida schema e erra explicitamente.
    """
    if not isinstance(manifest_path, str) or not manifest_path.strip():
        raise ArtifactInvalid("manifest_path invalido")

    p = Path(manifest_path)
    if not p.is_absolute():
        base = artifact_dir or DEFAULT_ARTIFACT_DIR
        p = (base / p).resolve()

    if not p.exists():
        raise ArtifactNotFound(f"manifest nao encontrado: {p}")

    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise ArtifactInvalid(f"manifest invalido (json parse): {e}") from e

    if not isinstance(raw, dict):
        raise ArtifactInvalid("manifest invalido: raiz nao e dict")

    return _build_manifest(raw)
