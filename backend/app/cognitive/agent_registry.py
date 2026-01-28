class AgentRegistry:
    def __init__(self):
        """
        Inicializa o mapeamento de tipos de ação para seus respectivos adaptadores. 
        """
        self._map = {
            "collect_video": "app.agents.adapters.collector_adapter:CollectorAdapter",
            "segment_audio": "app.agents.adapters.segment_adapter:SegmenterAdapter",
            "transcribe_segments": "app.agents.adapters.transcriber_adapter:TranscriberAdapter",
            "write_artifact": "app.cognitive.adapters.file_writer_agent:FileWriterAgentAdapter",
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
        t = action["type"]
        if t not in self._map:
            raise ValueError(f"Unknown action type: {t}")
        module_path, class_name = self._map[t].split(":", 1)
        module = __import__(module_path, fromlist=[class_name])
        cls = getattr(module, class_name)
        return cls()
