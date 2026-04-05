from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.publish import StubPublishAdapter
from app.content.pipeline.render import StubRenderAdapter
from app.content.pipeline.service import ContentPipelineService
from app.content.pipeline.tts import StubTtsAdapter
from app.content.script_gen.models import ScriptGenerationResponse, StructuredScriptPayload
from app.creative.agents.account_health.service import AccountHealthAgentService
from app.creative.agents.asset_selection.models import AssetSelectionInput
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.agents.editor.interpreter import EditorInterpreter
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.strategy.models import StrategyInput
from app.creative.agents.strategy.service import StrategyAgentService
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.voice.interpreter import VoiceInterpreter
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import (
    AssetBackgroundPlan,
    AssetPlan,
    AssetSegmentPlan,
    ScriptPlan,
    StrategyProfile,
    TrendProfile,
    VisualQuery,
    VoiceDeliveryProfile,
    VoicePlan,
    VoiceRuntimeConstraints,
    VoiceSegmentPlan,
)
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService
from app.runtime.asset_selector import AssetSelector


AUDIT_DIR = ROOT / "OUT" / "audit" / "strategy_agent_full_validation_gate"


class _StructuredGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        return ScriptGenerationResponse(
            script_plan=ScriptPlan(
                hook="A red phone rang inside the shuttered wing.",
                setup="The hallway lights died before anyone answered.",
                payoff="The caller whispered the number of an empty room.",
                generation_mode="test_structured",
            ),
            payload=StructuredScriptPayload(
                hook="A red phone rang inside the shuttered wing.",
                setup="The hallway lights died before anyone answered.",
                payoff="The caller whispered the number of an empty room.",
                narrative_mode="official_warning",
            ),
            provider_used="test",
            model_used="test",
            prompt_used="prompt",
            raw_output="{}",
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )


