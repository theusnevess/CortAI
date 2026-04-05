from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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

AUDIT_DIR = ROOT / "OUT" / "audit" / "editor_final_parity_validation"
RUNTIME_DIR = AUDIT_DIR / "runtime"
EVENTS_DIR = AUDIT_DIR / "events"

SCENARIOS = [
    {"account_id": "acc_final_001", "niche": "true_crime", "topic": "station intercom warning"},
    {"account_id": "acc_final_002", "niche": "horror", "topic": "sealed room whisper phone rang inside"},
    {"account_id": "acc_final_003", "niche": "conspiracy", "topic": "station blueprint missing corridor"},
    {"account_id": "acc_final_004", "niche": "horror", "topic": "hospital intercom announced code from closed ward"},
    {"account_id": "acc_final_005", "niche": "true_crime", "topic": "dispatch recording captured impossible reply"},
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


def _load_metadata(render_job_id: str) -> dict[str, object]:
    metadata_path = RUNTIME_DIR / "content" / "metadata" / f"{render_job_id}.json"
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def _role_durations(subtitle_cues: list[dict[str, object]], role: str) -> list[float]:
    values: list[float] = []
    for cue in subtitle_cues:
        if cue.get("style_role") != role:
            continue
        values.append(round(float(cue.get("end") or 0.0) - float(cue.get("start") or 0.0), 3))
    return values


def _evaluate(metadata: dict[str, object], execution: dict[str, object]) -> dict[str, object]:
    edit_plan = dict(metadata.get("edit_plan") or {})
    caption_plan = dict(edit_plan.get("caption_plan") or {})
    motion_plan = dict(metadata.get("motion_plan") or {})
    color_plan = dict(metadata.get("color_plan") or {})
    timing_plan = dict(metadata.get("timing_plan") or {})
    music_plan = dict(metadata.get("music_plan") or {})
    subtitle_cues = list(metadata.get("subtitle_cues") or [])

    caption_profile = str(caption_plan.get("caption_behavior_profile") or "")
    animation_profile = dict(caption_plan.get("segment_caption_animation_profile") or {})
    style_profile = str(edit_plan.get("editor_style_profile") or "")

    caption_punch = (
        caption_plan.get("emphasis_animation_mode") == "scale_pulse"
        and caption_plan.get("emphasis_strength") == "high"
        and bool(caption_plan.get("key_word_emphasis_rules"))
        and "hook" in animation_profile
        and "payoff" in animation_profile
    )
    micro_variation = (
        "__" in style_profile
        and len({motion_plan.get("hook_motion_type"), motion_plan.get("setup_motion_type"), motion_plan.get("payoff_motion_type")}) >= 2
        and animation_profile.get("hook") != animation_profile.get("setup")
        and animation_profile.get("setup") != animation_profile.get("payoff")
        and caption_profile.endswith(("clean_snap", "measured_surge", "pressure_hold"))
    )
    payoff_durations = _role_durations(subtitle_cues, "payoff")
    payoff_memorability = (
        timing_plan.get("segment_landing_profile") == "hook_snap_setup_hold_payoff_land"
        and bool(payoff_durations)
        and payoff_durations[-1] >= max(payoff_durations)
        and float(music_plan.get("volume_payoff") or 0.0) > float(music_plan.get("volume_setup") or 0.0)
    )
    motif_progression = (
        motion_plan.get("hook_motion_type") != motion_plan.get("setup_motion_type")
        and motion_plan.get("setup_motion_type") != motion_plan.get("payoff_motion_type")
        and motion_plan.get("hook_motion_params", {}).get("scale_delta") != motion_plan.get("setup_motion_params", {}).get("scale_delta")
    )
    readability_preserved = (
        caption_plan.get("font_size_mode") == "large_mobile"
        and 3 <= len(subtitle_cues) <= 9
        and all(str(cue.get("text") or "").strip() for cue in subtitle_cues)
    )
    audiovisual_cohesion = (
        execution["video_qc"]["status"] == "APPROVE"
        and color_plan.get("polish_intensity") in {"medium", "high"}
        and bool(color_plan.get("atmosphere_behavior_profile"))
        and readability_preserved
    )

    return {
        "render_job_id": metadata.get("render_job_id", ""),
        "video_path": execution["pipeline_output"]["result"]["artifacts"].get("video", ""),
        "caption_punch": "high" if caption_punch else "medium",
        "micro_variation": "high" if micro_variation else "medium",
        "payoff_memorability": "high" if payoff_memorability else "medium",
        "motif_progression": "high" if motif_progression else "medium",
        "readability_preserved": readability_preserved,
        "audiovisual_cohesion": "high" if audiovisual_cohesion else "medium",
        "overall_quality": "good" if (caption_punch and micro_variation and payoff_memorability and motif_progression and audiovisual_cohesion) else "acceptable",
    }


def main() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)

    test_blocks = [
        _run_unittest_block(
            "final_parity_unit",
            [
                "tests.test_editor_plan_unittest",
                "tests.test_editor_interpreter_unittest",
                "tests.test_editor_expression_caption_unittest",
                "tests.test_editor_expression_motion_unittest",
            ],
        ),
        _run_unittest_block(
            "final_parity_integration",
            [
                "tests.test_editor_agent_service_unittest",
                "tests.test_editor_pipeline_integration_unittest",
                "tests.test_editor_expression_pipeline_integration_unittest",
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
        reviews.append(_evaluate(_load_metadata(str(result.get("render_job_id") or "")), payload))

    (AUDIT_DIR / "execution_batch.json").write_text(json.dumps(executions, indent=2, ensure_ascii=False), encoding="utf-8")
    (AUDIT_DIR / "human_review.json").write_text(json.dumps(reviews, indent=2, ensure_ascii=False), encoding="utf-8")

    total = len(reviews) or 1
    metrics = {
        "total_videos": len(reviews),
        "good_videos_rate": round(sum(1 for item in reviews if item["overall_quality"] == "good") / total, 4),
        "caption_punch_rate": round(sum(1 for item in reviews if item["caption_punch"] == "high") / total, 4),
        "micro_variation_rate": round(sum(1 for item in reviews if item["micro_variation"] == "high") / total, 4),
        "payoff_memorability_rate": round(sum(1 for item in reviews if item["payoff_memorability"] == "high") / total, 4),
        "motif_progression_rate": round(sum(1 for item in reviews if item["motif_progression"] == "high") / total, 4),
        "readability_preserved_rate": round(sum(1 for item in reviews if item["readability_preserved"]) / total, 4),
        "audiovisual_cohesion_rate": round(sum(1 for item in reviews if item["audiovisual_cohesion"] == "high") / total, 4),
        "batch_failures": failures,
    }
    (AUDIT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    block_summary = {
        "focused_unit_tests": {
            "status": "PASS" if test_blocks[0]["passed"] else "FAIL",
            "modules": test_blocks[0]["modules"],
        },
        "focused_integration_tests": {
            "status": "PASS" if test_blocks[1]["passed"] else "FAIL",
            "modules": test_blocks[1]["modules"],
        },
        "real_product_batch": {
            "status": "PASS" if not failures and metrics["good_videos_rate"] >= 0.8 else "FAIL",
            "metrics": metrics,
        },
    }
    (AUDIT_DIR / "block_summary.json").write_text(json.dumps(block_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    main_failures: list[str] = []
    if not test_blocks[0]["passed"]:
        main_failures.append("focused_unit_tests_failed")
    if not test_blocks[1]["passed"]:
        main_failures.append("focused_integration_tests_failed")
    if failures:
        main_failures.append(f"pipeline_failures:{','.join(failures)}")
    for key in (
        "caption_punch_rate",
        "micro_variation_rate",
        "payoff_memorability_rate",
        "motif_progression_rate",
        "readability_preserved_rate",
        "audiovisual_cohesion_rate",
    ):
        if metrics[key] < 0.8:
            main_failures.append(f"{key}_below_threshold:{metrics[key]}")

    verdict = "GO" if not main_failures else "HOLD"
    final_verdict = {
        "verdict": verdict,
        "caption_punch": "high" if metrics["caption_punch_rate"] >= 0.9 else ("medium" if metrics["caption_punch_rate"] >= 0.7 else "low"),
        "micro_variation": "high" if metrics["micro_variation_rate"] >= 0.9 else ("medium" if metrics["micro_variation_rate"] >= 0.7 else "low"),
        "payoff_memorability": "high" if metrics["payoff_memorability_rate"] >= 0.9 else ("medium" if metrics["payoff_memorability_rate"] >= 0.7 else "low"),
        "motif_progression": "high" if metrics["motif_progression_rate"] >= 0.9 else ("medium" if metrics["motif_progression_rate"] >= 0.7 else "low"),
        "readability_preserved": metrics["readability_preserved_rate"] >= 0.95,
        "audiovisual_cohesion": "high" if metrics["audiovisual_cohesion_rate"] >= 0.9 else ("medium" if metrics["audiovisual_cohesion_rate"] >= 0.7 else "low"),
        "good_videos_rate": metrics["good_videos_rate"],
        "main_failures": main_failures,
        "next_action": "editor_ready_for_manual_parity_judgment" if verdict == "GO" else "inspect_final_perceptual_gaps",
    }
    (AUDIT_DIR / "final_verdict.json").write_text(json.dumps(final_verdict, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(final_verdict, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
