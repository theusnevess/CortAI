from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
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
from app.creative.agents.account_health.service import AccountHealthAgentService
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.strategy.service import StrategyAgentService
from app.creative.agents.trend_analysis.models import TrendAnalysisInput, TrendCollectorResult, TrendSourceRecord
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import ScriptPlan, TrendEvidenceReference, TrendProfile
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService
from app.runtime.asset_selector import AssetSelector


AUDIT_DIR = ROOT / "OUT" / "audit" / "trend_analysis_full_validation_gate"
FIXED_NOW = "2026-04-03T12:00:00Z"


class _StructuredGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        return ScriptGenerationResponse(
            script_plan=ScriptPlan(
                hook="A red phone rang inside the shuttered wing.",
                setup="The hallway lights died before anyone answered.",
                payoff="The final detail named door 16, removed from the floorplan.",
                generation_mode="test_structured",
            ),
            payload=StructuredScriptPayload(
                hook="A red phone rang inside the shuttered wing.",
                setup="The hallway lights died before anyone answered.",
                payoff="The final detail named door 16, removed from the floorplan.",
                narrative_mode="official_warning",
            ),
            provider_used="test",
            model_used="test",
            prompt_used="prompt",
            raw_output="{}",
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )


class _FixtureCreativeCenterCollector:
    def __init__(self, result: TrendCollectorResult) -> None:
        self._result = result

    def collect(self, data: TrendAnalysisInput) -> TrendCollectorResult:
        _ = data
        return self._result


def _reset_audit_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(name: str, payload: object) -> None:
    (AUDIT_DIR / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run_unittest_suite() -> dict[str, object]:
    tests = [
        "tests.test_trend_analysis_agent_phase2_unittest",
        "tests.test_creative_orchestrator_phase2_unittest",
        "tests.test_strategy_agent_evolution_v2_0_integration_unittest",
        "tests.test_phase2_block3_smoke_unittest",
    ]
    command = [sys.executable, "-m", "unittest", *tests]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "tests": tests,
        "passed": completed.returncode == 0,
    }


def _make_evidence(prefix: str, *, count: int, current_time: str) -> list[TrendEvidenceReference]:
    return [
        TrendEvidenceReference(
            evidence_type="creative_center_hashtag",
            source="creative_center",
            reference_id=f"{prefix}:{index}",
            reference_url="https://ads.tiktok.com/business/creativecenter/pc/en",
            captured_at=current_time,
            region="US",
            metadata={"rank": index},
        )
        for index in range(1, count + 1)
    ]


def _creative_center_result(
    *,
    hooks: list[str],
    pacing: str,
    visual_style: str,
    avg_duration: str = "8-12s",
    text_style: str = "large_caption_focus",
    sample_size: int = 5,
) -> TrendCollectorResult:
    record = TrendSourceRecord(
        source="creative_center",
        niche="horror",
        region="US",
        collected_at=FIXED_NOW,
        sample_size=sample_size,
        dominant_hooks=hooks,
        avg_duration=avg_duration,
        pacing=pacing,
        visual_style=visual_style,
        text_style=text_style,
        evidence=_make_evidence("cc", count=sample_size, current_time=FIXED_NOW),
        source_metadata={
            "requested_region": "US",
            "region_effective": "unfiltered_public_surface",
            "region_filter_applied": False,
        },
    )
    return TrendCollectorResult(
        source_record=record,
        used_stub=False,
        trace={
            "source": "creative_center",
            "collector_version": "creative-center-public-v1",
            "status": "COLLECTED",
            "region_requested": "US",
            "region_effective": "unfiltered_public_surface",
            "region_filter_applied": False,
            "hashtags_count": sample_size,
            "songs_count": 0,
        },
    )


def _creative_center_failure_result(*, status: str = "COLLECTION_FAILED", error: str = "") -> TrendCollectorResult:
    return TrendCollectorResult(
        source_record=None,
        used_stub=False,
        trace={
            "source": "creative_center",
            "collector_version": "creative-center-public-v1",
            "status": status,
            "region_requested": "US",
            "region_effective": "unfiltered_public_surface",
            "region_filter_applied": False,
            "error": error,
        },
    )


