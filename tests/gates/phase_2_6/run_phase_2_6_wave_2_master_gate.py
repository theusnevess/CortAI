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

from app.creative.agents.asset_selection.models import AssetSelectionInput
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.agents.script.models import ScriptAgentInput
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.strategy.models import StrategyInput
from app.creative.agents.strategy.service import StrategyAgentService
from app.creative.agents.video_qc.models import VideoQcInput
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.contracts.creative_pack import StrategyProfile, TrendProfile
from app.runtime.asset_selector import AssetSelector


AUDIT_DIR = ROOT / "OUT" / "audit" / "phase_2_6_wave_2_master_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
CROSS_AGENT_CONSISTENCY_PATH = AUDIT_DIR / "cross_agent_consistency.json"

REQUIRED_DOCS = {
    "wave_2_plan": "docs/runtime/phase-2-6/master/PHASE_2_6_WAVE_2_OUTPUT_EXCELLENCE_PLAN.md",
    "script_plan": "docs/runtime/phase-2-6/agents/script/SCRIPT_AGENT_V2_6_EXCELLENCE_PLAN.md",
    "voice_plan": "docs/runtime/phase-2-6/agents/voice/VOICE_AGENT_V2_6_EXCELLENCE_PLAN.md",
    "asset_plan": "docs/runtime/phase-2-6/agents/asset-selection/ASSET_SELECTION_AGENT_V2_6_EXCELLENCE_PLAN.md",
    "video_qc_plan": "docs/runtime/phase-2-6/agents/video-qc/VIDEO_QC_AGENT_V2_6_EXCELLENCE_PLAN.md",
    "wave_2_master_gate_doc": "docs/runtime/phase-2-6/master-gates/PHASE_2_6_WAVE_2_MASTER_GATE.md",
    "master_state": "docs/runtime/architecture/CORTAI_RUNTIME_MASTER_STATE_V2_5.md",
}

REQUIRED_RUNNERS = {
    "script_gate_runner": "tests/gates/agents/script/run_script_agent_v2_6_excellence_gate.py",
    "voice_gate_runner": "tests/gates/agents/voice/run_voice_agent_v2_6_excellence_gate.py",
    "asset_gate_runner": "tests/gates/agents/asset_selection/run_asset_selection_agent_v2_6_excellence_gate.py",
    "video_qc_gate_runner": "tests/gates/agents/video_qc/run_video_qc_agent_v2_6_excellence_gate.py",
    "wave_2_master_gate_runner": "tests/gates/phase_2_6/run_phase_2_6_wave_2_master_gate.py",
}

REQUIRED_JSON_ARTIFACTS = {
    "script_gate": "OUT/audit/script_agent_v2_6_excellence_gate/final_verdict.json",
    "voice_gate": "OUT/audit/voice_agent_v2_6_excellence_gate/final_verdict.json",
    "asset_gate": "OUT/audit/asset_selection_agent_v2_6_excellence_gate/final_verdict.json",
    "video_qc_gate": "OUT/audit/video_qc_agent_v2_6_excellence_gate/final_verdict.json",
    "system_governance_registry": "OUT/audit/system_governance_registry.json",
}

OPTIONAL_JSON_ARTIFACTS = {
    "wave_1_master_gate": "OUT/audit/phase_2_6_wave_1_master_gate/final_verdict.json",
    "absolute_master_pre_wave_2": "OUT/audit/cortai_absolute_master_gate/final_verdict.json",
}

UNIT_TEST_FILES = [
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
    "tests/agents/voice/test_voice_trace_auditability_unittest.py",
    "tests/agents/voice/test_voice_confidence_calibration_unittest.py",
    "tests/agents/voice/test_voice_audio_validation_linkage_unittest.py",
    "tests/agents/voice/test_voice_provider_fallback_honesty_unittest.py",
    "tests/agents/voice/test_voice_monotony_contrast_analysis_unittest.py",
    "tests/agents/voice/test_voice_segment_timing_pause_unittest.py",
    "tests/agents/voice/test_voice_delivery_profile_semantics_unittest.py",
    "tests/agents/voice/test_voice_plan_contract_governance_unittest.py",
    "tests/agents/voice/test_voice_agent_phase2_unittest.py",
    "tests/agents/voice/test_voice_agent_service_phase2_5_unittest.py",
    "tests/agents/voice/test_tts_router_phase2_5_unittest.py",
    "tests/agents/voice/test_tts_router_kokoro_phase2_5b_unittest.py",
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
    "tests/agents/video_qc/test_video_qc_trace_auditability_unittest.py",
    "tests/agents/video_qc/test_video_qc_decision_semantics_unittest.py",
    "tests/agents/video_qc/test_video_qc_confidence_evidence_unittest.py",
    "tests/agents/video_qc/test_video_qc_input_governance_unittest.py",
    "tests/agents/video_qc/test_video_qc_agent_phase2_unittest.py",
    "tests/runtime/pipeline/test_creative_orchestrator_phase2_unittest.py",
    "tests/agents/strategy/test_strategy_agent_phase2_unittest.py",
    "tests/content/test_content_pipeline_d27_unittest.py",
    "tests/experiment/test_experiment_capability_phase2_unittest.py",
    "tests/attribution/test_content_attribution_phase_d_bounded_integration_unittest.py",
]

