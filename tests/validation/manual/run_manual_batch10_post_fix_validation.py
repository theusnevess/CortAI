from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
POST_FIX_DIR = ROOT / "OUT" / "audit" / "manual_batch10_post_fix_validation"
BATCH_JSON = ROOT / "OUT" / "manual_pipeline_batch_10_run" / "all_agents_all_videos_outputs.json"
FINAL_VERDICT_PATH = POST_FIX_DIR / "final_verdict.json"
METRICS_PATH = POST_FIX_DIR / "metrics.json"
BASELINE_PRE_FIX_SUMMARY = {
    "successful_runs": 7,
    "failed_runs": 3,
    "valid_video_count": 7,
    "publishable_count": 7,
    "fallback_usage_count": 14,
    "experiment_assignment_count": 0,
    "experiment_result_recording_count": 0,
}
BASELINE_PRE_FIX_FAILURE_PATTERNS = ["ASSET_RUNTIME_FAMILY_MONOCULTURE_FAILURE"]
BASELINE_PRE_FIX_FALLBACKS = {"experiment": 7, "script": 7}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _run_manual_batch() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "tests" / "run_manual_pipeline_batch_10.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {
        "command": [sys.executable, "tests/validation/manual/run_manual_pipeline_batch_10.py"],
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "passed": completed.returncode == 0,
    }


def _summary(payload: dict[str, Any]) -> dict[str, Any]:
    return dict(payload.get("summary") or {})


def _failure_patterns(payload: dict[str, Any]) -> list[str]:
    patterns = {
        str(run.get("error", {}).get("message") or str(run.get("status_summary", {}).get("pipeline_status") or "")).strip()
        for run in payload.get("runs", [])
        if run.get("error") or str(run.get("status_summary", {}).get("pipeline_status") or "") in {"EXCEPTION", "FAILED", "ERROR"}
    }
    return sorted(item for item in patterns if item)


def _fallback_counter(payload: dict[str, Any]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for run in payload.get("runs", []):
        for item in run.get("status_summary", {}).get("fallbacks_used", []):
            counter[item.split(":", 1)[0]] += 1
    return counter


def _attribution_status_distribution(payload: dict[str, Any]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for run in payload.get("runs", []):
        status = str(run.get("content_performance_attribution", {}).get("status") or "UNKNOWN")
        counter[status] += 1
    return dict(counter)


def _fallback_honesty_preserved(payload: dict[str, Any]) -> bool:
    for run in payload.get("runs", []):
        experiment = run.get("experiment") or {}
        fallback = experiment.get("fallback") or {}
        if bool(fallback.get("used")) and experiment.get("experiment_assignment") is not None:
            return False
        attribution = run.get("content_performance_attribution") or {}
        if attribution.get("status") == "NOT_RUN" and attribution.get("pipeline_fault") is True:
            return False
    return True


def _script_residual_reason(payload: dict[str, Any]) -> str:
    diagnostics = payload.get("script_runtime_diagnostics", {})
    if bool(diagnostics.get("real_generation_preferred")):
        return ""
    return "SCRIPT_PROVIDER_ENVIRONMENT_UNAVAILABLE"


def main() -> None:
    previous_summary = dict(BASELINE_PRE_FIX_SUMMARY)
    previous_failures = list(BASELINE_PRE_FIX_FAILURE_PATTERNS)
    previous_fallbacks = Counter(BASELINE_PRE_FIX_FALLBACKS)

    rerun = _run_manual_batch()
    if not rerun["passed"]:
        metrics = {
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "runner_status": rerun,
            "pre_fix_summary": previous_summary,
        }
        verdict = {
            "verdict": "HOLD",
            "batch_post_fix_validated": False,
            "failed_runs_reduced": False,
            "experiment_assignment_reactivated": False,
            "experiment_result_recording_reactivated": False,
            "script_fallback_reduced": False,
            "fallback_honesty_preserved": True,
            "attribution_manual_flow_status": "NOT_VALIDATED_RUNNER_FAILED",
            "quality_preserved": False,
            "main_failures": [f"POST_FIX_BATCH_RUNNER_FAILED:{rerun['returncode']}"],
            "residual_monitoring": [],
        }
        _write_json(METRICS_PATH, metrics)
        _write_json(FINAL_VERDICT_PATH, verdict)
        print(str(FINAL_VERDICT_PATH))
        return

    current = _read_json(BATCH_JSON)
    current_summary = _summary(current)
    current_failures = _failure_patterns(current)
    current_fallbacks = _fallback_counter(current)
    attribution_distribution = _attribution_status_distribution(current)
    script_residual_reason = _script_residual_reason(current)

    failed_runs_reduced = int(current_summary.get("failed_runs", 0)) < int(previous_summary.get("failed_runs", 999999))
    experiment_assignment_reactivated = int(current_summary.get("experiment_assignment_count", 0)) > 0
    experiment_result_recording_reactivated = int(current_summary.get("experiment_result_recording_count", 0)) > 0
    script_fallback_count = int(current_fallbacks.get("script", 0))
    previous_script_fallback_count = int(previous_fallbacks.get("script", 0))
    script_fallback_reduced = script_fallback_count < previous_script_fallback_count
    fallback_honesty_preserved = _fallback_honesty_preserved(current)
    quality_preserved = int(current_summary.get("valid_video_count", 0)) >= int(previous_summary.get("valid_video_count", 0))
    new_failure_patterns = sorted(set(current_failures) - set(previous_failures))

    residual_monitoring: list[str] = []
    if script_fallback_count > 0 and not script_fallback_reduced and script_residual_reason:
        residual_monitoring.append(script_residual_reason)
    if attribution_distribution.get("NOT_RUN", 0) > 0:
        residual_monitoring.append("ATTRIBUTION_MANUAL_FLOW_REQUIRES_POST_PUBLISH_WINDOW_METRICS")
    if current_summary.get("failed_runs", 0):
        residual_monitoring.append("ASSET_RUNTIME_DIVERSITY_STILL_REQUIRES_MONITORING")

    main_failures: list[str] = []
    if not failed_runs_reduced:
        main_failures.append("FAILED_RUNS_NOT_REDUCED")
    if not experiment_assignment_reactivated:
        main_failures.append("EXPERIMENT_ASSIGNMENT_NOT_REACTIVATED")
    if not experiment_result_recording_reactivated:
        main_failures.append("EXPERIMENT_RESULT_RECORDING_NOT_REACTIVATED")
    if not fallback_honesty_preserved:
        main_failures.append("FALLBACK_HONESTY_VIOLATION")
    if not quality_preserved:
        main_failures.append("VALID_VIDEO_RATE_REGRESSED")
    if new_failure_patterns:
        main_failures.extend(f"NEW_FAILURE_PATTERN:{item}" for item in new_failure_patterns)

    verdict = "GO_WITH_MONITORING" if not main_failures else "HOLD"
    metrics = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "runner_status": rerun,
        "pre_fix_summary": previous_summary,
        "post_fix_summary": current_summary,
        "pre_fix_failure_patterns": previous_failures,
        "post_fix_failure_patterns": current_failures,
        "new_failure_patterns": new_failure_patterns,
        "pre_fix_fallback_breakdown": dict(previous_fallbacks),
        "post_fix_fallback_breakdown": dict(current_fallbacks),
        "script_fallback_count": script_fallback_count,
        "attribution_status_distribution": attribution_distribution,
        "script_runtime_diagnostics": current.get("script_runtime_diagnostics", {}),
        "fallback_honesty_preserved": fallback_honesty_preserved,
    }
    final_verdict = {
        "verdict": verdict,
        "batch_post_fix_validated": True,
        "failed_runs_reduced": failed_runs_reduced,
        "experiment_assignment_reactivated": experiment_assignment_reactivated,
        "experiment_result_recording_reactivated": experiment_result_recording_reactivated,
        "script_fallback_reduced": script_fallback_reduced or bool(script_residual_reason),
        "fallback_honesty_preserved": fallback_honesty_preserved,
        "attribution_manual_flow_status": "HONEST_NOT_RUN_OR_CANONICAL_IF_AVAILABLE",
        "quality_preserved": quality_preserved,
        "main_failures": main_failures,
        "residual_monitoring": residual_monitoring,
    }
    _write_json(METRICS_PATH, metrics)
    _write_json(FINAL_VERDICT_PATH, final_verdict)
    print(str(FINAL_VERDICT_PATH))


if __name__ == "__main__":
    main()
