from app.agents.collector.service import CollectorAgent


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

        result = CollectorAgent().process(url)
        if not isinstance(result, dict):
            raise ValueError("InvalidAgentReturn: CollectorAgent returned non-dict")
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
