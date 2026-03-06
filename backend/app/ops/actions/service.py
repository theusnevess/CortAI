from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.observability.event_append.service import append_event, build_event_record
from app.observability.event_query.index_store.rebuild import rebuild_event_index
from app.observability.event_query.index_store.writer import EventIndexWriter
from app.observability.event_query.indexer import EventIndexer
from app.ops.actions.policy import (
    OperatorActionPolicyError,
    require_operator,
    require_reason,
    validate_requeue_status,
)
from app.runtime.models import DistributedTask, TaskStatus, TaskType
from app.runtime.paths import resolve_out_dir
from app.runtime.queue import InMemoryTaskQueue


class OperatorActionError(RuntimeError):
    """Erro operacional explícito para endpoints de ação."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class OperatorActionResult:
    action_type: str
    status: str
    reason_code: str
    target_id: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OperatorActionService:
    """Serviço mínimo e auditável de ações operacionais."""

    def __init__(
        self,
        *,
        base_dir: Path | None = None,
        queue: InMemoryTaskQueue | None = None,
    ) -> None:
        self.base_dir = base_dir or resolve_out_dir()
        self.queue = queue

    def pause_rollout(self, *, operator_id: str, reason: str) -> OperatorActionResult:
        return self._set_rollout_enabled(False, action_type="pause-rollout", operator_id=operator_id, reason=reason)

    def resume_rollout(self, *, operator_id: str, reason: str) -> OperatorActionResult:
        return self._set_rollout_enabled(True, action_type="resume-rollout", operator_id=operator_id, reason=reason)

    def requeue_task(
        self,
        *,
        operator_id: str,
        reason: str,
        task_id: str,
        task_type: str,
        status: str,
        op_key: str,
        account_id: str | None = None,
        window_id: str | None = None,
    ) -> OperatorActionResult:
        operator = require_operator(operator_id)
        reason_text = require_reason(reason)
        allowed_status = validate_requeue_status(status)
        target_id = task_id.strip()
        if not target_id:
            raise OperatorActionError("TASK_ID_REQUIRED", "task_id is required", 400)

        request_key = f"REQUEUE:{target_id}:{op_key}"
        payload = {
            "task_id": target_id,
            "task_type": task_type,
            "status": allowed_status,
            "op_key": op_key,
            "account_id": account_id,
            "window_id": window_id,
        }
        existing = self._find_request(request_key)
        if existing is not None and existing.get("payload_hash") == self._payload_hash(payload):
            result = OperatorActionResult(
                action_type="requeue-task",
                status="NOOP",
                reason_code="REQUEUE_ALREADY_REQUESTED",
                target_id=target_id,
                details={"request_key": request_key},
            )
            self._audit("requeue-task", operator, target_id, reason_text, result.status, result.reason_code)
            return result

        new_task_id = f"task_{uuid4().hex}"
        if self.queue is not None:
            enum_task_type = TaskType[str(task_type).strip().upper()]
            self.queue.enqueue(
                DistributedTask(
                    task_id=new_task_id,
                    task_type=enum_task_type,
                    account_id=account_id,
                    window_id=window_id,
                    op_key=f"{op_key}:REQUEUE:{target_id}",
                    payload={"requeued_from": target_id, "reason": reason_text},
                    created_at=self._now_iso(),
                    status=TaskStatus.PENDING,
                )
            )

        self._append_jsonl(
            self.base_dir / "ops" / "requeue_requests.jsonl",
            {
                "request_key": request_key,
                "payload_hash": self._payload_hash(payload),
                "task_id": target_id,
                "new_task_id": new_task_id,
                "task_type": task_type,
                "status": allowed_status,
                "op_key": op_key,
                "account_id": account_id,
                "window_id": window_id,
                "operator_id": operator,
                "reason": reason_text,
                "ts": self._now_iso(),
            },
        )
        result = OperatorActionResult(
            action_type="requeue-task",
            status="WRITTEN",
            reason_code="REQUEUE_REQUESTED",
            target_id=target_id,
            details={"new_task_id": new_task_id, "request_key": request_key},
        )
        self._audit("requeue-task", operator, target_id, reason_text, result.status, result.reason_code, result.details)
        return result

    def rebuild_event_index(self, *, operator_id: str, reason: str) -> OperatorActionResult:
        operator = require_operator(operator_id)
        reason_text = require_reason(reason)
        result = rebuild_event_index(
            indexer=EventIndexer(base_dir=self.base_dir),
            writer=EventIndexWriter(self.base_dir / "index" / "event_index.sqlite3"),
        )
        payload = {
            "written": result.written,
            "noop": result.noop,
            "invalid_jsonl_lines": result.invalid_jsonl_lines,
            "invalid_shape_lines": result.invalid_shape_lines,
        }
        action_result = OperatorActionResult(
            action_type="rebuild-event-index",
            status="WRITTEN",
            reason_code="EVENT_INDEX_REBUILT",
            target_id="event_index",
            details=payload,
        )
        self._audit("rebuild-event-index", operator, "event_index", reason_text, action_result.status, action_result.reason_code, payload)
        return action_result

    def acknowledge_alert(self, *, operator_id: str, reason: str, alert_code: str) -> OperatorActionResult:
        operator = require_operator(operator_id)
        reason_text = require_reason(reason)
        target_id = (alert_code or "").strip()
        if not target_id:
            raise OperatorActionError("ALERT_CODE_REQUIRED", "alert_code is required", 400)
        existing = self._find_ack(target_id)
        if existing is not None:
            result = OperatorActionResult(
                action_type="ack-alert",
                status="NOOP",
                reason_code="ALERT_ALREADY_ACKNOWLEDGED",
                target_id=target_id,
                details={"acknowledged_by": existing.get("operator_id")},
            )
            self._audit("ack-alert", operator, target_id, reason_text, result.status, result.reason_code)
            return result

        payload = {
            "alert_code": target_id,
            "operator_id": operator,
            "reason": reason_text,
            "acknowledged_at": self._now_iso(),
        }
        self._append_jsonl(self.base_dir / "ops" / "alert_acknowledgements.jsonl", payload)
        result = OperatorActionResult(
            action_type="ack-alert",
            status="WRITTEN",
            reason_code="ALERT_ACKNOWLEDGED",
            target_id=target_id,
            details=payload,
        )
        self._audit("ack-alert", operator, target_id, reason_text, result.status, result.reason_code, payload)
        return result

    def _set_rollout_enabled(
        self,
        enabled: bool,
        *,
        action_type: str,
        operator_id: str,
        reason: str,
    ) -> OperatorActionResult:
        operator = require_operator(operator_id)
        reason_text = require_reason(reason)
        state = self._read_rollout_state()
        if state.get("rollout_enabled") is enabled:
            result = OperatorActionResult(
                action_type=action_type,
                status="NOOP",
                reason_code="ROLLOUT_STATE_UNCHANGED",
                target_id="rollout_control",
                details={"rollout_enabled": enabled},
            )
            self._audit(action_type, operator, "rollout_control", reason_text, result.status, result.reason_code)
            return result

        payload = {
            "rollout_enabled": enabled,
            "kill_switch_enabled": False if enabled else state.get("kill_switch_enabled", False),
            "updated_by": operator,
            "updated_at": self._now_iso(),
            "reason": reason_text,
        }
        self._write_rollout_state(payload)
        result = OperatorActionResult(
            action_type=action_type,
            status="WRITTEN",
            reason_code="ROLLOUT_STATE_UPDATED",
            target_id="rollout_control",
            details=payload,
        )
        self._audit(action_type, operator, "rollout_control", reason_text, result.status, result.reason_code, payload)
        return result

    def _read_rollout_state(self) -> dict[str, Any]:
        path = self.base_dir / "ops" / "operator_control.json"
        if not path.exists():
            return {"rollout_enabled": True, "kill_switch_enabled": False}
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_rollout_state(self, payload: dict[str, Any]) -> None:
        path = self.base_dir / "ops" / "operator_control.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def _find_request(self, request_key: str) -> dict[str, Any] | None:
        path = self.base_dir / "ops" / "requeue_requests.jsonl"
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as reader:
            for line in reader:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                if payload.get("request_key") == request_key:
                    return payload
        return None

    def _find_ack(self, alert_code: str) -> dict[str, Any] | None:
        path = self.base_dir / "ops" / "alert_acknowledgements.jsonl"
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as reader:
            for line in reader:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                if payload.get("alert_code") == alert_code:
                    return payload
        return None

    def _audit(
        self,
        action_type: str,
        operator_id: str,
        target_id: str,
        reason: str,
        result: str,
        reason_code: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        event = build_event_record(
            "OPS/action_executed",
            {
                "event_id": f"evt_{uuid4().hex}",
                "timestamp": self._now_iso(),
                "operator_id": operator_id,
                "action_type": action_type,
                "target_id": target_id,
                "reason": reason,
                "result": result,
                "reason_code": reason_code,
                **(details or {}),
            },
            writer_id="operator_actions",
        )
        append_event(event, path=self.base_dir / "events" / "events.jsonl")

    def _append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as writer:
            writer.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")

    def _payload_hash(self, payload: dict[str, Any]) -> str:
        return sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
