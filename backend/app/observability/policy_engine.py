from __future__ import annotations

"""Shim de compatibilidade para o nucleo puro de decisao operacional."""

from app.decision_core.policy import POLICY_DECISION_VERSION, derive_operational_policy, derive_policy_bridge

__all__ = [
    "POLICY_DECISION_VERSION",
    "derive_operational_policy",
    "derive_policy_bridge",
]
