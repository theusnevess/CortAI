from __future__ import annotations

import json
import shutil
import subprocess
import sys
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


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
from app.runtime.asset_selector import AssetSelector


BATCH_DIR = ROOT / "OUT" / "manual_pipeline_batch_10_run"
RUNTIME_DIR = BATCH_DIR / "runtime"
FINAL_JSON = BATCH_DIR / "all_agents_all_videos_outputs.json"

RUN_SPECS = [
    {"run_id": "run_1", "account_id": "acc_manual_batch10_001", "niche": "horror", "topic": "sealed corridor mirror warning"},
    {"run_id": "run_2", "account_id": "acc_manual_batch10_002", "niche": "horror", "topic": "station intercom blackout signal"},
    {"run_id": "run_3", "account_id": "acc_manual_batch10_003", "niche": "horror", "topic": "maintenance tunnel warning loop"},
    {"run_id": "run_4", "account_id": "acc_manual_batch10_004", "niche": "horror", "topic": "voice behind the fire exit"},
    {"run_id": "run_5", "account_id": "acc_manual_batch10_005", "niche": "true_crime", "topic": "police reopened locked evidence room"},
    {"run_id": "run_6", "account_id": "acc_manual_batch10_006", "niche": "true_crime", "topic": "dispatcher tape reopened"},
    {"run_id": "run_7", "account_id": "acc_manual_batch10_007", "niche": "true_crime", "topic": "missing witness transcript"},
    {"run_id": "run_8", "account_id": "acc_manual_batch10_008", "niche": "facts", "topic": "museum receipt with impossible timestamp"},
    {"run_id": "run_9", "account_id": "acc_manual_batch10_009", "niche": "conspiracy", "topic": "numbers station rooftop signal pattern"},
    {"run_id": "run_10", "account_id": "acc_manual_batch10_010", "niche": "history", "topic": "night watch log with future date"},
]


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _reset_dir() -> None:
    if BATCH_DIR.exists():
        shutil.rmtree(BATCH_DIR, ignore_errors=True)
    BATCH_DIR.mkdir(parents=True, exist_ok=True)


