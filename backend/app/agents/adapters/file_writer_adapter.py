from app.agents.file_writer_agent import main as file_writer_execute

class FileWriterAgentAdapter:
    """
    Adapter para o FileWriterAgent. 
    Args:
        state (dict): O estado atual do processo.
        payload (dict, optional): O payload contendo os dados necessários para a escrita do artefato.
    Returns:
        dict: O estado atualizado indicando que o artefato foi escrito.
    """
    def process(self, state, payload=None):
        file_writer_execute()
        if isinstance(state, dict):
            state.setdefault("artifacts", {})
            state["artifacts"]["write_artifact"] = True
            return state
        return {}
