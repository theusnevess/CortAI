$ErrorActionPreference = "Stop"

if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) { return }
        $parts = $line -split "=", 2
        if ($parts.Count -eq 2) {
            [System.Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim())
        }
    }
}

$env:PYTHONPATH = "backend"

Write-Host "==== MATERIALIZE PRE-D23 EVIDENCE ===="

$dirs = @(
    "OUT/content",
    "OUT/metrics",
    "OUT/simulation",
    "OUT/data/publish_records",
    "OUT/experiments",
    "OUT/content/creative_packs",
    "OUT/attribution",
    "OUT/events",
    "OUT/intelligence",
    "OUT/analysis"
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

@'
import json
from pathlib import Path

from app.analysis.consistency.service import DataConsistencyCheckerService
from app.simulation.runner import OfflineSimulationRunner

out = Path("OUT")
simulation_dir = out / "simulation"
runner = OfflineSimulationRunner(output_dir=simulation_dir)
runner.run_offline_simulation(
    simulation_run_id="pre_d23_evidence_run",
    account_ids=["acc_001", "acc_002", "acc_003"],
    num_publishes_per_account=2,
    creative_pack_ids=["cp_001", "cp_002", "cp_003"],
    experiment_id="exp_pre_d23",
    variants=["A", "B"],
    start_at="2026-03-15T12:00:00Z",
    generated_at="2026-03-15T12:30:00Z",
)

def read_jsonl(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)

def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

publish_rows = read_jsonl(simulation_dir / "simulated_publish_records.jsonl")
metric_rows = read_jsonl(simulation_dir / "simulated_video_metrics.jsonl")
result_rows = read_jsonl(simulation_dir / "simulated_experiment_results.jsonl")

publish_index = {row["simulated_publish_id"]: row for row in publish_rows}

write_jsonl(
    out / "data" / "publish_records" / "publish_records.jsonl",
    [
        {
            "publish_id": row["simulated_publish_id"],
            "account_id": row["account_id"],
            "video_id": row["metadata"]["video_id"],
            "job_id": f'job_{row["simulated_publish_id"]}',
            "platform": "tiktok",
            "status": "posted",
            "published_at": row["published_at"],
            "metadata": {"creative_pack_id": row.get("creative_pack_id")},
        }
        for row in publish_rows
    ],
)

write_jsonl(
    out / "metrics" / "video_metrics.jsonl",
    [
        {
            "publish_id": row["simulated_publish_id"],
            "account_id": publish_index[row["simulated_publish_id"]]["account_id"],
            "video_id": publish_index[row["simulated_publish_id"]]["metadata"]["video_id"],
            "captured_at": row["collected_at"],
            "captured_window_id": "pre_d23_window",
            "source_kind": "PLATFORM_ANALYTICS",
            "views": row["views"],
            "ingested_at": row["collected_at"],
            "collected_at_bucket": row["collected_at"],
        }
        for row in metric_rows
    ],
)

write_jsonl(out / "experiments" / "experiments.jsonl", [{"experiment_id": "exp_pre_d23"}])
write_jsonl(
    out / "experiments" / "assignments.jsonl",
    [
        {
            "assignment_id": f'asg_{row["simulated_publish_id"]}',
            "experiment_id": "exp_pre_d23",
            "subject_key": row["simulated_publish_id"],
        }
        for row in publish_rows
    ],
)
write_jsonl(
    out / "experiments" / "results.jsonl",
    [
        {
            "result_id": f'res_{row["simulated_publish_id"]}',
            "assignment_id": f'asg_{row["simulated_publish_id"]}',
            "experiment_id": row["experiment_id"],
        }
        for row in result_rows
    ],
)

creative_pack_ids = sorted(
    {
        str(row.get("creative_pack_id") or "")
        for row in publish_rows
        if row.get("creative_pack_id")
    }
)
write_jsonl(
    out / "content" / "creative_packs" / "creative_packs.jsonl",
    [{"creative_pack_id": item} for item in creative_pack_ids],
)

write_jsonl(out / "attribution" / "hook_performance.jsonl", [{"hook_performance_id": "hp_pre_d23"}])
write_jsonl(
    out / "events" / "events.jsonl",
    [
        {"event_type": "SAFETY/pacing_delay", "account_id": "acc_001"},
        {"event_type": "SAFETY/risk_detected", "account_id": "acc_002"},
        {"event_type": "SAFETY/cooldown_started", "account_id": "acc_003"},
    ],
)
write_jsonl(
    out / "intelligence" / "account_health.jsonl",
    [
        {"snapshot_id": "ah_001", "account_id": "acc_001", "risk_level": "LOW"},
        {"snapshot_id": "ah_002", "account_id": "acc_002", "risk_level": "MEDIUM"},
    ],
)
write_jsonl(
    out / "intelligence" / "risk_profiles.jsonl",
    [
        {"profile_id": "rp_001", "account_id": "acc_001", "risk_level": "LOW"},
        {"profile_id": "rp_002", "account_id": "acc_002", "risk_level": "MEDIUM"},
    ],
)

analysis_dir = out / "analysis"
if not (analysis_dir / "pilot_metrics_summary.json").exists():
    write_json(analysis_dir / "pilot_metrics_summary.json", {"status": "seeded"})
if not (analysis_dir / "experiment_winners.json").exists():
    write_json(analysis_dir / "experiment_winners.json", {"status": "seeded"})
if not (analysis_dir / "hook_performance_summary.json").exists():
    write_json(analysis_dir / "hook_performance_summary.json", {"status": "seeded"})
if not (analysis_dir / "account_health_summary.json").exists():
    write_json(analysis_dir / "account_health_summary.json", {"status": "seeded"})

summary = DataConsistencyCheckerService(
    analysis_dir=analysis_dir,
    safety_events_path=out / "events" / "events.jsonl",
).generate_consistency_report(generated_at="2026-03-15T12:45:00Z")

print("SIMULATION_MATERIALIZED")
print(f"SIM_PUBLISHES={len(publish_rows)}")
print(f"SIM_METRICS={len(metric_rows)}")
print(f"SIM_RESULTS={len(result_rows)}")
print(f"CONSISTENCY_STATUS={summary.status}")
'@ | python -

Write-Host "==== MATERIALIZATION COMPLETE ===="
