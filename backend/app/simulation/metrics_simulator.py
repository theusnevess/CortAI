from __future__ import annotations

from datetime import datetime, timedelta
from hashlib import sha256

from app.simulation.models import SimulatedPublishRecord, SimulatedVideoMetrics


def _deterministic_score(*, simulation_run_id: str, simulated_publish_id: str) -> int:
    material = f"{simulation_run_id}|{simulated_publish_id}".encode("utf-8")
    return int(sha256(material).hexdigest()[:8], 16)


def _iso_after(published_at: str, hours: int) -> str:
    base = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    return (base + timedelta(hours=hours)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def simulate_video_metrics(
    publishes: list[SimulatedPublishRecord],
) -> list[SimulatedVideoMetrics]:
    metrics: list[SimulatedVideoMetrics] = []
    for item in publishes:
        score = _deterministic_score(
            simulation_run_id=item.simulation_run_id,
            simulated_publish_id=item.simulated_publish_id,
        )
        variant_bonus = 15 if item.variant == "B" else 0
        views = 120 + (score % 180) + variant_bonus
        avg_watch_time = round(3.0 + ((score % 40) / 10.0), 2)
        completion_rate = round(min(0.95, 0.15 + ((score % 45) / 100.0) + (0.05 if item.variant == "B" else 0.0)), 4)
        view_3s_rate = round(min(0.99, completion_rate + 0.18), 4)
        watch_time_total = round(views * avg_watch_time, 2)
        metrics.append(
            SimulatedVideoMetrics(
                simulation_run_id=item.simulation_run_id,
                simulated_publish_id=item.simulated_publish_id,
                views=views,
                watch_time_total=watch_time_total,
                avg_watch_time=avg_watch_time,
                completion_rate=completion_rate,
                view_3s_rate=view_3s_rate,
                collected_at=_iso_after(item.published_at, 1),
            )
        )
    return metrics