def _seed_runtime_inputs() -> dict[str, Path]:
    publish_path = RUNTIME_DIR / "data" / "publish_records" / "publish_records.jsonl"
    metrics_path = RUNTIME_DIR / "metrics" / "video_metrics.jsonl"
    analysis_dir = RUNTIME_DIR / "analysis"
    qc_events_path = RUNTIME_DIR / "events" / "creative_events.jsonl"

    publish_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    analysis_dir.mkdir(parents=True, exist_ok=True)
    qc_events_path.parent.mkdir(parents=True, exist_ok=True)

    publish_rows: list[dict[str, Any]] = []
    metrics_rows: list[dict[str, Any]] = []
    for index, spec in enumerate(RUN_SPECS, start=1):
        account_id = spec["account_id"]
        for offset in range(4):
            publish_rows.append(
                {
                    "account_id": account_id,
                    "publish_id": f"{account_id}_seed_pub_{offset+1}",
                    "scheduled_time": f"2026-04-0{offset+1}T1{offset}:00:00Z",
                }
            )
        base_views = 220 + (index * 7)
        for offset, views in enumerate((base_views, base_views + 12, base_views - 5, base_views + 20), start=1):
            metrics_rows.append(
                {
                    "account_id": account_id,
                    "video_id": f"{account_id}_seed_vid_{offset}",
                    "views": views,
                    "completion_rate": round(0.44 + (offset * 0.02), 4),
                    "duration_s": round(9.4 + (offset * 0.35), 2),
                }
            )

    publish_path.write_text("\n".join(json.dumps(row, ensure_ascii=True) for row in publish_rows), encoding="utf-8")
    metrics_path.write_text("\n".join(json.dumps(row, ensure_ascii=True) for row in metrics_rows), encoding="utf-8")
    (analysis_dir / "hook_performance_summary.json").write_text(
        json.dumps(
            {
                "hooks": [
                    {"hook_style": "story_opening"},
                    {"hook_style": "question"},
                    {"hook_style": "official_warning"},
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "publish_path": publish_path,
        "metrics_path": metrics_path,
        "analysis_dir": analysis_dir,
        "qc_events_path": qc_events_path,
    }


def _prepare_runtime_experiment_paths() -> dict[str, Path]:
    runtime_experiments_dir = RUNTIME_DIR / "experiments"
    runtime_experiments_dir.mkdir(parents=True, exist_ok=True)
    source_config = ROOT / "backend" / "data" / "experiments" / "experiment_config.json"
    config_path = runtime_experiments_dir / "experiment_config.json"
    if source_config.exists():
        shutil.copyfile(source_config, config_path)
    return {
        "config_path": config_path,
        "output_path": runtime_experiments_dir / "experiment_plan.json",
        "experiments_path": runtime_experiments_dir / "experiments.jsonl",
        "assignments_path": runtime_experiments_dir / "assignments.jsonl",
        "results_path": runtime_experiments_dir / "results.jsonl",
    }


def _build_orchestrator(seed_paths: dict[str, Path]) -> CreativeOrchestratorService:
    experiment_paths = _prepare_runtime_experiment_paths()
    pipeline = ContentPipelineService(
        tts_adapter=StubTtsAdapter(base_dir=RUNTIME_DIR / "content"),
        render_adapter=StubRenderAdapter(base_dir=RUNTIME_DIR / "content"),
        publish_adapter=StubPublishAdapter(),
        event_path=RUNTIME_DIR / "events" / "events.jsonl",
    )
    return CreativeOrchestratorService(
        pipeline_service=pipeline,
        account_health_agent=AccountHealthAgentService(),
        trend_analysis_agent=TrendAnalysisAgentService(),
        learning_agent=LearningAgentService(
            default_publish_records_path=seed_paths["publish_path"],
            default_video_metrics_path=seed_paths["metrics_path"],
            default_analysis_dir=seed_paths["analysis_dir"],
            default_qc_events_path=seed_paths["qc_events_path"],
            default_execution_history_dir=RUNTIME_DIR,
            default_output_path=RUNTIME_DIR / "learning" / "latest_learning_result.json",
        ),
        novelty_agent=NoveltyEngineService(history_dir=RUNTIME_DIR / "novelty_history"),
        strategy_agent=StrategyAgentService(),
        experiment_capability=ExperimentCapabilityService(
            default_config_path=experiment_paths["config_path"],
            default_output_path=experiment_paths["output_path"],
            default_experiments_path=experiment_paths["experiments_path"],
            default_assignments_path=experiment_paths["assignments_path"],
            default_results_path=experiment_paths["results_path"],
        ),
        asset_selection_agent=AssetSelectionAgentService(),
        editor_agent=EditorAgentService(),
        script_agent=ScriptAgentService(),
        voice_agent=VoiceAgentService(),
        video_qc_agent=VideoQcAgentService(),
        event_emitter=CreativeEventEmitter(event_path=RUNTIME_DIR / "events" / "creative_events.jsonl"),
    )


def _script_runtime_diagnostics() -> dict[str, Any]:
    ollama_base_url = os.getenv("CORTAI_OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    ollama_healthy = False
    try:
        health = subprocess.run(
            ["curl", "-sS", f"{ollama_base_url}/api/tags"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=8,
        )
        ollama_healthy = health.returncode == 0
    except Exception:
        ollama_healthy = False
    groq_key_present = bool(os.getenv("GROQ_API_KEY", "").strip())
    return {
        "groq_key_present": groq_key_present,
        "ollama_base_url": ollama_base_url,
        "ollama_healthy": ollama_healthy,
        "real_generation_preferred": groq_key_present or ollama_healthy,
        "fallback_residual_expected": not (groq_key_present or ollama_healthy),
    }


def _run_command(command: list[str]) -> dict[str, Any]:
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


def _ffprobe(path: Path) -> dict[str, Any]:
    result = _run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            str(path),
        ]
    )
    if not result["passed"]:
        return {
            "path": str(path),
            "probe_ok": False,
            "error": result["stderr"] or result["stdout"],
        }
    payload = json.loads(str(result["stdout"] or "{}"))
    video_stream = next((stream for stream in payload.get("streams", []) if stream.get("codec_type") == "video"), {})
    audio_stream = next((stream for stream in payload.get("streams", []) if stream.get("codec_type") == "audio"), {})
    return {
        "path": str(path),
        "probe_ok": True,
        "video_codec": video_stream.get("codec_name"),
        "audio_codec": audio_stream.get("codec_name"),
        "width": video_stream.get("width"),
        "height": video_stream.get("height"),
        "duration_s": float(payload.get("format", {}).get("duration") or 0.0),
        "size_bytes": int(payload.get("format", {}).get("size") or 0),
        "has_audio_stream": bool(audio_stream),
    }


def _resolve_path(value: str | None) -> str | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str((ROOT / path).resolve())


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _collect_fallbacks(execution: dict[str, Any], script: dict[str, Any], voice: dict[str, Any], editor: dict[str, Any]) -> list[str]:
    fallbacks: list[str] = []
    for key in ("account_health", "trend_analysis", "learning", "strategy", "experiment", "asset_selection"):
        payload = _safe_dict(execution.get(key))
        fallback = _safe_dict(payload.get("fallback"))
        if bool(fallback.get("used")):
            fallbacks.append(f"{key}:{fallback.get('reason') or 'UNKNOWN'}")
    if str(_safe_dict(script.get("script_plan")).get("generation_mode") or "").startswith("fallback"):
        fallbacks.append(f"script:{_safe_dict(script.get('fallback')).get('reason') or 'SCRIPT_GENERATION_FALLBACK'}")
    if bool(_safe_dict(voice.get("fallback")).get("used")):
        fallbacks.append(f"voice:{_safe_dict(voice.get('fallback')).get('reason') or 'VOICE_FALLBACK'}")
    if bool(_safe_dict(editor.get("fallback")).get("used")):
        fallbacks.append(f"editor:{_safe_dict(editor.get('fallback')).get('reason') or 'EDITOR_FALLBACK'}")
    tts_trace = _safe_dict(_safe_dict(execution.get("pipeline_output")).get("result")).get("tts_trace")
    if isinstance(tts_trace, dict) and bool(tts_trace.get("fallback_used")):
        fallbacks.append(f"tts:{tts_trace.get('fallback_reason') or 'TTS_FALLBACK'}")
    return fallbacks


def _append_publish_record(run: dict[str, Any], publish_path: Path) -> None:
    manifest = _safe_dict(_safe_dict(_safe_dict(run.get("pipeline_output")).get("result")).get("publish_manifest"))
    if not manifest:
        return
    row = {
        "account_id": manifest.get("account_id"),
        "publish_id": manifest.get("publish_id"),
        "video_path": manifest.get("video_path"),
        "scheduled_time": manifest.get("scheduled_time"),
    }
    with publish_path.open("a", encoding="utf-8") as handle:
        if publish_path.stat().st_size > 0:
            handle.write("\n")
        handle.write(json.dumps(row, ensure_ascii=True))


def _build_agent_views(execution: dict[str, Any]) -> dict[str, Any]:
    creative_pack = _safe_dict(execution.get("creative_pack"))
    script_plan = _safe_dict(creative_pack.get("script_plan"))
    voice_plan = _safe_dict(creative_pack.get("voice_plan"))
    asset_plan = _safe_dict(creative_pack.get("asset_plan"))
    edit_plan = _safe_dict(creative_pack.get("edit_plan"))
    experiment = _safe_dict(execution.get("experiment"))

    script = {
        "script_plan": script_plan,
        "hook": script_plan.get("hook"),
        "setup": script_plan.get("setup"),
        "payoff": script_plan.get("payoff"),
        "fallback": {
            "used": str(script_plan.get("generation_mode") or "").startswith("fallback"),
            "mode": "SAFE_DEFAULT" if str(script_plan.get("generation_mode") or "").startswith("fallback") else "NONE",
            "reason": "SCRIPT_GENERATION_FALLBACK" if str(script_plan.get("generation_mode") or "").startswith("fallback") else "",
        },
    }
    voice = {
        "voice_plan": voice_plan,
        "fallback": {
            "used": bool(voice_plan.get("fallback_used")),
            "mode": "SAFE_DEFAULT" if bool(voice_plan.get("fallback_used")) else "NONE",
            "reason": str(voice_plan.get("fallback_reason") or ""),
        },
    }
    editor = {
        "edit_plan": edit_plan,
        "fallback": {
            "used": False,
            "mode": "NONE",
            "reason": "",
        },
    }
    asset = _safe_dict(execution.get("asset_selection"))
    if not asset:
        asset = {
            "asset_plan": asset_plan,
            "fallback": {
                "used": False,
                "mode": "NONE",
                "reason": "",
            },
        }
    else:
        asset = {
            "asset_selection": asset.get("asset_selection"),
            "asset_plan": asset.get("asset_selection"),
            "fallback": asset.get("fallback"),
        }
    novelty = _safe_dict(execution.get("novelty"))
    novelty_profile = _safe_dict(novelty.get("novelty_pressure_profile"))
    novelty_view = {
        "pressure_level": novelty_profile.get("pressure_level"),
        "semantic_saturation_level": novelty_profile.get("semantic_saturation_level"),
        "visual_saturation_level": novelty_profile.get("visual_saturation_level"),
        "structural_saturation_level": novelty_profile.get("structural_saturation_level"),
        "blocked_payoff_structures": novelty_profile.get("blocked_payoff_structures"),
        "blocked_visual_payoff_categories": novelty_profile.get("blocked_visual_payoff_categories"),
        "recommended_variation_policy": novelty_profile.get("recommended_variation_policy"),
        "trace": novelty_profile.get("trace"),
        "novelty_pressure_profile": novelty_profile,
        "signatures_considered": novelty.get("signatures_considered"),
    }
    experiment_view = {
        "experiment_plan": experiment.get("experiment_plan"),
        "experiment_assignment": experiment.get("experiment_assignment"),
        "experiment_result": experiment.get("experiment_result"),
        "decision_trace": experiment.get("decision_trace"),
        "experiment_trace": experiment.get("experiment_trace"),
        "fallback": experiment.get("fallback"),
    }
    return {
        "script": script,
        "voice": voice,
        "asset": asset,
        "editor": editor,
        "novelty": novelty_view,
        "experiment": experiment_view,
    }


def _run_batch() -> dict[str, Any]:
    _reset_dir()
    seed_paths = _seed_runtime_inputs()
    orchestrator = _build_orchestrator(seed_paths)
    script_runtime = _script_runtime_diagnostics()
    start_slot = datetime(2026, 4, 4, 12, 0, 0, tzinfo=timezone.utc)
    runs: list[dict[str, Any]] = []
    previous_niche: str | None = None

    for index, spec in enumerate(RUN_SPECS, start=1):
        if previous_niche is not None and spec["niche"] != previous_niche:
            AssetSelector._global_video_signatures.clear()
            AssetSelector._global_failed_sequences_prevented.clear()
        previous_niche = spec["niche"]
        run_dir = BATCH_DIR / spec["run_id"]
        run_dir.mkdir(parents=True, exist_ok=True)
        publish_slot = (start_slot + timedelta(hours=index)).isoformat().replace("+00:00", "Z")
        run_input = {
            "account_id": spec["account_id"],
            "niche": spec["niche"],
            "topic": spec["topic"],
            "publish_slot": publish_slot,
        }
        execution_outputs_path = run_dir / "execution_outputs.json"
        creative_pack_path = run_dir / "creative_pack.json"
        error_summary: dict[str, Any] | None = None

        try:
            execution = orchestrator.execute(
                CreativeOrchestratorInput(
                    account_id=spec["account_id"],
                    niche=spec["niche"],
                    topic=spec["topic"],
                    publish_slot=publish_slot,
                )
            )
            execution_payload = execution.to_dict()
            _write_json(execution_outputs_path, execution_payload)
            _write_json(RUNTIME_DIR / "history" / spec["run_id"] / "execution_outputs.json", execution_payload)
            if execution_payload.get("creative_pack") is not None:
                _write_json(creative_pack_path, execution_payload["creative_pack"])
            _append_publish_record(execution_payload, seed_paths["publish_path"])
        except Exception as exc:  # noqa: BLE001
            execution_payload = {}
            error_summary = {
                "code": type(exc).__name__,
                "message": str(exc),
            }

        pipeline_output = _safe_dict(execution_payload.get("pipeline_output"))
        pipeline_result = _safe_dict(pipeline_output.get("result"))
        artifacts = _safe_dict(pipeline_result.get("artifacts"))
        render_job_id = str(pipeline_result.get("render_job_id") or "")
        metadata_path = RUNTIME_DIR / "content" / "metadata" / f"{render_job_id}.json"
        metadata = _read_json(metadata_path) if metadata_path.exists() else {}
        subtitle_path = _resolve_path(str(metadata.get("subtitle_path") or "")) if metadata else None
        audio_path = _resolve_path(str(artifacts.get("audio") or "")) if artifacts else None
        video_path = _resolve_path(str(artifacts.get("video") or "")) if artifacts else None
        video_probe = _ffprobe(Path(video_path)) if video_path and Path(video_path).exists() else {"path": video_path, "probe_ok": False}
        audio_probe = _ffprobe(Path(audio_path)) if audio_path and Path(audio_path).exists() else {"path": audio_path, "probe_ok": False}

        agent_views = _build_agent_views(execution_payload)
        script = agent_views["script"]
        voice = agent_views["voice"]
        asset = agent_views["asset"]
        editor = agent_views["editor"]
        novelty = agent_views["novelty"]
        experiment = agent_views["experiment"]

        qc = _safe_dict(execution_payload.get("video_qc"))
        status_summary = {
            "pipeline_status": str(pipeline_result.get("status") or ("EXCEPTION" if error_summary else "")),
            "qc_status": str(qc.get("status") or ""),
            "publishable": bool(qc.get("publishable")) if qc else False,
            "fallbacks_used": _collect_fallbacks(execution_payload, script, voice, editor),
            "valid_video": bool(video_probe.get("probe_ok")),
        }

        run_record = {
            "run_id": spec["run_id"],
            "input": run_input,
            "account_health": _safe_dict(execution_payload.get("account_health")),
            "trend_analysis": _safe_dict(execution_payload.get("trend_analysis")),
            "learning": _safe_dict(execution_payload.get("learning")),
            "novelty": novelty,
            "strategy": _safe_dict(execution_payload.get("strategy")),
            "experiment": experiment,
            "script": script,
            "voice": voice,
            "asset": asset,
            "editor": editor,
            "pipeline_output": pipeline_output,
            "video_qc": qc,
            "content_performance_attribution": {
                "status": "NOT_RUN",
                "reason": "WINDOW_METRICS_NOT_AVAILABLE_IN_MANUAL_BATCH_FLOW",
                "eligibility_status": "INSUFFICIENT_POST_PUBLISH_WINDOW_METRICS",
                "required_inputs_missing": ["window_metrics"],
                "pipeline_fault": False,
            },
            "artifacts": {
                "video_path": video_path,
                "audio_path": audio_path,
                "subtitles_path": subtitle_path,
                "metadata_path": str(metadata_path) if metadata_path.exists() else None,
                "execution_outputs_path": str(execution_outputs_path) if execution_outputs_path.exists() else None,
                "creative_pack_path": str(creative_pack_path) if creative_pack_path.exists() else None,
                "video_probe": video_probe,
                "audio_probe": audio_probe,
                "metadata_exists": metadata_path.exists(),
            },
            "status_summary": status_summary,
        }
        if error_summary is not None:
            run_record["error"] = error_summary
        runs.append(run_record)

    summary = {
        "successful_runs": sum(1 for run in runs if str(_safe_dict(run.get("status_summary")).get("pipeline_status") or "") not in {"EXCEPTION", "FAILED", "ERROR"}),
        "failed_runs": sum(1 for run in runs if str(_safe_dict(run.get("status_summary")).get("pipeline_status") or "") in {"EXCEPTION", "FAILED", "ERROR"}),
        "valid_video_count": sum(1 for run in runs if bool(_safe_dict(run.get("status_summary")).get("valid_video"))),
        "publishable_count": sum(1 for run in runs if bool(_safe_dict(run.get("status_summary")).get("publishable"))),
        "fallback_usage_count": sum(len(list(_safe_dict(run.get("status_summary")).get("fallbacks_used") or [])) for run in runs),
        "experiment_assignment_count": sum(1 for run in runs if _safe_dict(_safe_dict(run.get("experiment")).get("experiment_assignment"))),
        "experiment_result_recording_count": sum(1 for run in runs if _safe_dict(_safe_dict(run.get("experiment")).get("experiment_result"))),
    }

    return {
        "batch_id": "manual_pipeline_batch_10_run",
        "system_version": "CORTAI_RUNTIME_V2_5",
        "governance_mode": "FROZEN_AND_VALIDATED_BASELINE_EXECUTION",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "total_runs": len(RUN_SPECS),
        "runs_completed": len(runs),
        "script_runtime_diagnostics": script_runtime,
        "summary": summary,
        "runs": runs,
    }


def main() -> None:
    payload = _run_batch()
    _write_json(FINAL_JSON, payload)
    print(str(FINAL_JSON))


if __name__ == "__main__":
    main()