SCRIPT_TRACE_SECTIONS = {
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

VOICE_TRACE_SECTIONS = {
    "voice_plan_governance",
    "delivery_semantics",
    "segment_timing",
    "monotony_contrast_analysis",
    "provider_fallback_honesty",
    "audio_validation_linkage",
    "confidence_calibration",
    "final_voice_plan_rationale",
    "missing_or_degraded_inputs",
    "audit_summary",
}

ASSET_TRACE_SECTIONS = {
    "asset_context_governance",
    "catalog_governance",
    "segment_visual_intent",
    "visual_alignment",
    "visual_truthfulness",
    "asset_fallback_honesty",
    "asset_diversity",
    "confidence_calibration",
    "final_asset_plan_rationale",
    "missing_or_degraded_inputs",
    "audit_summary",
}

QC_TRACE_SECTIONS = {
    "input_governance",
    "evidence_scoring",
    "confidence_calibration",
    "decision_semantics",
    "final_qc_decision_rationale",
    "missing_or_degraded_inputs",
    "audit_summary",
}

ALLOWED_RESIDUAL_FRAGMENTS = {
    "RUNTIME_HISTORY_STILL_SHORT",
    "PROVIDER_HISTORY_STILL_SHORT",
    "PROVIDER_EXECUTION_HISTORY_STILL_SHORT",
    "LONGITUDINAL",
    "CATALOG_COVERAGE_STILL_EXPANDING",
    "PRODUCER_COVERAGE_STILL_EXPANDING",
    "PRODUCT_SIGNAL_CALIBRATION_STILL_MATURING",
    "MEDIA_PROBE_COVERAGE_ENVIRONMENT_DEPENDENT",
    "LAYER_ATTRIBUTION_EVIDENCE_STILL_LIMITED",
    "REPAIR_METADATA_NOT_REPORTED",
    "REPAIR_METADATA_STILL_NOT_REPORTED",
    "TTS_TRACE_NOT_AVAILABLE",
    "AUDIO_VALIDATION_HISTORY_STILL_SHORT",
    "VISUAL_HISTORY_STILL_SHORT",
    "IMAGE_PIXEL_VALIDATION_NOT_AVAILABLE_AT_SELECTION_LAYER",
    "PIXEL_LEVEL_VALIDATION_OUT_OF_SCOPE",
}

FORBIDDEN_KEY_FRAGMENTS = {
    "predicted",
    "forecast",
    "expected_performance",
    "performance_prediction",
    "likely_to_perform",
}


class _StaticProbeVideoQcAgentService(VideoQcAgentService):
    def _probe_video(self, video_path: Path) -> dict[str, object]:
        return {"width": 1080, "height": 1920, "has_audio": True, "probe_mode": "ffprobe"}


def _reset_audit_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR, ignore_errors=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_json(path: Path) -> tuple[dict[str, Any], str]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except Exception as exc:  # noqa: BLE001
        return {}, f"{type(exc).__name__}: {exc}"


def _run_pytest(test_files: list[str]) -> dict[str, Any]:
    command = [sys.executable, "-m", "pytest", "-q", *test_files]
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=1500,
        )
        duration = round(time.perf_counter() - started, 3)
        lines = [
            line.strip()
            for line in (completed.stdout + "\n" + completed.stderr).splitlines()
            if line.strip()
        ]
        return {
            "command": command,
            "passed": completed.returncode == 0,
            "timeout": False,
            "returncode": completed.returncode,
            "duration_seconds": duration,
            "test_files": test_files,
            "output_tail": lines[-30:],
        }
    except subprocess.TimeoutExpired as exc:
        duration = round(time.perf_counter() - started, 3)
        output = f"{exc.stdout or ''}\n{exc.stderr or ''}"
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        return {
            "command": command,
            "passed": False,
            "timeout": True,
            "timeout_classification": "critical_validation_timeout",
            "returncode": None,
            "duration_seconds": duration,
            "test_files": test_files,
            "output_tail": lines[-30:] + ["PYTEST_TIMEOUT"],
        }


