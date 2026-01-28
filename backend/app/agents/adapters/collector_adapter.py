from app.agents.collector.service import CollectorAgent


class CollectorAdapter:
    def process(self, state: dict, payload: dict) -> dict:
        """
        Processa o payload para coletar dados usando o CollectorAgent.
        Args:
            state (dict): O estado atual do processo.
            payload (dict): O payload contendo os dados necessários para a coleta.
        Returns:
            dict: O estado atualizado com os resultados da coleta.
        """
        if "url" not in payload:
            raise TypeError("MissingField: payload.url")
        result = CollectorAgent().process(payload["url"])
        state.setdefault("artifacts", {})
        state["artifacts"]["collector"] = result # Armazena o resultado da coleta no estado
        return state
