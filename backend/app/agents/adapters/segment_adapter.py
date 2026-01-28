from app.agents.segmenter.service import SegmenterAgent


class SegmenterAdapter:
    def process(self, state: dict, payload: dict) -> dict:
        """
        Processa o payload para segmentar áudio usando o SegmenterAgent.
        Args:       
            state (dict): O estado atual do processo.
            payload (dict): O payload contendo os dados necessários para a segmentação.         
        Returns:
            dict: O estado atualizado com os resultados da segmentação. 
        """
        if "audio_path" not in payload:
            raise TypeError("MissingField: payload.audio_path")
        segments = SegmenterAgent().process(payload["audio_path"])
        state.setdefault("artifacts", {})
        state["artifacts"]["segments"] = segments
        return state
