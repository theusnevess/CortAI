# backend/app/cognitive/agent_registry.py

from app.agents.adapters.collector_adapter import CollectorAdapter
from app.agents.adapters.segment_adapter import SegmenterAdapter
from app.agents.adapters.transcriber_adapter import TranscriberAdapter
from app.agents.adapters.file_writer_adapter import FileWriterAgentAdapter
from app.agents.adapters.audio_extractor_adapter import AudioExtractorAdapter


class AgentRegistry:
    def __init__(self):
        """
        Inicializa o mapeamento de tipos de ação para seus respectivos adaptadores.
        """
        self._map = {
            "collect_video": CollectorAdapter,
            "segment_audio": SegmenterAdapter,
            "transcribe_segments": TranscriberAdapter,
            "write_artifact": FileWriterAgentAdapter,
            "extract_audio": AudioExtractorAdapter,
        }

    def resolve(self, action):
        """
        Resolve o adaptador apropriado com base no tipo de ação.
        Args:
            action (dict): A ação contendo o campo "type".
        Returns:
            object: Uma instância do adaptador correspondente.
        Raises:
            ValueError: Se o tipo de ação for desconhecido. 
        """
        action_type = action.get("type")
        if action_type not in self._map:
            raise ValueError(f"Unknown action type: {action_type}")
        return self._map[action_type]()

