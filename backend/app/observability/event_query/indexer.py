from __future__ import annotations

from pathlib import Path


class EventIndexer:
    """Responsavel por localizar arquivos JSONL usados nas consultas D13."""

    def __init__(self, base_dir: Path = Path("OUT")) -> None:
        self.base_dir = base_dir

    def scan_sources(self) -> list[Path]:
        """Lista fontes candidatas de eventos sem carregar conteudo."""
        candidates = [
            self.base_dir / "events",
            self.base_dir / "data",
            self.base_dir / "audit",
        ]
        files: list[Path] = []
        for directory in candidates:
            if not directory.exists():
                continue
            files.extend(sorted(directory.glob("*.jsonl")))
        return files