def _load_artifacts() -> tuple[dict[str, dict[str, Any]], dict[str, str], dict[str, bool]]:
    artifacts: dict[str, dict[str, Any]] = {}
    json_errors: dict[str, str] = {}
    existence: dict[str, bool] = {}
    for name, rel_path in {**REQUIRED_JSON_ARTIFACTS, **OPTIONAL_JSON_ARTIFACTS}.items():
        path = ROOT / rel_path
        existence[name] = path.exists()
        if not path.exists():
            artifacts[name] = {}
            if name in REQUIRED_JSON_ARTIFACTS:
                json_errors[name] = "missing"
            continue
        payload, error = _load_json(path)
        artifacts[name] = payload
        if error:
            json_errors[name] = error
    return artifacts, json_errors, existence


def _metadata_from_script(script_text: str) -> dict[str, Any]:
    sentences = [part.strip() for part in script_text.replace("\n", " ").split(".") if part.strip()]
    while len(sentences) < 3:
        sentences.append("The final frame confirms the warning")
    return {
        "aspect_ratio": "9:16",
        "render_duration_s": 8.0,
        "setup_background_mean_luma": 90.0,
        "payoff_background_mean_luma": 105.0,
        "subtitle_cues": [
            {"start": 0.0, "end": 2.0, "text": sentences[0][:80]},
            {"start": 2.2, "end": 4.8, "text": sentences[1][:80]},
            {"start": 6.0, "end": 7.8, "text": sentences[2][:80]},
        ],
    }


def _write_qc_artifacts(root: Path, script_text: str) -> dict[str, Path]:
    root.mkdir(parents=True, exist_ok=True)
    video_path = root / "video.mp4"
    audio_path = root / "audio.wav"
    metadata_path = root / "metadata.json"
    video_path.write_bytes(b"wave2-video-bytes")
    audio_path.write_bytes(b"wave2-audio-bytes")
    metadata_path.write_text(json.dumps(_metadata_from_script(script_text)), encoding="utf-8")
    return {"video": video_path, "audio": audio_path, "metadata": metadata_path}


def _trend_profile() -> TrendProfile:
    return TrendProfile(
        niche="horror",
        dominant_hooks=["sealed warning", "impossible sign"],
        avg_duration="8-12",
        pacing="fast_first_3s",
        visual_style="dark_backgrounds",
        text_style="caption_focus",
        trend_source="manual_curation",
        confidence_scores={"context": 0.82},
        sample_size=12,
        trend_version="2.6",
        collector_version="wave2_master_gate",
    )


def _reset_asset_selector_state() -> None:
    AssetSelector._global_video_signatures.clear()
    AssetSelector._global_failed_sequences_prevented.clear()


def _run_output_chain(tmp_root: Path) -> dict[str, Any]:
    strategy = StrategyAgentService().generate(
        StrategyInput(account_id="wave2_master", account_goal="retention", health_status="SAFE")
    )
    script = ScriptAgentService().generate(
        ScriptAgentInput(
            account_id="wave2_master",
            niche="horror",
            topic="sealed corridor warning",
            account_health_status="SAFE",
            strategy_profile=strategy.strategy_profile,
            trend_profile=_trend_profile(),
        )
    )
    voice = VoiceAgentService().resolve(
        account_id="wave2_master",
        niche="horror",
        script_plan=script.script_plan,
        strategy_profile=strategy.strategy_profile,
    )
    _reset_asset_selector_state()
    asset = AssetSelectionAgentService().select(
        AssetSelectionInput(
            niche="horror",
            topic="sealed corridor warning",
            strategy_profile=strategy.strategy_profile,
            trend_profile=_trend_profile(),
            script_plan=script.script_plan,
        )
    )
    artifacts = _write_qc_artifacts(tmp_root / "qc_artifacts", script.script_plan.narration_text())
    qc = _StaticProbeVideoQcAgentService().evaluate(
        qc_input=VideoQcInput(
            render_job_id="wave2_master_output_chain",
            video_path=str(artifacts["video"]),
            audio_path=str(artifacts["audio"]),
            metadata_path=str(artifacts["metadata"]),
            script_text=script.script_plan.narration_text(),
            tts_trace=voice.voice_trace,
            visual_trace=asset.asset_trace,
            edit_trace={"source": "wave2_master_gate_controlled_artifact", "segments": ["hook", "setup", "payoff"]},
        )
    )
    return {
        "strategy": strategy.to_dict(),
        "script": script.to_dict(),
        "voice": voice.to_dict(),
        "asset": asset.to_dict(),
        "video_qc": qc.to_dict(),
        "summary": _chain_summary(script.to_dict(), voice.to_dict(), asset.to_dict(), qc.to_dict()),
    }


