from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_SIMULATION_DIR = Path("OUT/simulation")
SIMULATED_PUBLISH_RECORDS_PATH = DEFAULT_SIMULATION_DIR / "simulated_publish_records.jsonl"
SIMULATED_VIDEO_METRICS_PATH = DEFAULT_SIMULATION_DIR / "simulated_video_metrics.jsonl"
SIMULATED_EXPERIMENT_RESULTS_PATH = DEFAULT_SIMULATION_DIR / "simulated_experiment_results.jsonl"
SIMULATION_RUNS_PATH = DEFAULT_SIMULATION_DIR / "simulation_runs.jsonl"


def append_record(record: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()


def read_all_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows

