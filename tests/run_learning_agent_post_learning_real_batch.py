from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.publish import StubPublishAdapter
from app.content.pipeline.render import StubRenderAdapter
from app.content.pipeline.service import ContentPipelineService
from app.content.pipeline.tts import StubTtsAdapter
from app.creative.agents.account_health.service import AccountHealthAgentService
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.agents.editor.service import EditorAgentService
from app.creative.agents.learning.service import LearningAgentService
from app.creative.agents.novelty.service import NoveltyEngineService
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.strategy.service import StrategyAgentService
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput
from app.creative.experiments.service import ExperimentCapabilityService
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService


AUDIT_DIR = ROOT / "OUT" / "audit" / "learning_agent_post_learning_real_batch"
RUNTIME_DIR = AUDIT_DIR / "runtime"
BASELINE_BATCH_DIR = ROOT / "OUT" / "manual_pipeline_batch_3_run"
ACCOUNT_ID = "acc_learning_post_batch_001"
RUN_TOPICS = [
    "sealed corridor mirror warning",
    "shuttered wing red phone",
    "station intercom blackout signal",
    "police reopened locked evidence room",
]


def _reset_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR, ignore_errors=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _run_command(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "passed": completed.returncode == 0,
    }


def _ffprobe(video_path: Path) -> dict[str, object]:
    result = _run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            str(video_path),
        ]
    )
    if not result["passed"]:
        return {
            "path": str(video_path),
            "probe_ok": False,
            "error": result["stderr"] or result["stdout"],
        }
    payload = json.loads(str(result["stdout"] or "{}"))
    video_stream = next((stream for stream in payload.get("streams", []) if stream.get("codec_type") == "video"), {})
    audio_stream = next((stream for stream in payload.get("streams", []) if stream.get("codec_type") == "audio"), {})
    return {
        "path": str(video_path),
        "probe_ok": True,
        "video_codec": video_stream.get("codec_name"),
        "audio_codec": audio_stream.get("codec_name"),
        "width": video_stream.get("width"),
        "height": video_stream.get("height"),
        "duration_s": float(payload.get("format", {}).get("duration") or 0.0),
        "size_bytes": int(payload.get("format", {}).get("size") or 0),
    }


def _prepare_trends_dir(base_dir: Path) -> Path:
    trends_dir = base_dir / "trends"
    trends_dir.mkdir(parents=True, exist_ok=True)
    (trends_dir / "horror.json").write_text(
        json.dumps(
            {
                "niche": "horror",
                "dominant_hooks": ["story_opening"],
                "avg_duration": "35-60",
                "pacing": "fast_first_3s",
                "visual_style": "dark_backgrounds",
                "text_style": "large_caption_focus",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return trends_dir


def _seed_learning_inputs(base_dir: Path) -> dict[str, Path]:
    publish_path = base_dir / "data" / "publish_records" / "publish_records.jsonl"
    metrics_path = base_dir / "metrics" / "video_metrics.jsonl"
    analysis_dir = base_dir / "analysis"
    qc_events_path = base_dir / "events" / "creative_events.jsonl"

    publish_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    analysis_dir.mkdir(parents=True, exist_ok=True)

    publish_rows = [
        {"account_id": ACCOUNT_ID, "publish_id": "seed_pub_1"},
        {"account_id": ACCOUNT_ID, "publish_id": "seed_pub_2"},
        {"account_id": ACCOUNT_ID, "publish_id": "seed_pub_3"},
        {"account_id": ACCOUNT_ID, "publish_id": "seed_pub_4"},
        {"account_id": ACCOUNT_ID, "publish_id": "seed_pub_5"},
    ]
    metrics_rows = [
        {"account_id": ACCOUNT_ID, "views": 180, "completion_rate": 0.58, "duration_s": 9.9},
        {"account_id": ACCOUNT_ID, "views": 210, "completion_rate": 0.61, "duration_s": 10.2},
        {"account_id": ACCOUNT_ID, "views": 160, "completion_rate": 0.55, "duration_s": 9.4},
    ]
    publish_path.write_text("\n".join(json.dumps(row) for row in publish_rows), encoding="utf-8")
    metrics_path.write_text("\n".join(json.dumps(row) for row in metrics_rows), encoding="utf-8")
    (analysis_dir / "hook_performance_summary.json").write_text(
        json.dumps({"hooks": [{"hook_style": "story_opening"}]}, indent=2),
        encoding="utf-8",
    )
    return {
        "publish_path": publish_path,
        "metrics_path": metrics_path,
        "analysis_dir": analysis_dir,
        "qc_events_path": qc_events_path,
    }


def _build_orchestrator(base_dir: Path) -> CreativeOrchestratorService:
    trends_dir = _prepare_trends_dir(base_dir)
    learning_paths = _seed_learning_inputs(base_dir)
    pipeline = ContentPipelineService(
        tts_adapter=StubTtsAdapter(base_dir=base_dir / "content"),
        render_adapter=StubRenderAdapter(base_dir=base_dir / "content"),
        publish_adapter=StubPublishAdapter(),
        event_path=base_dir / "events" / "pipeline_events.jsonl",
    )
    return CreativeOrchestratorService(
        pipeline_service=pipeline,
        account_health_agent=AccountHealthAgentService(),
        trend_analysis_agent=TrendAnalysisAgentService(trends_dir=trends_dir),
        learning_agent=LearningAgentService(
            default_publish_records_path=learning_paths["publish_path"],
            default_video_metrics_path=learning_paths["metrics_path"],
            default_analysis_dir=learning_paths["analysis_dir"],
            default_qc_events_path=learning_paths["qc_events_path"],
            default_execution_history_dir=base_dir,
            default_output_path=base_dir / "learning" / "latest_learning_result.json",
        ),
        novelty_agent=NoveltyEngineService(history_dir=base_dir / "runtime" / "novelty_history"),
        strategy_agent=StrategyAgentService(),
        experiment_capability=ExperimentCapabilityService(),
        asset_selection_agent=AssetSelectionAgentService(),
        editor_agent=EditorAgentService(),
        script_agent=ScriptAgentService(),
        voice_agent=VoiceAgentService(),
        video_qc_agent=VideoQcAgentService(),
        event_emitter=CreativeEventEmitter(event_path=base_dir / "events" / "creative_events.jsonl"),
    )


def _load_baseline_metrics() -> dict[str, object]:
    batch_summary_path = BASELINE_BATCH_DIR / "batch_summary.json"
    payload = json.loads(batch_summary_path.read_text(encoding="utf-8"))
    runs = payload.get("runs", [])
    scores: list[float] = []
    for run in runs:
        execution_path = Path(str(run.get("execution_outputs") or ""))
        execution = json.loads(execution_path.read_text(encoding="utf-8"))
        qc = execution.get("video_qc") or {}
        decision = qc.get("decision") if isinstance(qc.get("decision"), dict) else {}
        score_summary = decision.get("score_summary") if isinstance(decision.get("score_summary"), dict) else {}
        scores.append(float(score_summary.get("overall_score") or 0.0))
    qc_statuses = [str(run.get("qc_status") or "") for run in runs]
    return {
        "baseline_reference": str(batch_summary_path),
        "baseline_approve_rate": round(sum(1 for status in qc_statuses if status == "APPROVE") / len(qc_statuses), 4) if qc_statuses else 0.0,
        "baseline_average_overall_score": round(mean(scores), 4) if scores else 0.0,
        "baseline_batch_size": len(runs),
    }


def _governance_ok(execution_payload: dict[str, object]) -> bool:
    pipeline_output = execution_payload.get("pipeline_output") if isinstance(execution_payload.get("pipeline_output"), dict) else {}
    result = pipeline_output.get("result") if isinstance(pipeline_output.get("result"), dict) else {}
    qc = execution_payload.get("video_qc") if isinstance(execution_payload.get("video_qc"), dict) else {}
    qc_status = str(qc.get("status") or "")
    publishable = bool(qc.get("publishable"))
    pipeline_status = str(result.get("status") or "")
    if qc_status == "APPROVE":
        return publishable and pipeline_status == "READY"
    if qc_status in {"HOLD", "REJECT"}:
        return (not publishable) and pipeline_status in {"HOLD", "REJECT"}
    return False


def _run_batch() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    orchestrator = _build_orchestrator(RUNTIME_DIR)
    runs: list[dict[str, object]] = []
    examples: list[dict[str, object]] = []
    for index, topic in enumerate(RUN_TOPICS, start=1):
        execution = orchestrator.execute(
            CreativeOrchestratorInput(
                account_id=ACCOUNT_ID,
                niche="horror",
                topic=topic,
                publish_slot=f"2026-04-02T2{index}:00:00Z",
            )
        )
        payload = execution.to_dict()
        run_dir = AUDIT_DIR / f"run_{index}"
        run_dir.mkdir(parents=True, exist_ok=True)
        execution_path = run_dir / "execution_outputs.json"
        _write_json(execution_path, payload)
        learning_history_path = RUNTIME_DIR / "history" / f"run_{index}" / "execution_outputs.json"
        _write_json(learning_history_path, payload)

        creative_pack = payload.get("creative_pack") if isinstance(payload.get("creative_pack"), dict) else {}
        learning_policy = creative_pack.get("learning_policy") if isinstance(creative_pack.get("learning_policy"), dict) else {}
        strategy = payload.get("strategy") if isinstance(payload.get("strategy"), dict) else {}
        decision_trace = strategy.get("decision_trace") if isinstance(strategy.get("decision_trace"), dict) else {}
        qc = payload.get("video_qc") if isinstance(payload.get("video_qc"), dict) else {}
        decision = qc.get("decision") if isinstance(qc.get("decision"), dict) else {}
        score_summary = decision.get("score_summary") if isinstance(decision.get("score_summary"), dict) else {}
        pipeline_output = payload.get("pipeline_output") if isinstance(payload.get("pipeline_output"), dict) else {}
        pipeline_result = pipeline_output.get("result") if isinstance(pipeline_output.get("result"), dict) else {}
        video_path = Path(str((pipeline_result.get("artifacts") or {}).get("video") or ""))
        probe = _ffprobe(video_path) if video_path.exists() else {"path": str(video_path), "probe_ok": False}

        run_summary = {
            "run_id": index,
            "topic": topic,
            "execution_outputs": str(execution_path),
            "video_path": str(video_path),
            "video_probe": probe,
            "pipeline_status": str(pipeline_result.get("status") or ""),
            "qc_status": str(qc.get("status") or ""),
            "publishable": bool(qc.get("publishable")),
            "overall_score": float(score_summary.get("overall_score") or 0.0),
            "learning_policy_applied": bool(learning_policy) and int(((learning_policy.get("hook_type_bias") or {}).get("evidence_count") or 0)) > 0,
            "learning_policy_evidence_count": int(((learning_policy.get("hook_type_bias") or {}).get("evidence_count") or 0)),
            "strategy_learning_response_observed": len(list(decision_trace.get("learning_adjustments") or [])) > 0,
            "strategy_learning_adjustments": list(decision_trace.get("learning_adjustments") or []),
            "novelty_active": payload.get("novelty") is not None,
            "novelty_pressure_level": str((((payload.get("novelty") or {}).get("novelty_pressure_profile") or {}).get("pressure_level") or "")),
            "governance_preserved": _governance_ok(payload),
        }
        runs.append(run_summary)
        examples.append(
            {
                "run_id": index,
                "topic": topic,
                "learning_policy": learning_policy,
                "strategy_profile": (strategy.get("strategy_profile") if isinstance(strategy.get("strategy_profile"), dict) else {}),
                "video_qc": qc,
            }
        )
    return runs, examples


def main() -> None:
    _reset_dir()
    baseline = _load_baseline_metrics()
    runs, examples = _run_batch()

    approve_rate = round(sum(1 for run in runs if run["qc_status"] == "APPROVE") / len(runs), 4) if runs else 0.0
    average_overall_score = round(mean([float(run["overall_score"]) for run in runs]), 4) if runs else 0.0
    learning_policy_applied_rate = round(sum(1 for run in runs if run["learning_policy_applied"]) / len(runs), 4) if runs else 0.0
    strategy_response_rate = round(sum(1 for run in runs if run["strategy_learning_response_observed"]) / len(runs), 4) if runs else 0.0
    novelty_active_rate = round(sum(1 for run in runs if run["novelty_active"]) / len(runs), 4) if runs else 0.0
    governance_rate = round(sum(1 for run in runs if run["governance_preserved"]) / len(runs), 4) if runs else 0.0
    valid_video_rate = round(sum(1 for run in runs if bool((run["video_probe"] or {}).get("probe_ok"))) / len(runs), 4) if runs else 0.0
    new_failure_patterns = sorted(
        {
            run["qc_status"]
            for run in runs
            if run["qc_status"] not in {"APPROVE", ""}
        }
    )

    metrics = {
        **baseline,
        "post_learning_approve_rate": approve_rate,
        "post_learning_average_overall_score": average_overall_score,
        "delta_approve_rate": round(approve_rate - float(baseline["baseline_approve_rate"]), 4),
        "delta_average_overall_score": round(average_overall_score - float(baseline["baseline_average_overall_score"]), 4),
        "learning_policy_applied_rate": learning_policy_applied_rate,
        "strategy_response_rate": strategy_response_rate,
        "novelty_active_rate": novelty_active_rate,
        "qc_governance_preserved_rate": governance_rate,
        "valid_video_rate": valid_video_rate,
        "new_failure_patterns": new_failure_patterns,
    }

    no_new_failure_patterns = len(new_failure_patterns) == 0
    strategy_response_observed = strategy_response_rate > 0.0
    novelty_active = novelty_active_rate >= 0.75
    qc_governance_preserved = governance_rate == 1.0
    learning_policy_applied = learning_policy_applied_rate >= 0.75

    systemic_failure = (
        valid_video_rate < 1.0
        or not qc_governance_preserved
        or not novelty_active
        or not learning_policy_applied
    )

    if (
        approve_rate >= float(baseline["baseline_approve_rate"])
        and average_overall_score >= float(baseline["baseline_average_overall_score"]) - 0.02
        and no_new_failure_patterns
        and learning_policy_applied
        and strategy_response_observed
        and novelty_active
        and qc_governance_preserved
        and not systemic_failure
    ):
        verdict = "GO"
    elif (
        approve_rate >= float(baseline["baseline_approve_rate"]) - 0.1
        and average_overall_score >= float(baseline["baseline_average_overall_score"]) - 0.05
        and not systemic_failure
        and novelty_active
        and qc_governance_preserved
    ):
        verdict = "GO_WITH_MONITORING"
    else:
        verdict = "HOLD"

    batch_summary = {
        "base_dir": str(AUDIT_DIR),
        "runs": runs,
    }
    human_review = {
        "summary": (
            "This batch runs fresh post-learning executions under the active Learning v2.0, Strategy integration, Novelty engine, and QC. "
            "Promotion is allowed only if approve rate and quality hold against the recent stabilized baseline."
        ),
        "observations": [
            f"learning_policy_applied_rate={learning_policy_applied_rate}",
            f"strategy_response_rate={strategy_response_rate}",
            f"novelty_active_rate={novelty_active_rate}",
            f"qc_governance_preserved_rate={governance_rate}",
            f"valid_video_rate={valid_video_rate}",
        ],
        "residuals": [] if verdict == "GO" else [
            "REVIEW_BATCH_RESIDUALS_BEFORE_PROMOTION" if verdict == "GO_WITH_MONITORING" else "REGRESSION_OR_GOVERNANCE_FAILURE_DETECTED",
        ],
    }
    final_verdict = {
        "verdict": verdict,
        "baseline_reference": baseline["baseline_reference"],
        "learning_v2_active": True,
        "strategy_consuming_policy": learning_policy_applied,
        "strategy_response_observed": strategy_response_observed,
        "novelty_active": novelty_active,
        "qc_governance_preserved": qc_governance_preserved,
        "main_failures": [] if verdict != "HOLD" else [
            failure
            for failure, active in {
                "APPROVE_RATE_DROP": approve_rate < float(baseline["baseline_approve_rate"]) - 0.1,
                "AVERAGE_SCORE_DROP": average_overall_score < float(baseline["baseline_average_overall_score"]) - 0.05,
                "NEW_FAILURE_PATTERNS": not no_new_failure_patterns,
                "LEARNING_POLICY_NOT_APPLIED": not learning_policy_applied,
                "NOVELTY_NOT_ACTIVE": not novelty_active,
                "QC_GOVERNANCE_NOT_PRESERVED": not qc_governance_preserved,
                "VIDEO_INVALID": valid_video_rate < 1.0,
            }.items()
            if active
        ],
    }

    _write_json(AUDIT_DIR / "batch_summary.json", batch_summary)
    _write_json(AUDIT_DIR / "execution_batch.json", examples)
    _write_json(AUDIT_DIR / "metrics.json", metrics)
    _write_json(AUDIT_DIR / "human_review.json", human_review)
    _write_json(AUDIT_DIR / "final_verdict.json", final_verdict)


if __name__ == "__main__":
    main()