def _chain_summary(script: dict[str, Any], voice: dict[str, Any], asset: dict[str, Any], qc: dict[str, Any]) -> dict[str, Any]:
    return {
        "script_generation_mode": script.get("script_plan", {}).get("generation_mode"),
        "script_trace_reconstructible": script.get("script_trace", {}).get("audit_summary", {}).get("reconstructible"),
        "voice_provider": voice.get("voice_plan", {}).get("provider"),
        "voice_trace_reconstructible": voice.get("voice_trace", {}).get("audit_summary", {}).get("reconstructible"),
        "asset_fallback_used": asset.get("fallback", {}).get("used"),
        "asset_trace_reconstructible": asset.get("asset_trace", {}).get("audit_summary", {}).get("reconstructible"),
        "qc_status": qc.get("status"),
        "qc_publishable": qc.get("publishable"),
        "qc_trace_reconstructible": qc.get("qc_trace", {}).get("audit_summary", {}).get("reconstructible"),
        "qc_confidence_meaning": qc.get("confidence_rationale", {}).get("confidence_meaning"),
    }


def _run_scenarios() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _run_output_chain(Path(tmp))
        replay_root = Path(tmp) / "replay"
        replay_one = _run_output_chain(replay_root)
        replay_two = _run_output_chain(replay_root)
    replay_fields = {
        "script_plan": (replay_one["script"]["script_plan"], replay_two["script"]["script_plan"]),
        "voice_plan": (replay_one["voice"]["voice_plan"], replay_two["voice"]["voice_plan"]),
        "asset_selection": (replay_one["asset"]["asset_selection"], replay_two["asset"]["asset_selection"]),
        "qc_status": (replay_one["video_qc"]["status"], replay_two["video_qc"]["status"]),
        "qc_publishable": (replay_one["video_qc"]["publishable"], replay_two["video_qc"]["publishable"]),
        "qc_confidence": (replay_one["video_qc"]["confidence"], replay_two["video_qc"]["confidence"]),
        "qc_trace": (replay_one["video_qc"]["qc_trace"], replay_two["video_qc"]["qc_trace"]),
    }
    replay_failures = [
        field
        for field, (left, right) in replay_fields.items()
        if left != right
    ]
    return {
        "output_chain_contract_flow": {
            "passed": _output_chain_passed(chain),
            "summary": chain["summary"],
            "result": chain,
        },
        "determinism_replay": {
            "passed": not replay_failures,
            "failures": replay_failures,
            "first_summary": replay_one["summary"],
            "second_summary": replay_two["summary"],
        },
        "backward_compatibility": {
            "passed": _all_serializable(chain),
            "summary": chain["summary"],
        },
    }


def _output_chain_passed(chain: dict[str, Any]) -> bool:
    script = chain["script"]
    voice = chain["voice"]
    asset = chain["asset"]
    qc = chain["video_qc"]
    return (
        bool(script.get("script_plan", {}).get("hook"))
        and bool(voice.get("voice_plan", {}).get("provider"))
        and bool(asset.get("asset_selection"))
        and qc.get("status") in {"APPROVE", "HOLD", "REJECT"}
        and qc.get("qc_trace", {}).get("audit_summary", {}).get("reconstructible") is True
        and script.get("script_trace", {}).get("audit_summary", {}).get("reconstructible") is True
        and voice.get("voice_trace", {}).get("audit_summary", {}).get("reconstructible") is True
        and asset.get("asset_trace", {}).get("audit_summary", {}).get("reconstructible") is True
    )


def _all_serializable(payload: dict[str, Any]) -> bool:
    try:
        json.dumps(payload)
        return True
    except TypeError:
        return False


def _child_gate_passed(payload: dict[str, Any], *, required_true: list[str]) -> bool:
    if payload.get("verdict") not in {"GO", "GO_WITH_MONITORING"}:
        return False
    if payload.get("blocking_failures", []) not in ([], None):
        return False
    if int(payload.get("critical_failures", 0) or 0) != 0:
        return False
    release_state = str(payload.get("release_state") or payload.get("release_verdict") or "")
    if release_state and "READY_FOR_V3_WITH_MONITORING" not in release_state and "READY" not in release_state:
        return False
    if payload.get("silent_failures_detected") is not False:
        return False
    if payload.get("boundary_preserved") is not True:
        return False
    for key in required_true:
        if payload.get(key) is not True:
            return False
    if "fallback_honest" in payload and payload.get("fallback_honest") is not True:
        return False
    if "determinism_where_required" in payload and payload.get("determinism_where_required") is not True:
        return False
    return True


