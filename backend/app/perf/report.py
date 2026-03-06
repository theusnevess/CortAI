from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from app.perf.load_harness import LoadHarnessResult


def write_load_report(
    results: Iterable["LoadHarnessResult"],
    *,
    output_dir: Path,
) -> tuple[Path, Path]:
    """Persiste relatorio JSON e Markdown do D18."""
    output_dir.mkdir(parents=True, exist_ok=True)
    results_list = list(results)
    json_path = output_dir / "load_test_report.json"
    md_path = output_dir / "load_test_report.md"

    payload = {"scenarios": [result.to_dict() for result in results_list]}
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_to_markdown(results_list), encoding="utf-8")
    return json_path, md_path


def _to_markdown(results: list["LoadHarnessResult"]) -> str:
    lines = [
        "# Load Test Report",
        "",
    ]
    for result in results:
        lines.extend(
            [
                f"## {result.scenario_name}",
                "",
                f"- Throughput: `{result.throughput_ops_s}` ops/s",
                f"- Error rate: `{result.error_rate}`",
                f"- Lease contention rate: `{result.lease_contention_rate}`",
                f"- Idempotency conflict rate: `{result.idempotency_conflict_rate}`",
                f"- Fallback hit rate: `{result.fallback_hit_rate}`",
                "",
                "| Metric | Count | p50 ms | p95 ms | p99 ms | max ms | avg ms |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for name, summary in sorted(result.latency.items()):
            lines.append(
                f"| `{name}` | {summary.count} | {summary.p50_ms} | {summary.p95_ms} | {summary.p99_ms} | {summary.max_ms} | {summary.avg_ms} |"
            )
        lines.extend(
            [
                "",
                f"- Ops: `{result.total_ops}`",
                f"- Success: `{result.success_count}`",
                f"- Errors: `{result.error_count}`",
                f"- Notes: `{', '.join(result.notes) if result.notes else 'none'}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"
