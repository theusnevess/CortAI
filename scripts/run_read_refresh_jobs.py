#!/usr/bin/env python
"""
Wrapper para executar o runner de jobs de refresh via raiz do repositorio.
"""

from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    backend_script = root / "backend" / "scripts" / "run_read_refresh_jobs.py"
    runpy.run_path(str(backend_script), run_name="__main__")


if __name__ == "__main__":
    main()
