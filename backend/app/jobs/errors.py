from __future__ import annotations


class WindowPostPipelineError(ValueError):
    """Erro base do wiring pos-janela."""


class WindowSnapshotMissingError(WindowPostPipelineError):
    """Snapshot obrigatorio ausente para execucao do D10 sob D12."""


class WindowLeaseExpiredError(WindowPostPipelineError):
    """Lease de janela expirou durante secao critica."""
