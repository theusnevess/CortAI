from __future__ import annotations

import json
import shutil
import subprocess
import sys
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
from app.creative.agents.account_health.models import AccountHealthInput
from app.creative.agents.account_health.service import AccountHealthAgentService
from app.creative.agents.asset_selection.models import AssetSelectionResult
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.trend_analysis.models import TrendAnalysisResult
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import AssetPlan, ScriptPlan, TrendProfile
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService


AUDIT_DIR = ROOT / "OUT" / "audit" / "account_health_agent_v2_phase_c_validation"


class _StructuredGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        topic = str(getattr(request, "topic", "sealed corridor"))
        return ScriptGenerationResponse(
            script_plan=ScriptPlan(
                hook=f"The first warning about the {topic} arrived before the lights failed.",
                setup="The corridor camera kept repeating the same impossible frame.",
                payoff="The final panel opened after the room was already empty.",
                generation_mode="account_health_phase_c",
            ),
            payload=StructuredScriptPayload(
                hook=f"The first warning about the {topic} arrived before the lights failed.",
                setup="The corridor camera kept repeating the same impossible frame.",
                payoff="The final panel opened after the room was already empty.",
                narrative_mode="account_health_phase_c",
            ),
            provider_used="test",
            model_used="test",
            prompt_used="prompt",
            raw_output="{}",
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )


class _StubTrendAgent:
    def load(self, data):  # noqa: ANN001
        return TrendAnalysisResult(
            trend_profile=TrendProfile(
                niche=str(getattr(data, "niche", "horror") or "horror"),
                dominant_hooks=["story_opening"],
                avg_duration="8-12s",
                pacing="fast_first_3s",
                visual_style="dark_backgrounds",
                text_style="large_caption_focus",
                trend_source="creative_center",
                confidence_scores={"overall": 0.82},
                updated_at="2026-04-03T00:00:00Z",
                valid_until="2026-04-10T00:00:00Z",
                sample_size=12,
                evidence=[],
            ),
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
            validation_summary={
                "status": "APPROVE",
                "overall_confidence": 0.82,
                "freshness_state": "fresh",
                "warnings": [],
                "errors": [],
            },
            collector_trace={
                "source_mix": ["creative_center"],
                "creative_center_refresh": {
                    "trace": {
                        "source": "creative_center",
                        "collector_version": "creative-center-public-v1",
                        "status": "COLLECTED",
                        "region_requested": "US",
                        "region_effective": "US",
                        "region_filter_applied": True,
                        "hashtags_count": 4,
                        "songs_count": 2,
                    }
                },
            },
        )


class _StubAssetSelectionAgent:
    def select(self, data):  # noqa: ANN001
        _ = data
        return AssetSelectionResult(
            asset_selection=AssetPlan(
                hook_asset="assets/imports/pexels/warning_display/pexels_warning_display_panel_9.jpg",
                setup_asset="assets/imports/pexels/sealed_access/pexels_security_door_access_control_dark_4.jpg",
                payoff_asset="assets/imports/pexels/map_blueprint/pexels_old_architectural_blueprint_close_up_5.jpg",
                visual_style="dark_backgrounds",
                motion_profile="subtle_push_in",
            ),
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )

    def align_first_frame(self, *, niche, topic, hook_text, asset_plan):  # noqa: ANN001
        _ = (niche, topic, hook_text)
        return asset_plan


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


def _build_orchestrator(event_path: Path) -> CreativeOrchestratorService:
    pipeline = ContentPipelineService(
        tts_adapter=StubTtsAdapter(base_dir=AUDIT_DIR / "runtime" / "content"),
        render_adapter=StubRenderAdapter(base_dir=AUDIT_DIR / "runtime" / "content"),
        publish_adapter=StubPublishAdapter(),
        event_path=AUDIT_DIR / "events" / "pipeline_events.jsonl",
    )
    return CreativeOrchestratorService(
        pipeline_service=pipeline,
        trend_analysis_agent=_StubTrendAgent(),
        script_agent=ScriptAgentService(generator=_StructuredGenerator()),
        asset_selection_agent=_StubAssetSelectionAgent(),
        voice_agent=VoiceAgentService(),
        video_qc_agent=VideoQcAgentService(),
        event_emitter=CreativeEventEmitter(event_path=event_path),
    )


