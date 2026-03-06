from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.runtime.paths import resolve_out_dir

_DELTA_METRICS = (
    "avg_views",
    "avg_retention_3s",
    "avg_completion_rate",
    "avg_rpm",
    "total_views",
    "total_follows",
    "completion_rate",
    "follow_rate",
    "rpm",
)


class StrategyObservatoryNotFoundError(RuntimeError):
    """Erro explícito quando um patch não existe."""

    def __init__(self, patch_id: str) -> None:
        super().__init__(patch_id)
        self.patch_id = patch_id


@dataclass(frozen=True)
class StrategyObservatoryService:
    """Serviço read-only para ligar patch, aplicação e resultado por janela."""

    base_dir: Path | None = None

    def list_patches(
        self,
        *,
        account_id: str | None = None,
        policy_stage: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        applications = self._applications_by_patch_id()
        items: list[dict[str, Any]] = []
        for patch in self._read_jsonl(self._data_dir / "strategy_patches.jsonl"):
            if account_id and patch.get("account_id") != account_id:
                continue
            if policy_stage and patch.get("policy_stage") != policy_stage:
                continue
            application = applications.get(str(patch.get("patch_id") or ""))
            items.append(self._build_patch_item(patch, application))
        return sorted(items, key=lambda item: (item["created_at"], item["patch_id"]), reverse=True)[:limit]

    def get_patch(self, patch_id: str) -> dict[str, Any]:
        applications = self._applications_by_patch_id()
        for patch in self._read_jsonl(self._data_dir / "strategy_patches.jsonl"):
            if patch.get("patch_id") != patch_id:
                continue
            application = applications.get(patch_id)
            return {
                **self._build_patch_item(patch, application),
                "reason_codes": list(patch.get("reason_codes") or []),
                "layers_applied": list(patch.get("layers_applied") or []),
                "overrides": dict(patch.get("overrides") or {}),
                "inputs": dict(patch.get("inputs") or {}),
                "application": dict(application) if isinstance(application, dict) else None,
            }
        raise StrategyObservatoryNotFoundError(patch_id)

    def list_impact(self, *, account_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        scorecards = self._rows_by_account(self._read_jsonl(self._data_dir / "scorecards.jsonl"))
        window_metrics = self._rows_by_account(self._read_jsonl(self._data_dir / "window_metrics.jsonl"))
        items: list[dict[str, Any]] = []
        for patch in self.list_patches(account_id=account_id, limit=limit * 2):
            before = self._find_row_for_window(scorecards, patch["account_id"], patch["window_id"]) or self._find_row_for_window(
                window_metrics,
                patch["account_id"],
                patch["window_id"],
            )
            after = self._find_next_row(
                scorecards,
                patch["account_id"],
                patch["window_id"],
                patch["created_at"],
            ) or self._find_next_row(
                window_metrics,
                patch["account_id"],
                patch["window_id"],
                patch["created_at"],
            )
            items.append(
                {
                    "patch_id": patch["patch_id"],
                    "account_id": patch["account_id"],
                    "policy_stage": patch["policy_stage"],
                    "status": patch["status"],
                    "window_id_before": patch["window_id"],
                    "window_id_after": (after or {}).get("window_id"),
                    "scorecard_delta": self._build_delta(before, after),
                }
            )
        return items[:limit]

    def list_timeline(self, *, account_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        patches = self.list_patches(account_id=account_id, limit=limit * 2)
        items = [
            {
                "patch_id": patch["patch_id"],
                "account_id": patch["account_id"],
                "window_id": patch["window_id"],
                "policy_stage": patch["policy_stage"],
                "status": patch["status"],
                "reason_code": patch["reason_code"],
                "created_at": patch["created_at"],
            }
            for patch in patches
        ]
        return sorted(items, key=lambda item: (item["created_at"], item["patch_id"]))[:limit]

    @property
    def _out_dir(self) -> Path:
        return self.base_dir or resolve_out_dir()

    @property
    def _data_dir(self) -> Path:
        return self._out_dir / "data"

    def _read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as reader:
            for line in reader:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                if isinstance(payload, dict):
                    rows.append(payload)
        return rows

    def _applications_by_patch_id(self) -> dict[str, dict[str, Any]]:
        found: dict[str, dict[str, Any]] = {}
        for item in self._read_jsonl(self._data_dir / "strategy_patch_applications.jsonl"):
            patch_id = str(item.get("patch_id") or "")
            if not patch_id:
                continue
            found[patch_id] = item
        return found

    def _build_patch_item(self, patch: dict[str, Any], application: dict[str, Any] | None) -> dict[str, Any]:
        reason_codes = list(patch.get("reason_codes") or [])
        return {
            "patch_id": str(patch.get("patch_id") or ""),
            "account_id": str(patch.get("account_id") or ""),
            "window_id": str(patch.get("window_id") or ""),
            "policy_stage": str(patch.get("policy_stage") or ""),
            "reason_code": reason_codes[0] if reason_codes else None,
            "created_at": str(patch.get("generated_at") or ""),
            "status": self._derive_patch_status(patch, application),
        }

    def _derive_patch_status(self, patch: dict[str, Any], application: dict[str, Any] | None) -> str:
        if isinstance(application, dict):
            raw_status = str(application.get("status") or "").upper()
            if raw_status == "APPLIED":
                return "applied"
            if raw_status == "ROLLED_BACK":
                return "reverted"
        reason_codes = [str(item).upper() for item in patch.get("reason_codes") or []]
        if any("CONFLICT" in item for item in reason_codes):
            return "conflict"
        if not patch.get("active", False) or not list(patch.get("layers_applied") or []):
            return "noop"
        return "generated"

    def _rows_by_account(self, rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            account_id = str(row.get("account_id") or "")
            if not account_id:
                continue
            grouped.setdefault(account_id, []).append(row)
        for account_rows in grouped.values():
            account_rows.sort(key=lambda row: self._row_order_key(row))
        return grouped

    def _find_row_for_window(
        self,
        grouped: dict[str, list[dict[str, Any]]],
        account_id: str,
        window_id: str,
    ) -> dict[str, Any] | None:
        for row in grouped.get(account_id, []):
            if row.get("window_id") == window_id:
                return row
        return None

    def _find_next_row(
        self,
        grouped: dict[str, list[dict[str, Any]]],
        account_id: str,
        window_id: str,
        created_at: str,
    ) -> dict[str, Any] | None:
        current_seen = False
        fallback_key = (created_at or "", window_id or "")
        for row in grouped.get(account_id, []):
            row_key = self._row_order_key(row)
            if row.get("window_id") == window_id:
                current_seen = True
                continue
            if current_seen:
                return row
            if row_key > fallback_key:
                return row
        return None

    def _row_order_key(self, row: dict[str, Any]) -> tuple[str, str]:
        ts = str(
            row.get("generated_at")
            or row.get("computed_at")
            or row.get("captured_at")
            or row.get("applied_at")
            or ""
        )
        return (ts, str(row.get("window_id") or ""))

    def _build_delta(self, before: dict[str, Any] | None, after: dict[str, Any] | None) -> dict[str, float | None]:
        if not isinstance(before, dict) or not isinstance(after, dict):
            return {}
        delta: dict[str, float | None] = {}
        for metric in _DELTA_METRICS:
            before_value = before.get(metric)
            after_value = after.get(metric)
            if isinstance(before_value, (int, float)) and isinstance(after_value, (int, float)):
                delta[metric] = round(float(after_value) - float(before_value), 4)
        return delta