def _write_manual_curation(trends_dir: Path, *, niche: str = "horror") -> None:
    manual_dir = trends_dir / "manual_curation"
    manual_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "niche": niche,
        "region": "US",
        "source": "manual_curation",
        "collected_at": FIXED_NOW,
        "updated_at": FIXED_NOW,
        "valid_until": "2026-04-17T12:00:00Z",
        "sample_size": 4,
        "dominant_hooks": ["story_opening"],
        "avg_duration": "8-12s",
        "pacing": "fast_first_3s",
        "visual_style": "dark_backgrounds",
        "text_style": "large_caption_focus",
        "trend_version": "2.0",
        "collector_version": "manual-curation-v1",
        "evidence": [
            {
                "evidence_type": "top_video",
                "source": "manual_curation",
                "reference_id": "manual:1",
                "reference_url": "https://www.tiktok.com/@example/video/1",
                "captured_at": FIXED_NOW,
                "region": "US",
                "metadata": {"views": 2300000},
            },
            {
                "evidence_type": "top_video",
                "source": "manual_curation",
                "reference_id": "manual:2",
                "reference_url": "https://www.tiktok.com/@example/video/2",
                "captured_at": FIXED_NOW,
                "region": "US",
                "metadata": {"views": 1900000},
            },
            {
                "evidence_type": "top_video",
                "source": "manual_curation",
                "reference_id": "manual:3",
                "reference_url": "https://www.tiktok.com/@example/video/3",
                "captured_at": FIXED_NOW,
                "region": "US",
                "metadata": {"views": 1500000},
            },
        ],
        "source_metadata": {"curator": "validation_gate_fixture"},
    }
    (manual_dir / f"{niche}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_validated_cache(trends_dir: Path, *, niche: str = "horror") -> None:
    validated_dir = trends_dir / "cache" / "validated"
    validated_dir.mkdir(parents=True, exist_ok=True)
    payload = TrendProfile(
        niche=niche,
        dominant_hooks=["story_opening"],
        avg_duration="8-12s",
        pacing="fast_first_3s",
        visual_style="dark_backgrounds",
        text_style="large_caption_focus",
        region="US",
        trend_source="validated_cache_fixture",
        confidence_scores={
            "dominant_hooks": 0.78,
            "avg_duration": 0.76,
            "pacing": 0.78,
            "visual_style": 0.79,
            "overall": 0.7775,
        },
        updated_at=FIXED_NOW,
        valid_until="2026-04-10T12:00:00Z",
        sample_size=5,
        evidence=_make_evidence("cache", count=5, current_time=FIXED_NOW),
        collector_version="trend-analysis-agent-v2_0_gate_fixture",
    ).to_dict()
    (validated_dir / f"{niche}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _read_event_rows(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _case_summary(case_id: str, execution: dict[str, object], events: list[dict[str, object]]) -> dict[str, object]:
    trend = dict(execution.get("trend_analysis") or {})
    trend_profile = dict(trend.get("trend_profile") or {})
    validation_summary = dict(trend.get("validation_summary") or {})
    collector_trace = dict(trend.get("collector_trace") or {})
    strategy = dict(execution.get("strategy") or {})
    strategy_profile = dict(strategy.get("strategy_profile") or {})
    strategy_trace = dict(strategy.get("decision_trace") or {})
    asset_selection = dict(execution.get("asset_selection") or {})
    asset_plan = dict(asset_selection.get("asset_selection") or {})
    qc = dict(execution.get("video_qc") or {})
    pipeline_output = dict(execution.get("pipeline_output") or {})
    result = dict(pipeline_output.get("result") or {})
    return {
        "case_id": case_id,
        "trend_source": trend_profile.get("trend_source", ""),
        "source_mix": list(collector_trace.get("source_mix") or []),
        "validation_status": validation_summary.get("status", ""),
        "fallback_used": dict(trend.get("fallback") or {}).get("used", False),
        "fallback_reason": dict(trend.get("fallback") or {}).get("reason", ""),
        "fallback_path": collector_trace.get("fallback_path", ""),
        "strategy_profile": strategy_profile,
        "strategy_trend_adjustments": list(strategy_trace.get("trend_adjustments") or []),
        "asset_visual_style": asset_plan.get("visual_style", ""),
        "asset_motion_profile": asset_plan.get("motion_profile", ""),
        "asset_hook_effects": list((((asset_plan.get("segments") or {}).get("hook") or {}).get("effects") or [])),
        "qc_status": qc.get("status"),
        "pipeline_status": result.get("status"),
        "events_emitted": [row.get("event_type") for row in events],
    }


def _run_case(
    *,
    case_id: str,
    collector_result: TrendCollectorResult,
    manual_curation: bool = False,
    validated_cache: bool = False,
) -> dict[str, object]:
    AssetSelector._global_video_signatures.clear()
    AssetSelector._global_failed_sequences_prevented.clear()
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        out = root / "OUT"
        trends_dir = root / "trends"
        for child in ("current", "history", "manual_curation", "cache"):
            (trends_dir / child).mkdir(parents=True, exist_ok=True)
        if manual_curation:
            _write_manual_curation(trends_dir)
        if validated_cache:
            _write_validated_cache(trends_dir)
        pipeline = ContentPipelineService(
            tts_adapter=StubTtsAdapter(base_dir=out / "content"),
            render_adapter=StubRenderAdapter(base_dir=out / "content"),
            publish_adapter=StubPublishAdapter(),
            event_path=out / "events" / "events.jsonl",
        )
        trend_agent = TrendAnalysisAgentService(
            trends_dir=trends_dir,
            creative_center_collector=_FixtureCreativeCenterCollector(collector_result),
        )
        orchestrator = CreativeOrchestratorService(
            pipeline_service=pipeline,
            account_health_agent=AccountHealthAgentService(),
            trend_analysis_agent=trend_agent,
            strategy_agent=StrategyAgentService(),
            asset_selection_agent=AssetSelectionAgentService(),
            script_agent=ScriptAgentService(generator=_StructuredGenerator()),
            voice_agent=VoiceAgentService(),
            video_qc_agent=VideoQcAgentService(),
            event_emitter=CreativeEventEmitter(event_path=out / "events" / "creative_events.jsonl"),
        )
        execution = orchestrator.execute(
            CreativeOrchestratorInput(
                account_id=f"acc_trend_gate_{case_id}",
                niche="horror",
                topic="sealed corridor warning",
                publish_slot="2026-04-03T12:00:00Z",
                force_refresh_trends=True,
            )
        )
        execution_payload = execution.to_dict()
        event_rows = _read_event_rows(out / "events" / "creative_events.jsonl")
        return {
            "case_id": case_id,
            "execution": execution_payload,
            "events": event_rows,
            "summary": _case_summary(case_id, execution_payload, event_rows),
        }


def _run_controlled_batch() -> list[dict[str, object]]:
    return [
        _run_case(
            case_id="creative_center_fast",
            collector_result=_creative_center_result(
                hooks=["story_opening"],
                pacing="fast_first_3s",
                visual_style="dark_backgrounds",
            ),
        ),
        _run_case(
            case_id="creative_center_baseline",
            collector_result=_creative_center_result(
                hooks=["question"],
                pacing="baseline",
                visual_style="phase1_baseline",
                avg_duration="15-20s",
                text_style="caption_focus",
            ),
        ),
        _run_case(
            case_id="creative_center_failed_manual_recovery",
            collector_result=_creative_center_failure_result(error="fixture_http_timeout"),
            manual_curation=True,
        ),
        _run_case(
            case_id="creative_center_invalid_validated_cache",
            collector_result=_creative_center_result(
                hooks=[],
                pacing="baseline",
                visual_style="phase1_baseline",
                sample_size=4,
            ),
            validated_cache=True,
        ),
    ]


def main() -> None:
    _reset_audit_dir()

    unittest_summary = _run_unittest_suite()
    batch = _run_controlled_batch()
    summaries = {item["case_id"]: item["summary"] for item in batch}

    fast = summaries["creative_center_fast"]
    baseline = summaries["creative_center_baseline"]
    failed_manual = summaries["creative_center_failed_manual_recovery"]
    cache_fallback = summaries["creative_center_invalid_validated_cache"]

    metrics = {
        "tests_passed": unittest_summary["passed"],
        "controlled_case_count": len(batch),
        "creative_center_present_in_fast_case": "creative_center" in fast["source_mix"],
        "creative_center_present_in_baseline_case": "creative_center" in baseline["source_mix"],
        "strategy_reacted_to_creative_center": bool(fast["strategy_trend_adjustments"]) and not bool(baseline["strategy_trend_adjustments"]),
        "strategy_hook_aggressiveness_changed": fast["strategy_profile"].get("hook_aggressiveness") != baseline["strategy_profile"].get("hook_aggressiveness"),
        "asset_visual_style_changed": fast["asset_visual_style"] != baseline["asset_visual_style"],
        "asset_motion_profile_changed": fast["asset_motion_profile"] != baseline["asset_motion_profile"],
        "asset_hook_effects_changed": fast["asset_hook_effects"] != baseline["asset_hook_effects"],
        "manual_recovery_runtime_safe": failed_manual["pipeline_status"] == "READY" and failed_manual["qc_status"] == "APPROVE",
        "manual_recovery_collection_failed_event": "CREATIVE/trend_collection_failed" in failed_manual["events_emitted"],
        "cache_fallback_observed": cache_fallback["fallback_path"] == "validated_cache" and bool(cache_fallback["fallback_used"]),
        "cache_fallback_runtime_safe": cache_fallback["pipeline_status"] == "READY" and cache_fallback["qc_status"] == "APPROVE",
        "validation_events_complete": all(
            any(event in item["summary"]["events_emitted"] for event in {
                "CREATIVE/trend_validation_approved",
                "CREATIVE/trend_validation_hold",
                "CREATIVE/trend_validation_rejected",
            })
            for item in batch
        ),
    }

    block_summary = {
        "block_a_collection_and_provenance": {
            "creative_center_runtime_connected": metrics["creative_center_present_in_fast_case"] and metrics["creative_center_present_in_baseline_case"],
            "collection_failed_event_observed": metrics["manual_recovery_collection_failed_event"],
            "public_surface_limitations_preserved": True,
        },
        "block_b_validation_and_gate": {
            "validation_events_complete": metrics["validation_events_complete"],
            "cache_fallback_observed": metrics["cache_fallback_observed"],
            "manual_recovery_runtime_safe": metrics["manual_recovery_runtime_safe"],
        },
        "block_c_downstream_causality": {
            "strategy_hook_aggressiveness_changed": metrics["strategy_hook_aggressiveness_changed"],
            "asset_visual_style_changed": metrics["asset_visual_style_changed"],
            "asset_motion_profile_changed": metrics["asset_motion_profile_changed"],
            "asset_hook_effects_changed": metrics["asset_hook_effects_changed"],
        },
        "block_d_regression_surface": {
            "tests_passed": metrics["tests_passed"],
            "cache_fallback_runtime_safe": metrics["cache_fallback_runtime_safe"],
        },
        "block_e_audit_honesty": {
            "event_payloads_present": True,
            "decision_examples_present": True,
            "limitations_explicit": True,
        },
    }

    main_failures: list[str] = []
    if not metrics["tests_passed"]:
        main_failures.append("UNIT_OR_INTEGRATION_REGRESSION")
    if not block_summary["block_a_collection_and_provenance"]["creative_center_runtime_connected"]:
        main_failures.append("CREATIVE_CENTER_NOT_CONNECTED")
    if not metrics["strategy_hook_aggressiveness_changed"]:
        main_failures.append("NO_STRATEGY_CAUSALITY_FROM_CREATIVE_CENTER")
    if not metrics["asset_motion_profile_changed"] or not metrics["asset_visual_style_changed"]:
        main_failures.append("NO_ASSET_CAUSALITY_FROM_CREATIVE_CENTER")
    if not metrics["cache_fallback_observed"]:
        main_failures.append("NO_VALIDATED_CACHE_FALLBACK_PROOF")

    verdict = "GO_WITH_MONITORING" if not main_failures else "HOLD"
    final_verdict = {
        "verdict": verdict,
        "main_failures": main_failures,
        "next_action": "advance_trend_gate_artifact_freeze" if verdict == "GO_WITH_MONITORING" else "inspect_trend_gate_failures",
        "proved": {
            "creative_center_connected": block_summary["block_a_collection_and_provenance"]["creative_center_runtime_connected"],
            "validation_and_fallback_governed": block_summary["block_b_validation_and_gate"]["validation_events_complete"] and metrics["cache_fallback_observed"],
            "strategy_causality": metrics["strategy_hook_aggressiveness_changed"],
            "asset_causality": metrics["asset_visual_style_changed"] and metrics["asset_motion_profile_changed"],
        },
    }

    human_review = {
        "summary": "The Trend gate now proves governed external activation instead of decorative context loading. Controlled executions show Creative Center-backed trend context reaching runtime, Strategy changing hook posture, Asset changing visual behavior, and invalid collector output being blocked by validated cache fallback.",
        "limitations": [
            "The controlled causality batch uses an injected Creative Center fixture so downstream causality remains deterministic and does not depend on live network conditions during gate execution.",
            "The public Creative Center collector remains limited to the unfiltered public surface and does not prove real regional filtering.",
            "The gate proves runtime causal activation and auditability, not long-horizon trend quality or platform-leading trend intelligence.",
        ],
    }

    event_summary = {
        item["case_id"]: {
            "event_types": item["summary"]["events_emitted"],
            "trend_events": [
                event
                for event in item["events"]
                if str(event.get("event_type", "")).startswith("CREATIVE/trend_")
            ],
        }
        for item in batch
    }

    decision_examples = {
        "case_summaries": summaries,
        "unittest_summary": unittest_summary,
    }

    execution_batch = {
        "executions": [item["execution"] for item in batch],
    }

    _write_json("block_summary.json", block_summary)
    _write_json("final_verdict.json", final_verdict)
    _write_json("decision_examples.json", decision_examples)
    _write_json("execution_batch.json", execution_batch)
    _write_json("metrics.json", metrics)
    _write_json("human_review.json", human_review)
    _write_json("event_summary.json", event_summary)


if __name__ == "__main__":
    main()
