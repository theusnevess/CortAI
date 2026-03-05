from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.guard.data_consistency.guard import run_data_consistency_guard
from app.guard.data_consistency.models import GuardResult


def run_window_guard_pipeline(
    *,
    account_id: str,
    window_id: str,
    deps: dict[str, Any],
    output_root: Path = Path("OUT/guards/data_consistency"),
) -> GuardResult:
    """Executa o guard de consistencia e persiste resultado auditavel."""
    result = run_data_consistency_guard(account_id, window_id, deps)

    account_dir = output_root / account_id
    account_dir.mkdir(parents=True, exist_ok=True)
    output_path = account_dir / f"{window_id}.json"
    output_path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result