def _validate_blocks(
    *,
    artifacts: dict[str, dict[str, Any]],
    json_errors: dict[str, str],
    existence: dict[str, bool],
    scenarios: dict[str, Any],
    pytest_result: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    blocks: dict[str, dict[str, Any]] = {}
    cross_agent = _cross_agent_consistency(scenarios)

    def add(block_id: str, passed: bool, details: Any = None) -> None:
        blocks[block_id] = {"passed": bool(passed), "details": details}

    required_doc_status = {name: (ROOT / path).exists() for name, path in REQUIRED_DOCS.items()}
    required_runner_status = {name: (ROOT / path).exists() for name, path in REQUIRED_RUNNERS.items()}
    required_json_status = {name: existence.get(name, False) and name not in json_errors for name in REQUIRED_JSON_ARTIFACTS}
    add("block_a_artifact_integrity", all(required_doc_status.values()) and all(required_runner_status.values()) and all(required_json_status.values()), {
        "docs": required_doc_status,
        "runners": required_runner_status,
        "json_artifacts": required_json_status,
        "json_errors": json_errors,
    })

    governance = artifacts.get("system_governance_registry", {})
    governance_passed = (
        governance.get("core_pipeline", {}).get("status") == "FROZEN_AND_VALIDATED"
        and governance.get("core_pipeline", {}).get("change_policy") == "FROZEN_UNLESS_GOVERNANCE_REOPEN"
        and governance.get("global_rules", {}).get("no_core_modification") is True
        and governance.get("global_rules", {}).get("no_subsystem_mutation_without_reopen") is True
        and governance.get("global_rules", {}).get("new_work_must_be_isolated_subsystems") is True
    )
    add("block_b_governance_consistency", governance_passed, governance.get("core_pipeline", {}))

    add("block_c_script_gate_integrity", _child_gate_passed(
        artifacts.get("script_gate", {}),
        required_true=["runtime_real", "context_governed", "confidence_calibrated", "traceability_complete", "boundary_preserved"],
    ), _child_summary(artifacts.get("script_gate", {})))
    add("block_d_voice_gate_integrity", _child_gate_passed(
        artifacts.get("voice_gate", {}),
        required_true=["runtime_real", "contract_governed", "confidence_calibrated", "traceability_complete", "boundary_preserved"],
    ), _child_summary(artifacts.get("voice_gate", {})))
    add("block_e_asset_gate_integrity", _child_gate_passed(
        artifacts.get("asset_gate", {}),
        required_true=["runtime_real", "context_governed", "catalog_source_governed", "confidence_calibrated", "traceability_complete", "boundary_preserved"],
    ), _child_summary(artifacts.get("asset_gate", {})))
    add("block_f_video_qc_gate_integrity", _child_gate_passed(
        artifacts.get("video_qc_gate", {}),
        required_true=["runtime_real", "input_governed", "evidence_scoring_complete", "confidence_honest", "traceability_complete", "boundary_preserved"],
    ), _child_summary(artifacts.get("video_qc_gate", {})))

    chain = scenarios.get("output_chain_contract_flow", {}).get("result", {})
    add("block_g_contract_integrity", _contracts_valid(chain), _chain_contract_summary(chain))
    add("block_h_output_pipeline_integration", scenarios.get("output_chain_contract_flow", {}).get("passed") is True, scenarios.get("output_chain_contract_flow", {}).get("summary"))
    add("block_i_orchestrator_compatibility", pytest_result.get("passed") is True, pytest_result.get("output_tail"))
    add("block_j_determinism_and_replay", scenarios.get("determinism_replay", {}).get("passed") is True, scenarios.get("determinism_replay", {}).get("failures"))
    add("block_k_fallback_honesty", _fallback_honest(artifacts=artifacts, chain=chain), _fallback_summary(artifacts=artifacts, chain=chain))
    add("block_l_boundary_preservation", cross_agent.get("boundary_preserved") is True, cross_agent)
    add("block_m_trace_auditability", _trace_complete(chain), _trace_summary(chain))
    add("block_n_security_logical_vulnerability_surface", _security_surface_clean(artifacts=artifacts, chain=chain), _security_summary(artifacts=artifacts, chain=chain))
    add("block_o_residual_monitoring_classification", _residuals_valid(artifacts), _residual_summary(artifacts))

    preliminary_failures = [
        name
        for name, result in blocks.items()
        if name != "block_p_final_release_decision" and not result.get("passed")
    ]
    add("block_p_final_release_decision", not preliminary_failures, {"preliminary_failures": preliminary_failures})
    return blocks, cross_agent


def _child_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "verdict": payload.get("verdict"),
        "release_state": payload.get("release_state"),
        "critical_failures": payload.get("critical_failures", payload.get("metrics", {}).get("critical_failures")),
        "blocking_failures": payload.get("blocking_failures"),
        "silent_failures_detected": payload.get("silent_failures_detected"),
        "boundary_preserved": payload.get("boundary_preserved"),
        "residual_monitoring": payload.get("residual_monitoring", []),
    }


