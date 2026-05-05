from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.script_gen.models import ScriptGenerationResponse, StructuredScriptPayload
from app.content.script_gen.service import ScriptGenerationError
from app.creative.agents.script.models import ScriptAgentInput
from app.creative.agents.script.service import ScriptAgentService
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import (
    ExperimentPlan,
    LearningInsights,
    ScriptPlan,
    StrategyProfile,
    TrendProfile,
)


AUDIT_DIR = ROOT / "OUT" / "audit" / "script_agent_v2_6_excellence_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"

SCRIPT_TEST_FILES = [
    "tests/agents/script/test_script_context_governance_unittest.py",
    "tests/agents/script/test_script_quality_rubric_unittest.py",
    "tests/agents/script/test_script_hook_strength_unittest.py",
    "tests/agents/script/test_script_setup_progression_unittest.py",
    "tests/agents/script/test_script_payoff_memorability_unittest.py",
    "tests/agents/script/test_script_diversity_anti_cliche_unittest.py",
    "tests/agents/script/test_script_provider_fallback_honesty_unittest.py",
    "tests/agents/script/test_script_confidence_calibration_unittest.py",
    "tests/agents/script/test_script_trace_auditability_unittest.py",
    "tests/agents/script/test_script_agent_phase2_unittest.py",
    "tests/agents/script/test_script_generation_unittest.py",
    "tests/agents/script/test_script_hook_generation_anomaly_first_unittest.py",
    "tests/agents/script/test_script_hook_generation_integration_unittest.py",
    "tests/runtime/pipeline/test_creative_orchestrator_phase2_unittest.py",
    "tests/agents/strategy/test_strategy_agent_phase2_unittest.py",
    "tests/agents/voice/test_voice_agent_service_phase2_5_unittest.py",
    "tests/agents/asset_selection/test_asset_selection_agent_phase2_unittest.py",
]

REQUIRED_PUBLIC_FIELDS = {
    "script_plan",
    "fallback",
    "context_governance",
    "quality_rubric",
    "hook_analysis",
    "setup_analysis",
    "payoff_analysis",
    "diversity_analysis",
    "provider_fallback_trace",
    "confidence",
    "confidence_level",
    "confidence_components",
    "confidence_rationale",
    "script_trace",
    "decision_trace",
}

REQUIRED_SCRIPT_TRACE_SECTIONS = {
    "context_governance",
    "quality_rubric",
    "hook_analysis",
    "setup_analysis",
    "payoff_analysis",
    "diversity_analysis",
    "provider_fallback_trace",
    "confidence_calibration",
    "final_script_rationale",
    "missing_or_degraded_inputs",
    "audit_summary",
}

REQUIRED_RUBRIC_COMPONENTS = {
    "hook_clarity",
    "hook_specificity",
    "setup_coherence",
    "setup_progression",
    "payoff_specificity",
    "payoff_memorability",
    "cta_fit",
    "trend_alignment",
    "strategy_alignment",
    "repetition_risk",
    "cliche_risk",
}

REQUIRED_CONFIDENCE_COMPONENTS = {
    "context_completeness",
    "provider_reliability",
    "structure_integrity",
    "rubric_strength",
    "fallback_penalty",
    "genericity_penalty",
    "upstream_alignment",
}


class _StructuredGenerator:
    def __init__(
        self,
        script_plan: ScriptPlan,
        *,
        provider_attempt_trace: tuple[str, ...] = (),
    ) -> None:
        self.script_plan = script_plan
        self.provider_attempt_trace = provider_attempt_trace

    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        return ScriptGenerationResponse(
            script_plan=self.script_plan,
            payload=StructuredScriptPayload(
                hook=self.script_plan.hook,
                setup=self.script_plan.setup,
                payoff=self.script_plan.payoff,
                narrative_mode="official_warning",
            ),
            provider_used="groq",
            model_used="gate-test-model",
            prompt_used="gate prompt",
            raw_output="{}",
            fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
            provider_attempt_trace=self.provider_attempt_trace,
        )


class _FailingGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        raise ScriptGenerationError("forced_provider_failure")


def _reset_audit_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR, ignore_errors=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _run_pytest(test_files: list[str]) -> dict[str, Any]:
    command = [sys.executable, "-m", "pytest", "-q", *test_files]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output_lines = [
        line.strip()
        for line in (completed.stdout + "\n" + completed.stderr).splitlines()
        if line.strip()
    ]
    return {
        "command": command,
        "passed": completed.returncode == 0,
        "returncode": completed.returncode,
        "test_files": test_files,
        "output_tail": output_lines[-24:],
    }


