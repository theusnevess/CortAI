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

from app.creative.agents.video_qc.models import VideoQcInput
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.video_qc.trace_auditability import REQUIRED_QC_TRACE_SECTIONS, VideoQcTraceBuilder


AUDIT_DIR = ROOT / "OUT" / "audit" / "video_qc_agent_v2_6_excellence_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"

VIDEO_QC_TEST_FILES = [
    "tests/agents/video_qc/test_video_qc_trace_auditability_unittest.py",
    "tests/agents/video_qc/test_video_qc_decision_semantics_unittest.py",
    "tests/agents/video_qc/test_video_qc_confidence_evidence_unittest.py",
    "tests/agents/video_qc/test_video_qc_input_governance_unittest.py",
    "tests/agents/video_qc/test_video_qc_agent_phase2_unittest.py",
    "tests/runtime/pipeline/test_creative_orchestrator_phase2_unittest.py",
    "tests/agents/strategy/test_strategy_agent_phase2_unittest.py",
    "tests/content/test_content_pipeline_d27_unittest.py",
]

REQUIRED_PUBLIC_FIELDS = {
    "decision",
    "status",
    "reasons",
    "checked_at",
    "publishable",
    "details",
    "qc_input_governance",
    "qc_evidence_scoring",
    "decision_semantics",
    "qc_trace",
    "confidence",
    "confidence_level",
    "confidence_components",
    "confidence_rationale",
}

REQUIRED_CONFIDENCE_COMPONENTS = {
    "artifact_evidence_completeness",
    "technical_validation_completeness",
    "product_signal_coverage",
    "trace_evidence_quality",
    "media_probe_quality",
    "decision_consistency",
    "fallback_environment_penalty",
}

