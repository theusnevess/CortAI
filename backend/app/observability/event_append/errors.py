from __future__ import annotations


class EventAppendError(RuntimeError):
    """Erro base para append centralizado de eventos."""


class EventAppendJsonlError(EventAppendError):
    """Falha dura ao persistir o evento na trilha canonica JSONL."""