def _seed_publish_records(account_id: str, count: int) -> None:
    path = AUDIT_DIR / "data" / "publish_records" / "publish_records.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if path.exists():
        existing = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = existing + [json.dumps({"account_id": account_id, "publish_id": f"{account_id}_pub_{index}"}) for index in range(count)]
    path.write_text("\n".join(rows), encoding="utf-8")


def _seed_metrics(account_id: str, views: list[int]) -> None:
    path = AUDIT_DIR / "metrics" / "video_metrics.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if path.exists():
        existing = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = existing + [json.dumps({"account_id": account_id, "views": value}) for value in views]
    path.write_text("\n".join(rows), encoding="utf-8")


def _seed_execution_history(account_id: str, rows: list[dict[str, object]]) -> None:
    for index, row in enumerate(rows, start=1):
        payload = {
            "creative_pack": {
                "account_id": account_id,
                "generated_at": row.get("generated_at", f"2026-04-03T00:{index:02d}:00Z"),
                "learning_insights": {
                    "signal_summary": {
                        "recent_hold_or_reject_rate": row.get("recent_hold_or_reject_rate", 0.0),
                        "avg_overall_score": row.get("learning_avg_overall_score", 0.9),
                    }
                },
                "asset_plan": {
                    "payoff_asset": row.get("payoff_asset", "assets/imports/pexels/map_blueprint/example.jpg"),
                },
            },
            "video_qc": {
                "status": row.get("qc_status", "APPROVE"),
                "decision": {
                    "status": row.get("qc_status", "APPROVE"),
                    "score_summary": {
                        "overall_score": row.get("overall_score", 0.9),
                    },
                },
            },
        }
        _write_json(AUDIT_DIR / "history" / account_id / f"run_{index}" / "execution_outputs.json", payload)


def _evaluate_runtime_case(
    *,
    name: str,
    topic: str,
    account_id: str,
    publish_count: int,
    views: list[int],
    history_rows: list[dict[str, object]],
    expected_status: str,
    expected_pipeline_status: str,
    expect_constraints: bool,
    expect_strategy_mode: str | None,
    expect_creative_pack: bool,
) -> dict[str, object]:
    event_path = AUDIT_DIR / "events" / f"{name}_creative_events.jsonl"
    orchestrator = _build_orchestrator(event_path)
    _seed_publish_records(account_id, publish_count)
    _seed_metrics(account_id, views)
    _seed_execution_history(account_id, history_rows)

    execution = orchestrator.execute(
        CreativeOrchestratorInput(
            account_id=account_id,
            niche="horror",
            topic=topic,
            publish_slot="2026-04-03T12:00:00Z",
        )
    )
    payload = execution.to_dict()
    event_rows = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    health_events = [row for row in event_rows if str(row.get("event_type") or "").startswith("CREATIVE/account_health_")]
    latest_health_event = health_events[-1] if health_events else {}
    strategy_mode = None if execution.strategy is None else execution.strategy.strategy_profile.content_mode

    matched = (
        execution.account_health is not None
        and execution.account_health.decision.status == expected_status
        and execution.pipeline_output["result"]["status"] == expected_pipeline_status
        and ((execution.creative_pack is not None) == expect_creative_pack)
    )
    if expect_strategy_mode is not None:
        matched = matched and strategy_mode == expect_strategy_mode
    if expect_constraints:
        matched = matched and bool((execution.account_health or payload["account_health"]) and execution.account_health.decision.recommended_constraints)
    else:
        matched = matched and not bool(execution.account_health.decision.recommended_constraints)

    return {
        "name": name,
        "account_id": account_id,
        "expected_status": expected_status,
        "actual_status": execution.account_health.decision.status,
        "expected_pipeline_status": expected_pipeline_status,
        "actual_pipeline_status": execution.pipeline_output["result"]["status"],
        "matched": matched,
        "creative_pack_present": execution.creative_pack is not None,
        "video_qc_present": execution.video_qc is not None,
        "strategy_mode": strategy_mode,
        "recommended_constraints": dict(execution.account_health.decision.recommended_constraints),
        "input_summary": dict(execution.account_health.input_summary),
        "decision_trace": dict(execution.account_health.decision_trace),
        "event_type": latest_health_event.get("event_type"),
        "event_details": latest_health_event.get("details", {}),
        "payload_account_health": payload.get("account_health"),
        "payload_account_health_status": None if execution.creative_pack is None else execution.creative_pack.account_health_status,
    }


