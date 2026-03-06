from __future__ import annotations


class OperatorActionPolicyError(ValueError):
    """Erro determinístico de policy para ações operacionais."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


ALLOWED_REQUEUE_STATUSES = {"FAILED", "BLOCKED", "NOOP"}


def require_reason(reason: str) -> str:
    normalized = (reason or "").strip()
    if not normalized:
        raise OperatorActionPolicyError("ACTION_REASON_REQUIRED", "reason is required", 400)
    return normalized


def require_operator(operator_id: str) -> str:
    normalized = (operator_id or "").strip()
    if not normalized:
        raise OperatorActionPolicyError("ACTION_OPERATOR_REQUIRED", "operator_id is required", 400)
    return normalized


def validate_requeue_status(status: str) -> str:
    normalized = (status or "").strip().upper()
    if normalized not in ALLOWED_REQUEUE_STATUSES:
        raise OperatorActionPolicyError(
            "REQUEUE_STATUS_NOT_ALLOWED",
            "task status is not eligible for requeue",
            409,
        )
    return normalized
