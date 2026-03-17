from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import ExperimentPlan
from app.creative.experiments.models import ExperimentCapabilityInput, ExperimentCapabilityResult
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
        config_path = data.config_path or self.default_config_path
        if not config_path.exists():
            result = self._fallback_result()
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
        variant_id, payload = service.resolve_variant_payload(experiment=experiment, subject_key=subject_key)
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
            fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
        )

    def _fallback_result(self) -> ExperimentCapabilityResult:
        return ExperimentCapabilityResult(
            experiment_plan=ExperimentPlan(
                experiment_id="exp_default",
                variant_id="A",
                variant_type="baseline",
                variant_params={},
                fallback_used=True,
            ),
            fallback=FallbackDecision(
                used=True,
                mode=FallbackMode.SAFE_DEFAULT.value,
                reason="EXPERIMENT_PLAN_FALLBACK",
            ),
        )

    def _persist(self, plan: ExperimentPlan, output_path: Path | None) -> None:
        if output_path is None:
            return
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")
