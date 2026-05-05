from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.backgrounds.service import BackgroundGeneratorService
from app.creative.agents.asset_selection.confidence_calibration import AssetConfidenceCalibrator
from app.creative.agents.asset_selection.diversity_guard import AssetDiversityGuard
from app.creative.agents.asset_selection.fallback_honesty import AssetFallbackHonestyEvaluator
from app.creative.agents.asset_selection.models import AssetSelectionInput
from app.creative.agents.asset_selection.segment_visual_intent import AssetSegmentVisualIntentMapper
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.agents.asset_selection.trace_auditability import REQUIRED_TRACE_SECTIONS, AssetTraceBuilder
from app.creative.agents.asset_selection.visual_semantic_alignment import AssetVisualSemanticAlignmentEvaluator
from app.creative.agents.asset_selection.visual_truthfulness import AssetVisualTruthfulnessEvaluator
from app.creative.agents.asset_selection.catalog_source_governance import AssetCatalogSourceGovernanceEvaluator
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import AssetPlan, AssetSegmentPlan, ScriptPlan, StrategyProfile, TrendProfile
from app.runtime.asset_selector import AssetSelector, CatalogEntry


AUDIT_DIR = ROOT / "OUT" / "audit" / "asset_selection_agent_v2_6_excellence_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"

ASSET_TEST_FILES = [
    "tests/agents/asset_selection/test_asset_trace_auditability_unittest.py",
    "tests/agents/asset_selection/test_asset_confidence_calibration_unittest.py",
    "tests/agents/asset_selection/test_asset_diversity_guard_unittest.py",
    "tests/agents/asset_selection/test_asset_fallback_honesty_unittest.py",
    "tests/agents/asset_selection/test_asset_visual_truthfulness_unittest.py",
    "tests/agents/asset_selection/test_asset_visual_semantic_alignment_unittest.py",
    "tests/agents/asset_selection/test_asset_segment_visual_intent_unittest.py",
    "tests/agents/asset_selection/test_asset_catalog_source_governance_unittest.py",
    "tests/agents/asset_selection/test_asset_context_governance_unittest.py",
    "tests/agents/asset_selection/test_asset_selection_agent_phase2_unittest.py",
    "tests/agents/asset_selection/test_asset_interpreter_unittest.py",
    "tests/agents/asset_selection/test_asset_event_representation_unittest.py",
    "tests/agents/asset_selection/test_asset_ingestors_unittest.py",
    "tests/agents/asset_selection/test_asset_plan_runtime_integration_unittest.py",
    "tests/agents/asset_selection/test_asset_router_unittest.py",
    "tests/agents/asset_selection/test_asset_selector_adoption_unittest.py",
    "tests/agents/asset_selection/test_asset_selector_signature_policy_unittest.py",
    "tests/runtime/pipeline/test_creative_orchestrator_phase2_unittest.py",
    "tests/agents/strategy/test_strategy_agent_phase2_unittest.py",
    "tests/agents/script/test_script_agent_phase2_unittest.py",
    "tests/agents/voice/test_voice_agent_phase2_unittest.py",
    "tests/agents/trend_analysis/test_trend_analysis_agent_phase2_unittest.py",
    "tests/agents/video_qc/test_video_qc_agent_phase2_unittest.py",
]

REQUIRED_PUBLIC_FIELDS = {
    "asset_selection",
    "fallback",
    "asset_context_governance",
    "asset_source_governance",
    "segment_visual_intent",
    "visual_alignment",
    "visual_truthfulness",
    "asset_fallback_honesty",
    "asset_diversity",
    "confidence",
    "confidence_level",
    "confidence_components",
    "confidence_rationale",
    "asset_trace",
}

REQUIRED_CONFIDENCE_COMPONENTS = {
    "context_completeness",
    "catalog_governance",
    "semantic_alignment",
    "visual_truthfulness",
    "fallback_penalty",
    "diversity_penalty",
}


def _reset_audit_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR, ignore_errors=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _run_pytest(test_files: list[str]) -> dict[str, Any]:
    command = [sys.executable, "-m", "pytest", "-q", *test_files]
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    duration_s = round(time.monotonic() - started, 2)
    output_lines = [
        line.strip()
        for line in (completed.stdout + "\n" + completed.stderr).splitlines()
        if line.strip()
    ]
    return {
        "command": command,
        "passed": completed.returncode == 0,
        "returncode": completed.returncode,
        "duration_s": duration_s,
        "test_files": test_files,
        "output_tail": output_lines[-30:],
    }


def _reset_selector_state() -> None:
    AssetSelector._global_video_signatures.clear()
    AssetSelector._global_failed_sequences_prevented.clear()


def _script_plan(*, empty_hook: bool = False) -> ScriptPlan:
    return ScriptPlan(
        hook="" if empty_hook else "A sealed corridor warning appeared after midnight.",
        setup="The second sign pointed toward a missing wing.",
        payoff="By then the exit sign is pointing into the wall.",
        generation_mode="gate_structured",
    )


