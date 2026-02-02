from app.agents.segmenter.service import SegmenterAgent


class SegmenterAdapter:
    def process(self, state: dict, payload: dict | None = None) -> dict:
        """
        Adapta o estado para o agente segmentador e atualiza o estado com os segmentos de áudio.
        Args:
            state (dict): O estado atual contendo informações necessárias para a segmentação.
        Returns:    
            dict: O estado atualizado com os segmentos de áudio.
        Raises:
            ValueError: Se campos obrigatórios estiverem ausentes ou se o agente retornar dados inválidos.
        """
        payload = payload or state.get("_action", {}).get("payload", {})
        audio_local_path = payload.get("audio_local_path")
        if not isinstance(audio_local_path, str) or not audio_local_path:
            raise ValueError("MissingField: payload.audio_local_path")

        segments = SegmenterAgent().process(audio_local_path)
        if not isinstance(segments, list):
            raise ValueError("InvalidAgentReturn: SegmenterAgent returned non-list")

        state["audio_local_path"] = audio_local_path
        state["segments"] = segments
        state.setdefault("artifacts", {})
        state["artifacts"]["segments_ready"] = True
        return state