def _contracts_valid(chain: dict[str, Any]) -> bool:
    required = {
        "script": ["script_plan", "fallback", "script_trace", "confidence"],
        "voice": ["voice_plan", "fallback", "voice_trace", "confidence"],
        "asset": ["asset_selection", "fallback", "asset_trace", "confidence"],
        "video_qc": ["decision", "status", "publishable", "qc_trace", "confidence"],
        "strategy": ["strategy_profile", "fallback", "decision_trace"],
    }
    return all(
        all(field in chain.get(agent, {}) for field in fields)
        for agent, fields in required.items()
    ) and _all_serializable(chain)


def _chain_contract_summary(chain: dict[str, Any]) -> dict[str, Any]:
    return {
        "script_fields": sorted(chain.get("script", {}).keys()),
        "voice_fields": sorted(chain.get("voice", {}).keys()),
        "asset_fields": sorted(chain.get("asset", {}).keys()),
        "video_qc_fields": sorted(chain.get("video_qc", {}).keys()),
    }


def _fallback_honest(*, artifacts: dict[str, dict[str, Any]], chain: dict[str, Any]) -> bool:
    child_fallback = all(
        payload.get("fallback_honest", True) is True
        for payload in [
            artifacts.get("script_gate", {}),
            artifacts.get("voice_gate", {}),
            artifacts.get("asset_gate", {}),
            artifacts.get("video_qc_gate", {}),
        ]
    )
    voice_missing_audio_visible = chain.get("voice", {}).get("audio_validation_linkage", {}).get("audio_trace_available") is False
    qc_missing_trace_visible = "tts_trace" in chain.get("video_qc", {}).get("qc_input_governance", {}).get("degraded_inputs", []) or "tts_trace" in chain.get("video_qc", {}).get("qc_input_governance", {}).get("missing_inputs", [])
    return child_fallback and voice_missing_audio_visible and qc_missing_trace_visible


def _fallback_summary(*, artifacts: dict[str, dict[str, Any]], chain: dict[str, Any]) -> dict[str, Any]:
    return {
        "child_fallback_honest": {
            name: artifacts.get(name, {}).get("fallback_honest", True)
            for name in ["script_gate", "voice_gate", "asset_gate", "video_qc_gate"]
        },
        "voice_audio_trace_available": chain.get("voice", {}).get("audio_validation_linkage", {}).get("audio_trace_available"),
        "qc_missing_inputs": chain.get("video_qc", {}).get("qc_input_governance", {}).get("missing_inputs", []),
        "qc_degraded_inputs": chain.get("video_qc", {}).get("qc_input_governance", {}).get("degraded_inputs", []),
    }


def _trace_complete(chain: dict[str, Any]) -> bool:
    script_trace = chain.get("script", {}).get("script_trace", {})
    voice_trace = chain.get("voice", {}).get("voice_trace", {})
    asset_trace = chain.get("asset", {}).get("asset_trace", {})
    qc_trace = chain.get("video_qc", {}).get("qc_trace", {})
    return (
        SCRIPT_TRACE_SECTIONS.issubset(script_trace)
        and VOICE_TRACE_SECTIONS.issubset(voice_trace)
        and ASSET_TRACE_SECTIONS.issubset(asset_trace)
        and QC_TRACE_SECTIONS.issubset(qc_trace)
        and script_trace.get("audit_summary", {}).get("reconstructible") is True
        and voice_trace.get("audit_summary", {}).get("reconstructible") is True
        and asset_trace.get("audit_summary", {}).get("reconstructible") is True
        and qc_trace.get("audit_summary", {}).get("reconstructible") is True
    )


def _trace_summary(chain: dict[str, Any]) -> dict[str, Any]:
    return {
        "script_missing": sorted(SCRIPT_TRACE_SECTIONS.difference(chain.get("script", {}).get("script_trace", {}))),
        "voice_missing": sorted(VOICE_TRACE_SECTIONS.difference(chain.get("voice", {}).get("voice_trace", {}))),
        "asset_missing": sorted(ASSET_TRACE_SECTIONS.difference(chain.get("asset", {}).get("asset_trace", {}))),
        "qc_missing": sorted(QC_TRACE_SECTIONS.difference(chain.get("video_qc", {}).get("qc_trace", {}))),
        "reconstructible": {
            "script": chain.get("script", {}).get("script_trace", {}).get("audit_summary", {}).get("reconstructible"),
            "voice": chain.get("voice", {}).get("voice_trace", {}).get("audit_summary", {}).get("reconstructible"),
            "asset": chain.get("asset", {}).get("asset_trace", {}).get("audit_summary", {}).get("reconstructible"),
            "video_qc": chain.get("video_qc", {}).get("qc_trace", {}).get("audit_summary", {}).get("reconstructible"),
        },
    }