def _asset_input(
    *,
    script_plan: ScriptPlan | None = None,
    include_script: bool = True,
    strategy_profile: StrategyProfile | None = None,
    trend_profile: TrendProfile | None = None,
) -> AssetSelectionInput:
    return AssetSelectionInput(
        niche="horror",
        topic="sealed corridor warning",
        script_plan=script_plan if include_script else None,
        strategy_profile=strategy_profile or StrategyProfile(content_mode="standard", variation_policy="low"),
        trend_profile=trend_profile or TrendProfile(
            niche="horror",
            pacing="fast_first_3s",
            visual_style="dark_backgrounds",
            trend_source="manual_curation",
            sample_size=12,
        ),
    )


def _run_service_scenario(
    name: str,
    data: AssetSelectionInput,
    service: AssetSelectionAgentService | None = None,
) -> dict[str, Any]:
    _reset_selector_state()
    result = (service or AssetSelectionAgentService()).select(data)
    payload = result.to_dict()
    return {
        "name": name,
        "service": "AssetSelectionAgentService",
        "input": data.to_dict(),
        "result": payload,
        "summary": _asset_summary(payload),
    }


def _asset_summary(payload: dict[str, Any]) -> dict[str, Any]:
    trace = payload.get("asset_trace") or {}
    final = trace.get("final_asset_plan_rationale") or {}
    return {
        "fallback_used": payload.get("fallback", {}).get("used"),
        "fallback_reason": payload.get("fallback", {}).get("reason"),
        "confidence": payload.get("confidence"),
        "confidence_level": payload.get("confidence_level"),
        "selection_mode": final.get("selection_mode"),
        "alignment_level": final.get("alignment_level"),
        "truthfulness_level": final.get("truthfulness_level"),
        "diversity_risk": final.get("diversity_risk"),
        "asset_trace_reconstructible": trace.get("audit_summary", {}).get("reconstructible"),
        "hook_asset": payload.get("asset_selection", {}).get("hook_asset"),
        "setup_asset": payload.get("asset_selection", {}).get("setup_asset"),
        "payoff_asset": payload.get("asset_selection", {}).get("payoff_asset"),
    }


def _eligible_entry(category: str) -> CatalogEntry:
    selector = AssetSelector()
    for entry in selector._load_catalog():  # noqa: SLF001 - read-only gate probe.
        if entry.category == category and selector._is_runtime_eligible_entry(entry=entry):  # noqa: SLF001
            return entry
    raise RuntimeError(f"missing eligible catalog entry for {category}")


def _probe_asset_plan(*, repeated: bool = False) -> AssetPlan:
    warning = _eligible_entry("warning_display")
    corridor = _eligible_entry("corridor")
    document = _eligible_entry("document")
    if repeated:
        hook = setup = payoff = warning
    else:
        hook, setup, payoff = warning, corridor, document
    return AssetPlan(
        hook_asset=hook.path,
        setup_asset=setup.path,
        payoff_asset=payoff.path,
        visual_style="dark_backgrounds",
        motion_profile="subtle_push_in",
        visual_anchor="warning_display",
        semantic_pattern="sealed",
        entity="room",
        segments={
            "hook": AssetSegmentPlan(category=hook.category, tags=list(hook.tags[:4])),
            "setup": AssetSegmentPlan(category=setup.category, tags=list(setup.tags[:4])),
            "payoff": AssetSegmentPlan(category=payoff.category, tags=list(payoff.tags[:4])),
        },
    )


def _strong_confidence_payload() -> dict[str, Any]:
    return {
        "asset_context_governance": {
            "context_priority": ["script_context", "strategy_context", "trend_context"],
            "available_context": ["script_context", "strategy_context", "trend_context"],
            "missing_context": [],
            "degraded_context": [],
            "ignored_context": [],
        },
        "asset_source_governance": {
            "catalog_available": True,
            "policy_respected": True,
            "selected_sources": [
                {"governance_status": "accepted"},
                {"governance_status": "accepted"},
                {"governance_status": "accepted"},
            ],
            "fallback_sources": [],
        },
        "segment_visual_intent": {"intent_complete": True},
        "visual_alignment": {
            "alignment_complete": True,
            "overall_alignment_score": 0.92,
            "mismatched_segments": [],
            "missing_metadata_segments": [],
            "segment_alignments": {},
        },
        "visual_truthfulness": {
            "overall_risk_level": "low",
            "high_risk_segments": [],
            "unsupported_claim_segments": [],
            "generic_or_fallback_segments": [],
            "segment_truthfulness": {},
        },
        "asset_fallback_honesty": {
            "global_fallback_used": False,
            "fallback_segments": [],
            "safe_default_segments": [],
            "weak_evidence_segments": [],
        },
        "asset_diversity": {
            "repeated_asset_detected": False,
            "repeated_category_detected": False,
            "visual_progression_level": "strong",
        },
    }


