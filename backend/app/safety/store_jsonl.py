from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.safety.models import AccountSafetyState, RiskSignal

DEFAULT_SAFETY_DIR = Path("OUT/safety")
DEFAULT_ACCOUNT_STATE_PATH = DEFAULT_SAFETY_DIR / "account_state.jsonl"
DEFAULT_COOLDOWNS_PATH = DEFAULT_SAFETY_DIR / "cooldowns.jsonl"
DEFAULT_PACING_EVENTS_PATH = DEFAULT_SAFETY_DIR / "pacing_events.jsonl"


def append_account_state(state: AccountSafetyState, *, path: Path = DEFAULT_ACCOUNT_STATE_PATH) -> None:
    _append_jsonl(path, state.to_dict())


def append_cooldown_event(payload: dict[str, Any], *, path: Path = DEFAULT_COOLDOWNS_PATH) -> None:
    _append_jsonl(path, payload)


def append_pacing_event(payload: dict[str, Any], *, path: Path = DEFAULT_PACING_EVENTS_PATH) -> None:
    _append_jsonl(path, payload)


def append_risk_signal(signal: RiskSignal, *, path: Path = DEFAULT_PACING_EVENTS_PATH) -> None:
    _append_jsonl(path, signal.to_dict())


def read_all(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as reader:
        for line in reader:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def reconstruct_latest_state(account_id: str, *, path: Path = DEFAULT_ACCOUNT_STATE_PATH) -> dict[str, Any] | None:
    latest = None
    for row in read_all(path):
        if row.get("account_id") == account_id:
            latest = row
    return latest


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as writer:
        writer.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