def _security_surface_clean(*, artifacts: dict[str, dict[str, Any]], chain: dict[str, Any]) -> bool:
    fake_confidence = any(
        payload.get("fake_confidence") is True or payload.get("fake_confidence_detected") is True
        for payload in artifacts.values()
    )
    silent = any(payload.get("silent_failures_detected") is True for payload in artifacts.values())
    forbidden = bool(_forbidden_keys(chain))
    qc_publishability_ok = chain.get("video_qc", {}).get("status") != "APPROVE" or chain.get("video_qc", {}).get("publishable") is True
    no_publisher = "publish_manifest" not in chain.get("video_qc", {})
    return not fake_confidence and not silent and not forbidden and qc_publishability_ok and no_publisher


def _security_summary(*, artifacts: dict[str, dict[str, Any]], chain: dict[str, Any]) -> dict[str, Any]:
    return {
        "fake_confidence_flags": {
            name: payload.get("fake_confidence", payload.get("fake_confidence_detected"))
            for name, payload in artifacts.items()
            if "gate" in name
        },
        "silent_failure_flags": {
            name: payload.get("silent_failures_detected")
            for name, payload in artifacts.items()
            if "gate" in name
        },
        "forbidden_keys": _forbidden_keys(chain),
        "video_qc_status": chain.get("video_qc", {}).get("status"),
        "video_qc_publishable": chain.get("video_qc", {}).get("publishable"),
    }


def _forbidden_keys(payload: Any) -> list[str]:
    found: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_text = str(key).lower()
            if any(fragment in key_text for fragment in FORBIDDEN_KEY_FRAGMENTS):
                found.append(str(key))
            found.extend(_forbidden_keys(value))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(_forbidden_keys(item))
    return found


def _residuals_valid(artifacts: dict[str, dict[str, Any]]) -> bool:
    residuals = _collect_residuals(artifacts)
    return all(
        any(fragment in residual for fragment in ALLOWED_RESIDUAL_FRAGMENTS)
        for residual in residuals
    )


