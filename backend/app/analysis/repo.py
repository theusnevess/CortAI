from __future__ import annotations

from pathlib import Path

from .models import (
    AccountHealthSummary,
    ExperimentWinners,
    HookPerformanceSummary,
    PilotMetricsSummary,
)
from .store_json import AnalysisJsonStore


class AnalysisRepo:
    def __init__(self, base_dir: str | Path = "OUT/analysis"):
        self.store = AnalysisJsonStore(base_dir=base_dir)

    def save_pilot_metrics_summary(self, summary: PilotMetricsSummary):
        return self.store.save_json("pilot_metrics_summary.json", summary.to_dict())

    def load_pilot_metrics_summary(self):
        return self.store.load_json("pilot_metrics_summary.json")

    def save_experiment_winners(self, summary: ExperimentWinners):
        return self.store.save_json("experiment_winners.json", summary.to_dict())

    def load_experiment_winners(self):
        return self.store.load_json("experiment_winners.json")

    def save_hook_performance_summary(self, summary: HookPerformanceSummary):
        return self.store.save_json("hook_performance_summary.json", summary.to_dict())

    def load_hook_performance_summary(self):
        return self.store.load_json("hook_performance_summary.json")

    def save_account_health_summary(self, summary: AccountHealthSummary):
        return self.store.save_json("account_health_summary.json", summary.to_dict())

    def load_account_health_summary(self):
        return self.store.load_json("account_health_summary.json")
