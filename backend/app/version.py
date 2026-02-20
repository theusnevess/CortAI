"""
Fonte unica da versao operacional da API.

Qualquer endpoint que exponha versao (health/status/report) deve importar
este modulo para evitar drift entre respostas.
"""

from __future__ import annotations

import os


DEFAULT_APP_VERSION = "1.9.8"


def get_app_version() -> str:
    """
    Retorna versao da API com fallback deterministico.
    """
    return os.getenv("APP_VERSION", DEFAULT_APP_VERSION)