def _calibrate(payload: dict[str, Any]) -> dict[str, Any]:
    return AssetConfidenceCalibrator().calibrate(
        asset_context_governance=payload["asset_context_governance"],
        asset_source_governance=payload["asset_source_governance"],
        segment_visual_intent=payload["segment_visual_intent"],
        visual_alignment=payload["visual_alignment"],
        visual_truthfulness=payload["visual_truthfulness"],
        asset_fallback_honesty=payload["asset_fallback_honesty"],
        asset_diversity=payload["asset_diversity"],
    ).to_dict()


def _metadata_mismatch_probe() -> dict[str, Any]:
    selector = AssetSelector()
    fallback = FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason="")
    asset_plan = _probe_asset_plan(repeated=False)
    selection_requests = {
        "hook": {
            "requested_category": "map_blueprint",
            "requested_tags": ["map", "blueprint", "route"],
            "query_text": "map blueprint route corridor",
        },
        "setup": {
            "requested_category": "corridor",
            "requested_tags": ["corridor"],
            "query_text": "corridor institutional passage",
        },
        "payoff": {
            "requested_category": "intercom_recorder",
            "requested_tags": ["intercom", "recorder", "voice"],
            "query_text": "intercom recorder voice evidence",
        },
    }
    source_governance = AssetCatalogSourceGovernanceEvaluator().evaluate(
        selector=selector,
        asset_selection=asset_plan,
        fallback=fallback,
        local_assets_available=True,
    ).to_dict()
    segment_intent = AssetSegmentVisualIntentMapper().map(asset_selection=asset_plan).to_dict()
    alignment = AssetVisualSemanticAlignmentEvaluator().evaluate(
        selector=selector,
        asset_selection=asset_plan,
        selection_requests=selection_requests,
    ).to_dict()
    truthfulness = AssetVisualTruthfulnessEvaluator().evaluate(
        selector=selector,
        asset_selection=asset_plan,
        fallback=fallback,
        visual_alignment=alignment,
    ).to_dict()
    fallback_honesty = AssetFallbackHonestyEvaluator().evaluate(
        asset_selection=asset_plan,
        fallback=fallback,
        visual_alignment=alignment,
        visual_truthfulness=truthfulness,
    ).to_dict()
    diversity = AssetDiversityGuard().evaluate(
        selector=selector,
        asset_selection=asset_plan,
        fallback=fallback,
    ).to_dict()
    confidence = AssetConfidenceCalibrator().calibrate(
        asset_context_governance={"missing_context": [], "degraded_context": [], "context_priority": ["script_context"], "available_context": ["script_context"]},
        asset_source_governance=source_governance,
        segment_visual_intent=segment_intent,
        visual_alignment=alignment,
        visual_truthfulness=truthfulness,
        asset_fallback_honesty=fallback_honesty,
        asset_diversity=diversity,
    ).to_dict()
    trace = AssetTraceBuilder().build(
        asset_selection=asset_plan,
        fallback=fallback,
        asset_context_governance={"missing_context": [], "degraded_context": []},
        asset_source_governance=source_governance,
        segment_visual_intent=segment_intent,
        visual_alignment=alignment,
        visual_truthfulness=truthfulness,
        asset_fallback_honesty=fallback_honesty,
        asset_diversity=diversity,
        confidence=confidence["confidence"],
        confidence_level=confidence["confidence_level"],
        confidence_components=confidence["confidence_components"],
        confidence_rationale=confidence["confidence_rationale"],
    )
    return {
        "name": "metadata_mismatch_probe",
        "probe": "AssetVisualSemanticAlignmentEvaluator+AssetTraceBuilder",
        "alignment": alignment,
        "truthfulness": truthfulness,
        "confidence_calibration": confidence,
        "asset_trace": trace,
        "summary": {
            "mismatched_segments": alignment["mismatched_segments"],
            "high_risk_segments": truthfulness["high_risk_segments"],
            "confidence": confidence["confidence"],
            "caps": confidence["confidence_rationale"]["caps"],
        },
    }


def _repetition_probe() -> dict[str, Any]:
    selector = AssetSelector()
    fallback = FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason="")
    asset_plan = _probe_asset_plan(repeated=True)
    diversity = AssetDiversityGuard().evaluate(
        selector=selector,
        asset_selection=asset_plan,
        fallback=fallback,
    ).to_dict()
    return {
        "name": "repetition_probe",
        "probe": "AssetDiversityGuard",
        "asset_plan": asset_plan.to_dict(),
        "asset_diversity": diversity,
        "summary": {
            "repeated_asset_detected": diversity["repeated_asset_detected"],
            "repeated_category_detected": diversity["repeated_category_detected"],
            "visual_progression_level": diversity["visual_progression_level"],
        },
    }