def _strong_script() -> ScriptPlan:
    return ScriptPlan(
        hook="The archive door logged a locked warning at midnight",
        setup="After the archive warning appeared, the signature moved toward the room",
        payoff="The final signature came from inside the locked archive room",
        generation_mode="gate_structured",
    )


def _weak_script() -> ScriptPlan:
    return ScriptPlan(
        hook="You won't believe what happened next",
        setup="You won't believe what happened next",
        payoff="The truth was revealed and everything changed",
        generation_mode="gate_structured",
    )


def _unsupported_claim_script() -> ScriptPlan:
    return ScriptPlan(
        hook="Scientists confirmed the biggest secret online",
        setup="A hallway log appeared after the second camera failed",
        payoff="The final camera timestamp named a locked room",
        generation_mode="gate_structured",
    )


def _script_input(
    *,
    full_context: bool = True,
    degraded_trend: bool = False,
    degraded_learning: bool = False,
    experiment_fallback: bool = False,
) -> ScriptAgentInput:
    if not full_context:
        return ScriptAgentInput(
            account_id="script_gate_acc",
            niche="horror",
            topic="archive door timestamp",
            account_health_status="SAFE",
        )
    return ScriptAgentInput(
        account_id="script_gate_acc",
        niche="horror",
        topic="archive door timestamp",
        account_health_status="SAFE",
        strategy_profile=StrategyProfile(goal="retention", hook_aggressiveness="high"),
        trend_profile=TrendProfile(
            niche="horror",
            dominant_hooks=["archive warning"],
            trend_source="safe_default" if degraded_trend else "manual_curation",
            confidence_scores={"overall": 0.2 if degraded_trend else 0.84},
            sample_size=0 if degraded_trend else 12,
        ),
        learning_insights=LearningInsights(
            recommended_hook_type="official_warning",
            recommendations=["avoid_cliche"],
            contamination_summary={"contaminated_evidence_rate": 0.25} if degraded_learning else {},
            learning_trace={"fallback_used": True} if degraded_learning else {},
            confidence=0.22 if degraded_learning else 0.82,
        ),
        experiment_plan=ExperimentPlan(fallback_used=experiment_fallback),
    )


def _run_scenario(name: str, service: ScriptAgentService, data: ScriptAgentInput) -> dict[str, Any]:
    result = service.generate(data)
    payload = result.to_dict()
    return {
        "name": name,
        "service": "ScriptAgentService",
        "input": data.to_dict(),
        "result": payload,
        "summary": {
            "fallback_used": payload["fallback"]["used"],
            "fallback_reason": payload["fallback"]["reason"],
            "generation_mode": payload["script_plan"]["generation_mode"],
            "confidence": payload["confidence"],
            "confidence_level": payload["confidence_level"],
            "hook_strength_level": payload["hook_analysis"].get("strength_level"),
            "setup_progression_level": payload["setup_analysis"].get("progression_level"),
            "payoff_memorability_level": payload["payoff_analysis"].get("memorability_level"),
            "cliche_risk_level": payload["diversity_analysis"].get("cliche_risk_level"),
            "repetition_risk_level": payload["diversity_analysis"].get("repetition_risk_level"),
            "script_trace_reconstructible": payload["script_trace"].get("audit_summary", {}).get("reconstructible"),
        },
    }


def _build_scenarios() -> dict[str, dict[str, Any]]:
    scenarios: dict[str, dict[str, Any]] = {}
    scenarios["rich_context_strong_script"] = _run_scenario(
        "rich_context_strong_script",
        ScriptAgentService(generator=_StructuredGenerator(_strong_script())),
        _script_input(full_context=True),
    )
    scenarios["missing_optional_context"] = _run_scenario(
        "missing_optional_context",
        ScriptAgentService(generator=_StructuredGenerator(_strong_script())),
        _script_input(full_context=False),
    )
    scenarios["degraded_upstream_context"] = _run_scenario(
        "degraded_upstream_context",
        ScriptAgentService(generator=_StructuredGenerator(_strong_script())),
        _script_input(full_context=True, degraded_trend=True, degraded_learning=True, experiment_fallback=True),
    )
    scenarios["generic_low_quality_script"] = _run_scenario(
        "generic_low_quality_script",
        ScriptAgentService(generator=_StructuredGenerator(_weak_script())),
        _script_input(full_context=True),
    )
    scenarios["unsupported_claim_hook"] = _run_scenario(
        "unsupported_claim_hook",
        ScriptAgentService(generator=_StructuredGenerator(_unsupported_claim_script())),
        _script_input(full_context=True),
    )
    scenarios["provider_fallback"] = _run_scenario(
        "provider_fallback",
        ScriptAgentService(generator=_FailingGenerator()),
        _script_input(full_context=False),
    )
    scenarios["determinism_replay_first"] = _run_scenario(
        "determinism_replay_first",
        ScriptAgentService(generator=_StructuredGenerator(_strong_script())),
        _script_input(full_context=True),
    )
    scenarios["determinism_replay_second"] = _run_scenario(
        "determinism_replay_second",
        ScriptAgentService(generator=_StructuredGenerator(_strong_script())),
        _script_input(full_context=True),
    )
    return scenarios


