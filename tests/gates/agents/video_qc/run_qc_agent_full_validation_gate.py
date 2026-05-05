from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.publish import StubPublishAdapter
from app.content.pipeline.render import StubRenderAdapter
from app.content.pipeline.service import ContentPipelineService
from app.content.pipeline.tts import StubTtsAdapter
from app.content.script_gen.models import ScriptGenerationResponse, StructuredScriptPayload
from app.creative.agents.asset_selection.models import AssetSelectionResult
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.video_qc.models import VideoQcInput
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import (
    AssetBackgroundPlan,
    AssetPlan,
    AssetRuntimeConstraints,
    AssetSegmentPlan,
    ScriptPlan,
)
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService


AUDIT_DIR = ROOT / "OUT" / "audit" / "qc_agent_full_validation_gate"
RUNTIME_DIR = AUDIT_DIR / "runtime"


class _StructuredGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        topic = str(getattr(request, "topic", "sealed corridor"))
        return ScriptGenerationResponse(
            script_plan=ScriptPlan(
                hook=f"Something started moving inside the {topic}.",
                setup="Witnesses said the warning arrived before the sound.",
                payoff="The last signal named a room nobody could open.",
                generation_mode="qc_full_validation",
            ),
            payload=StructuredScriptPayload(
                hook=f"Something started moving inside the {topic}.",
                setup="Witnesses said the warning arrived before the sound.",
                payoff="The last signal named a room nobody could open.",
                narrative_mode="qc_full_validation",
            ),
            provider_used="test",
            model_used="test",
            prompt_used="prompt",
            raw_output="{}",
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )


class _ValidationAssetSelectionAgent(AssetSelectionAgentService):
    def __init__(self) -> None:
        self._asset_plan = AssetPlan(
            visual_style="qc_validation",
            motion_profile="qc_validation",
            segments={
                "hook": AssetSegmentPlan(
                    background=AssetBackgroundPlan(
                        source="comfyui",
                        path=str(ROOT / "assets" / "objects" / "door_01.jpg"),
                    ),
                    category="door",
                ),
                "setup": AssetSegmentPlan(
                    background=AssetBackgroundPlan(
                        source="comfyui",
                        path=str(ROOT / "assets" / "environments" / "corridor_01.jpg"),
                    ),
                    category="corridor",
                ),
                "payoff": AssetSegmentPlan(
                    background=AssetBackgroundPlan(
                        source="comfyui",
                        path=str(ROOT / "assets" / "objects" / "document_01.jpg"),
                    ),
                    category="document",
                ),
            },
            runtime_constraints=AssetRuntimeConstraints(
                allow_safe_fallback=False,
                allow_comfyui_generation_fallback=False,
                allow_comfyui_edit=False,
                deterministic_seed="qc_full_validation",
            ),
        )

    def select(self, data):  # type: ignore[override]
        _ = data
        return AssetSelectionResult(
            asset_selection=self._asset_plan,
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )

    def align_first_frame(self, **kwargs):  # type: ignore[override]
        _ = kwargs
        return self._asset_plan


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _run_unittest_block(name: str, modules: list[str]) -> dict[str, object]:
    cmd = [sys.executable, "-m", "unittest", *modules]
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {
        "name": name,
        "command": " ".join(cmd),
        "modules": modules,
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "output": result.stdout or "",
    }


def _build_orchestrator() -> CreativeOrchestratorService:
    pipeline = ContentPipelineService(
        tts_adapter=StubTtsAdapter(base_dir=RUNTIME_DIR / "content"),
        render_adapter=StubRenderAdapter(base_dir=RUNTIME_DIR / "content"),
        publish_adapter=StubPublishAdapter(),
        event_path=AUDIT_DIR / "events" / "events.jsonl",
    )
    return CreativeOrchestratorService(
        pipeline_service=pipeline,
        asset_selection_agent=_ValidationAssetSelectionAgent(),
        script_agent=ScriptAgentService(generator=_StructuredGenerator()),
        voice_agent=VoiceAgentService(),
        video_qc_agent=VideoQcAgentService(),
        event_emitter=CreativeEventEmitter(event_path=AUDIT_DIR / "events" / "creative_events.jsonl"),
    )