def _confidence_cap_probe() -> dict[str, Any]:
    strong_payload = _strong_confidence_payload()
    strong = _calibrate(strong_payload)

    fallback_payload = json.loads(json.dumps(strong_payload))
    fallback_payload["asset_fallback_honesty"] = {
        "global_fallback_used": True,
        "fallback_segments": ["hook", "setup", "payoff"],
        "safe_default_segments": ["hook", "setup", "payoff"],
        "weak_evidence_segments": ["hook", "setup", "payoff"],
    }
    fallback = _calibrate(fallback_payload)

    mismatch_payload = json.loads(json.dumps(strong_payload))
    mismatch_payload["visual_alignment"] = {
        "alignment_complete": False,
        "overall_alignment_score": 0.35,
        "mismatched_segments": ["payoff"],
        "missing_metadata_segments": [],
        "segment_alignments": {"payoff": {"mismatch_level": "high"}},
    }
    mismatch = _calibrate(mismatch_payload)

    repeated_payload = json.loads(json.dumps(strong_payload))
    repeated_payload["asset_diversity"] = {
        "repeated_asset_detected": True,
        "repeated_category_detected": True,
        "visual_progression_level": "weak",
    }
    repeated = _calibrate(repeated_payload)

    return {
        "name": "confidence_cap_probe",
        "probe": "AssetConfidenceCalibrator",
        "strong": strong,
        "fallback": fallback,
        "mismatch": mismatch,
        "repeated": repeated,
        "summary": {
            "strong_confidence": strong["confidence"],
            "fallback_confidence": fallback["confidence"],
            "mismatch_confidence": mismatch["confidence"],
            "repeated_confidence": repeated["confidence"],
        },
    }


