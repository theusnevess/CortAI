from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

_env_path = ROOT / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            _k, _v = _k.strip(), _v.strip()
            if _k and _k not in os.environ:
                os.environ[_k] = _v

from app.content.pipeline.publish import StubPublishAdapter
from app.content.pipeline.render import StubRenderAdapter
from app.content.pipeline.service import ContentPipelineService
from app.content.pipeline.tts import StubTtsAdapter
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService

AUDIT_DIR = ROOT / "OUT" / "audit" / "editor_expression_validation_gate"
RUNTIME_DIR = AUDIT_DIR / "runtime"
EVENTS_DIR = AUDIT_DIR / "events"

SCENARIOS = [
    {"account_id": "acc_expr_val_001", "niche": "true_crime", "topic": "station intercom warning"},
    {"account_id": "acc_expr_val_002", "niche": "horror", "topic": "sealed room whisper phone rang inside"},
    {"account_id": "acc_expr_val_003", "niche": "conspiracy", "topic": "station blueprint missing corridor"},
    {"account_id": "acc_expr_val_004", "niche": "horror", "topic": "hospital intercom announced code from closed ward"},
    {"account_id": "acc_expr_val_005", "niche": "true_crime", "topic": "dispatch recording captured impossible reply"},
]


def _run_unittest_block(name: str, modules: list[str]) -> dict[str, object]:
    cmd = ["python", "-m", "unittest", *modules]
    result = subprocess.run(
        cmd,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {
        "name": name,
        "modules": modules,
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "output": result.stdout or "",
    }


def _load_metadata(runtime_dir: Path, render_job_id: str) -> dict[str, object]:
    metadata_path = runtime_dir / "content" / "metadata" / f"{render_job_id}.json"
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def _evaluate(metadata: dict[str, object], execution: dict[str, object]) -> dict[str, object]:
    caption_plan = dict(metadata.get("edit_plan", {}).get("caption_plan", {}))
    motion_plan = dict(metadata.get("motion_plan") or {})
    color_plan = dict(metadata.get("color_plan") or {})
    timing_plan = dict(metadata.get("timing_plan") or {})
    subtitle_cues = list(metadata.get("subtitle_cues") or [])
    tts_trace = dict(execution["pipeline_output"]["result"].get("tts_trace") or {})

    caption_legibility = (
        caption_plan.get("caption_animation_mode") == "progressive_word_reveal"
        and 3 <= len(subtitle_cues) <= 9
        and all(str(cue.get("text") or "").strip() for cue in subtitle_cues)
    )
    caption_expression = (
        caption_legibility
        and caption_plan.get("emphasis_animation_mode") == "scale_pulse"
        and bool(caption_plan.get("emphasis_timing_points"))
        and bool(caption_plan.get("key_word_emphasis_rules"))
    )
    motion_expression = (
        motion_plan.get("motion_intent") == "narrative_attention"
        and motion_plan.get("motion_behavior_profile") not in {"", "baseline"}
        and len({motion_plan.get("hook_motion_type"), motion_plan.get("setup_motion_type"), motion_plan.get("payoff_motion_type")}) >= 2
    )
    atmosphere_quality = (
        bool(color_plan.get("atmosphere_profile"))
        and color_plan.get("polish_intensity") in {"medium", "high"}
        and color_plan.get("atmosphere_behavior_profile") not in {"", "baseline"}
    )
    timing_impact = (
        bool(timing_plan.get("emphasis_sync_points"))
        and bool(timing_plan.get("micro_timing_adjustments"))
        and bool(tts_trace.get("segment_durations"))
    )
    audiovisual_cohesion = (
        execution["video_qc"]["status"] == "APPROVE"
        and caption_expression
        and motion_expression
        and atmosphere_quality
        and timing_impact
    )
    slideshow_feel = not (caption_expression and motion_expression and atmosphere_quality)

    return {
        "render_job_id": metadata.get("render_job_id", ""),
        "video_path": execution["pipeline_output"]["result"]["artifacts"].get("video", ""),
        "caption_legibility": "high" if caption_legibility else "low",
        "caption_expression": "high" if caption_expression else "low",
        "motion_expression": "high" if motion_expression else "low",
        "atmosphere_quality": "high" if atmosphere_quality else "low",
        "timing_impact": "high" if timing_impact else "low",
        "audiovisual_cohesion": "high" if audiovisual_cohesion else "low",
        "slideshow_feel": slideshow_feel,
        "overall_quality": "good" if audiovisual_cohesion else "acceptable" if execution["video_qc"]["status"] == "APPROVE" else "bad",
    }


def main() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)

    unit_blocks = [
        _run_unittest_block(
            "editor_expression_unit",
            [
                "tests.test_editor_plan_unittest",
                "tests.test_editor_interpreter_unittest",
                "tests.test_editor_expression_caption_unittest",
                "tests.test_editor_expression_motion_unittest",
                "tests.test_editor_expression_atmosphere_unittest",
            ],
        ),
        _run_unittest_block(
            "editor_expression_integration",
            [
                "tests.test_editor_pipeline_integration_unittest",
                "tests.test_editor_expression_pipeline_integration_unittest",
                "tests.test_editor_agent_service_unittest",
                "tests.test_creative_orchestrator_phase2_unittest",
            ],
        ),
    ]

    pipeline = ContentPipelineService(
        tts_adapter=StubTtsAdapter(base_dir=RUNTIME_DIR / "content"),
        render_adapter=StubRenderAdapter(base_dir=RUNTIME_DIR / "content"),
        publish_adapter=StubPublishAdapter(),
        event_path=EVENTS_DIR / "events.jsonl",
    )
    orchestrator = CreativeOrchestratorService(
        pipeline_service=pipeline,
        video_qc_agent=VideoQcAgentService(),
        event_emitter=CreativeEventEmitter(event_path=EVENTS_DIR / "creative_events.jsonl"),
    )

    started = datetime.now(timezone.utc).replace(microsecond=0)
    executions: list[dict[str, object]] = []
    reviews: list[dict[str, object]] = []
    failures: list[str] = []

    for idx, scenario in enumerate(SCENARIOS):
        publish_slot = (started + timedelta(minutes=idx)).isoformat().replace("+00:00", "Z")
        execution = orchestrator.execute(
            CreativeOrchestratorInput(
                account_id=scenario["account_id"],
                niche=scenario["niche"],
                topic=scenario["topic"],
                publish_slot=publish_slot,
            )
        )
        payload = {
            "account_id": scenario["account_id"],
            "niche": scenario["niche"],
            "topic": scenario["topic"],
            "publish_slot": publish_slot,
            "pipeline_output": execution.pipeline_output,
            "video_qc": None if execution.video_qc is None else asdict(execution.video_qc),
        }
        executions.append(payload)
        result = execution.pipeline_output["result"]
        if result.get("status") != "READY" or execution.video_qc is None:
            failures.append(f"{scenario['topic']}:{result.get('status') or 'UNKNOWN'}")
            continue
        metadata = _load_metadata(RUNTIME_DIR, str(result.get("render_job_id") or ""))
        reviews.append(_evaluate(metadata, payload))

    (AUDIT_DIR / "execution_batch.json").write_text(json.dumps(executions, indent=2, ensure_ascii=False), encoding="utf-8")
    (AUDIT_DIR / "human_review.json").write_text(json.dumps(reviews, indent=2, ensure_ascii=False), encoding="utf-8")

    total = len(reviews) or 1
    good_count = sum(1 for item in reviews if item["overall_quality"] == "good")
    caption_legibility = sum(1 for item in reviews if item["caption_legibility"] == "high")
    caption_expression = sum(1 for item in reviews if item["caption_expression"] == "high")
    motion_expression = sum(1 for item in reviews if item["motion_expression"] == "high")
    atmosphere_quality = sum(1 for item in reviews if item["atmosphere_quality"] == "high")
    timing_impact = sum(1 for item in reviews if item["timing_impact"] == "high")
    audiovisual_cohesion = sum(1 for item in reviews if item["audiovisual_cohesion"] == "high")
    slideshow_count = sum(1 for item in reviews if item["slideshow_feel"])

    metrics = {
        "total_videos": len(reviews),
        "good_videos_rate": round(good_count / total, 4),
        "caption_legibility_rate": round(caption_legibility / total, 4),
        "caption_expression_rate": round(caption_expression / total, 4),
        "motion_expression_rate": round(motion_expression / total, 4),
        "atmosphere_quality_rate": round(atmosphere_quality / total, 4),
        "timing_impact_rate": round(timing_impact / total, 4),
        "audiovisual_cohesion_rate": round(audiovisual_cohesion / total, 4),
        "slideshow_feel_rate": round(slideshow_count / total, 4),
        "batch_failures": failures,
    }
    (AUDIT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    block_summary = {
        "expression_unit": {
            "status": "PASS" if unit_blocks[0]["passed"] else "FAIL",
            "modules": unit_blocks[0]["modules"],
        },
        "expression_integration": {
            "status": "PASS" if unit_blocks[1]["passed"] else "FAIL",
            "modules": unit_blocks[1]["modules"],
        },
        "expression_product_batch": {
            "status": "PASS" if not failures and metrics["good_videos_rate"] >= 0.7 and metrics["slideshow_feel_rate"] <= 0.2 else "FAIL",
            "metrics": metrics,
        },
    }
    (AUDIT_DIR / "block_summary.json").write_text(json.dumps(block_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    main_failures: list[str] = []
    if not unit_blocks[0]["passed"]:
        main_failures.append("expression_unit_tests_failed")
    if not unit_blocks[1]["passed"]:
        main_failures.append("expression_integration_tests_failed")
    if failures:
        main_failures.append(f"pipeline_failures:{','.join(failures)}")
    if metrics["caption_expression_rate"] < 0.8:
        main_failures.append(f"caption_expression_rate_below_threshold:{metrics['caption_expression_rate']}")
    if metrics["motion_expression_rate"] < 0.8:
        main_failures.append(f"motion_expression_rate_below_threshold:{metrics['motion_expression_rate']}")
    if metrics["atmosphere_quality_rate"] < 0.8:
        main_failures.append(f"atmosphere_quality_rate_below_threshold:{metrics['atmosphere_quality_rate']}")
    if metrics["timing_impact_rate"] < 0.8:
        main_failures.append(f"timing_impact_rate_below_threshold:{metrics['timing_impact_rate']}")
    if metrics["slideshow_feel_rate"] > 0.2:
        main_failures.append(f"slideshow_feel_rate_too_high:{metrics['slideshow_feel_rate']}")

    verdict = "GO" if not main_failures else "HOLD"
    final_verdict = {
        "verdict": verdict,
        "editplan_operational": not failures and len(reviews) == len(SCENARIOS),
        "caption_expression": "high" if metrics["caption_expression_rate"] >= 0.9 else ("medium" if metrics["caption_expression_rate"] >= 0.7 else "low"),
        "atmosphere_strength": "high" if metrics["atmosphere_quality_rate"] >= 0.9 else ("medium" if metrics["atmosphere_quality_rate"] >= 0.7 else "low"),
        "motion_expression": "high" if metrics["motion_expression_rate"] >= 0.9 else ("medium" if metrics["motion_expression_rate"] >= 0.7 else "low"),
        "timing_impact": "high" if metrics["timing_impact_rate"] >= 0.9 else ("medium" if metrics["timing_impact_rate"] >= 0.7 else "low"),
        "audiovisual_cohesion": "high" if metrics["audiovisual_cohesion_rate"] >= 0.9 else ("medium" if metrics["audiovisual_cohesion_rate"] >= 0.7 else "low"),
        "good_videos_rate": metrics["good_videos_rate"],
        "main_failures": main_failures,
        "next_action": "freeze_editor_expression_baseline_if_stable" if verdict == "GO" else "inspect_expression_failures",
        "metrics": metrics,
    }
    (AUDIT_DIR / "final_verdict.json").write_text(json.dumps(final_verdict, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(final_verdict, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
