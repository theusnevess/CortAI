from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.publish import StubPublishAdapter
from app.content.pipeline.render import StubRenderAdapter
from app.content.pipeline.service import ContentPipelineService
from app.content.pipeline.tts import StubTtsAdapter
from app.creative.agents.asset_selection.models import AssetSelectionResult
from app.content.script_gen.models import ScriptGenerationResponse, StructuredScriptPayload
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


AUDIT_DIR = ROOT / "OUT" / "audit" / "qc_agent_evolution_v2_0_validation"
RUNTIME_DIR = AUDIT_DIR / "runtime"


class _StructuredGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        topic = str(getattr(request, "topic", "sealed corridor"))
        return ScriptGenerationResponse(
            script_plan=ScriptPlan(
                hook=f"Something started moving inside the {topic}.",
                setup="Witnesses said the warning arrived before the sound.",
                payoff="The last signal named a room nobody could open.",
                generation_mode="qc_validation_structured",
            ),
            payload=StructuredScriptPayload(
                hook=f"Something started moving inside the {topic}.",
                setup="Witnesses said the warning arrived before the sound.",
                payoff="The last signal named a room nobody could open.",
                narrative_mode="qc_validation_structured",
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
                deterministic_seed="qc_validation",
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
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run_unittest_suite() -> dict[str, object]:
    cmd = [
        sys.executable,
        "-m",
        "unittest",
        "tests.test_video_qc_agent_phase2_unittest",
        "tests.test_qc_agent_evolution_v2_0_integration_unittest",
        "tests.test_content_pipeline_d27_unittest",
        "tests.test_creative_orchestrator_phase2_unittest",
    ]
    result = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
    return {
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "output": result.stdout,
        "passed": result.returncode == 0,
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


def _build_decision_examples(execution) -> dict[str, object]:  # noqa: ANN001
    qc_service = VideoQcAgentService()
    approve_input = _build_qc_input(execution)
    approve = qc_service.evaluate(qc_input=approve_input).to_dict()

    metadata_path = Path(approve_input.metadata_path or "")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    hold_metadata = json.loads(json.dumps(metadata))
    hold_metadata["subtitle_cues"][0]["start"] = 0.6
    hold_metadata["subtitle_cues"][0]["end"] = 1.6
    hold_metadata["subtitle_cues"][0]["text"] = "LOOK BACK"
    hold_metadata["subtitle_cues"][-1]["start"] = max(0.0, float(hold_metadata["render_duration_s"]) - 1.2)
    hold_metadata["subtitle_cues"][-1]["end"] = float(hold_metadata["render_duration_s"]) - 0.2
    hold_metadata["subtitle_cues"][-1]["text"] = "TURN NOW"
    hold_metadata_path = metadata_path.with_name(f"{metadata_path.stem}_hold.json")
    hold_metadata_path.write_text(json.dumps(hold_metadata), encoding="utf-8")
    hold = qc_service.evaluate(
        qc_input=VideoQcInput(
            render_job_id=approve_input.render_job_id,
            video_path=approve_input.video_path,
            audio_path=approve_input.audio_path,
            metadata_path=str(hold_metadata_path),
            script_text="Look back now. Turn away before the final door opens.",
            tts_trace=approve_input.tts_trace,
            visual_trace=approve_input.visual_trace,
            edit_trace=approve_input.edit_trace,
        )
    ).to_dict()

    reject_metadata = json.loads(json.dumps(metadata))
    reject_metadata["payoff_background_mean_luma"] = 20.0
    reject_metadata_path = metadata_path.with_name(f"{metadata_path.stem}_reject.json")
    reject_metadata_path.write_text(json.dumps(reject_metadata), encoding="utf-8")
    reject = qc_service.evaluate(
        qc_input=VideoQcInput(
            render_job_id=approve_input.render_job_id,
            video_path=approve_input.video_path,
            audio_path=approve_input.audio_path,
            metadata_path=str(reject_metadata_path),
            script_text=approve_input.script_text,
            tts_trace=approve_input.tts_trace,
            visual_trace=approve_input.visual_trace,
            edit_trace=approve_input.edit_trace,
        )
    ).to_dict()

    return {
        "approve": approve,
        "hold": hold,
        "reject": reject,
    }


def main() -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    test_summary = _run_unittest_suite()
    _write_json(AUDIT_DIR / "block_summary.json", {"unit_and_integration_tests": test_summary})

    orchestrator = _build_orchestrator()
    inputs = [
        ("acc_qc_v20_01", "horror", "sealed corridor"),
        ("acc_qc_v20_02", "horror", "mirror corridor"),
        ("acc_qc_v20_03", "horror", "closed platform"),
        ("acc_qc_v20_04", "horror", "service elevator"),
        ("acc_qc_v20_05", "horror", "empty archive"),
    ]
    execution_batch: list[dict[str, object]] = []
    first_approved_execution = None
    for index, (account_id, niche, topic) in enumerate(inputs, start=1):
        execution = orchestrator.execute(
            CreativeOrchestratorInput(
                account_id=account_id,
                niche=niche,
                topic=topic,
                publish_slot=f"2026-03-28T1{index}:00:00Z",
            )
        )
        payload = execution.to_dict()
        execution_batch.append(payload)
        if first_approved_execution is None and execution.video_qc and execution.video_qc.status == "APPROVE":
            first_approved_execution = execution

    _write_json(AUDIT_DIR / "execution_batch.json", execution_batch)

    decision_examples = {}
    if first_approved_execution is not None:
        decision_examples = _build_decision_examples(first_approved_execution)
    _write_json(AUDIT_DIR / "decision_examples.json", decision_examples)

    statuses = [row.get("video_qc", {}).get("status") for row in execution_batch if row.get("video_qc")]
    approve_count = sum(1 for status in statuses if status == "APPROVE")
    hold_count = sum(1 for status in statuses if status == "HOLD")
    reject_count = sum(1 for status in statuses if status == "REJECT")
    publishable_count = sum(1 for row in execution_batch if row.get("pipeline_output", {}).get("result", {}).get("publishable") is True)
    publish_manifest_count = sum(1 for row in execution_batch if row.get("pipeline_output", {}).get("result", {}).get("publish_manifest"))
    decision_statuses = {name: payload.get("status") for name, payload in decision_examples.items()}

    metrics = {
        "batch_size": len(execution_batch),
        "approve_count": approve_count,
        "hold_count": hold_count,
        "reject_count": reject_count,
        "publishable_count": publishable_count,
        "publish_manifest_count": publish_manifest_count,
        "decision_example_statuses": decision_statuses,
    }
    _write_json(AUDIT_DIR / "metrics.json", metrics)

    human_review = {
        "enforcement": "APPROVE paths create publish manifests; HOLD and REJECT remain non-publishable by decision contract and orchestrator enforcement tests.",
        "decision_model": "Hard failures remain reject-only. Borderline product quality now maps to HOLD. Clean technical and product-safe outputs approve.",
        "product_layer": "Phase 2.0 product layer remains minimal and heuristic: hook_quality, payoff_quality, and publishability_signal.",
        "limitations": [
            "No dynamic baseline.",
            "No batch-aware ranking.",
            "No calibrated confidence model.",
        ],
    }
    _write_json(AUDIT_DIR / "human_review.json", human_review)

    main_failures: list[str] = []
    if not test_summary["passed"]:
        main_failures.append("UNIT_OR_INTEGRATION_TEST_FAILURE")
    if decision_statuses.get("approve") != "APPROVE":
        main_failures.append("APPROVE_EXAMPLE_MISSING")
    if decision_statuses.get("hold") != "HOLD":
        main_failures.append("HOLD_EXAMPLE_MISSING")
    if decision_statuses.get("reject") != "REJECT":
        main_failures.append("REJECT_EXAMPLE_MISSING")
    if publishable_count != approve_count:
        main_failures.append("PUBLISHABLE_COUNT_MISMATCH")

    verdict = {
        "verdict": "GO" if not main_failures else "HOLD",
        "enforcement_operational": not ("PUBLISHABLE_COUNT_MISMATCH" in main_failures),
        "decision_model_operational": decision_statuses.get("approve") == "APPROVE"
        and decision_statuses.get("hold") == "HOLD"
        and decision_statuses.get("reject") == "REJECT",
        "product_layer_minimum": "high" if first_approved_execution is not None else "medium",
        "approve_hold_reject_exercised": decision_statuses,
        "batch_size": len(execution_batch),
        "publishable_count": publishable_count,
        "main_failures": main_failures,
        "next_action": "promote_qc_v2_governor_if_stable" if not main_failures else "fix_validation_failures_before_promotion",
    }
    _write_json(AUDIT_DIR / "final_verdict.json", verdict)


if __name__ == "__main__":
    main()