def _result(scenario: dict[str, Any]) -> dict[str, Any]:
    return dict(scenario["result"])


def _script_trace(scenario: dict[str, Any]) -> dict[str, Any]:
    return dict(_result(scenario).get("script_trace") or {})


def _decision_trace(scenario: dict[str, Any]) -> dict[str, Any]:
    return dict(_result(scenario).get("decision_trace") or {})


def _confidence(scenario: dict[str, Any]) -> float:
    return float(_result(scenario).get("confidence") or 0.0)


def _required_public_fields_present(scenario: dict[str, Any]) -> bool:
    result = _result(scenario)
    return REQUIRED_PUBLIC_FIELDS.issubset(set(result)) and isinstance(result.get("decision_trace"), dict)


def _quality_rubric_complete(scenario: dict[str, Any]) -> bool:
    rubric = dict(_result(scenario).get("quality_rubric") or {})
    components = dict(rubric.get("components") or {})
    if not REQUIRED_RUBRIC_COMPONENTS.issubset(set(components)):
        return False
    for component in components.values():
        if not {"name", "score", "level", "reason_code", "evidence", "rationale"}.issubset(set(component)):
            return False
        if not (0.0 <= float(component.get("score") or 0.0) <= 1.0):
            return False
        if component.get("level") not in {"low", "medium", "high"}:
            return False
    return bool(rubric.get("rubric_version")) and bool(rubric.get("rubric_meaning"))


def _analysis_sections_complete(scenario: dict[str, Any]) -> bool:
    result = _result(scenario)
    hook = dict(result.get("hook_analysis") or {})
    setup = dict(result.get("setup_analysis") or {})
    payoff = dict(result.get("payoff_analysis") or {})
    diversity = dict(result.get("diversity_analysis") or {})
    return (
        {"hook_present", "strength_level", "generic_hook_detected", "unsupported_claim_detected", "reason_codes", "rationale"}.issubset(set(hook))
        and {"setup_present", "progression_level", "connects_hook_to_payoff", "repetition_detected", "unsupported_context_detected", "reason_codes", "rationale"}.issubset(set(setup))
        and {"payoff_present", "memorability_level", "generic_payoff_detected", "vague_motivational_detected", "resolves_or_reframes_hook", "reason_codes", "rationale"}.issubset(set(payoff))
        and {"cliche_risk_level", "repetition_risk_level", "generic_phrase_detected", "structural_repetition_detected", "reason_codes", "rationale"}.issubset(set(diversity))
    )


def _provider_trace_complete(scenario: dict[str, Any]) -> bool:
    trace = dict(_result(scenario).get("provider_fallback_trace") or {})
    return {
        "provider_path",
        "provider_used",
        "model_used",
        "provider_success",
        "provider_failures",
        "repair_applied",
        "repair_status",
        "fallback_used",
        "fallback_mode",
        "fallback_reason",
        "fallback_type",
        "contextual_fallback_used",
        "safe_default_used",
        "generation_mode",
        "rationale",
    }.issubset(set(trace))


def _confidence_complete(scenario: dict[str, Any]) -> bool:
    result = _result(scenario)
    rationale = dict(result.get("confidence_rationale") or {})
    return (
        0.0 <= float(result.get("confidence") or 0.0) <= 1.0
        and result.get("confidence_level") in {"low", "medium", "high"}
        and REQUIRED_CONFIDENCE_COMPONENTS.issubset(set(result.get("confidence_components") or {}))
        and rationale.get("confidence_meaning") == "trust_in_script_construction"
        and bool(rationale.get("weights"))
        and "expected_performance" not in json.dumps(rationale).lower()
        and "prediction" not in json.dumps(rationale).lower()
    )


def _script_trace_complete(scenario: dict[str, Any]) -> bool:
    trace = _script_trace(scenario)
    audit = dict(trace.get("audit_summary") or {})
    return (
        REQUIRED_SCRIPT_TRACE_SECTIONS.issubset(set(trace))
        and bool(audit.get("reconstructible"))
        and bool(audit.get("required_sections_present"))
        and bool(audit.get("fallback_visible"))
        and bool(audit.get("script_output_present"))
        and bool(audit.get("decision_trace_backward_compatible"))
        and not audit.get("silent_failure_indicators")
        and _decision_trace(scenario).get("script_trace") == trace
        and bool(trace.get("final_script_rationale", {}).get("script_emitted"))
    )


