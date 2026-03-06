from __future__ import annotations

import json
from pathlib import Path

from app.ops.alerts.models import AlertRecord
from app.ops.slo.schema import SLOEvaluationResult


def persist_alert_bundle(
    *,
    alerts: list[AlertRecord],
    evaluation: SLOEvaluationResult,
    output_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Persiste alertas e status operacional derivados do D19."""
    base_dir = output_dir or Path("OUT/ops")
    base_dir.mkdir(parents=True, exist_ok=True)
    alerts_path = base_dir / "alerts.jsonl"
    status_path = base_dir / "slo_status.json"

    with alerts_path.open("w", encoding="utf-8") as writer:
        for alert in alerts:
            writer.write(json.dumps(alert.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")

    status_path.write_text(
        json.dumps(evaluation.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return alerts_path, status_path
