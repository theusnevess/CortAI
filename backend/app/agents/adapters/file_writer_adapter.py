from app.agents.file_writer_agent import write_manifest


class FileWriterAgentAdapter:
    """Adapter do agente de escrita de artefato final (manifest)."""

    def process(self, state, payload=None):
        """
        Executa a escrita do manifest final e atualiza artifacts no estado.
        Args:
            state (dict): Estado atual do processo.
            payload (dict | None): Payload da acao.
        Returns:
            dict: Estado atualizado com manifest_path.
        """
        manifest_path = write_manifest(state if isinstance(state, dict) else {}, payload or {})
        if isinstance(state, dict):
            state.setdefault("artifacts", {})
            state["artifacts"]["write_artifact"] = True
            state["artifacts"]["manifest_path"] = str(manifest_path)
            return state
        return {}
