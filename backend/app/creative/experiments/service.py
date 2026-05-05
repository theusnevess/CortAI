from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import ExperimentAssignment, ExperimentPlan
from app.creative.experiments.models import ExperimentCapabilityInput, ExperimentCapabilityResult
from app.experiments.repo import get_by_key
from app.experiments.service import ExperimentService


@dataclass
class ExperimentCapabilityService:
    default_config_path: Path = Path("backend/data/experiments/experiment_config.json")
    default_output_path: Path | None = None
    default_experiments_path: Path = Path("backend/data/experiments/experiments.jsonl")
    default_assignments_path: Path = Path("backend/data/experiments/assignments.jsonl")
    default_results_path: Path = Path("backend/data/experiments/results.jsonl")

    def generate(self, data: ExperimentCapabilityInput) -> ExperimentCapabilityResult:
        try:
            return self._generate(data)
        except Exception:  # noqa: BLE001
            result = self._fallback_result()
            self._persist(result.experiment_plan, data.output_path or self.default_output_path)
            return result

    def _generate(self, data: ExperimentCapabilityInput) -> ExperimentCapabilityResult:
        eligibility = self._evaluate_eligibility(data)
        decision_trace = self._build_decision_trace(data=data, eligibility=eligibility)
        if not bool(eligibility["allowed"]):
            return self._policy_default_result(
                reason=str(eligibility["reason"] or "EXPERIMENT_INELIGIBLE"),
                trace=eligibility,
                decision_trace=decision_trace,
            )

        config_path = data.config_path or self.default_config_path
        if not config_path.exists():
            result = self._fallback_result(decision_trace=decision_trace, config_path=config_path)
            self._persist(result.experiment_plan, data.output_path or self.default_output_path)
            return result

        config = json.loads(config_path.read_text(encoding="utf-8"))
        service = ExperimentService(
            experiments_path=self.default_experiments_path,
            assignments_path=self.default_assignments_path,
            results_path=self.default_results_path,
        )
        experiment, _ = service.create_experiment(
            name=str(config.get("name") or "creative_pack_baseline"),
            scope=str(config.get("scope") or "CREATIVE_PACK"),
            variant_a=dict(config.get("variant_a") or {"variant_type": "baseline", "hook_style": "question"}),
            variant_b=dict(config.get("variant_b") or {"variant_type": "baseline", "hook_style": "story_opening"}),
            status=str(config.get("status") or "ACTIVE"),
        )
        subject_key = f"{data.account_id}|{data.publish_slot}|{data.topic}".strip()
        assignment, _ = service.assign(experiment=experiment, subject_key=subject_key)
        variant_id, payload = service.resolve_variant_payload(experiment=experiment, subject_key=subject_key)
        payload = self._apply_safe_envelope(payload=payload, envelope=str(eligibility["envelope"] or "standard"))
        plan = ExperimentPlan(
            experiment_id=experiment.experiment_id,
            variant_id=variant_id,
            variant_type=str(payload.get("variant_type") or experiment.scope.lower()),
            variant_params=payload,
            fallback_used=False,
        )
        self._persist(plan, data.output_path or self.default_output_path)
        return ExperimentCapabilityResult(
            experiment_plan=plan,
            experiment_assignment=ExperimentAssignment(
                assignment_id=assignment.assignment_id,
                experiment_id=assignment.experiment_id,
                subject_key=assignment.subject_key,
                variant_id=assignment.variant,
                assigned_at=assignment.assigned_at,
            ),
            fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
            decision_trace={
                **decision_trace,
                "config_path": str(config_path),
                "config_exists": True,
                "assignment_path_used": "framework_assign",
                "variant_resolution_source": "framework_assignment",
                "subject_key": subject_key,
            },
            experiment_trace={
                "eligibility_allowed": True,
                "eligibility_reason": str(eligibility["reason"] or ""),
                "eligibility_envelope": str(eligibility["envelope"] or "standard"),
                "assignment_recorded": True,
                "assignment_action": "WRITTEN",
                "subject_key": assignment.subject_key,
                "assignment_id": assignment.assignment_id,
                "experiment_id": assignment.experiment_id,
                "variant_id": assignment.variant,
                "assigned_at": assignment.assigned_at,
            },
        )

    def _fallback_result(
        self,
        *,
        decision_trace: dict[str, Any] | None = None,
        config_path: Path | None = None,
    ) -> ExperimentCapabilityResult:
        return ExperimentCapabilityResult(
            experiment_plan=ExperimentPlan(
                experiment_id="exp_default",
                variant_id="A",
                variant_type="baseline",
                variant_params={},
                fallback_used=True,
            ),
            experiment_assignment=None,
            fallback=FallbackDecision(
                used=True,
                mode=FallbackMode.SAFE_DEFAULT.value,
                reason="EXPERIMENT_PLAN_FALLBACK",
            ),
            decision_trace={
                **(decision_trace or {}),
                "config_path": "" if config_path is None else str(config_path),
                "config_exists": False if config_path is not None else None,
                "assignment_path_used": "none_fallback",
                "variant_resolution_source": "fallback_default",
                "subject_key": None,
            },
            experiment_trace={
                "eligibility_allowed": True,
                "eligibility_reason": "CONFIG_MISSING_FALLBACK",
                "eligibility_envelope": "conservative",
                "assignment_recorded": False,
                "result_recorded": False,
                "fallback_reason": "EXPERIMENT_PLAN_FALLBACK",
            },
        )

    def record_runtime_result(
        self,
        *,
        result: ExperimentCapabilityResult,
        window_id: str,
        metrics: dict[str, Any],
        recorded_at: str | None = None,
    ) -> tuple[dict[str, Any] | None, str]:
        assignment = result.experiment_assignment
        if assignment is None:
            return None, "SKIPPED_NO_ASSIGNMENT"
        experiment_record = get_by_key(
            "experiment_id",
            assignment.experiment_id,
            path=self.default_experiments_path,
        )
        if experiment_record is None:
            return None, "SKIPPED_EXPERIMENT_NOT_FOUND"
        service = ExperimentService(
            experiments_path=self.default_experiments_path,
            assignments_path=self.default_assignments_path,
            results_path=self.default_results_path,
        )
        experiment_result, action = service.record_result(
            experiment=experiment_record,
            subject_key=assignment.subject_key,
            window_id=window_id,
            metrics=metrics,
            recorded_at=recorded_at,
        )
        return experiment_result.to_dict(), action

    def _evaluate_eligibility(self, data: ExperimentCapabilityInput) -> dict[str, Any]:
        health_status = str(data.account_health_status or "SAFE").upper()
        novelty_pressure = str(data.novelty_pressure_level or "low").lower()
        hold_or_reject_rate = float(data.recent_hold_or_reject_rate or 0.0)
        avg_overall_score = float(data.recent_avg_overall_score or 0.0)

        if health_status == "HOLD":
            return {
                "allowed": False,
                "reason": "ACCOUNT_HEALTH_HOLD",
                "envelope": "blocked",
            }
        if novelty_pressure in {"medium", "high"}:
            return {
                "allowed": True,
                "reason": "NOVELTY_PRESSURE_ALLOW",
                "envelope": "standard",
            }
        if hold_or_reject_rate >= 0.4 or (0.0 < avg_overall_score < 0.82):
            return {
                "allowed": True,
                "reason": "QUALITY_UNSTABLE_CONSERVATIVE_ALLOW",
                "envelope": "conservative",
            }
        return {
            "allowed": True,
            "reason": "DEFAULT_CONSERVATIVE_ALLOW",
            "envelope": "conservative",
        }

    def _policy_default_result(
        self,
        *,
        reason: str,
        trace: dict[str, Any],
        decision_trace: dict[str, Any],
    ) -> ExperimentCapabilityResult:
        return ExperimentCapabilityResult(
            experiment_plan=ExperimentPlan(
                experiment_id="exp_policy_default",
                variant_id="A",
                variant_type="baseline",
                variant_params={},
                fallback_used=False,
            ),
            experiment_assignment=None,
            fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
            decision_trace={
                **decision_trace,
                "config_path": None,
                "config_exists": None,
                "assignment_path_used": "none_policy_blocked",
                "variant_resolution_source": "policy_default",
                "subject_key": None,
            },
            experiment_trace={
                "eligibility_allowed": False,
                "eligibility_reason": reason,
                "eligibility_envelope": str(trace.get("envelope") or "blocked"),
                "assignment_recorded": False,
                "result_recorded": False,
            },
        )

    def _build_decision_trace(
        self,
        *,
        data: ExperimentCapabilityInput,
        eligibility: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "account_health_status": str(data.account_health_status or "SAFE").upper(),
            "novelty_pressure_level": str(data.novelty_pressure_level or "low").lower(),
            "recent_hold_or_reject_rate": float(data.recent_hold_or_reject_rate or 0.0),
            "recent_avg_overall_score": float(data.recent_avg_overall_score or 0.0),
            "eligibility_allowed": bool(eligibility.get("allowed")),
            "eligibility_reason": str(eligibility.get("reason") or ""),
            "eligibility_envelope": str(eligibility.get("envelope") or ""),
            "publish_slot": str(data.publish_slot or ""),
            "topic": str(data.topic or ""),
        }

    def _apply_safe_envelope(self, *, payload: dict[str, Any], envelope: str) -> dict[str, Any]:
        normalized_envelope = str(envelope or "standard").lower()
        if normalized_envelope != "conservative":
            return dict(payload)
        constrained: dict[str, Any] = {}
        for key in ("variant_type", "hook_style", "narrative_mode"):
            if key in payload:
                constrained[key] = payload[key]
        constrained.setdefault("variant_type", str(payload.get("variant_type") or "baseline"))
        return constrained

    def _persist(self, plan: ExperimentPlan, output_path: Path | None) -> None:
        if output_path is None:
            return
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")
