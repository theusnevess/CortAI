from __future__ import annotations

import json
import os
import re
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

AUDIT_DIR = ROOT / "OUT" / "audit" / "editor_agent_full_validation_gate"
RUNTIME_DIR = AUDIT_DIR / "runtime"
EVENTS_DIR = AUDIT_DIR / "events"

SCENARIOS = [
    {"account_id": "acc_editor_001", "niche": "true_crime", "topic": "station intercom warning"},
    {"account_id": "acc_editor_002", "niche": "horror", "topic": "sealed room whisper phone rang inside"},
    {"account_id": "acc_editor_003", "niche": "conspiracy", "topic": "station blueprint missing corridor"},
    {"account_id": "acc_editor_004", "niche": "horror", "topic": "hospital intercom announced code from closed ward"},
    {"account_id": "acc_editor_005", "niche": "true_crime", "topic": "dispatch recording captured impossible reply"},
]

ALLOWED_MOTION_TYPES = {
    "static",
    "slow_zoom_in",
    "slow_zoom_out",
    "pan_left",
    "pan_right",
    "pan_up",
    "pan_down",
    "subtle_push",
    "subtle_pull",
}
ALLOWED_TRANSITIONS = {"hard_cut", "crossfade", "fade_to_black"}
ALLOWED_GRADES = {
    "documentary_dark",
    "institutional_cold",
    "horror_lowkey",
    "neutral_investigative",
    "device_alert_tense",
}


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
    output = result.stdout or ""
    match = re.search(r"Ran (\d+) tests? in", output)
    total = int(match.group(1)) if match else 0
    return {
        "name": name,
        "modules": modules,
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "tests_ran": total,
        "output": output,
    }


def _caption_legibility(metadata: dict[str, object]) -> tuple[bool, str]:
    subtitle_cues = list(metadata.get("subtitle_cues") or [])
    caption_plan = dict(metadata.get("edit_plan", {}).get("caption_plan", {}))
    max_words = int(caption_plan.get("max_words_per_block") or 5)
    if not subtitle_cues:
        return False, "low"
    valid = True
    for cue in subtitle_cues:
        text = str(cue.get("text") or "").strip()
        if not text:
            valid = False
            break
        if len(text.split()) > max_words + 1:
            valid = False
            break
    quality = "high" if valid and 3 <= len(subtitle_cues) <= 9 else ("medium" if valid else "low")
    return valid, quality


def _music_balance(metadata: dict[str, object]) -> tuple[bool, str]:
    music_plan = dict(metadata.get("music_plan") or {})
    enabled = bool(music_plan.get("ducking_enabled"))
    ducking_level = float(music_plan.get("ducking_level_db") or 0.0)
    volumes = [float(music_plan.get(key) or 0.0) for key in ("volume_hook", "volume_setup", "volume_payoff")]
    valid = enabled and ducking_level <= -10.0 and max(volumes, default=0.0) <= 0.25
    quality = "high" if valid else "low"
    return valid, quality


def _motion_quality(metadata: dict[str, object]) -> tuple[bool, str]:
    motion_plan = dict(metadata.get("motion_plan") or {})
    motions = [
        str(motion_plan.get("hook_motion_type") or ""),
        str(motion_plan.get("setup_motion_type") or ""),
        str(motion_plan.get("payoff_motion_type") or ""),
    ]
    valid = all(motion in ALLOWED_MOTION_TYPES for motion in motions) and any(motion != "static" for motion in motions)
    quality = "high" if valid else "low"
    return valid, quality


def _transition_quality(metadata: dict[str, object]) -> tuple[bool, str]:
    transition_plan = dict(metadata.get("transition_plan") or {})
    t1 = str(transition_plan.get("hook_to_setup_type") or "")
    t2 = str(transition_plan.get("setup_to_payoff_type") or "")
    d1 = int(transition_plan.get("hook_to_setup_duration_ms") or 0)
    d2 = int(transition_plan.get("setup_to_payoff_duration_ms") or 0)
    valid = t1 in ALLOWED_TRANSITIONS and t2 in ALLOWED_TRANSITIONS and 80 <= d1 <= 400 and 80 <= d2 <= 400
    quality = "high" if valid else "low"
    return valid, quality