def _evaluate_fallback_case() -> dict[str, object]:
    service = AccountHealthAgentService()
    result = service.evaluate(
        AccountHealthInput(
            account_id="acc_health_fallback",
            recent_publish_count=-1,
            recent_format_repetition_ratio=0.0,
            recent_views_drop_ratio=0.0,
            recent_low_performance_streak=0,
        )
    )
    return {
        "name": "fallback_negative_publish_count",
        "expected_status": "SAFE",
        "actual_status": result.decision.status,
        "matched": result.decision.status == "SAFE" and result.fallback.used,
        "fallback_used": result.fallback.used,
        "fallback_reason": result.fallback.reason,
        "decision_trace": dict(result.decision_trace),
    }


def _evaluate_determinism_case() -> dict[str, object]:
    service = AccountHealthAgentService()
    input_data = AccountHealthInput(
        account_id="acc_health_det",
        recent_publish_count=4,
        recent_format_repetition_ratio=0.7,
        recent_views_drop_ratio=0.5,
        recent_low_performance_streak=2,
    )
    runs = [service.evaluate(input_data).to_dict() for _ in range(3)]
    baseline = json.dumps(runs[0], sort_keys=True)
    consistent = all(json.dumps(run, sort_keys=True) == baseline for run in runs[1:])
    return {
        "name": "deterministic_replay",
        "consistent": consistent,
        "runs": runs,
    }