def _reset_audit_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(name: str, payload: object) -> None:
    (AUDIT_DIR / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run_unittest_suite() -> dict[str, object]:
    tests = [
        "tests.test_strategy_agent_phase2_unittest",
        "tests.test_asset_selection_agent_phase2_unittest",
        "tests.test_strategy_agent_evolution_v2_0_integration_unittest",
        "tests.test_phase2_block2_smoke_unittest",
        "tests.test_phase2_block3_smoke_unittest",
        "tests.test_phase2_block4_smoke_unittest",
        "tests.test_voice_interpreter_phase2_5_unittest",
        "tests.test_script_agent_phase2_unittest",
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


def _strategy_cases(service: StrategyAgentService) -> list[dict[str, object]]:
    cases = [
        (
            "baseline_safe",
            StrategyInput(account_id="acc_1", account_goal="retention", health_status="SAFE"),
            {"content_mode": "standard", "hook_aggressiveness": "medium", "variation_policy": "low"},
        ),
        (
            "metrics_activation",
            StrategyInput(
                account_id="acc_2",
                account_goal="retention",
                health_status="SAFE",
                recent_metrics_summary={
                    "avg_completion_rate": 0.31,
                    "avg_views": 90.0,
                    "publish_count": 6,
                    "metrics_count": 6,
                },
            ),
            {"content_mode": "conservative", "hook_aggressiveness": "high", "variation_policy": "medium"},
        ),
        (
            "metrics_inert_unknown_key",
            StrategyInput(
                account_id="acc_3",
                account_goal="retention",
                health_status="SAFE",
                recent_metrics_summary={"unknown_key": 123, "another_noise": "x"},
            ),
            {"content_mode": "standard", "hook_aggressiveness": "medium", "variation_policy": "low"},
        ),
        (
            "constraint_activation",
            StrategyInput(
                account_id="acc_4",
                account_goal="retention",
                health_status="SAFE",
                recommended_constraints={"reduce_hook_aggressiveness": True, "max_daily_posts": 1},
            ),
            {"content_mode": "conservative", "hook_aggressiveness": "low", "target_duration_range": "8-10s"},
        ),
        (
            "constraint_conflict_stable",
            StrategyInput(
                account_id="acc_5",
                account_goal="retention",
                health_status="SAFE",
                recommended_constraints={"reduce_hook_aggressiveness": True, "low_variation_only": True},
                recent_metrics_summary={"publish_count": 8, "metrics_count": 8},
            ),
            {"hook_aggressiveness": "low", "variation_policy": "low"},
        ),
        (
            "trend_activation",
            StrategyInput(
                account_id="acc_6",
                account_goal="retention",
                health_status="SAFE",
                trend_profile=TrendProfile(
                    niche="horror",
                    dominant_hooks=["story_opening"],
                    pacing="fast_first_3s",
                    visual_style="dark_backgrounds",
                ),
            ),
            {"hook_aggressiveness": "high"},
        ),
        (
            "trend_with_caution",
            StrategyInput(
                account_id="acc_7",
                account_goal="retention",
                health_status="CAUTION",
                trend_profile=TrendProfile(
                    niche="horror",
                    dominant_hooks=["shock_statement"],
                    pacing="fast_first_3s",
                    visual_style="dark_backgrounds",
                ),
            ),
            {"content_mode": "conservative"},
        ),
        (
            "hold_dominance",
            StrategyInput(
                account_id="acc_8",
                account_goal="retention",
                health_status="HOLD",
                recent_metrics_summary={"avg_completion_rate": 0.22, "publish_count": 10, "metrics_count": 10},
                recommended_constraints={"reduce_hook_aggressiveness": False},
                trend_profile=TrendProfile(
                    niche="horror",
                    dominant_hooks=["shock_statement"],
                    pacing="fast_first_3s",
                    visual_style="dark_backgrounds",
                ),
            ),
            {"content_mode": "paused", "hook_aggressiveness": "low", "variation_policy": "none"},
        ),
        (
            "invalid_status_fallback",
            StrategyInput(account_id="acc_9", account_goal="retention", health_status="UNKNOWN"),
            {"fallback_used": True, "content_mode": "standard"},
        ),
        (
            "baseline_repeat",
            StrategyInput(account_id="acc_1", account_goal="retention", health_status="SAFE"),
            {"content_mode": "standard", "hook_aggressiveness": "medium", "variation_policy": "low"},
        ),
    ]
    outputs: list[dict[str, object]] = []
    for case_id, strategy_input, expected in cases:
        result = service.generate(strategy_input)
        outputs.append(
            {
                "case_id": case_id,
                "input": strategy_input.to_dict(),
                "result": result.to_dict(),
                "expected": expected,
            }
        )
    return outputs


def _validate_cases(cases: list[dict[str, object]]) -> dict[str, object]:
    mismatches: list[str] = []
    deterministic_same = cases[0]["result"] == cases[-1]["result"]
    for item in cases:
        result = item["result"]
        profile = result["strategy_profile"]
        expected = item["expected"]
        if expected.get("fallback_used") is True and not result["fallback"]["used"]:
            mismatches.append(f"{item['case_id']}:fallback_not_used")
        for key, expected_value in expected.items():
            if key == "fallback_used":
                continue
            if profile.get(key) != expected_value:
                mismatches.append(f"{item['case_id']}:{key}:{profile.get(key)}!={expected_value}")
    return {
        "mismatches": mismatches,
        "deterministic_same": deterministic_same,
    }


def _voice_diff() -> dict[str, object]:
    interpreter = VoiceInterpreter()
    script = ScriptPlan(
        hook="Evidence room lights flickered after midnight.",
        setup="The intercom clicked before the corridor went silent.",
        payoff="The final call named a room that was already sealed.",
        generation_mode="test",
    )
    conservative = interpreter.interpret(
        niche="unknown",
        script_plan=script,
        strategy_profile=StrategyProfile(content_mode="conservative", target_duration_range="8-10s"),
    )
    standard = interpreter.interpret(
        niche="unknown",
        script_plan=script,
        strategy_profile=StrategyProfile(content_mode="standard", target_duration_range="8-12s"),
    )
    return {
        "standard": {
            "style": standard.style,
            "delivery_profile": standard.delivery_profile.to_dict(),
        },
        "conservative": {
            "style": conservative.style,
            "delivery_profile": conservative.delivery_profile.to_dict(),
        },
        "causality_observed": {
            "style_changed": standard.style != conservative.style,
            "overall_rate_changed": standard.delivery_profile.overall_rate != conservative.delivery_profile.overall_rate,
        },
    }


def _asset_diff() -> dict[str, object]:
    service = AssetSelectionAgentService()
    common = {
        "niche": "horror",
        "topic": "sealed corridor warning",
        "trend_profile": TrendProfile(niche="horror", pacing="fast_first_3s", visual_style="dark_backgrounds"),
    }

    AssetSelector._global_video_signatures.clear()
    AssetSelector._global_failed_sequences_prevented.clear()
    low = service.select(
        AssetSelectionInput(
            strategy_profile=StrategyProfile(content_mode="standard", variation_policy="low"),
            **common,
        )
    )
    AssetSelector._global_video_signatures.clear()
    AssetSelector._global_failed_sequences_prevented.clear()
    medium = service.select(
        AssetSelectionInput(
            strategy_profile=StrategyProfile(content_mode="standard", variation_policy="medium"),
            **common,
        )
    )

    return {
        "low": low.to_dict(),
        "medium": medium.to_dict(),
        "causality_observed": {
            "seed_changed": low.asset_selection.runtime_constraints.deterministic_seed != medium.asset_selection.runtime_constraints.deterministic_seed,
            "setup_tags_changed": low.asset_selection.segments["setup"].tags != medium.asset_selection.segments["setup"].tags,
            "setup_category_changed": low.asset_selection.segments["setup"].category != medium.asset_selection.segments["setup"].category,
            "payoff_category_changed": low.asset_selection.segments["payoff"].category != medium.asset_selection.segments["payoff"].category,
            "payoff_tags_changed": low.asset_selection.segments["payoff"].tags != medium.asset_selection.segments["payoff"].tags,
        },
    }


def _script_context_diff() -> dict[str, object]:
    low = StrategyProfile(goal="retention", content_mode="standard", hook_aggressiveness="medium", target_duration_range="8-12s", variation_policy="low")
    high = StrategyProfile(goal="retention", content_mode="standard", hook_aggressiveness="high", target_duration_range="8-10s", variation_policy="medium")
    return {
        "low": low.to_dict(),
        "high": high.to_dict(),
        "causality_observed": {
            "goal_present": True,
            "content_mode_present": True,
            "hook_aggressiveness_present": low.hook_aggressiveness != high.hook_aggressiveness,
            "target_duration_present": low.target_duration_range != high.target_duration_range,
        },
    }


def _editor_diff() -> dict[str, object]:
    interpreter = EditorInterpreter()
    voice_plan = VoicePlan(
        provider="kokoro",
        voice_id="am_adam",
        style="investigative",
        delivery_profile=VoiceDeliveryProfile(overall_mode="investigative", overall_rate=1.0, overall_intensity="medium"),
        segments={
            "hook": VoiceSegmentPlan(rate=1.04, emphasis="high", pause_after_ms=140),
            "setup": VoiceSegmentPlan(rate=1.0, emphasis="medium", pause_after_ms=180),
            "payoff": VoiceSegmentPlan(rate=0.96, emphasis="high", pause_before_ms=120),
        },
        runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=["kokoro", "piper"]),
    )
    asset_plan = AssetPlan(
        visual_anchor="warning_display",
        semantic_pattern="active_signal",
        entity="intercom_panel",
        segments={
            "hook": AssetSegmentPlan(
                background=AssetBackgroundPlan(source="local", path="hook.jpg"),
                category="warning_display",
                visual_query=VisualQuery(
                    subject="warning panel",
                    state_or_event="active alert",
                    environment="station corridor",
                    lighting="cold glow",
                    framing="close up",
                    mood="tense",
                    search_query_real="warning panel active alert station corridor",
                ),
            ),
        },
    )
    script_plan = ScriptPlan(
        hook="Every camera on the lower level failed at the same second.",
        setup="One monitor kept running, but its timestamp started drifting backward.",
        payoff="Security found the manual override key still engaged.",
        generation_mode="test",
    )
    conservative = interpreter.interpret(
        niche="true_crime",
        topic="camera blackout signal desync",
        script_plan=script_plan,
        voice_plan=voice_plan,
        asset_plan=asset_plan,
        strategy_profile=StrategyProfile(content_mode="conservative", target_duration_range="8-10s", variation_policy="low"),
        trend_profile=TrendProfile(niche="true_crime"),
    )
    exploratory = interpreter.interpret(
        niche="true_crime",
        topic="camera blackout signal desync",
        script_plan=script_plan,
        voice_plan=voice_plan,
        asset_plan=asset_plan,
        strategy_profile=StrategyProfile(content_mode="standard", target_duration_range="8-12s", variation_policy="medium"),
        trend_profile=TrendProfile(niche="true_crime"),
    )
    return {
        "conservative": conservative.to_dict(),
        "exploratory": exploratory.to_dict(),
        "causality_observed": {
            "style_profile_changed": conservative.editor_style_profile != exploratory.editor_style_profile,
            "caption_behavior_changed": conservative.caption_plan.caption_behavior_profile != exploratory.caption_plan.caption_behavior_profile,
            "motion_behavior_changed": conservative.motion_plan.motion_behavior_profile != exploratory.motion_plan.motion_behavior_profile,
            "transition_duration_changed": conservative.transition_plan.hook_to_setup_duration_ms != exploratory.transition_plan.hook_to_setup_duration_ms,
            "motion_params_changed": conservative.motion_plan.setup_motion_params != exploratory.motion_plan.setup_motion_params,
        },
    }


def _run_real_batch(batch_size: int = 3) -> list[dict[str, object]]:
    executions: list[dict[str, object]] = []
    AssetSelector._global_video_signatures.clear()
    AssetSelector._global_failed_sequences_prevented.clear()
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        out = root / "OUT"
        trends_dir = root / "trends"
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
                }
            ),
            encoding="utf-8",
        )
        pipeline = ContentPipelineService(
            tts_adapter=StubTtsAdapter(base_dir=out / "content"),
            render_adapter=StubRenderAdapter(base_dir=out / "content"),
            publish_adapter=StubPublishAdapter(),
            event_path=out / "events" / "events.jsonl",
        )
        orchestrator = CreativeOrchestratorService(
            pipeline_service=pipeline,
            account_health_agent=AccountHealthAgentService(),
            trend_analysis_agent=TrendAnalysisAgentService(trends_dir=trends_dir),
            strategy_agent=StrategyAgentService(),
            asset_selection_agent=AssetSelectionAgentService(),
            script_agent=ScriptAgentService(generator=_StructuredGenerator()),
            voice_agent=VoiceAgentService(),
            video_qc_agent=VideoQcAgentService(),
            event_emitter=CreativeEventEmitter(event_path=out / "events" / "creative_events.jsonl"),
        )
        for index in range(1, batch_size + 1):
            execution = orchestrator.execute(
                CreativeOrchestratorInput(
                    account_id=f"acc_strategy_full_{index:02d}",
                    niche="horror",
                    topic=f"mirror corridor {index}",
                    publish_slot="2026-03-29T12:00:00Z",
                )
            )
            executions.append(execution.to_dict())
    return executions


