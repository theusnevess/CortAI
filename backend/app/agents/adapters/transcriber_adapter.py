from app.agents.transcriber.service import TranscriberAgent


class TranscriberAdapter:
    def process(self, state: dict, payload: dict | None = None) -> dict:
        """
        Adapta o estado para o agente transcritor e atualiza o estado com as transcrições.
        Args:
            state (dict): O estado atual contendo informações necessárias para a transcrição.
        Returns:
            dict: O estado atualizado com as transcrições.
        Raises: 
            ValueError: Se campos obrigatórios estiverem ausentes ou se o agente retornar dados inválidos.
        """
        payload = payload or state.get("_action", {}).get("payload", {})

        audio_local_path = payload.get("audio_local_path") or state.get("audio_local_path")
        if not isinstance(audio_local_path, str) or not audio_local_path:
            raise ValueError("MissingField: audio_local_path")

        segments = state.get("segments")
        if not isinstance(segments, list):
            segments = payload.get("segments")
        if not isinstance(segments, list):
            raise ValueError("MissingField: segments not found in state or payload")

        transcriptions = TranscriberAgent().transcribe(audio_local_path, segments)
        if not isinstance(transcriptions, list):
            raise ValueError("InvalidAgentReturn: TranscriberAgent returned non-list")

        state["transcriptions"] = transcriptions
        state.setdefault("artifacts", {})
        state["artifacts"]["transcriptions_ready"] = True
        return state