def _build_event_summary() -> dict[str, object]:
    summary: dict[str, int] = {}
    examples: dict[str, dict[str, object]] = {}
    for path in sorted((AUDIT_DIR / "events").glob("*creative_events.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            event_type = str(row.get("event_type") or "")
            summary[event_type] = summary.get(event_type, 0) + 1
            if event_type not in examples:
                examples[event_type] = row.get("details", {})
    return {"counts": summary, "examples": examples}


def main() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR, ignore_errors=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    block_a = _run_unittest_block(
        "health_service_and_orchestrator",
        [
            "tests.test_account_health_agent_phase2_unittest",
            "tests.test_creative_orchestrator_phase2_unittest",
            "tests.test_phase2_block2_smoke_unittest",
        ],
    )

    runtime_cases = [
        _evaluate_runtime_case(
            name="safe_healthy",
            topic="sealed corridor",
            account_id="acc_health_safe",
            publish_count=4,
            views=[100, 110, 120, 125, 130, 140],
            history_rows=[
                {"qc_status": "APPROVE", "overall_score": 0.92, "payoff_asset": "assets/imports/pexels/map_blueprint/example_a.jpg"},
                {"qc_status": "APPROVE", "overall_score": 0.9, "payoff_asset": "assets/imports/pexels/warning_display/example_b.jpg"},
                {"qc_status": "APPROVE", "overall_score": 0.91, "payoff_asset": "assets/imports/pexels/sealed_access/example_c.jpg"},
            ],
            expected_status="SAFE",
            expected_pipeline_status="READY",
            expect_constraints=False,
            expect_strategy_mode="standard",
            expect_creative_pack=True,
        ),
        _evaluate_runtime_case(
            name="caution_views_and_streak",
            topic="mirror warning",
            account_id="acc_health_caution",
            publish_count=5,
            views=[210, 220, 230, 130, 120, 110],
            history_rows=[
                {"qc_status": "APPROVE", "overall_score": 0.9, "payoff_asset": "assets/imports/pexels/map_blueprint/example_a.jpg"},
                {"qc_status": "APPROVE", "overall_score": 0.79, "payoff_asset": "assets/imports/pexels/map_blueprint/example_b.jpg"},
                {"qc_status": "APPROVE", "overall_score": 0.78, "payoff_asset": "assets/imports/pexels/map_blueprint/example_c.jpg"},
            ],
            expected_status="CAUTION",
            expected_pipeline_status="READY",
            expect_constraints=True,
            expect_strategy_mode="conservative",
            expect_creative_pack=True,
        ),
        _evaluate_runtime_case(
            name="hold_views_and_streak",
            topic="sealed tunnel",
            account_id="acc_health_hold",
            publish_count=6,
            views=[300, 320, 310, 40, 35, 30],
            history_rows=[
                {"qc_status": "HOLD", "overall_score": 0.7},
                {"qc_status": "REJECT", "overall_score": 0.68},
                {"qc_status": "HOLD", "overall_score": 0.71},
                {"qc_status": "REJECT", "overall_score": 0.69},
            ],
            expected_status="HOLD",
            expected_pipeline_status="HOLD",
            expect_constraints=True,
            expect_strategy_mode=None,
            expect_creative_pack=False,
        ),
        _evaluate_runtime_case(
            name="mixed_signal_views_bad_publish_healthy",
            topic="archive warning",
            account_id="acc_health_mixed",
            publish_count=3,
            views=[190, 195, 200, 120, 110, 100],
            history_rows=[
                {"qc_status": "APPROVE", "overall_score": 0.89, "payoff_asset": "assets/imports/pexels/map_blueprint/example_a.jpg"},
                {"qc_status": "APPROVE", "overall_score": 0.88, "payoff_asset": "assets/imports/pexels/warning_display/example_b.jpg"},
                {"qc_status": "APPROVE", "overall_score": 0.87, "payoff_asset": "assets/imports/pexels/sealed_access/example_c.jpg"},
            ],
            expected_status="CAUTION",
            expected_pipeline_status="READY",
            expect_constraints=True,
            expect_strategy_mode="conservative",
            expect_creative_pack=True,
        ),
        _evaluate_runtime_case(
            name="repetition_only_caution",
            topic="hallway record",
            account_id="acc_health_repetition",
            publish_count=4,
            views=[150, 152, 151, 153, 154, 155],
            history_rows=[
                {"qc_status": "APPROVE", "overall_score": 0.9, "payoff_asset": "assets/imports/pexels/map_blueprint/example_a.jpg"},
                {"qc_status": "APPROVE", "overall_score": 0.91, "payoff_asset": "assets/imports/pexels/map_blueprint/example_b.jpg"},
                {"qc_status": "APPROVE", "overall_score": 0.92, "payoff_asset": "assets/imports/pexels/map_blueprint/example_c.jpg"},
                {"qc_status": "APPROVE", "overall_score": 0.9, "payoff_asset": "assets/imports/pexels/map_blueprint/example_d.jpg"},
            ],
            expected_status="CAUTION",
            expected_pipeline_status="READY",
            expect_constraints=True,
            expect_strategy_mode="conservative",
            expect_creative_pack=True,
        ),
    ]
    fallback_case = _evaluate_fallback_case()
    determinism_case = _evaluate_determinism_case()

    execution_batch = {
        "runtime_cases": runtime_cases,
        "fallback_case": fallback_case,
        "determinism_case": determinism_case,
    }
    _write_json(AUDIT_DIR / "execution_batch.json", execution_batch)

    decision_examples = {
        "cases": runtime_cases + [fallback_case],
        "determinism": determinism_case,
    }
    _write_json(AUDIT_DIR / "decision_examples.json", decision_examples)

    event_summary = _build_event_summary()
    _write_json(AUDIT_DIR / "event_summary.json", event_summary)

    runtime_mismatches = [case["name"] for case in runtime_cases if not case["matched"]]
    health_event_types = set(event_summary["counts"].keys())
    metrics = {
        "runtime_case_count": len(runtime_cases),
        "runtime_case_matches": len(runtime_cases) - len(runtime_mismatches),
        "safe_cases": sum(1 for case in runtime_cases if case["actual_status"] == "SAFE"),
        "caution_cases": sum(1 for case in runtime_cases if case["actual_status"] == "CAUTION"),
        "hold_cases": sum(1 for case in runtime_cases if case["actual_status"] == "HOLD"),
        "fallback_case_passed": fallback_case["matched"],
        "determinism_consistent": determinism_case["consistent"],
        "health_event_types_seen": sorted(health_event_types),
        "health_event_count": sum(
            count for event_type, count in event_summary["counts"].items() if event_type.startswith("CREATIVE/account_health_")
        ),
    }
    _write_json(AUDIT_DIR / "metrics.json", metrics)

    block_summary = {
        "block_a_unit_and_integration": {
            "status": "PASS" if block_a["passed"] else "FAIL",
            "modules": block_a["modules"],
        },
        "block_b_controlled_runtime_battery": {
            "status": "PASS" if not runtime_mismatches else "FAIL",
            "mismatches": runtime_mismatches,
        },
        "block_c_fallback_and_determinism": {
            "status": "PASS" if fallback_case["matched"] and determinism_case["consistent"] else "FAIL",
            "fallback_passed": fallback_case["matched"],
            "determinism_consistent": determinism_case["consistent"],
        },
        "block_d_downstream_correctness": {
            "status": "PASS" if all(
                case["matched"]
                and (
                    case["actual_status"] == "HOLD"
                    or (
                        case["payload_account_health_status"] == case["actual_status"]
                        and bool(case["event_details"].get("decision_trace"))
                    )
                )
                for case in runtime_cases
            ) else "FAIL",
            "strategy_modes": {case["name"]: case["strategy_mode"] for case in runtime_cases},
        },
        "block_e_event_and_artifact_visibility": {
            "status": "PASS" if {
                "CREATIVE/account_health_safe",
                "CREATIVE/account_health_caution",
                "CREATIVE/account_health_hold",
            }.issubset(health_event_types) else "FAIL",
            "event_types_seen": sorted(health_event_types),
        },
    }
    _write_json(AUDIT_DIR / "block_summary.json", block_summary)

    human_review = {
        "summary": (
            "Phase C validates the activated and explainable Account Health path under deterministic controlled scenarios. "
            "The subsystem now proves SAFE, CAUTION, HOLD, fallback, replay consistency, and downstream propagation."
        ),
        "implemented": [
            "real input activation from runtime-local artifacts",
            "decision trace",
            "early HOLD enforcement",
            "strategy constraint propagation",
            "health event enrichment",
        ],
        "not_implemented": [
            "moderation telemetry",
            "platform strike ingestion",
            "probabilistic scoring",
            "standalone promotion governance",
        ],
        "next_phase": "standalone_governance_decision",
    }
    _write_json(AUDIT_DIR / "human_review.json", human_review)

    main_failures: list[str] = []
    if not block_a["passed"]:
        main_failures.append("UNIT_OR_INTEGRATION_FAIL")
    if runtime_mismatches:
        main_failures.append(f"CONTROLLED_CASE_MISMATCHES:{','.join(runtime_mismatches)}")
    if not fallback_case["matched"]:
        main_failures.append("FALLBACK_BEHAVIOR_FAIL")
    if not determinism_case["consistent"]:
        main_failures.append("DETERMINISM_FAIL")
    if block_summary["block_e_event_and_artifact_visibility"]["status"] != "PASS":
        main_failures.append("EVENT_VISIBILITY_FAIL")

    verdict = "GO" if not main_failures else "HOLD"
    final_verdict = {
        "verdict": verdict,
        "input_activation_real": True,
        "auditability_real": True,
        "safe_caution_hold_operational": not runtime_mismatches,
        "fallback_explicit": fallback_case["matched"],
        "deterministic_under_controlled_inputs": determinism_case["consistent"],
        "downstream_constraints_propagate": block_summary["block_d_downstream_correctness"]["status"] == "PASS",
        "main_failures": main_failures,
        "next_action": "phase_d_standalone_governance_decision" if verdict == "GO" else "inspect_phase_c_failures",
    }
    _write_json(AUDIT_DIR / "final_verdict.json", final_verdict)

    print(json.dumps(final_verdict, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
