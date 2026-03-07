from __future__ import annotations

from hashlib import sha256

from app.attribution.models import StructurePerformance


def build_structure_key(script_skeleton: str) -> str:
    sections: list[str] = []
    for line in script_skeleton.splitlines():
        if ":" not in line:
            continue
        head = line.split(":", 1)[0].strip().upper()
        if head:
            sections.append(head)
    return ">".join(sections) if sections else "UNKNOWN"


def build_structure_performance(
    *,
    account_id: str,
    publish_id: str,
    creative_pack_id: str,
    structure_key: str,
    views: int,
    completion_rate: float,
    experiment_variant: str | None,
    generated_at: str,
) -> StructurePerformance:
    key = f"{account_id}|{publish_id}|{structure_key}"
    record_id = f"struct_{sha256(key.encode('utf-8')).hexdigest()[:16]}"
    return StructurePerformance(
        structure_performance_id=record_id,
        account_id=account_id,
        publish_id=publish_id,
        creative_pack_id=creative_pack_id,
        structure_key=structure_key,
        views=views,
        completion_rate=completion_rate,
        experiment_variant=experiment_variant,
        generated_at=generated_at,
    )
