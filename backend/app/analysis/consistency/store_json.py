from __future__ import annotations

import json
import tempfile
from pathlib import Path

from app.analysis.consistency.models import ConsistencySummary

DEFAULT_JSON_PATH = Path("OUT/analysis/consistency_check.json")
DEFAULT_MD_PATH = Path("OUT/analysis/consistency_check.md")


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", dir=str(path.parent)) as handle:
        handle.write(content)
        temp_name = handle.name
    Path(temp_name).replace(path)


def save_consistency_json(summary: ConsistencySummary, path: Path = DEFAULT_JSON_PATH) -> None:
    payload = json.dumps(summary.to_dict(), ensure_ascii=False, indent=2)
    _atomic_write(path, payload + "\n")


def render_consistency_markdown(summary: ConsistencySummary) -> str:
    lines = [
        "# Consistency Check",
        "",
        "## Status",
        "",
        f"- Overall: `{summary.status}`",
        f"- Generated at: `{summary.generated_at}`",
        "",
        "## Summary Counts",
        "",
        f"- Checks run: `{summary.checks_run}`",
        f"- Checks failed: `{summary.checks_failed}`",
        "",
        "## Checks",
        "",
    ]
    for item in summary.checks:
        lines.append(f"- `{item.check_id}` -> `{item.status}`")
        if item.expected is not None or item.found is not None or item.missing_count is not None:
            lines.append(
                f"  expected={item.expected} found={item.found} missing_count={item.missing_count}"
            )
        if item.details:
            lines.append(f"  details: {item.details}")
    failures = [item for item in summary.checks if item.status == "FAIL"]
    lines.extend(["", "## Failures", ""])
    if not failures:
        lines.append("- none")
    else:
        for item in failures:
            lines.append(f"- `{item.check_id}`")
            if item.details:
                lines.append(f"  {item.details}")
    lines.append("")
    return "\n".join(lines)


def save_consistency_markdown(summary: ConsistencySummary, path: Path = DEFAULT_MD_PATH) -> None:
    _atomic_write(path, render_consistency_markdown(summary))

