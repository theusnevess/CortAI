import importlib


class AgentRegistry:
    def __init__(self):
        """
        Inicializa o mapeamento de tipos de ação para seus respectivos adaptadores.
        """
        self._map = {
            "collect_video": "app.agents.adapters.collector_adapter:CollectorAdapter",
            "extract_audio": "app.agents.adapters.audio_extractor_adapter:AudioExtractorAdapter",
            "segment_audio": "app.agents.adapters.segment_adapter:SegmenterAdapter",
            "transcribe_segments": "app.agents.adapters.transcriber_adapter:TranscriberAdapter",
            "write_artifact": "app.agents.adapters.file_writer_adapter:FileWriterAgentAdapter",
            "publish_manifest": "app.agents.adapters.publisher_adapter:PublisherAdapter",
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
        module_path, class_name = self._map[action_type].split(":", 1)
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        return cls()
