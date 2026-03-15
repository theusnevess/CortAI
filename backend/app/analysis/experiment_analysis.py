from __future__ import annotations

from typing import Any


def build_experiment_winners(
    *,
    generated_at: str,
    experiments: list[dict[str, Any]],
    assignments: list[dict[str, Any]],
    metrics: list[dict[str, Any]],
) -> dict[str, Any]:
    assignment_map = {
        str(item.get("subject_key") or ""): str(item.get("variant") or "")
        for item in assignments
        if str(item.get("subject_key") or "") and str(item.get("variant") or "")
    }
    metrics_by_subject = {
        str(row.get("publish_id") or row.get("video_id") or row.get("external_video_id") or ""): row
        for row in metrics
        if str(row.get("publish_id") or row.get("video_id") or row.get("external_video_id") or "")
    }

    result_items: list[dict[str, Any]] = []
    for experiment in sorted(experiments, key=lambda row: str(row.get("experiment_id") or "")):
        experiment_id = str(experiment.get("experiment_id") or "")
        variant_scores = {"A": [], "B": []}
        evidence_count = 0
        for subject_key, variant in assignment_map.items():
            if variant not in variant_scores:
                continue
            metric = metrics_by_subject.get(subject_key)
            if metric is None:
                continue
            value = float(metric.get("completion_rate") or 0.0)
            variant_scores[variant].append(value)
            evidence_count += 1

        avg_a = _avg(variant_scores["A"])
        avg_b = _avg(variant_scores["B"])
        winner_variant = None
        notes = None
        confidence_level = None

        if evidence_count == 0:
            notes = "no_evidence"
        elif avg_a > avg_b:
            winner_variant = "A"
        elif avg_b > avg_a:
            winner_variant = "B"
        else:
            notes = "tie"

        if evidence_count >= 4:
            confidence_level = "MEDIUM"
        elif evidence_count >= 2:
            confidence_level = "LOW"

        result_items.append(
            {
                "experiment_id": experiment_id,
                "winner_variant": winner_variant,
                "confidence_level": confidence_level,
                "supporting_metric": "completion_rate",
                "notes": notes,
            }
        )

    return {"generated_at": generated_at, "experiments": result_items}


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