def _color_unification(metadata: dict[str, object]) -> tuple[bool, str]:
    color_plan = dict(metadata.get("color_plan") or {})
    preset = str(color_plan.get("grade_preset") or "")
    contrast = float(color_plan.get("contrast_level") or 0.0)
    saturation = float(color_plan.get("saturation_level") or 0.0)
    valid = preset in ALLOWED_GRADES and 0.7 <= saturation <= 1.1 and 0.95 <= contrast <= 1.15
    quality = "high" if valid else "low"
    return valid, quality


def _audiovisual_review(metadata: dict[str, object], qc_status: str, execution: dict[str, object]) -> dict[str, object]:
    caption_ok, caption_quality = _caption_legibility(metadata)
    music_ok, music_quality = _music_balance(metadata)
    motion_ok, motion_quality = _motion_quality(metadata)
    transition_ok, transition_quality = _transition_quality(metadata)
    color_ok, color_quality = _color_unification(metadata)

    edit_plan = dict(metadata.get("edit_plan") or {})
    timing_plan = dict(edit_plan.get("timing_plan") or {})
    total_duration = float(metadata.get("render_duration_s") or 0.0)
    expected_duration = float(timing_plan.get("total_duration_s") or 0.0)
    timing_ok = abs(total_duration - expected_duration) <= 1.5 if expected_duration > 0 else False
    subtitle_count = len(list(metadata.get("subtitle_cues") or []))
    edited_feel = caption_ok and music_ok and motion_ok and transition_ok and subtitle_count >= 3
    cohesion_ok = qc_status == "APPROVE" and edited_feel and timing_ok and color_ok

    return {
        "render_job_id": metadata.get("render_job_id", ""),
        "video_path": execution["pipeline_output"]["result"]["artifacts"].get("video", ""),
        "audio_path": execution["pipeline_output"]["result"]["artifacts"].get("audio", ""),
        "qc_status": qc_status,
        "caption_readability": caption_quality,
        "caption_timing_coherence": "high" if timing_ok and caption_ok else "medium" if caption_ok else "low",
        "music_voice_balance": music_quality,
        "motion_quality": motion_quality,
        "transition_naturalness": transition_quality,
        "color_consistency": color_quality,
        "audiovisual_cohesion": "high" if cohesion_ok else "medium" if edited_feel else "low",
        "feels_edited_not_slideshow": edited_feel,
        "overall_quality": "good" if cohesion_ok else ("acceptable" if edited_feel else "bad"),
        "subtitle_count": subtitle_count,
        "music_track_type": dict(metadata.get("music_plan") or {}).get("track_type"),
        "grade_preset": dict(metadata.get("color_plan") or {}).get("grade_preset"),
        "motion_profile": {
            "hook": dict(metadata.get("motion_plan") or {}).get("hook_motion_type"),
            "setup": dict(metadata.get("motion_plan") or {}).get("setup_motion_type"),
            "payoff": dict(metadata.get("motion_plan") or {}).get("payoff_motion_type"),
        },
    }