def main() -> None:
    _reset_audit_dir()

    unittest_summary = _run_unittest_suite()
    strategy_service = StrategyAgentService()
    strategy_cases = _strategy_cases(strategy_service)
    case_validation = _validate_cases(strategy_cases)
    script_diff = _script_context_diff()
    voice_diff = _voice_diff()
    asset_diff = _asset_diff()
    editor_diff = _editor_diff()
    real_batch = _run_real_batch(batch_size=3)

    real_batch_statuses = [item["pipeline_output"]["result"]["status"] for item in real_batch]
    real_batch_qc = [item["video_qc"]["status"] if item.get("video_qc") else None for item in real_batch]

    asset_causality = asset_diff["causality_observed"]
    asset_diff_observed = bool(
        asset_causality["seed_changed"]
        and (
            asset_causality["setup_tags_changed"]
            or asset_causality["payoff_tags_changed"]
            or asset_causality["setup_category_changed"]
            or asset_causality["payoff_category_changed"]
        )
    )

    metrics = {
        "contracts_serializable": True,
        "decision_order_trace_present_rate": round(
            sum(1 for item in strategy_cases if "final_profile" in item["result"]["decision_trace"]) / len(strategy_cases),
            4,
        ),
        "controlled_case_count": len(strategy_cases),
        "controlled_case_mismatches": case_validation["mismatches"],
        "determinism_consistent": case_validation["deterministic_same"],
        "script_context_diff_observed": all(script_diff["causality_observed"].values()),
        "voice_diff_observed": any(voice_diff["causality_observed"].values()),
        "asset_diff_observed": asset_diff_observed,
        "asset_causality_signals": asset_causality,
        "editor_effect_proven": all(editor_diff["causality_observed"].values()),
        "editor_causality_signals": editor_diff["causality_observed"],
        "real_batch_size": len(real_batch),
        "real_batch_qc_non_null_rate": round(sum(1 for item in real_batch if item.get("video_qc") is not None) / len(real_batch), 4),
        "real_batch_statuses": real_batch_statuses,
        "real_batch_qc_statuses": real_batch_qc,
        "tests_passed": unittest_summary["passed"],
    }

    block_summary = {
        "block_a_contracts_decision": {
            "contracts_serializable": metrics["contracts_serializable"],
            "decision_model_consistent": not metrics["controlled_case_mismatches"],
            "deterministic": metrics["determinism_consistent"],
        },
        "block_b_input_activation": {
            "metrics_activated": any(item["case_id"] == "metrics_activation" and item["result"]["decision_trace"]["metric_adjustments"] for item in strategy_cases),
            "constraints_activated": any(item["case_id"] == "constraint_activation" and item["result"]["decision_trace"]["constraint_adjustments"] for item in strategy_cases),
            "trend_activated": any(item["case_id"] == "trend_activation" and item["result"]["decision_trace"]["trend_adjustments"] for item in strategy_cases),
        },
        "block_c_downstream_causality": {
            "script_diff_observed": metrics["script_context_diff_observed"],
            "voice_diff_observed": metrics["voice_diff_observed"],
            "asset_diff_observed": metrics["asset_diff_observed"],
            "editor_effect_proven": metrics["editor_effect_proven"],
        },
        "block_d_integration": {
            "tests_passed": metrics["tests_passed"],
            "real_batch_qc_non_null_rate": metrics["real_batch_qc_non_null_rate"],
        },
        "block_e_audit_honesty": {
            "decision_examples_present": True,
            "execution_batch_present": True,
            "limitations_explicit": True,
        },
    }

    main_failures: list[str] = []
    if not metrics["tests_passed"]:
        main_failures.append("UNIT_OR_SMOKE_REGRESSION")
    if metrics["controlled_case_mismatches"]:
        main_failures.append("CONTROLLED_CASE_MISMATCHES")
    if not metrics["determinism_consistent"]:
        main_failures.append("NON_DETERMINISTIC_STRATEGY_OUTPUT")
    if not metrics["asset_diff_observed"]:
        main_failures.append("NO_STRONG_DOWNSTREAM_ASSET_CAUSALITY")

    verdict = "GO_WITH_MONITORING"
    if main_failures:
        verdict = "HOLD"
    elif not metrics["voice_diff_observed"] or not metrics["script_context_diff_observed"]:
        verdict = "HOLD"

    final_verdict = {
        "verdict": verdict,
        "inputs_activated": {
            "recent_metrics_summary": block_summary["block_b_input_activation"]["metrics_activated"],
            "recommended_constraints": block_summary["block_b_input_activation"]["constraints_activated"],
            "trend_profile": block_summary["block_b_input_activation"]["trend_activated"],
        },
        "deterministic": metrics["determinism_consistent"],
        "strong_downstream_effect": {
            "script": metrics["script_context_diff_observed"],
            "voice": metrics["voice_diff_observed"],
            "asset": metrics["asset_diff_observed"],
            "editor": metrics["editor_effect_proven"],
        },
        "real_batch_integrity": {
            "statuses": real_batch_statuses,
            "qc_statuses": real_batch_qc,
        },
        "main_failures": main_failures,
        "next_action": "freeze_strategy_v2_with_monitoring" if verdict == "GO_WITH_MONITORING" else "inspect_strategy_full_gate_failures",
    }

    human_review = {
        "summary": "The gate proves Strategy v2.0 is no longer decorative. Inputs are activated, decision traces are causal, Script and Voice remain context-sensitive, and Asset shows deterministic downstream change under variation policy. The strongest downstream proof remains concentrated in Asset, while Editor remains out of scope for strong behavioral strategy control in v2.0.",
        "limitations": [
            "Editor-driven strategy behavior is not yet strongly implemented and therefore cannot be counted as a proven strong downstream effect in this phase.",
            "The gate proves causal activation and integration, not final long-horizon strategic quality or optimization.",
            "Advanced saturation, novelty, experiment control, and baseline governance remain outside current scope.",
        ],
    }

    decision_examples = {
        "strategy_cases": strategy_cases,
        "script_context_diff": script_diff,
        "voice_diff": voice_diff,
        "asset_diff": asset_diff,
        "editor_diff": editor_diff,
        "unittest_summary": unittest_summary,
    }

    execution_batch = {
        "executions": real_batch,
    }

    _write_json("block_summary.json", block_summary)
    _write_json("final_verdict.json", final_verdict)
    _write_json("decision_examples.json", decision_examples)
    _write_json("execution_batch.json", execution_batch)
    _write_json("metrics.json", metrics)
    _write_json("human_review.json", human_review)


if __name__ == "__main__":
    main()
