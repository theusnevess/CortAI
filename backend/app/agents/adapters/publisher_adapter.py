from app.artifacts import ArtifactInvalid, ArtifactNotFound
from app.agents.publisher.service import publish_manifest
from app.publish_receipts import upsert_publish_receipt


class PublisherAdapter:
    """
    Adapter do publicador manifest-only.
    """

    def process(self, state: dict, payload: dict | None = None) -> dict:
        """
        Publica artefato final usando somente decision_id -> manifest.
        Args:
            state (dict): Estado atual.
            payload (dict | None): Payload da acao (deve conter decision_id).
        Returns:
            dict: Estado atualizado com marca de publicacao.
        Raises:
            ValueError: Campos obrigatorios ausentes.
            ArtifactNotFound: Manifest nao encontrado (guardrail -> blocked no executor).
            ArtifactInvalid: Manifest invalido (guardrail -> failed no executor).
        """
        payload = payload or {}
        manifest_decision_id = payload.get("decision_id")
        publish_decision_id = ((state or {}).get("_action") or {}).get("decision_id")
        target = payload.get("target") or "unknown"

        if not isinstance(manifest_decision_id, str) or not manifest_decision_id:
            raise ValueError("MissingField: decision_id")
        if not isinstance(publish_decision_id, str) or not publish_decision_id:
            raise ValueError("MissingField: publish_decision_id")

        try:
            result = publish_manifest(manifest_decision_id)
            process_id = result.get("process_id") or (state or {}).get("process_id") or ""
            upsert_publish_receipt(
                publish_decision_id=publish_decision_id,
                process_id=process_id,
                manifest_decision_id=manifest_decision_id,
                execution_status="success",
                target=target,
                external_post_id=result.get("external_post_id"),
            )
        except ArtifactNotFound as e:
            upsert_publish_receipt(
                publish_decision_id=publish_decision_id,
                process_id=(state or {}).get("process_id") or "",
                manifest_decision_id=manifest_decision_id,
                execution_status="blocked",
                target=target,
                error_type="ArtifactNotFound",
                error_message=str(e),
            )
            raise
        except ArtifactInvalid as e:
            upsert_publish_receipt(
                publish_decision_id=publish_decision_id,
                process_id=(state or {}).get("process_id") or "",
                manifest_decision_id=manifest_decision_id,
                execution_status="failed",
                target=target,
                error_type="ArtifactInvalid",
                error_message=str(e),
            )
            raise

        if not isinstance(state, dict):
            state = {}
        state["process_id"] = result.get("process_id")
        state.setdefault("artifacts", {})
        state["artifacts"]["published"] = True  # Marcador final de publicacao.
        state["artifacts"]["published_decision_id"] = result.get("decision_id")
        state["artifacts"]["published_from_decision_id"] = manifest_decision_id
        state["artifacts"]["published_manifest_path"] = result.get("manifest_path")
        return state
