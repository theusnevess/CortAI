from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_rollout_report(
    *,
    output_dir: Path,
    rollout_name: str,
    batch_summary: dict[str, Any],
    alerts: list[dict[str, Any]],
) -> tuple[Path, Path, Path, Path]:
    """Persiste artefatos mínimos do rollout real controlado."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report_json = output_dir / "pilot_rollout_report.json"
    report_md = output_dir / "pilot_rollout_report.md"
    summary_json = output_dir / "pilot_batch_window_summary.json"
    alerts_json = output_dir / "pilot_alerts.json"

    payload = {
        "rollout_name": rollout_name,
        "batch_summary": batch_summary,
        "alerts": alerts,
    }
    report_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    summary_json.write_text(json.dumps(batch_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    alerts_json.write_text(json.dumps(alerts, indent=2, ensure_ascii=False), encoding="utf-8")
    report_md.write_text(_to_markdown(rollout_name=rollout_name, batch_summary=batch_summary, alerts=alerts), encoding="utf-8")
    return report_json, report_md, summary_json, alerts_json


def _to_markdown(*, rollout_name: str, batch_summary: dict[str, Any], alerts: list[dict[str, Any]]) -> str:
    lines = [
        f"# {rollout_name}",
        "",
        "## Batch Summary",
        "",
    ]
    for key, value in batch_summary.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Alerts", ""])
    if not alerts:
        lines.append("- none")
    else:
        for alert in alerts:
            lines.append(f"- `{alert.get('severity', 'INFO')}` `{alert.get('code', 'ALERT')}`")
    return "\n".join(lines).rstrip() + "\n"
