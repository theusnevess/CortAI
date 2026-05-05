from __future__ import annotations

__all__ = ["CreativeOrchestratorService"]


def __getattr__(name: str):
    if name == "CreativeOrchestratorService":
        from app.creative.orchestrator.service import CreativeOrchestratorService

        return CreativeOrchestratorService
    raise AttributeError(name)
