from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from app.experiments.assignment import assign_variant
from app.experiments.models import (
    ALLOWED_SCOPES,
    ALLOWED_STATUSES,
    ALLOWED_VARIANTS,
    Experiment,
    ExperimentAssignment,
    ExperimentResult,
)
from app.experiments.repo import get_by_key, save_if_absent
from app.experiments.store_jsonl import ASSIGNMENTS_PATH, EXPERIMENTS_PATH, RESULTS_PATH


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _experiment_id(*, name: str, scope: str) -> str:
    material = f"{scope}|{name.strip()}".encode("utf-8")
    return f"exp_{sha256(material).hexdigest()[:16]}"


def _assignment_id(*, experiment_id: str, subject_key: str) -> str:
    material = f"{experiment_id}|{subject_key}".encode("utf-8")
    return f"asg_{sha256(material).hexdigest()[:16]}"


def _result_id(*, experiment_id: str, subject_key: str, window_id: str) -> str:
    material = f"{experiment_id}|{subject_key}|{window_id}".encode("utf-8")
    return f"res_{sha256(material).hexdigest()[:16]}"


@dataclass
class ExperimentService:
    experiments_path: Path = EXPERIMENTS_PATH
    assignments_path: Path = ASSIGNMENTS_PATH
    results_path: Path = RESULTS_PATH

    def create_experiment(
        self,
        *,
        name: str,
        scope: str,
        variant_a: dict[str, Any],
        variant_b: dict[str, Any],
        status: str = "ACTIVE",
        created_at: str | None = None,
    ) -> tuple[Experiment, str]:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("EXPERIMENT_NAME_INVALID")
        if scope not in ALLOWED_SCOPES:
            raise ValueError("EXPERIMENT_SCOPE_INVALID")
        if status not in ALLOWED_STATUSES:
            raise ValueError("EXPERIMENT_STATUS_INVALID")
        experiment_id = _experiment_id(name=normalized_name, scope=scope)
        existing = get_by_key("experiment_id", experiment_id, path=self.experiments_path)
        if existing is not None:
            current = Experiment(
                experiment_id=str(existing["experiment_id"]),
                name=str(existing["name"]),
                scope=str(existing["scope"]),
                variant_a=dict(existing["variant_a"]),
                variant_b=dict(existing["variant_b"]),
                status=str(existing["status"]),
                created_at=str(existing["created_at"]),
            )
            if (
                current.name == normalized_name
                and current.scope == scope
                and current.variant_a == dict(variant_a)
                and current.variant_b == dict(variant_b)
                and current.status == status
            ):
                return current, "NOOP"
            raise ValueError("EXPERIMENT_DEFINITION_CONFLICT")
        record = Experiment(
            experiment_id=experiment_id,
            name=normalized_name,
            scope=scope,
            variant_a=dict(variant_a),
            variant_b=dict(variant_b),
            status=status,
            created_at=created_at or _now_iso(),
        )
        action = save_if_absent(record.to_dict(), key_field="experiment_id", path=self.experiments_path)
        return record, action

    def assign(
        self,
        *,
        experiment: Experiment | dict[str, Any],
        subject_key: str,
        assigned_at: str | None = None,
    ) -> tuple[ExperimentAssignment, str]:
        exp = self._coerce_experiment(experiment)
        normalized_subject = subject_key.strip()
        if not normalized_subject:
            raise ValueError("EXPERIMENT_SUBJECT_INVALID")
        assignment_id = _assignment_id(experiment_id=exp.experiment_id, subject_key=normalized_subject)
        existing = get_by_key("assignment_id", assignment_id, path=self.assignments_path)
        if existing is not None:
            return (
                ExperimentAssignment(
                    assignment_id=str(existing["assignment_id"]),
                    experiment_id=str(existing["experiment_id"]),
                    subject_key=str(existing["subject_key"]),
                    variant=str(existing["variant"]),
                    assigned_at=str(existing["assigned_at"]),
                ),
                "NOOP",
            )
        variant = assign_variant(experiment_id=exp.experiment_id, subject_key=normalized_subject)
        record = ExperimentAssignment(
            assignment_id=assignment_id,
            experiment_id=exp.experiment_id,
            subject_key=normalized_subject,
            variant=variant,
            assigned_at=assigned_at or _now_iso(),
        )
        action = save_if_absent(record.to_dict(), key_field="assignment_id", path=self.assignments_path)
        return record, action

    def record_result(
        self,
        *,
        experiment: Experiment | dict[str, Any],
        subject_key: str,
        window_id: str,
        metrics: dict[str, Any],
        recorded_at: str | None = None,
    ) -> tuple[ExperimentResult, str]:
        exp = self._coerce_experiment(experiment)
        assignment, _ = self.assign(experiment=exp, subject_key=subject_key, assigned_at=recorded_at)
        result_id = _result_id(experiment_id=exp.experiment_id, subject_key=subject_key, window_id=window_id)
        existing = get_by_key("result_id", result_id, path=self.results_path)
        if existing is not None:
            current = ExperimentResult(
                result_id=str(existing["result_id"]),
                experiment_id=str(existing["experiment_id"]),
                subject_key=str(existing["subject_key"]),
                variant=str(existing["variant"]),
                window_id=str(existing["window_id"]),
                metrics=dict(existing["metrics"]),
                recorded_at=str(existing["recorded_at"]),
            )
            if (
                current.experiment_id == exp.experiment_id
                and current.subject_key == subject_key
                and current.variant == assignment.variant
                and current.window_id == window_id
                and current.metrics == dict(metrics)
            ):
                return current, "NOOP"
            raise ValueError("EXPERIMENT_RESULT_CONFLICT")
        record = ExperimentResult(
            result_id=result_id,
            experiment_id=exp.experiment_id,
            subject_key=subject_key,
            variant=assignment.variant,
            window_id=window_id,
            metrics=dict(metrics),
            recorded_at=recorded_at or _now_iso(),
        )
        action = save_if_absent(record.to_dict(), key_field="result_id", path=self.results_path)
        return record, action

    def resolve_variant_payload(
        self,
        *,
        experiment: Experiment | dict[str, Any],
        subject_key: str,
    ) -> tuple[str, dict[str, Any]]:
        exp = self._coerce_experiment(experiment)
        variant = assign_variant(experiment_id=exp.experiment_id, subject_key=subject_key)
        if variant not in ALLOWED_VARIANTS:
            raise ValueError("EXPERIMENT_VARIANT_INVALID")
        payload = exp.variant_a if variant == "A" else exp.variant_b
        return variant, dict(payload)

    def _coerce_experiment(self, experiment: Experiment | dict[str, Any]) -> Experiment:
        if isinstance(experiment, Experiment):
            return experiment
        return Experiment(
            experiment_id=str(experiment["experiment_id"]),
            name=str(experiment["name"]),
            scope=str(experiment["scope"]),
            variant_a=dict(experiment["variant_a"]),
            variant_b=dict(experiment["variant_b"]),
            status=str(experiment["status"]),
            created_at=str(experiment["created_at"]),
        )
