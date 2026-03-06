from __future__ import annotations

import os
from pathlib import Path


def resolve_out_dir() -> Path:
    """Resolve o diretório base de artefatos operacionais."""
    raw = os.getenv("CORTAI_OUT_DIR") or os.getenv("OPS_DASHBOARD_BASE_DIR") or "OUT"
    return Path(raw)