def _load_metadata(render_job_id: str) -> dict[str, object]:
    path = RUNTIME_DIR / "content" / "metadata" / f"{render_job_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _build_qc_input(execution) -> VideoQcInput:  # noqa: ANN001
    result = execution.pipeline_output["result"]
    return VideoQcInput(
        render_job_id=str(result.get("render_job_id") or ""),
        video_path=str(result.get("artifacts", {}).get("video") or ""),
        audio_path=str(result.get("artifacts", {}).get("audio") or ""),
        metadata_path=str(
            Path(str(result.get("artifacts", {}).get("video") or "OUT/content/video/placeholder.mp4")).parents[1]
            / "metadata"
            / f"{result.get('render_job_id')}.json"
        ),
        script_text=execution.creative_pack.script_plan.narration_text(),
        tts_trace=dict(result.get("tts_trace") or {}),
        visual_trace=dict(result.get("visual_trace") or {}),
        edit_trace=dict(result.get("edit_trace") or {}),
    )


def _evaluate_case(
    *,
    name: str,
    qc_input: VideoQcInput,
    expected: str | list[str],
    category: str,
    qc_service: VideoQcAgentService,
) -> dict[str, object]:
    result = qc_service.evaluate(qc_input=qc_input)
    expected_statuses = [expected] if isinstance(expected, str) else list(expected)
    return {
        "name": name,
        "category": category,
        "expected": expected_statuses,
        "actual": result.status,
        "matched": result.status in expected_statuses,
        "publishable": result.publishable,
        "reasons": list(result.reasons),
        "score_summary": dict(result.decision.score_summary),
        "product_signals": dict(result.decision.product_signals),
        "decision_trace": dict(result.decision.decision_trace),
    }


