from app.agents.transcriber.service import TranscriberAgent


class TranscriberAdapter:
    def process(self, state: dict, payload: dict) -> dict:
        """
        Processa o payload para transcrever áudio usando o TranscriberAgent.
        Args:   
            state (dict): O estado atual do processo.
            payload (dict): O payload contendo os dados necessários para a transcrição.
        Returns:
            dict: O estado atualizado com os resultados da transcrição. 
        """
        if "audio_path" not in payload:
            raise TypeError("MissingField: payload.audio_path")
        segments = state.get("artifacts", {}).get("segments")
        if segments is None:
            raise TypeError("MissingField: state.artifacts.segments")
        transcriptions = TranscriberAgent().transcribe(payload["audio_path"], segments)
        state.setdefault("artifacts", {})
        state["artifacts"]["transcriptions"] = transcriptions
        return state
