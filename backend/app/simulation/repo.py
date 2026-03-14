from __future__ import annotations

from pathlib import Path

from app.simulation.store_jsonl import (
    SIMULATED_EXPERIMENT_RESULTS_PATH,
    SIMULATED_PUBLISH_RECORDS_PATH,
    SIMULATED_VIDEO_METRICS_PATH,
    SIMULATION_RUNS_PATH,
    append_record,
    read_all_records,
)


def append_simulated_publish_record(record: dict, *, path: Path = SIMULATED_PUBLISH_RECORDS_PATH) -> None:
    append_record(record, path)


def append_simulated_video_metrics(record: dict, *, path: Path = SIMULATED_VIDEO_METRICS_PATH) -> None:
    append_record(record, path)


def append_simulated_experiment_result(record: dict, *, path: Path = SIMULATED_EXPERIMENT_RESULTS_PATH) -> None:
    append_record(record, path)


def append_simulation_run_summary(record: dict, *, path: Path = SIMULATION_RUNS_PATH) -> None:
    append_record(record, path)


def load_simulated_publish_records(*, path: Path = SIMULATED_PUBLISH_RECORDS_PATH) -> list[dict]:
    return read_all_records(path)


def load_simulated_video_metrics(*, path: Path = SIMULATED_VIDEO_METRICS_PATH) -> list[dict]:
    return read_all_records(path)


def load_simulated_experiment_results(*, path: Path = SIMULATED_EXPERIMENT_RESULTS_PATH) -> list[dict]:
    return read_all_records(path)


def load_simulation_run_summaries(*, path: Path = SIMULATION_RUNS_PATH) -> list[dict]:
    return read_all_records(path)

