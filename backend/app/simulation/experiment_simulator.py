from __future__ import annotations

from app.simulation.models import SimulatedExperimentResult, SimulatedPublishRecord, SimulatedVideoMetrics


def simulate_experiment_results(
    publishes: list[SimulatedPublishRecord],
    metrics: list[SimulatedVideoMetrics],
) -> list[SimulatedExperimentResult]:
    metric_by_publish_id = {item.simulated_publish_id: item for item in metrics}
    results: list[SimulatedExperimentResult] = []
    for publish in publishes:
        if not publish.experiment_id or not publish.variant:
            continue
        metric = metric_by_publish_id.get(publish.simulated_publish_id)
        if metric is None:
            continue
        results.append(
            SimulatedExperimentResult(
                simulation_run_id=publish.simulation_run_id,
                experiment_id=publish.experiment_id,
                variant=publish.variant,
                simulated_publish_id=publish.simulated_publish_id,
                supporting_metric="completion_rate",
                score=metric.completion_rate,
            )
        )
    return results

