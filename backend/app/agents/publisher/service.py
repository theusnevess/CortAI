from app.artifacts import ArtifactInvalid, ArtifactNotFound, load_manifest


def publish_manifest(decision_id: str) -> dict:
    """
    Publica artefato final a partir do manifest canonico.
    Nao le JSONL e nao usa fallback.
    Args:
        decision_id (str): ID da decisao do write_artifact.
    Returns:
        dict: Dados objetivos de publicacao.
    Raises:
        ArtifactNotFound: Quando o manifest nao existe.
        ArtifactInvalid: Quando o manifest e invalido.
    """
    if not isinstance(decision_id, str) or not decision_id:
        raise ValueError("MissingField: decision_id")

    manifest = load_manifest(decision_id)
    return {
        "decision_id": manifest.decision_id,
        "process_id": manifest.process_id,
        "pipeline_status": manifest.pipeline_status,
        "termination_reason": manifest.termination_reason,
        "manifest_path": manifest.manifest_path,
        "artifacts": manifest.artifacts,
        "segments_count": manifest.segments_count,
        "transcriptions_count": manifest.transcriptions_count,
        "created_at": manifest.created_at,
    }