def _load_metadata(runtime_dir: Path, render_job_id: str) -> dict[str, object]:
    metadata_path = runtime_dir / "content" / "metadata" / f"{render_job_id}.json"
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def main() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)

    unit_blocks = [
        _run_unittest_block(
            "editor_contract_and_unit",
            [
                "tests.test_editor_plan_unittest",
                "tests.test_editor_interpreter_unittest",
                "tests.test_editor_agent_service_unittest",
            ],
        ),
        _run_unittest_block(
            "editor_integration",
            [
                "tests.test_editor_pipeline_integration_unittest",
                "tests.test_asset_plan_runtime_integration_unittest",
                "tests.test_creative_orchestrator_phase2_unittest",
                "tests.test_phase2_block4_smoke_unittest",
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
        reviews.append(_audiovisual_review(metadata, execution.video_qc.status, payload))

    (AUDIT_DIR / "execution_batch.json").write_text(json.dumps(executions, indent=2, ensure_ascii=False), encoding="utf-8")
    (AUDIT_DIR / "human_review.json").write_text(json.dumps(reviews, indent=2, ensure_ascii=False), encoding="utf-8")

    total_reviews = len(reviews) or 1
    good_count = sum(1 for item in reviews if item["overall_quality"] == "good")
    caption_good = sum(1 for item in reviews if item["caption_readability"] == "high")
    music_good = sum(1 for item in reviews if item["music_voice_balance"] == "high")
    motion_good = sum(1 for item in reviews if item["motion_quality"] == "high")
    transition_good = sum(1 for item in reviews if item["transition_naturalness"] == "high")
    color_good = sum(1 for item in reviews if item["color_consistency"] == "high")
    cohesion_good = sum(1 for item in reviews if item["audiovisual_cohesion"] == "high")

    metrics = {
        "total_videos": len(reviews),
        "good_videos_rate": round(good_count / total_reviews, 4),
        "caption_legibility_rate": round(caption_good / total_reviews, 4),
        "music_ducking_success_rate": round(music_good / total_reviews, 4),
        "motion_quality_rate": round(motion_good / total_reviews, 4),
        "transition_quality_rate": round(transition_good / total_reviews, 4),
        "color_unification_rate": round(color_good / total_reviews, 4),
        "audiovisual_cohesion_rate": round(cohesion_good / total_reviews, 4),
        "batch_failures": failures,
    }
    (AUDIT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    block_summary = {
        "contract_and_unit": {
            "status": "PASS" if unit_blocks[0]["passed"] else "FAIL",
            "tests_ran": unit_blocks[0]["tests_ran"],
            "modules": unit_blocks[0]["modules"],
        },
        "integration": {
            "status": "PASS" if unit_blocks[1]["passed"] else "FAIL",
            "tests_ran": unit_blocks[1]["tests_ran"],
            "modules": unit_blocks[1]["modules"],
        },
        "product_batch": {
            "status": "PASS" if not failures and metrics["good_videos_rate"] >= 0.7 else "FAIL",
            "requested_videos": len(SCENARIOS),
            "rendered_videos": len(reviews),
            "metrics": metrics,
        },
    }
    (AUDIT_DIR / "block_summary.json").write_text(json.dumps(block_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    main_failures: list[str] = []
    if not unit_blocks[0]["passed"]:
        main_failures.append("editor_unit_tests_failed")
    if not unit_blocks[1]["passed"]:
        main_failures.append("editor_integration_tests_failed")
    if failures:
        main_failures.append(f"pipeline_failures:{','.join(failures)}")
    if metrics["good_videos_rate"] < 0.7:
        main_failures.append(f"good_videos_rate_below_threshold:{metrics['good_videos_rate']}")
    if metrics["caption_legibility_rate"] < 0.8:
        main_failures.append(f"caption_legibility_rate_below_threshold:{metrics['caption_legibility_rate']}")
    if metrics["music_ducking_success_rate"] < 0.8:
        main_failures.append(f"music_ducking_success_rate_below_threshold:{metrics['music_ducking_success_rate']}")
    if metrics["audiovisual_cohesion_rate"] < 0.7:
        main_failures.append(f"audiovisual_cohesion_rate_below_threshold:{metrics['audiovisual_cohesion_rate']}")

    verdict = "GO" if not main_failures else "HOLD"
    final_verdict = {
        "verdict": verdict,
        "editplan_operational": not failures and len(reviews) == len(SCENARIOS),
        "caption_system": "high" if metrics["caption_legibility_rate"] >= 0.9 else ("medium" if metrics["caption_legibility_rate"] >= 0.7 else "low"),
        "music_atmosphere": "high" if metrics["music_ducking_success_rate"] >= 0.9 else ("medium" if metrics["music_ducking_success_rate"] >= 0.7 else "low"),
        "motion_quality": "high" if metrics["motion_quality_rate"] >= 0.9 else ("medium" if metrics["motion_quality_rate"] >= 0.7 else "low"),
        "transition_quality": "high" if metrics["transition_quality_rate"] >= 0.9 else ("medium" if metrics["transition_quality_rate"] >= 0.7 else "low"),
        "color_unification": "high" if metrics["color_unification_rate"] >= 0.9 else ("medium" if metrics["color_unification_rate"] >= 0.7 else "low"),
        "audiovisual_cohesion": "high" if metrics["audiovisual_cohesion_rate"] >= 0.9 else ("medium" if metrics["audiovisual_cohesion_rate"] >= 0.7 else "low"),
        "good_videos_rate": metrics["good_videos_rate"],
        "main_failures": main_failures,
        "next_action": "freeze_editor_baseline_if_stable" if verdict == "GO" else "inspect_editor_runtime_and_product_failures",
        "metrics": metrics,
    }
    (AUDIT_DIR / "final_verdict.json").write_text(json.dumps(final_verdict, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(final_verdict, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
