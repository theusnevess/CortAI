from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.simulation.models import SimulationRunSummary
from app.simulation.publish_simulator import simulate_publish_records
from app.simulation.metrics_simulator import simulate_video_metrics
from app.simulation.experiment_simulator import simulate_experiment_results
from app.simulation.repo import (
    append_simulated_experiment_result,
    append_simulated_publish_record,
    append_simulated_video_metrics,
    append_simulation_run_summary,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class OfflineSimulationRunner:
    output_dir: Path = Path("OUT/simulation")

    def run_offline_simulation(
        self,
        *,
        simulation_run_id: str,
        account_ids: list[str],
        num_publishes_per_account: int,
        creative_pack_ids: list[str] | None = None,
        experiment_id: str | None = None,
        variants: list[str] | None = None,
        start_at: str | None = None,
        generated_at: str | None = None,
    ) -> SimulationRunSummary:
        publishes = simulate_publish_records(
            simulation_run_id=simulation_run_id,
            account_ids=account_ids,
            num_publishes_per_account=num_publishes_per_account,
            creative_pack_ids=creative_pack_ids,
            experiment_id=experiment_id,
            variants=variants,
            start_at=start_at,
        )
        metrics = simulate_video_metrics(publishes)
        experiment_results = simulate_experiment_results(publishes, metrics)

        for item in publishes:
            append_simulated_publish_record(
                item.to_dict(),
                path=self.output_dir / "simulated_publish_records.jsonl",
            )
        for item in metrics:
            append_simulated_video_metrics(
                item.to_dict(),
                path=self.output_dir / "simulated_video_metrics.jsonl",
            )
        for item in experiment_results:
            append_simulated_experiment_result(
                item.to_dict(),
                path=self.output_dir / "simulated_experiment_results.jsonl",
            )

        summary = SimulationRunSummary(
            simulation_run_id=simulation_run_id,
            generated_at=generated_at or _now_iso(),
            total_accounts=len(account_ids),
            total_simulated_publishes=len(publishes),
            total_metrics=len(metrics),
            total_experiment_results=len(experiment_results),
        )
        append_simulation_run_summary(summary.to_dict(), path=self.output_dir / "simulation_runs.jsonl")
        return summary