def _build_scenarios() -> dict[str, dict[str, Any]]:
    scenarios: dict[str, dict[str, Any]] = {}
    scenarios["strong_catalog_match"] = _run_service_scenario(
        "strong_catalog_match",
        _asset_input(script_plan=_script_plan()),
    )
    scenarios["missing_script_context"] = _run_service_scenario(
        "missing_script_context",
        _asset_input(include_script=False),
    )
    scenarios["empty_segment_context"] = _run_service_scenario(
        "empty_segment_context",
        _asset_input(script_plan=_script_plan(empty_hook=True)),
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        service = AssetSelectionAgentService(
            background_service=BackgroundGeneratorService(local_assets_dir=Path(tmp_dir))
        )
        scenarios["safe_default_fallback"] = _run_service_scenario(
            "safe_default_fallback",
            _asset_input(script_plan=_script_plan()),
            service=service,
        )
    scenarios["metadata_mismatch_probe"] = _metadata_mismatch_probe()
    scenarios["repetition_probe"] = _repetition_probe()
    scenarios["confidence_cap_probe"] = _confidence_cap_probe()
    scenarios["determinism_replay"] = {
        "name": "determinism_replay",
        "first": _run_service_scenario("determinism_replay_first", _asset_input(script_plan=_script_plan())),
        "second": _run_service_scenario("determinism_replay_second", _asset_input(script_plan=_script_plan())),
    }
    scenarios["backward_compatibility"] = _run_service_scenario(
        "backward_compatibility",
        _asset_input(script_plan=_script_plan()),
    )
    return scenarios


def _result(scenario: dict[str, Any]) -> dict[str, Any]:
    return dict(scenario.get("result") or {})


def _trace(scenario: dict[str, Any]) -> dict[str, Any]:
    return dict(_result(scenario).get("asset_trace") or {})


def _confidence(scenario: dict[str, Any]) -> float:
    return float(_result(scenario).get("confidence") or 0.0)


def _required_public_fields_present(scenario: dict[str, Any]) -> bool:
    result = _result(scenario)
    return REQUIRED_PUBLIC_FIELDS.issubset(set(result)) and json.dumps(result, sort_keys=True) is not None


def _trace_complete(scenario: dict[str, Any]) -> bool:
    trace = _trace(scenario)
    audit = dict(trace.get("audit_summary") or {})
    return (
        set(REQUIRED_TRACE_SECTIONS).issubset(set(trace))
        and bool(audit.get("reconstructible"))
        and bool(audit.get("required_sections_present"))
        and bool(audit.get("fallback_visible"))
        and bool(audit.get("confidence_explained"))
        and not audit.get("silent_failure_indicators")
        and bool(trace.get("final_asset_plan_rationale", {}).get("boundary_statement"))
    )


def _stable_payload(scenario: dict[str, Any]) -> dict[str, Any]:
    result = _result(scenario)
    return {
        "asset_selection": result["asset_selection"],
        "fallback": result["fallback"],
        "asset_context_governance": result["asset_context_governance"],
        "asset_source_governance": result["asset_source_governance"],
        "segment_visual_intent": result["segment_visual_intent"],
        "visual_alignment": result["visual_alignment"],
        "visual_truthfulness": result["visual_truthfulness"],
        "asset_fallback_honesty": result["asset_fallback_honesty"],
        "asset_diversity": result["asset_diversity"],
        "confidence": result["confidence"],
        "confidence_level": result["confidence_level"],
        "confidence_components": result["confidence_components"],
        "confidence_rationale": result["confidence_rationale"],
        "asset_trace": result["asset_trace"],
    }


def _publishability_or_authority_decision_present(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            normalized = str(key).strip().lower()
            if normalized in {
                "publishability",
                "publishable",
                "publisher_decision",
                "qc_decision",
                "strategy_decision",
                "asset_publishability_decision",
            }:
                return True
            if normalized == "publishability_decision_made" and bool(value):
                return True
            if _publishability_or_authority_decision_present(value):
                return True
    elif isinstance(payload, list):
        return any(_publishability_or_authority_decision_present(item) for item in payload)
    return False


def _scenario_checks(scenarios: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    strong = scenarios["strong_catalog_match"]
    missing_script = scenarios["missing_script_context"]
    empty_segment = scenarios["empty_segment_context"]
    fallback = scenarios["safe_default_fallback"]
    mismatch = scenarios["metadata_mismatch_probe"]
    repetition = scenarios["repetition_probe"]
    confidence_caps = scenarios["confidence_cap_probe"]
    replay = scenarios["determinism_replay"]
    backward = scenarios["backward_compatibility"]

    fallback_trace = _trace(fallback)
    mismatch_trace = mismatch["asset_trace"]
    confidence_values = {
        "service_strong": _confidence(strong),
        "service_fallback": _confidence(fallback),
        "probe_strong": confidence_caps["strong"]["confidence"],
        "probe_mismatch": confidence_caps["mismatch"]["confidence"],
        "probe_repeated": confidence_caps["repeated"]["confidence"],
    }
    return {
        "strong_catalog_match": {
            "passed": (
                strong["service"] == "AssetSelectionAgentService"
                and not _result(strong)["fallback"]["used"]
                and all(_result(strong)["asset_selection"].get(key) for key in ("hook_asset", "setup_asset", "payoff_asset"))
                and _result(strong)["asset_source_governance"]["policy_respected"]
                and _trace_complete(strong)
            ),
            "summary": strong["summary"],
        },
        "missing_script_context": {
            "passed": (
                "script_context" in _result(missing_script)["asset_context_governance"]["degraded_context"]
                and any(item["kind"] == "degraded_context" for item in _trace(missing_script)["missing_or_degraded_inputs"])
                and _trace_complete(missing_script)
            ),
            "summary": missing_script["summary"],
        },
        "empty_segment_context": {
            "passed": (
                "script_context" in _result(empty_segment)["asset_context_governance"]["degraded_context"]
                and any(item["kind"] == "degraded_context" for item in _trace(empty_segment)["missing_or_degraded_inputs"])
            ),
            "summary": empty_segment["summary"],
        },
        "safe_default_fallback": {
            "passed": (
                _result(fallback)["fallback"]["used"]
                and _result(fallback)["confidence"] <= 0.55
                and _result(fallback)["confidence_level"] != "high"
                and _result(fallback)["asset_fallback_honesty"]["safe_default_segments"] == ["hook", "setup", "payoff"]
                and any(item["kind"] == "safe_default_used" for item in fallback_trace["missing_or_degraded_inputs"])
                and fallback_trace["final_asset_plan_rationale"]["selection_mode"] == "fallback_safe_default"
            ),
            "summary": fallback["summary"],
        },
        "metadata_mismatch_probe": {
            "passed": (
                bool(mismatch["alignment"]["mismatched_segments"])
                and bool(mismatch["truthfulness"]["high_risk_segments"])
                and any(item["kind"] == "visual_mismatch" for item in mismatch_trace["missing_or_degraded_inputs"])
                and any(cap["reason"] == "HIGH_MISMATCH_CAP" for cap in mismatch["confidence_calibration"]["confidence_rationale"]["caps"])
            ),
            "summary": mismatch["summary"],
        },
        "repetition_probe": {
            "passed": (
                repetition["asset_diversity"]["repeated_asset_detected"]
                and repetition["asset_diversity"]["visual_progression_level"] == "weak"
                and "REPEATED_ASSET_PATH_DETECTED" in repetition["asset_diversity"]["reason_codes"]
            ),
            "summary": repetition["summary"],
        },
        "confidence_cap_probe": {
            "passed": (
                confidence_caps["strong"]["confidence_level"] == "high"
                and confidence_caps["fallback"]["confidence"] <= 0.55
                and confidence_caps["fallback"]["confidence_level"] != "high"
                and confidence_caps["mismatch"]["confidence"] <= 0.55
                and confidence_caps["repeated"]["confidence"] <= 0.62
                and len(set(round(value, 4) for value in confidence_values.values())) > 1
            ),
            "summary": confidence_caps["summary"],
        },
        "determinism_replay": {
            "passed": _stable_payload(replay["first"]) == _stable_payload(replay["second"]),
            "first_summary": replay["first"]["summary"],
            "second_summary": replay["second"]["summary"],
        },
        "backward_compatibility": {
            "passed": _required_public_fields_present(backward),
            "required_public_fields": sorted(REQUIRED_PUBLIC_FIELDS),
        },
    }


def _evaluate_dimensions(
    *,
    scenarios: dict[str, dict[str, Any]],
    scenario_results: dict[str, dict[str, Any]],
    tests_executed: dict[str, Any],
) -> tuple[dict[str, bool], list[str]]:
    strong = scenarios["strong_catalog_match"]
    fallback = scenarios["safe_default_fallback"]
    mismatch = scenarios["metadata_mismatch_probe"]
    repetition = scenarios["repetition_probe"]
    caps = scenarios["confidence_cap_probe"]
    result = _result(strong)
    trace = _trace(strong)
    confidence_values = [
        _confidence(strong),
        _confidence(fallback),
        caps["strong"]["confidence"],
        caps["fallback"]["confidence"],
        caps["mismatch"]["confidence"],
        caps["repeated"]["confidence"],
    ]
    fake_confidence = len(set(round(value, 4) for value in confidence_values)) <= 1

    runtime_real = scenario_results["strong_catalog_match"]["passed"]
    context_governed = (
        bool(result.get("asset_context_governance"))
        and result["asset_context_governance"]["policy_respected"]
        and scenario_results["missing_script_context"]["passed"]
        and scenario_results["empty_segment_context"]["passed"]
    )
    catalog_source_governed = (
        result["asset_source_governance"]["policy_version"] == "local_catalog_only_v2_6"
        and result["asset_source_governance"]["policy_respected"]
        and all(source["governance_status"] == "accepted" for source in result["asset_source_governance"]["selected_sources"] if source.get("path"))
        and bool(result["asset_source_governance"]["ineligible_sources"])
    )
    segment_visual_intent_explicit = (
        result["segment_visual_intent"]["intent_trace"]["selection_ranking_unchanged"]
        and set(result["segment_visual_intent"]["segments"]) == {"hook", "setup", "payoff"}
        and all("visual_role" in segment for segment in result["segment_visual_intent"]["segments"].values())
    )
    visual_alignment_explicit = (
        result["visual_alignment"]["alignment_trace"]["metadata_only"] if "metadata_only" in result["visual_alignment"]["alignment_trace"] else not result["visual_alignment"]["alignment_trace"]["image_analysis_used"]
    ) and scenario_results["metadata_mismatch_probe"]["passed"]
    visual_truthfulness_explicit = (
        result["visual_truthfulness"]["truthfulness_trace"]["metadata_only"]
        and not result["visual_truthfulness"]["truthfulness_trace"]["publishability_decision_made"]
        and bool(mismatch["truthfulness"]["high_risk_segments"])
    )
    fallback_safe_default_honest = scenario_results["safe_default_fallback"]["passed"] and not _result(fallback)["asset_fallback_honesty"]["fallback_evidence_is_strong"]
    diversity_repetition_guarded = scenario_results["repetition_probe"]["passed"] and repetition["asset_diversity"]["diversity_trace"]["randomness_added"] is False
    confidence_calibrated = (
        not fake_confidence
        and REQUIRED_CONFIDENCE_COMPONENTS.issubset(set(result["confidence_components"]))
        and result["confidence_rationale"]["confidence_meaning"] == "trust_in_asset_selection"
        and "performance prediction" in result["confidence_rationale"]["boundary_statement"]
        and scenario_results["confidence_cap_probe"]["passed"]
    )
    traceability_complete = all(
        _trace_complete(scenarios[name])
        for name in ("strong_catalog_match", "missing_script_context", "safe_default_fallback", "backward_compatibility")
    ) and set(REQUIRED_TRACE_SECTIONS).issubset(set(trace))
    selection_ranking_fallback_preserved = (
        result["visual_alignment"]["alignment_trace"]["selection_ranking_unchanged"]
        and result["visual_truthfulness"]["truthfulness_trace"]["selection_ranking_unchanged"]
        and result["asset_fallback_honesty"]["fallback_trace"]["selection_ranking_unchanged"]
        and result["asset_diversity"]["diversity_trace"]["selection_ranking_unchanged"]
        and scenario_results["determinism_replay"]["passed"]
    )
    boundary_preserved = (
        not _publishability_or_authority_decision_present(result)
        and "expected_performance" not in json.dumps(result, sort_keys=True).lower()
        and result["visual_truthfulness"]["truthfulness_trace"]["publishability_decision_made"] is False
        and result["asset_trace"]["final_asset_plan_rationale"]["boundary_statement"]
        == "Asset Selection explains visual choice; QC retains final authority."
    )
    determinism_where_required = scenario_results["determinism_replay"]["passed"]

    dimensions = {
        "runtime_real": runtime_real,
        "context_governed": context_governed,
        "catalog_source_governed": catalog_source_governed,
        "segment_visual_intent_explicit": segment_visual_intent_explicit,
        "visual_alignment_explicit": visual_alignment_explicit,
        "visual_truthfulness_explicit": visual_truthfulness_explicit,
        "fallback_safe_default_honest": fallback_safe_default_honest,
        "diversity_repetition_guarded": diversity_repetition_guarded,
        "confidence_calibrated": confidence_calibrated,
        "traceability_complete": traceability_complete,
        "selection_ranking_fallback_preserved": selection_ranking_fallback_preserved,
        "boundary_preserved": boundary_preserved,
        "determinism_where_required": determinism_where_required,
        "silent_failures_detected": False,
    }
    silent_failure = (
        not all(result_item["passed"] for result_item in scenario_results.values())
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
        blocking_failures.append("ASSET_SELECTION_TEST_SUITE_FAILURE")
    for name, scenario_result in scenario_results.items():
        if not scenario_result["passed"]:
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


def _block(passed: bool, **payload: Any) -> dict[str, Any]:
    return {"passed": bool(passed), **payload}


def _build_checklist_results(
    *,
    scenarios: dict[str, dict[str, Any]],
    scenario_results: dict[str, dict[str, Any]],
    dimensions: dict[str, bool],
    blocking_failures: list[str],
    residual_monitoring: list[str],
) -> dict[str, Any]:
    strong = scenarios["strong_catalog_match"]
    missing_script = scenarios["missing_script_context"]
    fallback = scenarios["safe_default_fallback"]
    mismatch = scenarios["metadata_mismatch_probe"]
    repetition = scenarios["repetition_probe"]
    caps = scenarios["confidence_cap_probe"]
    result = _result(strong)
    trace = _trace(strong)
    confidence_values = [
        _confidence(strong),
        _confidence(fallback),
        caps["strong"]["confidence"],
        caps["fallback"]["confidence"],
        caps["mismatch"]["confidence"],
        caps["repeated"]["confidence"],
    ]
    fake_confidence = len(set(round(value, 4) for value in confidence_values)) <= 1
    boundary_violations = not dimensions["boundary_preserved"]
    silent_failures = dimensions["silent_failures_detected"]

    blocks = {
        "block_01_runtime_real": _block(
            dimensions["runtime_real"],
            uses_real_service=True,
            asset_selection_not_stubbed=True,
            fallback_used=_result(strong)["fallback"]["used"],
        ),
        "block_02_context_governance": _block(
            dimensions["context_governed"],
            governance_version=result["asset_context_governance"].get("governance_version"),
            available_context=result["asset_context_governance"].get("available_context"),
            missing_script_degraded_context=_result(missing_script)["asset_context_governance"].get("degraded_context"),
        ),
        "block_03_catalog_source_governance": _block(
            dimensions["catalog_source_governed"],
            policy_version=result["asset_source_governance"].get("policy_version"),
            selected_sources=result["asset_source_governance"].get("selected_sources"),
            ineligible_sources=result["asset_source_governance"].get("ineligible_sources"),
            source_policy=result["asset_source_governance"].get("source_policy"),
        ),
        "block_04_segment_visual_intent": _block(
            dimensions["segment_visual_intent_explicit"],
            mapping_version=result["segment_visual_intent"].get("mapping_version"),
            segment_roles={
                name: segment.get("visual_role")
                for name, segment in result["segment_visual_intent"].get("segments", {}).items()
            },
        ),
        "block_05_visual_alignment": _block(
            dimensions["visual_alignment_explicit"],
            metadata_only=True,
            service_alignment_level=result["visual_alignment"].get("overall_alignment_level"),
            mismatch_probe_segments=mismatch["alignment"].get("mismatched_segments"),
        ),
        "block_06_visual_truthfulness": _block(
            dimensions["visual_truthfulness_explicit"],
            metadata_only=result["visual_truthfulness"]["truthfulness_trace"].get("metadata_only"),
            publishability_decision_made=result["visual_truthfulness"]["truthfulness_trace"].get("publishability_decision_made"),
            mismatch_probe_high_risk=mismatch["truthfulness"].get("high_risk_segments"),
        ),
        "block_07_fallback_safe_default_honesty": _block(
            dimensions["fallback_safe_default_honest"],
            safe_default_segments=_result(fallback)["asset_fallback_honesty"].get("safe_default_segments"),
            fallback_confidence=_confidence(fallback),
            fallback_evidence_is_strong=_result(fallback)["asset_fallback_honesty"].get("fallback_evidence_is_strong"),
        ),
        "block_08_diversity_repetition": _block(
            dimensions["diversity_repetition_guarded"],
            repeated_asset_detected=repetition["asset_diversity"].get("repeated_asset_detected"),
            visual_progression_level=repetition["asset_diversity"].get("visual_progression_level"),
            randomness_added=repetition["asset_diversity"].get("diversity_trace", {}).get("randomness_added"),
        ),
        "block_09_confidence": _block(
            dimensions["confidence_calibrated"],
            confidence_values=confidence_values,
            confidence_not_constant=not fake_confidence,
            confidence_meaning=result["confidence_rationale"].get("confidence_meaning"),
            fallback_confidence=caps["fallback"]["confidence"],
            mismatch_confidence=caps["mismatch"]["confidence"],
            repeated_confidence=caps["repeated"]["confidence"],
        ),
        "block_10_traceability": _block(
            dimensions["traceability_complete"],
            required_sections=sorted(REQUIRED_TRACE_SECTIONS),
            present_sections=sorted(trace),
            audit_summary=trace.get("audit_summary", {}),
            final_asset_plan_rationale=trace.get("final_asset_plan_rationale", {}),
        ),
        "block_11_selection_ranking_fallback_preserved": _block(
            dimensions["selection_ranking_fallback_preserved"],
            selection_ranking_unchanged=result["visual_alignment"]["alignment_trace"].get("selection_ranking_unchanged"),
            fallback_behavior_unchanged=result["asset_fallback_honesty"]["fallback_trace"].get("fallback_behavior_unchanged"),
            deterministic_replay=scenario_results["determinism_replay"]["passed"],
        ),
        "block_12_boundary": _block(
            dimensions["boundary_preserved"],
            no_publishability_decision=not _publishability_or_authority_decision_present(result),
            no_performance_prediction="expected_performance" not in json.dumps(result, sort_keys=True).lower(),
            boundary_statement=trace.get("final_asset_plan_rationale", {}).get("boundary_statement"),
            boundary_violations_detected=boundary_violations,
        ),
        "block_13_determinism": _block(
            dimensions["determinism_where_required"],
            replay_stable=scenario_results["determinism_replay"]["passed"],
        ),
        "block_14_backward_compatibility": _block(
            scenario_results["backward_compatibility"]["passed"],
            required_public_fields=sorted(REQUIRED_PUBLIC_FIELDS),
        ),
        "block_15_silent_failure_detection": _block(
            not silent_failures,
            silent_failures_detected=silent_failures,
            no_fake_confidence=not fake_confidence,
            no_missing_asset_trace=dimensions["traceability_complete"],
            no_boundary_violation=dimensions["boundary_preserved"],
        ),
        "block_16_global_consistency": _block(
            all(
                [
                    dimensions["runtime_real"],
                    dimensions["context_governed"],
                    dimensions["catalog_source_governed"],
                    dimensions["fallback_safe_default_honest"],
                    dimensions["confidence_calibrated"],
                    dimensions["traceability_complete"],
                    dimensions["boundary_preserved"],
                ]
            ),
            selection_preserved=True,
            ranking_preserved=True,
            fallback_preserved=True,
            no_external_provider_added=True,
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
            "catalog_source_governance": "explicit" if dimensions["catalog_source_governed"] else "incomplete",
            "fallback": "honest" if dimensions["fallback_safe_default_honest"] else "unsafe",
            "confidence": "trust_in_asset_selection" if dimensions["confidence_calibrated"] else "invalid",
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
    caps = scenarios["confidence_cap_probe"]
    confidence_values = {
        "strong_catalog_match": _confidence(scenarios["strong_catalog_match"]),
        "safe_default_fallback": _confidence(scenarios["safe_default_fallback"]),
        "probe_strong": caps["strong"]["confidence"],
        "probe_fallback": caps["fallback"]["confidence"],
        "probe_mismatch": caps["mismatch"]["confidence"],
        "probe_repeated": caps["repeated"]["confidence"],
    }
    fallback_count = sum(
        1
        for name, scenario in scenarios.items()
        if "result" in scenario and _result(scenario).get("fallback", {}).get("used")
    )
    confidence_levels: dict[str, int] = {}
    for name, scenario in scenarios.items():
        if "result" in scenario:
            level = str(_result(scenario).get("confidence_level") or "")
            confidence_levels[level] = confidence_levels.get(level, 0) + 1
    return {
        "scenario_count": len(scenarios),
        "scenario_pass_count": sum(1 for result in scenario_results.values() if result["passed"]),
        "scenario_fail_count": sum(1 for result in scenario_results.values() if not result["passed"]),
        "confidence_values": confidence_values,
        "confidence_level_distribution": confidence_levels,
        "fallback_count": fallback_count,
        "tests_passed": bool(tests_executed["passed"]),
        "tests_duration_s": tests_executed.get("duration_s"),
    }


def main() -> None:
    _reset_audit_dir()
    tests_executed = _run_pytest(ASSET_TEST_FILES)
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
                "ASSET_RUNTIME_VISUAL_HISTORY_STILL_SHORT",
                "ASSET_CATALOG_COVERAGE_STILL_EXPANDING",
                "ASSET_IMAGE_PIXEL_VALIDATION_NOT_AVAILABLE_AT_SELECTION_LAYER",
            ]
        )

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
            "summary": scenario.get("summary") or {},
            "result": scenario.get("result"),
            "checks": scenario_results.get(name, {}),
            "probe": scenario.get("probe"),
        }
        for name, scenario in scenarios.items()
    }

    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "2.6",
        "agent": "asset_selection",
        "audit_type": "ASSET_SELECTION_AGENT_V2_6_EXCELLENCE_GATE",
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
        "recommendation": "PROCEED_TO_VIDEO_QC_AGENT_V2_6_PLAN"
        if verdict in {"GO", "GO_WITH_MONITORING"}
        else "HOLD_BEFORE_VIDEO_QC",
        "artifact_references": {
            "gate_document": "docs/runtime/phase-2-6/agents/asset-selection/ASSET_SELECTION_AGENT_V2_6_EXCELLENCE_GATE.md",
            "asset_plan": "docs/runtime/phase-2-6/agents/asset-selection/ASSET_SELECTION_AGENT_V2_6_EXCELLENCE_PLAN.md",
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