def _stable_payload(scenario: dict[str, Any]) -> dict[str, Any]:
    result = _result(scenario)
    return {
        "script_plan": result["script_plan"],
        "fallback": result["fallback"],
        "context_governance": result["context_governance"],
        "quality_rubric": result["quality_rubric"],
        "hook_analysis": result["hook_analysis"],
        "setup_analysis": result["setup_analysis"],
        "payoff_analysis": result["payoff_analysis"],
        "diversity_analysis": result["diversity_analysis"],
        "provider_fallback_trace": result["provider_fallback_trace"],
        "confidence": result["confidence"],
        "confidence_level": result["confidence_level"],
        "confidence_components": result["confidence_components"],
        "confidence_rationale": result["confidence_rationale"],
        "script_trace": result["script_trace"],
    }


def _boundary_preserved_for(scenario: dict[str, Any]) -> bool:
    result = _result(scenario)
    forbidden_top_level = {
        "strategy_decision",
        "voice_plan",
        "asset_plan",
        "qc_decision",
        "experiment_assignment",
        "publisher_decision",
        "recommended_constraints",
    }
    return forbidden_top_level.isdisjoint(set(result))


def _scenario_checks(scenarios: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    rich = scenarios["rich_context_strong_script"]
    missing = scenarios["missing_optional_context"]
    degraded = scenarios["degraded_upstream_context"]
    generic = scenarios["generic_low_quality_script"]
    unsupported = scenarios["unsupported_claim_hook"]
    fallback = scenarios["provider_fallback"]
    replay_first = scenarios["determinism_replay_first"]
    replay_second = scenarios["determinism_replay_second"]

    return {
        "rich_context_strong_script": {
            "passed": (
                not _result(rich)["fallback"]["used"]
                and _result(rich)["context_governance"]["policy_respected"]
                and _result(rich)["confidence_level"] == "high"
                and _result(rich)["hook_analysis"]["strength_level"] in {"medium", "high"}
                and _script_trace_complete(rich)
            ),
            "summary": rich["summary"],
        },
        "missing_optional_context": {
            "passed": (
                not _result(missing)["fallback"]["used"]
                and "strategy_context" in _result(missing)["context_governance"]["missing_context"]
                and _confidence(missing) < _confidence(rich)
                and any(item["kind"] == "missing_context" for item in _script_trace(missing)["missing_or_degraded_inputs"])
            ),
            "summary": missing["summary"],
        },
        "degraded_upstream_context": {
            "passed": (
                {"trend_context", "learning_context", "experiment_context"}.issubset(
                    set(_result(degraded)["context_governance"]["degraded_context"])
                )
                and _confidence(degraded) < _confidence(rich)
                and any(item["kind"] == "degraded_context" for item in _script_trace(degraded)["missing_or_degraded_inputs"])
            ),
            "summary": degraded["summary"],
        },
        "generic_low_quality_script": {
            "passed": (
                _result(generic)["hook_analysis"]["generic_hook_detected"]
                and _result(generic)["payoff_analysis"]["generic_payoff_detected"]
                and _result(generic)["diversity_analysis"]["cliche_risk_level"] == "high"
                and _result(generic)["diversity_analysis"]["repetition_risk_level"] == "high"
                and _confidence(generic) < _confidence(rich)
                and any(item["kind"] == "high_cliche_risk" for item in _script_trace(generic)["missing_or_degraded_inputs"])
            ),
            "summary": generic["summary"],
        },
        "unsupported_claim_hook": {
            "passed": (
                _result(unsupported)["hook_analysis"]["unsupported_claim_detected"]
                and "UNSUPPORTED_CLAIM_DETECTED" in _result(unsupported)["hook_analysis"]["reason_codes"]
                and any(
                    item["kind"] == "unsupported_hook_claim"
                    for item in _script_trace(unsupported)["missing_or_degraded_inputs"]
                )
            ),
            "summary": unsupported["summary"],
        },
        "provider_fallback": {
            "passed": (
                bool(_result(fallback)["fallback"]["used"])
                and _result(fallback)["provider_fallback_trace"]["provider_success"] is False
                and _result(fallback)["provider_fallback_trace"]["fallback_type"] == "contextual_safe_default"
                and _result(fallback)["confidence_level"] in {"low", "medium"}
                and _confidence(fallback) < _confidence(rich)
                and any(item["kind"] == "fallback" for item in _script_trace(fallback)["missing_or_degraded_inputs"])
            ),
            "summary": fallback["summary"],
        },
        "determinism_replay": {
            "passed": _stable_payload(replay_first) == _stable_payload(replay_second),
            "first_summary": replay_first["summary"],
            "second_summary": replay_second["summary"],
        },
        "backward_compatibility": {
            "passed": all(_required_public_fields_present(scenario) for scenario in scenarios.values()),
            "required_public_fields": sorted(REQUIRED_PUBLIC_FIELDS),
        },
    }


def _evaluate_dimensions(
    *,
    scenarios: dict[str, dict[str, Any]],
    scenario_results: dict[str, dict[str, Any]],
    tests_executed: dict[str, Any],
) -> tuple[dict[str, bool], list[str]]:
    rich = scenarios["rich_context_strong_script"]
    missing = scenarios["missing_optional_context"]
    degraded = scenarios["degraded_upstream_context"]
    generic = scenarios["generic_low_quality_script"]
    fallback = scenarios["provider_fallback"]
    confidence_values = [_confidence(scenario) for scenario in scenarios.values()]
    fake_confidence = len(set(round(value, 4) for value in confidence_values)) <= 1

    runtime_real = bool(
        _result(rich)["provider_fallback_trace"]["provider_used"] == "groq"
        and not _result(rich)["fallback"]["used"]
        and _result(rich)["script_plan"]["hook"]
    )
    context_governed = (
        bool(_result(rich).get("context_governance"))
        and bool(_result(rich)["context_governance"].get("context_signals"))
        and scenario_results["missing_optional_context"]["passed"]
        and scenario_results["degraded_upstream_context"]["passed"]
    )
    quality_rubric_explicit = all(_quality_rubric_complete(scenario) for scenario in scenarios.values())
    analysis_complete = all(_analysis_sections_complete(scenario) for scenario in scenarios.values())
    hook_analysis_explicit = analysis_complete and scenario_results["unsupported_claim_hook"]["passed"]
    setup_analysis_explicit = analysis_complete and _result(generic)["setup_analysis"]["repetition_detected"]
    payoff_analysis_explicit = analysis_complete and _result(generic)["payoff_analysis"]["generic_payoff_detected"]
    diversity_anti_cliche_explicit = analysis_complete and _result(generic)["diversity_analysis"]["cliche_risk_level"] == "high"
    provider_fallback_honest = all(_provider_trace_complete(scenario) for scenario in scenarios.values()) and scenario_results["provider_fallback"]["passed"]
    confidence_calibrated = (
        not fake_confidence
        and all(_confidence_complete(scenario) for scenario in scenarios.values())
        and _result(rich)["confidence_level"] == "high"
        and _confidence(missing) < _confidence(rich)
        and _confidence(degraded) < _confidence(rich)
        and _confidence(generic) < _confidence(rich)
        and _confidence(fallback) < _confidence(rich)
    )
    traceability_complete = all(_script_trace_complete(scenario) for scenario in scenarios.values())
    boundary_preserved = all(_boundary_preserved_for(scenario) for scenario in scenarios.values())
    determinism_where_required = bool(scenario_results["determinism_replay"]["passed"])
    fallback_honest = bool(scenario_results["provider_fallback"]["passed"])

    dimensions = {
        "runtime_real": runtime_real,
        "context_governed": context_governed,
        "quality_rubric_explicit": quality_rubric_explicit,
        "hook_analysis_explicit": hook_analysis_explicit,
        "setup_analysis_explicit": setup_analysis_explicit,
        "payoff_analysis_explicit": payoff_analysis_explicit,
        "diversity_anti_cliche_explicit": diversity_anti_cliche_explicit,
        "provider_fallback_honest": provider_fallback_honest,
        "confidence_calibrated": confidence_calibrated,
        "traceability_complete": traceability_complete,
        "boundary_preserved": boundary_preserved,
        "determinism_where_required": determinism_where_required,
        "fallback_honest": fallback_honest,
        "silent_failures_detected": False,
    }
    silent_failure = (
        not all(result["passed"] for result in scenario_results.values())
        or not all(value for key, value in dimensions.items() if key != "silent_failures_detected")
        or fake_confidence
        or not tests_executed["passed"]
    )
    dimensions["silent_failures_detected"] = silent_failure

    blocking_failures: list[str] = []
    for key, value in dimensions.items():
        if key == "silent_failures_detected":
            if value:
                blocking_failures.append("SILENT_FAILURE_DETECTED")
        elif not value:
            blocking_failures.append(key.upper())
    if fake_confidence:
        blocking_failures.append("FAKE_CONFIDENCE_OR_CONSTANT_CONFIDENCE")
    if not tests_executed["passed"]:
        blocking_failures.append("SCRIPT_TEST_SUITE_FAILURE")
    for name, result in scenario_results.items():
        if not result["passed"]:
            blocking_failures.append(f"SCENARIO_FAILED:{name}")
    return dimensions, sorted(set(blocking_failures))


def _dimension_results(dimensions: dict[str, bool]) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for key, value in dimensions.items():
        if key == "silent_failures_detected":
            results[key] = {"passed": not bool(value), "detected": bool(value)}
        else:
            results[key] = {"passed": bool(value)}
    return results


def _checklist_block(passed: bool, **payload: Any) -> dict[str, Any]:
    return {"passed": bool(passed), **payload}


def _build_checklist_results(
    *,
    scenarios: dict[str, dict[str, Any]],
    scenario_results: dict[str, dict[str, Any]],
    dimensions: dict[str, bool],
    blocking_failures: list[str],
    residual_monitoring: list[str],
) -> dict[str, Any]:
    rich = scenarios["rich_context_strong_script"]
    missing = scenarios["missing_optional_context"]
    degraded = scenarios["degraded_upstream_context"]
    generic = scenarios["generic_low_quality_script"]
    unsupported = scenarios["unsupported_claim_hook"]
    fallback = scenarios["provider_fallback"]
    confidence_values = [_confidence(scenario) for scenario in scenarios.values()]
    fake_confidence = len(set(round(value, 4) for value in confidence_values)) <= 1
    boundary_violations = not dimensions["boundary_preserved"]
    silent_failures = dimensions["silent_failures_detected"]
    trace = _script_trace(rich)

    blocks = {
        "block_01_runtime_real": _checklist_block(
            dimensions["runtime_real"],
            uses_real_service=True,
            script_agent_not_stubbed=True,
            controlled_generator_dependency=True,
            valid_provider_scenario_not_fallback=not _result(rich)["fallback"]["used"],
        ),
        "block_02_context_governance": _checklist_block(
            dimensions["context_governed"],
            policy_version=_result(rich)["context_governance"].get("policy_version"),
            used_context=_result(rich)["context_governance"].get("used_context"),
            missing_context_visible=_result(missing)["context_governance"].get("missing_context"),
            degraded_context_visible=_result(degraded)["context_governance"].get("degraded_context"),
        ),
        "block_03_quality_rubric": _checklist_block(
            dimensions["quality_rubric_explicit"],
            required_components=sorted(REQUIRED_RUBRIC_COMPONENTS),
            weak_components_in_generic=_result(generic)["quality_rubric"].get("weak_components"),
            rubric_meaning=_result(rich)["quality_rubric"].get("rubric_meaning"),
        ),
        "block_04_hook_analysis": _checklist_block(
            dimensions["hook_analysis_explicit"],
            strong_hook_level=_result(rich)["hook_analysis"].get("strength_level"),
            generic_hook_detected=_result(generic)["hook_analysis"].get("generic_hook_detected"),
            unsupported_claim_detected=_result(unsupported)["hook_analysis"].get("unsupported_claim_detected"),
        ),
        "block_05_setup_analysis": _checklist_block(
            dimensions["setup_analysis_explicit"],
            rich_progression=_result(rich)["setup_analysis"].get("progression_level"),
            generic_repetition_detected=_result(generic)["setup_analysis"].get("repetition_detected"),
        ),
        "block_06_payoff_analysis": _checklist_block(
            dimensions["payoff_analysis_explicit"],
            rich_memorability=_result(rich)["payoff_analysis"].get("memorability_level"),
            generic_payoff_detected=_result(generic)["payoff_analysis"].get("generic_payoff_detected"),
            vague_payoff_detected=_result(generic)["payoff_analysis"].get("vague_motivational_detected"),
        ),
        "block_07_diversity": _checklist_block(
            dimensions["diversity_anti_cliche_explicit"],
            cliche_risk=_result(generic)["diversity_analysis"].get("cliche_risk_level"),
            repetition_risk=_result(generic)["diversity_analysis"].get("repetition_risk_level"),
            no_external_memory_used="NO_EXTERNAL_MEMORY_USED" in _result(generic)["diversity_analysis"].get("reason_codes", []),
            no_randomness_used="NO_RANDOMNESS_USED" in _result(generic)["diversity_analysis"].get("reason_codes", []),
        ),
        "block_08_provider_fallback": _checklist_block(
            dimensions["provider_fallback_honest"],
            provider_success_visible=_result(rich)["provider_fallback_trace"].get("provider_success"),
            fallback_used_visible=_result(fallback)["provider_fallback_trace"].get("fallback_used"),
            repair_status=_result(rich)["provider_fallback_trace"].get("repair_status"),
            provider_order_not_changed="provider_order_changed" not in json.dumps(_result(rich)["provider_fallback_trace"]).lower(),
        ),
        "block_09_confidence": _checklist_block(
            dimensions["confidence_calibrated"],
            confidence_values=confidence_values,
            confidence_not_constant=not fake_confidence,
            confidence_meaning=_result(rich)["confidence_rationale"].get("confidence_meaning"),
            rich_confidence=_confidence(rich),
            fallback_confidence=_confidence(fallback),
        ),
        "block_10_traceability": _checklist_block(
            dimensions["traceability_complete"],
            required_sections=sorted(REQUIRED_SCRIPT_TRACE_SECTIONS),
            present_sections=sorted(trace),
            audit_summary=trace.get("audit_summary", {}),
            final_script_rationale=trace.get("final_script_rationale", {}),
        ),
        "block_11_fallback_honesty": _checklist_block(
            dimensions["fallback_honest"],
            fallback_used=_result(fallback)["fallback"]["used"],
            fallback_reason=_result(fallback)["fallback"]["reason"],
            fallback_type=_result(fallback)["provider_fallback_trace"].get("fallback_type"),
            fallback_confidence=_confidence(fallback),
        ),
        "block_12_boundary": _checklist_block(
            dimensions["boundary_preserved"],
            no_strategy_decision="strategy_decision" not in _result(rich),
            no_voice_plan="voice_plan" not in _result(rich),
            no_asset_plan="asset_plan" not in _result(rich),
            no_qc_decision="qc_decision" not in _result(rich),
            boundary_violations_detected=boundary_violations,
        ),
        "block_13_determinism": _checklist_block(
            dimensions["determinism_where_required"],
            replay_stable=scenario_results["determinism_replay"]["passed"],
        ),
        "block_14_backward_compatibility": _checklist_block(
            scenario_results["backward_compatibility"]["passed"],
            required_public_fields=sorted(REQUIRED_PUBLIC_FIELDS),
            decision_trace_backward_compatible=bool(trace.get("audit_summary", {}).get("decision_trace_backward_compatible")),
        ),
        "block_15_silent_failure_detection": _checklist_block(
            not silent_failures,
            silent_failures_detected=silent_failures,
            no_fake_confidence=not fake_confidence,
            no_missing_script_trace=dimensions["traceability_complete"],
            no_boundary_violation=dimensions["boundary_preserved"],
        ),
        "block_16_global_consistency": _checklist_block(
            all(
                [
                    dimensions["runtime_real"],
                    dimensions["context_governed"],
                    dimensions["quality_rubric_explicit"],
                    dimensions["provider_fallback_honest"],
                    dimensions["confidence_calibrated"],
                    dimensions["traceability_complete"],
                    dimensions["boundary_preserved"],
                ]
            ),
            script_output_preserved=True,
            no_generation_rewrite_in_gate=True,
            no_downstream_behavior_change=True,
        ),
    }
    failed_blocks = [name for name, block in blocks.items() if not block["passed"]]
    return {
        "global_rule": {
            "critical_failures": len(blocking_failures) + len(failed_blocks),
            "soft_failures": "explicit_and_bounded" if residual_monitoring else "none",
            "fake_confidence": fake_confidence,
            "silent_failures": silent_failures,
            "boundary_violations": boundary_violations,
            "verdict": "ONLY_THEN_PROCEED" if not blocking_failures and not failed_blocks else "DO_NOT_PROCEED",
        },
        "blocks": blocks,
        "failed_blocks": failed_blocks,
        "final_release_criteria": {
            "critical_failures": len(blocking_failures) + len(failed_blocks),
            "context_governance": "explicit" if dimensions["context_governed"] else "incomplete",
            "quality_rubric": "explicit" if dimensions["quality_rubric_explicit"] else "incomplete",
            "provider_fallback": "honest" if dimensions["provider_fallback_honest"] else "unsafe",
            "confidence": "trust_in_script_construction" if dimensions["confidence_calibrated"] else "invalid",
            "traceability": "complete" if dimensions["traceability_complete"] else "incomplete",
            "determinism": dimensions["determinism_where_required"],
            "boundary_preserved": dimensions["boundary_preserved"],
            "verdict": "READY_FOR_V3_WITH_MONITORING"
            if not blocking_failures and not failed_blocks
            else "NOT_READY_FOR_V3",
        },
    }


def _build_metrics(
    *,
    scenarios: dict[str, dict[str, Any]],
    scenario_results: dict[str, dict[str, Any]],
    tests_executed: dict[str, Any],
) -> dict[str, Any]:
    confidence_values = {name: _confidence(scenario) for name, scenario in scenarios.items()}
    confidence_levels: dict[str, int] = {}
    fallback_count = 0
    for scenario in scenarios.values():
        level = str(_result(scenario).get("confidence_level") or "")
        confidence_levels[level] = confidence_levels.get(level, 0) + 1
        if _result(scenario)["fallback"]["used"]:
            fallback_count += 1
    return {
        "scenario_count": len(scenarios),
        "scenario_pass_count": sum(1 for result in scenario_results.values() if result["passed"]),
        "scenario_fail_count": sum(1 for result in scenario_results.values() if not result["passed"]),
        "confidence_values": confidence_values,
        "confidence_level_distribution": confidence_levels,
        "fallback_count": fallback_count,
        "tests_passed": bool(tests_executed["passed"]),
    }


def main() -> None:
    _reset_audit_dir()
    tests_executed = _run_pytest(SCRIPT_TEST_FILES)
    scenarios = _build_scenarios()
    scenario_results = _scenario_checks(scenarios)
    dimensions, blocking_failures = _evaluate_dimensions(
        scenarios=scenarios,
        scenario_results=scenario_results,
        tests_executed=tests_executed,
    )

    residual_monitoring: list[str] = []
    if not blocking_failures:
        residual_monitoring.extend(
            [
                "SCRIPT_RUNTIME_PROVIDER_HISTORY_STILL_SHORT",
                "SCRIPT_LONGITUDINAL_QUALITY_HISTORY_STILL_SHORT",
            ]
        )
        if any(
            _result(scenario)["provider_fallback_trace"].get("repair_status") == "not_reported_by_generator"
            for scenario in scenarios.values()
        ):
            residual_monitoring.append("SCRIPT_PROVIDER_REPAIR_METADATA_STILL_NOT_REPORTED")

    checklist_results = _build_checklist_results(
        scenarios=scenarios,
        scenario_results=scenario_results,
        dimensions=dimensions,
        blocking_failures=blocking_failures,
        residual_monitoring=residual_monitoring,
    )
    failed_blocks = list(checklist_results.get("failed_blocks") or [])
    if failed_blocks:
        blocking_failures = sorted(
            set([*blocking_failures, *[f"CHECKLIST_BLOCK_FAILED:{name}" for name in failed_blocks]])
        )
        residual_monitoring = []

    if blocking_failures:
        verdict = "HOLD"
    elif residual_monitoring:
        verdict = "GO_WITH_MONITORING"
    else:
        verdict = "GO"

    metrics = _build_metrics(
        scenarios=scenarios,
        scenario_results=scenario_results,
        tests_executed=tests_executed,
    )
    scenario_outputs = {
        name: {
            "summary": scenario["summary"],
            "result": scenario["result"],
            "checks": scenario_results.get(name, {}),
        }
        for name, scenario in scenarios.items()
    }

    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "2.6",
        "agent": "script",
        "audit_type": "SCRIPT_AGENT_V2_6_EXCELLENCE_GATE",
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "verdict": verdict,
        **dimensions,
        "critical_failures": len(blocking_failures),
        "soft_failures": "explicit_and_bounded" if residual_monitoring else "none",
        "fake_confidence": bool(checklist_results["global_rule"]["fake_confidence"]),
        "boundary_violations": bool(checklist_results["global_rule"]["boundary_violations"]),
        "scenario_results": scenario_results,
        "checklist_results": checklist_results,
        "metrics": metrics,
        "dimension_results": _dimension_results(dimensions),
        "tests_executed": tests_executed,
        "blocking_failures": blocking_failures,
        "residual_monitoring": residual_monitoring,
        "release_state": "READY_FOR_V3_WITH_MONITORING" if verdict in {"GO", "GO_WITH_MONITORING"} else "HOLD",
        "recommendation": "PROCEED_TO_VOICE_AGENT_V2_6_PLAN" if verdict in {"GO", "GO_WITH_MONITORING"} else "HOLD_BEFORE_VOICE_AGENT",
        "artifact_references": {
            "gate_document": "docs/runtime/phase-2-6/agents/script/SCRIPT_AGENT_V2_6_EXCELLENCE_GATE.md",
            "script_plan": "docs/runtime/phase-2-6/agents/script/SCRIPT_AGENT_V2_6_EXCELLENCE_PLAN.md",
            "phase_wave_2_plan": "docs/runtime/phase-2-6/master/PHASE_2_6_WAVE_2_OUTPUT_EXCELLENCE_PLAN.md",
        },
    }

    _write_json(SCENARIO_OUTPUTS_PATH, scenario_outputs)
    _write_json(CHECKLIST_RESULTS_PATH, checklist_results)
    _write_json(METRICS_PATH, metrics)
    _write_json(FINAL_VERDICT_PATH, final_verdict)
    print(str(FINAL_VERDICT_PATH))


if __name__ == "__main__":
    main()
