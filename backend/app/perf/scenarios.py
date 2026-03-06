from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoadScenario:
    """Define um cenario de carga deterministico para os pipelines do D18."""

    name: str
    account_count: int
    videos_per_account: int
    windows_per_account: int = 1
    query_burst: int = 0
    run_rebuild: bool = False
    force_hot_store_failure: bool = False

    @property
    def total_windows(self) -> int:
        return self.account_count * self.windows_per_account


def default_load_scenarios() -> list[LoadScenario]:
    """Retorna a bateria basica de cenarios do D18."""
    return [
        LoadScenario(
            name="load_10_accounts",
            account_count=10,
            videos_per_account=10,
            windows_per_account=1,
            query_burst=10,
        ),
        LoadScenario(
            name="load_50_accounts",
            account_count=50,
            videos_per_account=10,
            windows_per_account=1,
            query_burst=25,
        ),
        LoadScenario(
            name="load_100_accounts",
            account_count=100,
            videos_per_account=10,
            windows_per_account=1,
            query_burst=50,
            run_rebuild=True,
        ),
        LoadScenario(
            name="query_burst_fallback",
            account_count=10,
            videos_per_account=10,
            windows_per_account=1,
            query_burst=100,
            force_hot_store_failure=True,
        ),
    ]
