from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256

from app.simulation.models import SimulatedPublishRecord


def _base_time(start_at: str | None) -> datetime:
    if isinstance(start_at, str) and start_at.strip():
        return datetime.fromisoformat(start_at.replace("Z", "+00:00"))
    return datetime(2026, 3, 14, 12, 0, tzinfo=timezone.utc)


def _iso(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_publish_id(*, simulation_run_id: str, account_id: str, index: int) -> str:
    material = f"{simulation_run_id}|{account_id}|{index}".encode("utf-8")
    return f"spub_{sha256(material).hexdigest()[:12]}"


def simulate_publish_records(
    *,
    simulation_run_id: str,
    account_ids: list[str],
    num_publishes_per_account: int,
    creative_pack_ids: list[str] | None = None,
    experiment_id: str | None = None,
    variants: list[str] | None = None,
    start_at: str | None = None,
) -> list[SimulatedPublishRecord]:
    if num_publishes_per_account < 1:
        raise ValueError("SIMULATION_PUBLISH_COUNT_INVALID")
    base = _base_time(start_at)
    packs = creative_pack_ids or []
    variant_values = variants or ["A", "B"]
    publishes: list[SimulatedPublishRecord] = []
    for account_offset, account_id in enumerate(account_ids):
        for index in range(num_publishes_per_account):
            publish_time = base + timedelta(minutes=(account_offset * 90) + (index * 120))
            creative_pack_id = packs[(account_offset + index) % len(packs)] if packs else None
            variant = variant_values[(account_offset + index) % len(variant_values)] if experiment_id else None
            simulated_publish_id = _stable_publish_id(
                simulation_run_id=simulation_run_id,
                account_id=account_id,
                index=index + 1,
            )
            publishes.append(
                SimulatedPublishRecord(
                    simulation_run_id=simulation_run_id,
                    simulated_publish_id=simulated_publish_id,
                    account_id=account_id,
                    creative_pack_id=creative_pack_id,
                    experiment_id=experiment_id,
                    variant=variant,
                    published_at=_iso(publish_time),
                    metadata={
                        "video_id": f"simvid_{simulated_publish_id}",
                        "sequence_index": index + 1,
                    },
                )
            )
    return publishes