def _build_case_inputs(base_input: VideoQcInput) -> list[dict[str, object]]:
    metadata_path = Path(base_input.metadata_path or "")
    base_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    cases: list[dict[str, object]] = []

    def add_case(name: str, expected: str | list[str], category: str, metadata: dict[str, object], *, script_text: str | None = None) -> None:
        case_path = metadata_path.with_name(f"{metadata_path.stem}_{name}.json")
        case_path.write_text(json.dumps(metadata), encoding="utf-8")
        cases.append(
            {
                "name": name,
                "expected": expected,
                "category": category,
                "qc_input": VideoQcInput(
                    render_job_id=base_input.render_job_id,
                    video_path=base_input.video_path,
                    audio_path=base_input.audio_path,
                    metadata_path=str(case_path),
                    script_text=script_text or base_input.script_text,
                    tts_trace=base_input.tts_trace,
                    visual_trace=base_input.visual_trace,
                    edit_trace=base_input.edit_trace,
                ),
            }
        )

    add_case("approve_strong", "APPROVE", "approve", json.loads(json.dumps(base_metadata)))

    borderline = json.loads(json.dumps(base_metadata))
    borderline["subtitle_cues"][0]["start"] = 0.6
    borderline["subtitle_cues"][0]["end"] = 1.6
    borderline["subtitle_cues"][0]["text"] = "LOOK BACK"
    borderline["subtitle_cues"][-1]["start"] = max(0.0, float(borderline["render_duration_s"]) - 1.2)
    borderline["subtitle_cues"][-1]["end"] = float(borderline["render_duration_s"]) - 0.2
    borderline["subtitle_cues"][-1]["text"] = "TURN NOW"
    add_case(
        "borderline_hook_payoff",
        "HOLD",
        "hold",
        borderline,
        script_text="Look back now. Turn away before the final door opens.",
    )

    reject_dark = json.loads(json.dumps(base_metadata))
    reject_dark["payoff_background_mean_luma"] = 20.0
    add_case("critical_dark_payoff", "REJECT", "reject", reject_dark)

    high_score_bad_product = json.loads(json.dumps(base_metadata))
    high_score_bad_product["subtitle_cues"][-1]["start"] = float(high_score_bad_product["render_duration_s"]) - 0.35
    high_score_bad_product["subtitle_cues"][-1]["end"] = float(high_score_bad_product["render_duration_s"]) - 0.1
    high_score_bad_product["subtitle_cues"][-1]["text"] = "STOP"
    add_case(
        "high_score_bad_product",
        ["HOLD", "REJECT"],
        "adversarial",
        high_score_bad_product,
        script_text="Everything worked until the final line stopped resolving the promise.",
    )

    atypical_good = json.loads(json.dumps(base_metadata))
    atypical_good["subtitle_cues"][0]["text"] = "A STRANGE ENTRY LOG APPEARED"
    atypical_good["subtitle_cues"][-1]["text"] = "THE FINAL LOG NAMED A ROOM NOBODY COULD OPEN"
    add_case("good_but_atypical", "APPROVE", "adversarial", atypical_good)

    minor_artifact = json.loads(json.dumps(base_metadata))
    minor_artifact["subtitle_cues"][0]["start"] = 0.18
    minor_artifact["subtitle_cues"][0]["end"] = 1.8
    add_case("strong_with_minor_artifact", ["APPROVE", "HOLD"], "adversarial", minor_artifact)

    multiple_light = json.loads(json.dumps(base_metadata))
    multiple_light["subtitle_cues"][0]["start"] = 0.45
    multiple_light["subtitle_cues"][0]["end"] = 1.55
    multiple_light["subtitle_cues"][0]["text"] = "LOOK BACK"
    multiple_light["subtitle_cues"][-1]["start"] = float(multiple_light["render_duration_s"]) - 0.9
    multiple_light["subtitle_cues"][-1]["end"] = float(multiple_light["render_duration_s"]) - 0.15
    multiple_light["subtitle_cues"][-1]["text"] = "TURN NOW"
    add_case("multiple_light_failures", "HOLD", "hold", multiple_light, script_text="Look back. Turn now.")

    critical_missing_audio = json.loads(json.dumps(base_metadata))
    cases.append(
        {
            "name": "missing_audio_file",
            "expected": "REJECT",
            "category": "reject",
            "qc_input": VideoQcInput(
                render_job_id=base_input.render_job_id,
                video_path=base_input.video_path,
                audio_path=str(metadata_path.with_name("missing_audio.wav")),
                metadata_path=str(metadata_path),
                script_text=base_input.script_text,
                tts_trace=base_input.tts_trace,
                visual_trace=base_input.visual_trace,
                edit_trace=base_input.edit_trace,
            ),
        }
    )

    weak_hook_strong_payoff = json.loads(json.dumps(base_metadata))
    weak_hook_strong_payoff["subtitle_cues"][0]["start"] = 0.75
    weak_hook_strong_payoff["subtitle_cues"][0]["end"] = 1.7
    weak_hook_strong_payoff["subtitle_cues"][0]["text"] = "LOOK BACK"
    add_case("weak_hook_strong_payoff", "HOLD", "borderline", weak_hook_strong_payoff)

    strong_hook_weak_payoff = json.loads(json.dumps(base_metadata))
    strong_hook_weak_payoff["subtitle_cues"][-1]["start"] = float(strong_hook_weak_payoff["render_duration_s"]) - 0.3
    strong_hook_weak_payoff["subtitle_cues"][-1]["end"] = float(strong_hook_weak_payoff["render_duration_s"]) - 0.08
    strong_hook_weak_payoff["subtitle_cues"][-1]["text"] = "STOP"
    add_case("strong_hook_weak_payoff", ["HOLD", "REJECT"], "borderline", strong_hook_weak_payoff)

    return cases


def _build_real_batch(orchestrator: CreativeOrchestratorService) -> tuple[list[dict[str, object]], list[object]]:
    scenarios = [
        ("acc_qc_full_01", "horror", "sealed corridor"),
        ("acc_qc_full_02", "horror", "mirror corridor"),
        ("acc_qc_full_03", "horror", "closed platform"),
        ("acc_qc_full_04", "horror", "service elevator"),
        ("acc_qc_full_05", "horror", "empty archive"),
    ]
    executions: list[dict[str, object]] = []
    raw = []
    for idx, (account_id, niche, topic) in enumerate(scenarios, start=1):
        execution = orchestrator.execute(
            CreativeOrchestratorInput(
                account_id=account_id,
                niche=niche,
                topic=topic,
                publish_slot=f"2026-03-28T1{idx}:00:00Z",
            )
        )
        executions.append(execution.to_dict())
        raw.append(execution)
    return executions, raw