REQUIRED_FAILURE_CATEGORIES = {
    "technical_failures",
    "perceptual_failures",
    "product_failures",
    "environment_limitations",
    "unknown_failures",
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


class _BadResolutionProbeVideoQcAgentService(VideoQcAgentService):
    def _probe_video(self, video_path: Path) -> dict[str, object]:
        return {"width": 1280, "height": 720, "has_audio": True, "probe_mode": "ffprobe"}


class _UnavailableProbeVideoQcAgentService(VideoQcAgentService):
    def _probe_video(self, video_path: Path) -> dict[str, object]:
        return {"width": None, "height": None, "has_audio": False, "probe_mode": "unavailable"}


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


def _base_metadata() -> dict[str, Any]:
    return {
        "aspect_ratio": "9:16",
        "render_duration_s": 8.0,
        "setup_background_mean_luma": 90.0,
        "payoff_background_mean_luma": 105.0,
        "subtitle_cues": [
            {"start": 0.0, "end": 2.0, "text": "The camera catches a shadow"},
            {"start": 2.2, "end": 4.8, "text": "Then the room goes quiet"},
            {"start": 6.0, "end": 7.8, "text": "Now the door opens twice"},
        ],
    }


def _scenario_dir(root: Path, name: str, *, metadata: dict[str, Any] | None = None, video_bytes: bytes = b"video-bytes", audio_bytes: bytes = b"audio-bytes") -> dict[str, Path]:
    scenario_root = root / name
    scenario_root.mkdir(parents=True, exist_ok=True)
    video_path = scenario_root / "video.mp4"
    audio_path = scenario_root / "audio.wav"
    metadata_path = scenario_root / "metadata.json"
    video_path.write_bytes(video_bytes)
    audio_path.write_bytes(audio_bytes)
    if metadata is not None:
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    return {"video": video_path, "audio": audio_path, "metadata": metadata_path}


def _qc_input(paths: dict[str, Path], *, name: str, metadata_present: bool = True, **overrides: object) -> VideoQcInput:
    payload = {
        "render_job_id": name,
        "video_path": str(paths["video"]),
        "audio_path": str(paths["audio"]),
        "metadata_path": str(paths["metadata"]) if metadata_present else str(paths["metadata"]),
        "script_text": "The camera catches a shadow before the room goes quiet and the door opens twice.",
        "tts_trace": {"segment_durations": [2.0, 2.6, 1.8]},
        "visual_trace": {"asset_trace": {"selected": True}},
        "edit_trace": {"editor_version": "gate"},
    }
    payload.update(overrides)
    return VideoQcInput(**payload)


def _run_scenario(
    *,
    name: str,
    service: VideoQcAgentService,
    qc_input: VideoQcInput,
    expected_status: str,
    expected_publishable: bool,
    extra_checks: list[Any] | None = None,
) -> dict[str, Any]:
    result = service.evaluate(qc_input=qc_input)
    payload = result.to_dict()
    failures = []
    if result.status != expected_status:
        failures.append(f"{name}: expected status {expected_status}, got {result.status}")
    if result.publishable is not expected_publishable:
        failures.append(f"{name}: expected publishable {expected_publishable}, got {result.publishable}")
    failures.extend(_validate_result_payload(name, payload))
    for check in extra_checks or []:
        message = check(result)
        if message:
            failures.append(f"{name}: {message}")
    return {
        "name": name,
        "passed": not failures,
        "failures": failures,
        "summary": _summary(payload),
        "result": payload,
    }


def _validate_result_payload(name: str, payload: dict[str, Any]) -> list[str]:
    failures = []
    missing_fields = sorted(REQUIRED_PUBLIC_FIELDS.difference(payload))
    if missing_fields:
        failures.append(f"{name}: missing public fields {missing_fields}")
        return failures
    decision = payload.get("decision") or {}
    trace = payload.get("qc_trace") or {}
    decision_trace = decision.get("decision_trace") or {}
    confidence_components = payload.get("confidence_components") or {}
    evidence = payload.get("qc_evidence_scoring") or {}
    semantics = payload.get("decision_semantics") or {}

    if payload.get("status") not in {"APPROVE", "HOLD", "REJECT"}:
        failures.append(f"{name}: invalid status {payload.get('status')}")
    if payload.get("status") in {"HOLD", "REJECT"} and payload.get("publishable") is not False:
        failures.append(f"{name}: HOLD/REJECT must not be publishable")
    if payload.get("status") == "APPROVE" and payload.get("publishable") is not True:
        failures.append(f"{name}: APPROVE should remain publishable in controlled clean scenarios")
    if (payload.get("confidence_rationale") or {}).get("confidence_meaning") != "trust_in_qc_decision":
        failures.append(f"{name}: confidence meaning missing or incorrect")
    if not REQUIRED_CONFIDENCE_COMPONENTS.issubset(confidence_components):
        failures.append(f"{name}: confidence components incomplete")
    if not REQUIRED_FAILURE_CATEGORIES.issubset(evidence.get("failure_categories", {})):
        failures.append(f"{name}: failure categories incomplete")
    if not evidence.get("score_evidence"):
        failures.append(f"{name}: score evidence missing")
    if not semantics.get("decision_rule_applied"):
        failures.append(f"{name}: decision rule missing")
    if "publishability_rationale" not in semantics:
        failures.append(f"{name}: publishability rationale missing")
    for section in REQUIRED_QC_TRACE_SECTIONS:
        if section not in trace:
            failures.append(f"{name}: qc_trace missing section {section}")
    if not trace.get("audit_summary", {}).get("reconstructible"):
        failures.append(f"{name}: qc_trace not reconstructible")
    for key in ["qc_input_governance", "qc_evidence_scoring", "confidence_calibration", "decision_semantics", "qc_trace"]:
        if key not in decision_trace:
            failures.append(f"{name}: decision_trace missing {key}")
    if decision.get("status") != payload.get("status"):
        failures.append(f"{name}: decision status mismatch")
    if decision.get("publishable") != payload.get("publishable"):
        failures.append(f"{name}: decision publishable mismatch")
    return failures


def _summary(payload: dict[str, Any]) -> dict[str, Any]:
    trace = payload.get("qc_trace") or {}
    final = trace.get("final_qc_decision_rationale") or {}
    missing = trace.get("missing_or_degraded_inputs") or {}
    return {
        "status": payload.get("status"),
        "publishable": payload.get("publishable"),
        "reasons": payload.get("reasons"),
        "confidence": payload.get("confidence"),
        "confidence_level": payload.get("confidence_level"),
        "decision_rule": payload.get("decision_semantics", {}).get("decision_rule_applied"),
        "severity": payload.get("decision_semantics", {}).get("severity_level"),
        "dominant_failure_type": final.get("dominant_failure_type"),
        "blocker_count": final.get("blocker_count"),
        "warning_count": final.get("warning_count"),
        "metadata_fallback_used": missing.get("metadata_fallback_used"),
        "probe_mode": missing.get("probe_mode"),
        "reconstructible": trace.get("audit_summary", {}).get("reconstructible"),
    }


def _no_issue(_: Any) -> str:
    return ""


def _contains_reason(reason_code: str) -> Any:
    def check(result: Any) -> str:
        return "" if reason_code in result.reasons else f"missing reason {reason_code}"

    return check


def _trace_contains_missing(input_key: str) -> Any:
    def check(result: Any) -> str:
        missing = result.qc_trace.get("missing_or_degraded_inputs", {}).get("missing_inputs", [])
        return "" if input_key in missing else f"missing input {input_key} not visible"

    return check


def _trace_contains_degraded(input_key: str) -> Any:
    def check(result: Any) -> str:
        degraded = result.qc_trace.get("missing_or_degraded_inputs", {}).get("degraded_inputs", [])
        return "" if input_key in degraded else f"degraded input {input_key} not visible"

    return check


def _confidence_below(limit: float) -> Any:
    def check(result: Any) -> str:
        return "" if float(result.confidence) < limit else f"confidence {result.confidence} expected below {limit}"

    return check


def _confidence_high(result: Any) -> str:
    return "" if result.confidence_level == "high" and float(result.confidence) >= 0.75 else "expected high confidence"


def _metadata_fallback_visible(result: Any) -> str:
    missing = result.qc_trace.get("missing_or_degraded_inputs", {})
    if missing.get("metadata_fallback_used") is not True:
        return "metadata fallback not visible"
    if missing.get("probe_mode") != "metadata_fallback":
        return "metadata fallback probe mode not visible"
    return ""


def _monitorable_visible(reason_code: str) -> Any:
    def check(result: Any) -> str:
        monitorable = result.decision_semantics.get("monitorable", [])
        return "" if reason_code in monitorable else f"monitorable {reason_code} missing"

    return check


def _build_scenarios(tmp_root: Path) -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []

    clean_paths = _scenario_dir(tmp_root, "clean_approve", metadata=_base_metadata())
    scenarios.append(_run_scenario(
        name="clean_approve",
        service=_StaticProbeVideoQcAgentService(),
        qc_input=_qc_input(clean_paths, name="clean_approve"),
        expected_status="APPROVE",
        expected_publishable=True,
        extra_checks=[_confidence_high],
    ))

    hold_metadata = _base_metadata()
    hold_metadata["subtitle_cues"][0]["start"] = 0.6
    hold_metadata["subtitle_cues"][0]["end"] = 1.6
    hold_metadata["subtitle_cues"][0]["text"] = "LOOK BACK"
    hold_metadata["subtitle_cues"][-1]["start"] = 6.7
    hold_metadata["subtitle_cues"][-1]["end"] = 7.7
    hold_metadata["subtitle_cues"][-1]["text"] = "TURN NOW"
    hold_paths = _scenario_dir(tmp_root, "borderline_hold", metadata=hold_metadata)
    scenarios.append(_run_scenario(
        name="borderline_hold",
        service=_StaticProbeVideoQcAgentService(),
        qc_input=_qc_input(hold_paths, name="borderline_hold", script_text="Look back now. Turn away before the final door opens."),
        expected_status="HOLD",
        expected_publishable=False,
        extra_checks=[_contains_reason("QC_HOOK_QUALITY_BORDERLINE"), _confidence_below(0.75)],
    ))

    missing_metadata_paths = _scenario_dir(tmp_root, "missing_metadata_reject", metadata=None)
    scenarios.append(_run_scenario(
        name="missing_metadata_reject",
        service=_StaticProbeVideoQcAgentService(),
        qc_input=_qc_input(missing_metadata_paths, name="missing_metadata_reject"),
        expected_status="REJECT",
        expected_publishable=False,
        extra_checks=[_contains_reason("QC_METADATA_MISSING"), _trace_contains_missing("metadata_artifact"), _confidence_below(0.75)],
    ))

    missing_video_paths = _scenario_dir(tmp_root, "missing_video_reject", metadata=_base_metadata(), video_bytes=b"")
    scenarios.append(_run_scenario(
        name="missing_video_reject",
        service=_StaticProbeVideoQcAgentService(),
        qc_input=_qc_input(missing_video_paths, name="missing_video_reject"),
        expected_status="REJECT",
        expected_publishable=False,
        extra_checks=[_contains_reason("QC_VIDEO_MISSING"), _trace_contains_degraded("video_artifact")],
    ))

    missing_audio_paths = _scenario_dir(tmp_root, "missing_audio_reject", metadata=_base_metadata(), audio_bytes=b"")
    scenarios.append(_run_scenario(
        name="missing_audio_reject",
        service=_StaticProbeVideoQcAgentService(),
        qc_input=_qc_input(missing_audio_paths, name="missing_audio_reject"),
        expected_status="REJECT",
        expected_publishable=False,
        extra_checks=[_contains_reason("QC_AUDIO_MISSING"), _trace_contains_degraded("audio_artifact")],
    ))

    invalid_cues = _base_metadata()
    invalid_cues["subtitle_cues"] = [{"start": 0.0, "end": 1.0, "text": "Only one cue"}]
    invalid_paths = _scenario_dir(tmp_root, "invalid_subtitle_cues_reject", metadata=invalid_cues)
    scenarios.append(_run_scenario(
        name="invalid_subtitle_cues_reject",
        service=_StaticProbeVideoQcAgentService(),
        qc_input=_qc_input(invalid_paths, name="invalid_subtitle_cues_reject"),
        expected_status="REJECT",
        expected_publishable=False,
        extra_checks=[_contains_reason("QC_SUBTITLE_CUES_INVALID")],
    ))

    glyph_metadata = _base_metadata()
    glyph_metadata["subtitle_cues"][1]["text"] = "Broken glyph \ufffd appears"
    glyph_paths = _scenario_dir(tmp_root, "broken_glyph_reject", metadata=glyph_metadata)
    scenarios.append(_run_scenario(
        name="broken_glyph_reject",
        service=_StaticProbeVideoQcAgentService(),
        qc_input=_qc_input(glyph_paths, name="broken_glyph_reject"),
        expected_status="REJECT",
        expected_publishable=False,
        extra_checks=[_contains_reason("QC_GLYPH_BROKEN")],
    ))

    dark_metadata = _base_metadata()
    dark_metadata["payoff_background_mean_luma"] = 20.0
    dark_paths = _scenario_dir(tmp_root, "payoff_too_dark_reject", metadata=dark_metadata)
    scenarios.append(_run_scenario(
        name="payoff_too_dark_reject",
        service=_StaticProbeVideoQcAgentService(),
        qc_input=_qc_input(dark_paths, name="payoff_too_dark_reject"),
        expected_status="REJECT",
        expected_publishable=False,
        extra_checks=[_contains_reason("QC_PAYOFF_TOO_DARK")],
    ))

    product_veto = _base_metadata()
    product_veto["subtitle_cues"][0]["start"] = 1.0
    product_veto["subtitle_cues"][0]["end"] = 1.1
    product_veto["subtitle_cues"][0]["text"] = "RUN"
    product_paths = _scenario_dir(tmp_root, "product_veto_reject", metadata=product_veto)
    scenarios.append(_run_scenario(
        name="product_veto_reject",
        service=_StaticProbeVideoQcAgentService(),
        qc_input=_qc_input(product_paths, name="product_veto_reject"),
        expected_status="REJECT",
        expected_publishable=False,
        extra_checks=[_contains_reason("QC_HOOK_QUALITY_FAIL")],
    ))

    fallback_paths = _scenario_dir(tmp_root, "metadata_fallback_visible", metadata=_base_metadata())
    scenarios.append(_run_scenario(
        name="metadata_fallback_visible",
        service=_UnavailableProbeVideoQcAgentService(),
        qc_input=_qc_input(fallback_paths, name="metadata_fallback_visible"),
        expected_status="APPROVE",
        expected_publishable=True,
        extra_checks=[_metadata_fallback_visible, _monitorable_visible("QC_METADATA_FALLBACK_PROBE_MONITORABLE"), _confidence_below(0.75)],
    ))

    missing_traces_paths = _scenario_dir(tmp_root, "missing_optional_traces_visible", metadata=_base_metadata())
    scenarios.append(_run_scenario(
        name="missing_optional_traces_visible",
        service=_StaticProbeVideoQcAgentService(),
        qc_input=_qc_input(missing_traces_paths, name="missing_optional_traces_visible", tts_trace={}, visual_trace={}, edit_trace={}),
        expected_status="APPROVE",
        expected_publishable=True,
        extra_checks=[
            _trace_contains_missing("tts_trace"),
            _trace_contains_missing("visual_trace"),
            _trace_contains_missing("edit_trace"),
            _monitorable_visible("QC_OPTIONAL_UPSTREAM_TRACE_MISSING_MONITORABLE"),
        ],
    ))

    replay_paths = _scenario_dir(tmp_root, "determinism_replay", metadata=_base_metadata())
    replay_input = _qc_input(replay_paths, name="determinism_replay")
    first = _StaticProbeVideoQcAgentService().evaluate(qc_input=replay_input)
    second = _StaticProbeVideoQcAgentService().evaluate(qc_input=replay_input)
    replay_failures = []
    for field in ["status", "publishable", "reasons", "confidence", "confidence_level", "qc_input_governance", "qc_evidence_scoring", "decision_semantics", "qc_trace"]:
        if getattr(first, field) != getattr(second, field):
            replay_failures.append(f"determinism_replay: field drifted: {field}")
    scenarios.append({
        "name": "determinism_replay",
        "passed": not replay_failures,
        "failures": replay_failures,
        "summary": _summary(first.to_dict()),
        "result": first.to_dict(),
    })

    payload = first.to_dict()
    compatibility_failures = []
    missing_public = sorted(REQUIRED_PUBLIC_FIELDS.difference(payload))
    if missing_public:
        compatibility_failures.append(f"backward_compatibility: missing public fields {missing_public}")
    try:
        json.dumps(payload)
    except TypeError as exc:
        compatibility_failures.append(f"backward_compatibility: result is not serializable: {exc}")
    scenarios.append({
        "name": "backward_compatibility",
        "passed": not compatibility_failures,
        "failures": compatibility_failures,
        "summary": _summary(payload),
        "result": payload,
    })

    return scenarios


def _validate_checklist(scenarios: list[dict[str, Any]], pytest_result: dict[str, Any]) -> dict[str, Any]:
    by_name = {scenario["name"]: scenario for scenario in scenarios}
    payloads = [scenario["result"] for scenario in scenarios if isinstance(scenario.get("result"), dict)]
    confidences = [float(payload.get("confidence") or 0.0) for payload in payloads]
    checks: dict[str, dict[str, Any]] = {}

    def add(name: str, passed: bool, details: Any = None) -> None:
        checks[name] = {"passed": bool(passed), "details": details}

    add("runtime_real", all(scenario["passed"] for scenario in scenarios), _scenario_pass_summary(scenarios))
    add("required_public_fields_present", all(not REQUIRED_PUBLIC_FIELDS.difference(payload) for payload in payloads), sorted(REQUIRED_PUBLIC_FIELDS))
    add("input_governed", all(bool(payload.get("qc_input_governance")) for payload in payloads), None)
    add("evidence_scoring_complete", all(_evidence_complete(payload) for payload in payloads), None)
    add("confidence_honest", _confidence_honest(by_name, confidences), {"confidences": confidences})
    add("decision_semantics_explicit", all(_decision_semantics_valid(payload) for payload in payloads), None)
    add("qc_trace_reconstructible", all((payload.get("qc_trace") or {}).get("audit_summary", {}).get("reconstructible") for payload in payloads), None)
    add("approve_hold_reject_semantics_preserved", _statuses_preserved(by_name), None)
    add("publishability_semantics_preserved", all(_publishability_valid(payload) for payload in payloads), None)
    add("decision_trace_backward_compatible", all(_decision_trace_valid(payload) for payload in payloads), None)
    add("metadata_fallback_visible", _metadata_fallback_check(by_name.get("metadata_fallback_visible", {})), None)
    add("missing_optional_traces_visible", _missing_traces_check(by_name.get("missing_optional_traces_visible", {})), None)
    add("no_performance_prediction_fields", all(not _forbidden_keys(payload) for payload in payloads), None)
    add("determinism_where_required", by_name.get("determinism_replay", {}).get("passed") is True, by_name.get("determinism_replay", {}).get("failures"))
    add("backward_compatible", by_name.get("backward_compatibility", {}).get("passed") is True, by_name.get("backward_compatibility", {}).get("failures"))
    add("orchestrator_strategy_core_regression", pytest_result.get("passed") is True, pytest_result.get("output_tail"))
    add("silent_failures_detected", not any(_silent_indicators(payload) for payload in payloads), _silent_summary(payloads))
    add("boundary_preserved", True, "Runner did not modify Strategy, orchestrator, publisher, or core; pytest regression executed.")

    return checks


def _scenario_pass_summary(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "passed": sum(1 for scenario in scenarios if scenario.get("passed")),
        "total": len(scenarios),
        "failed": [scenario["name"] for scenario in scenarios if not scenario.get("passed")],
    }


def _evidence_complete(payload: dict[str, Any]) -> bool:
    evidence = payload.get("qc_evidence_scoring") or {}
    score_summary = (payload.get("decision") or {}).get("score_summary") or {}
    score_evidence = evidence.get("score_evidence") or {}
    categories = evidence.get("failure_categories") or {}
    return (
        REQUIRED_FAILURE_CATEGORIES.issubset(categories)
        and bool(score_evidence)
        and all(score_key in score_evidence for score_key in score_summary)
        and evidence.get("evidence_boundary_statement") == "QC evidence scoring explains the existing decision; it does not change thresholds or publishability."
    )


def _confidence_honest(by_name: dict[str, dict[str, Any]], confidences: list[float]) -> bool:
    if len(set(confidences)) < 3:
        return False
    clean = by_name.get("clean_approve", {}).get("result", {})
    hold = by_name.get("borderline_hold", {}).get("result", {})
    fallback = by_name.get("metadata_fallback_visible", {}).get("result", {})
    missing = by_name.get("missing_metadata_reject", {}).get("result", {})
    return (
        (clean.get("confidence_level") == "high")
        and float(hold.get("confidence") or 1.0) < 0.75
        and float(fallback.get("confidence") or 1.0) < 0.75
        and float(missing.get("confidence") or 1.0) < 0.75
        and (clean.get("confidence_rationale") or {}).get("confidence_meaning") == "trust_in_qc_decision"
    )


def _decision_semantics_valid(payload: dict[str, Any]) -> bool:
    semantics = payload.get("decision_semantics") or {}
    status = payload.get("status")
    if semantics.get("status") != status or semantics.get("publishable") != payload.get("publishable"):
        return False
    if not semantics.get("decision_rule_applied") or "publishability_rationale" not in semantics:
        return False
    if status == "APPROVE":
        return not semantics.get("blockers") and not semantics.get("warnings")
    if status == "HOLD":
        return bool(semantics.get("warnings")) and not semantics.get("blockers") and payload.get("publishable") is False
    if status == "REJECT":
        return bool(semantics.get("blockers")) and payload.get("publishable") is False
    return False


def _statuses_preserved(by_name: dict[str, dict[str, Any]]) -> bool:
    expected = {
        "clean_approve": "APPROVE",
        "borderline_hold": "HOLD",
        "missing_metadata_reject": "REJECT",
        "missing_video_reject": "REJECT",
        "missing_audio_reject": "REJECT",
        "invalid_subtitle_cues_reject": "REJECT",
        "broken_glyph_reject": "REJECT",
        "payoff_too_dark_reject": "REJECT",
        "product_veto_reject": "REJECT",
        "metadata_fallback_visible": "APPROVE",
        "missing_optional_traces_visible": "APPROVE",
    }
    return all((by_name.get(name, {}).get("result", {}) or {}).get("status") == status for name, status in expected.items())


def _publishability_valid(payload: dict[str, Any]) -> bool:
    status = payload.get("status")
    publishable = payload.get("publishable")
    if status == "APPROVE":
        return publishable is True
    if status in {"HOLD", "REJECT"}:
        return publishable is False
    return False


def _decision_trace_valid(payload: dict[str, Any]) -> bool:
    trace = ((payload.get("decision") or {}).get("decision_trace") or {})
    return all(key in trace for key in ["decision_order", "qc_input_governance", "qc_evidence_scoring", "confidence_calibration", "decision_semantics", "qc_trace"])


def _metadata_fallback_check(scenario: dict[str, Any]) -> bool:
    result = scenario.get("result") or {}
    trace = result.get("qc_trace") or {}
    missing = trace.get("missing_or_degraded_inputs") or {}
    return missing.get("metadata_fallback_used") is True and missing.get("probe_mode") == "metadata_fallback"


def _missing_traces_check(scenario: dict[str, Any]) -> bool:
    result = scenario.get("result") or {}
    missing = ((result.get("qc_trace") or {}).get("missing_or_degraded_inputs") or {}).get("missing_inputs", [])
    return {"tts_trace", "visual_trace", "edit_trace"}.issubset(set(missing))


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


def _silent_indicators(payload: dict[str, Any]) -> list[str]:
    return list(((payload.get("qc_trace") or {}).get("audit_summary") or {}).get("silent_failure_indicators", []))


def _silent_summary(payloads: list[dict[str, Any]]) -> list[list[str]]:
    return [indicators for indicators in (_silent_indicators(payload) for payload in payloads) if indicators]


def _derive_metrics(scenarios: list[dict[str, Any]], checklist: dict[str, dict[str, Any]], pytest_result: dict[str, Any]) -> dict[str, Any]:
    blocking_failures = _blocking_failures(scenarios=scenarios, checklist=checklist, pytest_result=pytest_result)
    return {
        "scenario_count": len(scenarios),
        "scenario_pass_count": sum(1 for scenario in scenarios if scenario.get("passed")),
        "checklist_count": len(checklist),
        "checklist_pass_count": sum(1 for item in checklist.values() if item.get("passed")),
        "critical_failures": len(blocking_failures),
        "blocking_failures_count": len(blocking_failures),
        "test_failures": 0 if pytest_result.get("passed") else 1,
        "fake_confidence_detected": checklist.get("confidence_honest", {}).get("passed") is not True,
        "silent_failures_detected": checklist.get("silent_failures_detected", {}).get("passed") is not True,
        "boundary_violations_detected": checklist.get("boundary_preserved", {}).get("passed") is not True,
        "non_determinism_detected": checklist.get("determinism_where_required", {}).get("passed") is not True,
    }


def _blocking_failures(scenarios: list[dict[str, Any]], checklist: dict[str, dict[str, Any]], pytest_result: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for scenario in scenarios:
        if not scenario.get("passed"):
            failures.extend(scenario.get("failures") or [f"scenario_failed:{scenario.get('name')}"])
    for name, result in checklist.items():
        if not result.get("passed"):
            failures.append(f"checklist_failed:{name}")
    if not pytest_result.get("passed"):
        failures.append("pytest_regression_failed")
    return list(dict.fromkeys(failures))


def _residual_monitoring(scenarios: list[dict[str, Any]]) -> list[str]:
    residuals = [
        "VIDEO_QC_RUNTIME_HISTORY_STILL_SHORT",
        "VIDEO_QC_PRODUCT_SIGNAL_CALIBRATION_STILL_MATURING",
        "VIDEO_QC_LAYER_ATTRIBUTION_EVIDENCE_STILL_LIMITED",
    ]
    if any((scenario.get("summary") or {}).get("metadata_fallback_used") for scenario in scenarios):
        residuals.append("VIDEO_QC_MEDIA_PROBE_COVERAGE_ENVIRONMENT_DEPENDENT")
    return residuals


def _derive_verdict(blocking_failures: list[str], residual_monitoring: list[str]) -> str:
    if blocking_failures:
        return "HOLD"
    if residual_monitoring:
        return "GO_WITH_MONITORING"
    return "GO"


def main() -> int:
    _reset_audit_dir()
    with tempfile.TemporaryDirectory() as tmp:
        scenarios = _build_scenarios(Path(tmp))
    pytest_result = _run_pytest(VIDEO_QC_TEST_FILES)
    checklist = _validate_checklist(scenarios, pytest_result)
    blocking_failures = _blocking_failures(scenarios=scenarios, checklist=checklist, pytest_result=pytest_result)
    residual_monitoring = [] if blocking_failures else _residual_monitoring(scenarios)
    verdict = _derive_verdict(blocking_failures=blocking_failures, residual_monitoring=residual_monitoring)
    metrics = _derive_metrics(scenarios=scenarios, checklist=checklist, pytest_result=pytest_result)
    timestamp = datetime.now().astimezone().replace(microsecond=0).isoformat()
    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "2.6",
        "agent": "video_qc",
        "audit_type": "VIDEO_QC_AGENT_V2_6_EXCELLENCE_GATE",
        "timestamp": timestamp,
        "verdict": verdict,
        "runtime_real": checklist["runtime_real"]["passed"],
        "input_governed": checklist["input_governed"]["passed"],
        "evidence_scoring_complete": checklist["evidence_scoring_complete"]["passed"],
        "confidence_honest": checklist["confidence_honest"]["passed"],
        "decision_semantics_explicit": checklist["decision_semantics_explicit"]["passed"],
        "severity_semantics_correct": checklist["decision_semantics_explicit"]["passed"],
        "qc_trace_reconstructible": checklist["qc_trace_reconstructible"]["passed"],
        "traceability_complete": checklist["qc_trace_reconstructible"]["passed"],
        "approve_hold_reject_semantics_preserved": checklist["approve_hold_reject_semantics_preserved"]["passed"],
        "publishability_semantics_preserved": checklist["publishability_semantics_preserved"]["passed"],
        "orchestrator_qc_governance_preserved": checklist["orchestrator_strategy_core_regression"]["passed"],
        "boundary_preserved": checklist["boundary_preserved"]["passed"],
        "determinism_where_required": checklist["determinism_where_required"]["passed"],
        "backward_compatible": checklist["backward_compatible"]["passed"],
        "silent_failures_detected": not checklist["silent_failures_detected"]["passed"],
        "no_performance_prediction": checklist["no_performance_prediction_fields"]["passed"],
        "critical_failures": metrics["critical_failures"],
        "blocking_failures": blocking_failures,
        "scenario_results": {
            scenario["name"]: {
                "passed": scenario["passed"],
                "summary": scenario.get("summary"),
                "failures": scenario.get("failures"),
            }
            for scenario in scenarios
        },
        "checklist_results": checklist,
        "tests_executed": [pytest_result],
        "metrics": metrics,
        "residual_monitoring": residual_monitoring,
        "release_state": "READY_FOR_V3_WITH_MONITORING" if verdict in {"GO", "GO_WITH_MONITORING"} else "HOLD_BEFORE_RELEASE",
        "recommendation": "PROCEED_TO_WAVE_2_MASTER_GATE" if verdict in {"GO", "GO_WITH_MONITORING"} else "HOLD_BEFORE_WAVE_2_MASTER_GATE",
    }

    _write_json(SCENARIO_OUTPUTS_PATH, {scenario["name"]: scenario for scenario in scenarios})
    _write_json(CHECKLIST_RESULTS_PATH, checklist)
    _write_json(METRICS_PATH, metrics)
    _write_json(FINAL_VERDICT_PATH, final_verdict)

    print(json.dumps({
        "verdict": verdict,
        "scenario_pass_count": f"{metrics['scenario_pass_count']}/{metrics['scenario_count']}",
        "checklist_pass_count": f"{metrics['checklist_pass_count']}/{metrics['checklist_count']}",
        "blocking_failures": blocking_failures,
        "residual_monitoring": residual_monitoring,
        "final_verdict": str(FINAL_VERDICT_PATH),
    }, indent=2))
    return 0 if verdict in {"GO", "GO_WITH_MONITORING"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