def _residual_summary(artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    residuals = _collect_residuals(artifacts)
    invalid = [
        residual
        for residual in residuals
        if not any(fragment in residual for fragment in ALLOWED_RESIDUAL_FRAGMENTS)
    ]
    return {"residuals": residuals, "invalid_residuals": invalid}


def _collect_residuals(artifacts: dict[str, dict[str, Any]]) -> list[str]:
    residuals: list[str] = []
    for name in ["script_gate", "voice_gate", "asset_gate", "video_qc_gate"]:
        residuals.extend(str(item) for item in artifacts.get(name, {}).get("residual_monitoring", []))
    return list(dict.fromkeys(residuals))


def _cross_agent_consistency(scenarios: dict[str, Any]) -> dict[str, Any]:
    chain = scenarios.get("output_chain_contract_flow", {}).get("result", {})
    strategy = chain.get("strategy", {})
    script = chain.get("script", {})
    voice = chain.get("voice", {})
    asset = chain.get("asset", {})
    qc = chain.get("video_qc", {})
    checks = {
        "script_feeds_voice": bool(script.get("script_plan")) and voice.get("voice_trace", {}).get("audit_summary", {}).get("reconstructible") is True,
        "script_feeds_asset": bool(script.get("script_plan")) and asset.get("asset_trace", {}).get("audit_summary", {}).get("reconstructible") is True,
        "voice_does_not_become_strategy": "strategy_profile" not in voice and "publishable" not in voice,
        "asset_does_not_become_strategy_or_qc": "strategy_profile" not in asset and "publishable" not in asset,
        "qc_final_artifact_evaluator": qc.get("qc_trace", {}).get("audit_summary", {}).get("reconstructible") is True and "script_plan" not in qc and "asset_selection" not in qc,
        "strategy_remains_control_layer": bool(strategy.get("strategy_profile")) and "decision_trace" in strategy,
        "no_output_agent_overrides_strategy": all("strategy_profile" not in payload for payload in [script, voice, asset, qc]),
        "no_new_publishability_authority_except_qc": "publishable" not in script and "publishable" not in voice and "publishable" not in asset and "publishable" in qc,
        "fallbacks_visible": script.get("fallback") is not None and voice.get("fallback") is not None and asset.get("fallback") is not None,
    }
    checks["boundary_preserved"] = all(checks.values())
    return checks


def _metrics(blocks: dict[str, dict[str, Any]], tests: dict[str, Any], blocking_failures: list[str]) -> dict[str, Any]:
    return {
        "blocks_total": len(blocks),
        "blocks_passed": sum(1 for block in blocks.values() if block.get("passed")),
        "critical_failures": len(blocking_failures),
        "blocking_failures_count": len(blocking_failures),
        "test_failures": 0 if tests.get("passed") else 1,
        "boundary_violations_detected": blocks.get("block_l_boundary_preservation", {}).get("passed") is not True,
        "silent_failures_detected": blocks.get("block_n_security_logical_vulnerability_surface", {}).get("passed") is not True,
        "fake_confidence_detected": False if blocks.get("block_n_security_logical_vulnerability_surface", {}).get("passed") else None,
        "non_determinism_detected": blocks.get("block_j_determinism_and_replay", {}).get("passed") is not True,
        "trace_incomplete": blocks.get("block_m_trace_auditability", {}).get("passed") is not True,
    }


def _blocking_failures(blocks: dict[str, dict[str, Any]], tests: dict[str, Any]) -> list[str]:
    failures = [
        name
        for name, result in blocks.items()
        if not result.get("passed")
    ]
    if not tests.get("passed"):
        failures.append("critical_test_battery_failed")
    return list(dict.fromkeys(failures))


def _derive_verdict(blocking_failures: list[str], residuals: list[str]) -> str:
    if blocking_failures:
        return "HOLD"
    if residuals:
        return "GO_WITH_MONITORING"
    return "GO"


def main() -> int:
    _reset_audit_dir()
    artifacts, json_errors, existence = _load_artifacts()
    scenarios = _run_scenarios()
    pytest_result = _run_pytest(UNIT_TEST_FILES)
    blocks, cross_agent = _validate_blocks(
        artifacts=artifacts,
        json_errors=json_errors,
        existence=existence,
        scenarios=scenarios,
        pytest_result=pytest_result,
    )
    blocking_failures = _blocking_failures(blocks, pytest_result)
    residuals = [] if blocking_failures else _collect_residuals(artifacts)
    verdict = _derive_verdict(blocking_failures, residuals)
    metrics = _metrics(blocks, pytest_result, blocking_failures)
    timestamp = datetime.now().astimezone().replace(microsecond=0).isoformat()
    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "2.6",
        "audit_type": "PHASE_2_6_WAVE_2_MASTER_GATE",
        "timestamp": timestamp,
        "verdict": verdict,
        "wave_2_agents": {
            "script_agent_v2_6": _agent_summary(artifacts.get("script_gate", {})),
            "voice_agent_v2_6": _agent_summary(artifacts.get("voice_gate", {})),
            "asset_selection_agent_v2_6": _agent_summary(artifacts.get("asset_gate", {})),
            "video_qc_agent_v2_6": _agent_summary(artifacts.get("video_qc_gate", {})),
        },
        "blocks": blocks,
        "tests_executed": [pytest_result],
        "metrics": metrics,
        "blocking_failures": blocking_failures,
        "residual_monitoring": residuals,
        "recommendation": "PROCEED_TO_PHASE_2_6_FINAL_MASTER_GATE" if verdict in {"GO", "GO_WITH_MONITORING"} else "HOLD_BEFORE_PHASE_2_6_FINAL_MASTER_GATE",
    }
    _write_json(SCENARIO_OUTPUTS_PATH, scenarios)
    _write_json(CHECKLIST_RESULTS_PATH, blocks)
    _write_json(METRICS_PATH, metrics)
    _write_json(CROSS_AGENT_CONSISTENCY_PATH, cross_agent)
    _write_json(FINAL_VERDICT_PATH, final_verdict)
    print(json.dumps({
        "verdict": verdict,
        "blocks": f"{metrics['blocks_passed']}/{metrics['blocks_total']}",
        "tests_passed": pytest_result.get("passed"),
        "blocking_failures": blocking_failures,
        "residual_monitoring": residuals,
        "recommendation": final_verdict["recommendation"],
        "final_verdict": str(FINAL_VERDICT_PATH),
    }, indent=2))
    return 0 if verdict in {"GO", "GO_WITH_MONITORING"} else 1


def _agent_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "verdict": payload.get("verdict"),
        "ready_for_v3_with_monitoring": payload.get("release_state") == "READY_FOR_V3_WITH_MONITORING",
        "critical_failures": payload.get("critical_failures", payload.get("metrics", {}).get("critical_failures", 0)),
        "blocking_failures": payload.get("blocking_failures", []),
    }


if __name__ == "__main__":
    raise SystemExit(main())