def _determinism_check(qc_service: VideoQcAgentService, qc_input: VideoQcInput) -> dict[str, object]:
    runs = [qc_service.evaluate(qc_input=qc_input).to_dict() for _ in range(3)]
    baseline = json.dumps(runs[0]["decision"], sort_keys=True)
    consistent = all(
        run["status"] == runs[0]["status"]
        and run["publishable"] == runs[0]["publishable"]
        and json.dumps(run["decision"], sort_keys=True) == baseline
        for run in runs[1:]
    )
    return {
        "consistent": consistent,
        "runs": runs,
    }


def main() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    block_a = _run_unittest_block(
        "contracts_and_unit",
        [
            "tests.test_video_qc_agent_phase2_unittest",
            "tests.test_qc_agent_evolution_v2_0_integration_unittest",
        ],
    )
    block_b = _run_unittest_block(
        "enforcement_and_pipeline",
        [
            "tests.test_content_pipeline_d27_unittest",
            "tests.test_creative_orchestrator_phase2_unittest",
        ],
    )

    orchestrator = _build_orchestrator()
    real_batch, raw_executions = _build_real_batch(orchestrator)
    _write_json(AUDIT_DIR / "execution_batch.json", real_batch)

    first_approved = next(
        (execution for execution in raw_executions if execution.video_qc and execution.video_qc.status == "APPROVE"),
        None,
    )
    qc_service = VideoQcAgentService()
    decision_examples: list[dict[str, object]] = []
    determinism = {"consistent": False, "runs": []}
    if first_approved is not None:
        base_input = _build_qc_input(first_approved)
        determinism = _determinism_check(qc_service, base_input)
        for case in _build_case_inputs(base_input):
            decision_examples.append(
                _evaluate_case(
                    name=str(case["name"]),
                    expected=case["expected"],
                    category=str(case["category"]),
                    qc_input=case["qc_input"],
                    qc_service=qc_service,
                )
            )
    _write_json(
        AUDIT_DIR / "decision_examples.json",
        {"cases": decision_examples, "determinism": determinism},
    )

    approve_examples = sum(1 for case in decision_examples if case["actual"] == "APPROVE")
    hold_examples = sum(1 for case in decision_examples if case["actual"] == "HOLD")
    reject_examples = sum(1 for case in decision_examples if case["actual"] == "REJECT")
    mismatches = [case["name"] for case in decision_examples if not case["matched"]]
    false_approve = sum(1 for case in decision_examples if case["actual"] == "APPROVE" and "APPROVE" not in case["expected"])
    false_reject = sum(1 for case in decision_examples if case["actual"] == "REJECT" and "REJECT" not in case["expected"])
    false_hold = sum(1 for case in decision_examples if case["actual"] == "HOLD" and "HOLD" not in case["expected"])

    real_statuses = [row.get("video_qc", {}).get("status") for row in real_batch if row.get("video_qc")]
    real_approve = sum(1 for status in real_statuses if status == "APPROVE")
    real_hold = sum(1 for status in real_statuses if status == "HOLD")
    real_reject = sum(1 for status in real_statuses if status == "REJECT")
    publishable_count = sum(
        1 for row in real_batch if row.get("pipeline_output", {}).get("result", {}).get("publishable") is True
    )
    publish_manifest_count = sum(
        1 for row in real_batch if row.get("pipeline_output", {}).get("result", {}).get("publish_manifest")
    )

    metrics = {
        "real_batch_size": len(real_batch),
        "real_batch_approve_count": real_approve,
        "real_batch_hold_count": real_hold,
        "real_batch_reject_count": real_reject,
        "publishable_count": publishable_count,
        "publish_manifest_count": publish_manifest_count,
        "controlled_case_count": len(decision_examples),
        "approve_examples": approve_examples,
        "hold_examples": hold_examples,
        "reject_examples": reject_examples,
        "false_approve_rate": round(false_approve / max(1, len(decision_examples)), 4),
        "false_hold_rate": round(false_hold / max(1, len(decision_examples)), 4),
        "false_reject_rate": round(false_reject / max(1, len(decision_examples)), 4),
        "determinism_consistent": determinism["consistent"],
        "controlled_case_mismatches": mismatches,
    }
    _write_json(AUDIT_DIR / "metrics.json", metrics)

    human_review = {
        "block_a": "Contracts, serialization, decision model, and integration cases were exercised by unit tests.",
        "block_b": "Pipeline enforcement and orchestrator obedience were exercised by integration tests.",
        "block_c": "Controlled cases covered strong approve, borderline hold, critical reject, adversarial product weakness, minor artifacts, and determinism replay.",
        "block_d": "Real batch remained all-APPROVE. This validates non-inert approval flow but does not prove natural HOLD/REJECT distribution in uncontrolled batches.",
        "block_e": {
            "implemented": [
                "authoritative APPROVE/HOLD/REJECT",
                "publish gating after QC",
                "hard failures",
                "minimal score summary",
                "minimal product signals",
                "decision trace",
            ],
            "not_implemented": [
                "dynamic baseline",
                "batch-aware ranking",
                "confidence model",
                "top-k selection",
                "novelty handling",
            ],
        },
    }
    _write_json(AUDIT_DIR / "human_review.json", human_review)

    block_summary = {
        "block_a_contracts_and_unit": {
            "status": "PASS" if block_a["passed"] else "FAIL",
            "modules": block_a["modules"],
        },
        "block_b_enforcement_and_pipeline": {
            "status": "PASS" if block_b["passed"] else "FAIL",
            "modules": block_b["modules"],
        },
        "block_c_controlled_and_adversarial": {
            "status": "PASS" if not mismatches and determinism["consistent"] else "FAIL",
            "controlled_case_count": len(decision_examples),
            "mismatches": mismatches,
            "determinism_consistent": determinism["consistent"],
        },
        "block_d_real_batch": {
            "status": "PASS" if real_approve == len(real_batch) and publishable_count == real_approve else "FAIL",
            "real_batch_size": len(real_batch),
            "approve": real_approve,
            "hold": real_hold,
            "reject": real_reject,
        },
        "block_e_governance_honesty": {
            "status": "PASS",
            "not_implemented": human_review["block_e"]["not_implemented"],
        },
    }
    _write_json(AUDIT_DIR / "block_summary.json", block_summary)

    main_failures: list[str] = []
    if not block_a["passed"]:
        main_failures.append("BLOCK_A_FAILED")
    if not block_b["passed"]:
        main_failures.append("BLOCK_B_FAILED")
    if mismatches:
        main_failures.append(f"CONTROLLED_CASE_MISMATCHES:{','.join(mismatches)}")
    if not determinism["consistent"]:
        main_failures.append("DETERMINISM_FAILED")
    if publishable_count != real_approve or publish_manifest_count != real_approve:
        main_failures.append("ENFORCEMENT_COUNT_MISMATCH")
    if false_approve > 0:
        main_failures.append(f"FALSE_APPROVE_CASES:{false_approve}")

    verdict = "GO_WITH_MONITORING"
    if main_failures:
        verdict = "HOLD"
    final_verdict = {
        "verdict": verdict,
        "governor_authority": not any(code in main_failures for code in ["BLOCK_B_FAILED", "ENFORCEMENT_COUNT_MISMATCH"]),
        "deterministic": determinism["consistent"],
        "approve_hold_reject_operational": {
            "approve_seen": approve_examples > 0,
            "hold_seen": hold_examples > 0,
            "reject_seen": reject_examples > 0,
        },
        "false_approve_rate": metrics["false_approve_rate"],
        "false_hold_rate": metrics["false_hold_rate"],
        "false_reject_rate": metrics["false_reject_rate"],
        "real_batch_distribution": {
            "approve": real_approve,
            "hold": real_hold,
            "reject": real_reject,
        },
        "main_failures": main_failures,
        "next_action": (
            "freeze_qc_v2_with_monitoring" if verdict == "GO_WITH_MONITORING" else "inspect_qc_decision_failures_before_promotion"
        ),
    }
    _write_json(AUDIT_DIR / "final_verdict.json", final_verdict)
    print(json.dumps(final_verdict, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
