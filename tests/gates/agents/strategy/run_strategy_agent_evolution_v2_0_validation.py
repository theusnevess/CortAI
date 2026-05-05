from __future__ import annotations

import json
import shutil
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
from app.creative.agents.asset_selection.models import AssetSelectionInput
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.strategy.models import StrategyInput
from app.creative.agents.strategy.service import StrategyAgentService
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import ScriptPlan, StrategyProfile, TrendProfile
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService
from app.runtime.asset_selector import AssetSelector


AUDIT_DIR = ROOT / "OUT" / "audit" / "strategy_agent_evolution_v2_0_validation"


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


def _strategy_case_examples(service: StrategyAgentService) -> list[dict[str, object]]:
    examples: list[dict[str, object]] = []
    cases = [
        (
            "baseline_safe",
            StrategyInput(account_id="acc_1", account_goal="retention", health_status="SAFE"),
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
        ),
        (
            "constraint_activation",
            StrategyInput(
                account_id="acc_3",
                account_goal="retention",
                health_status="SAFE",
                recommended_constraints={"reduce_hook_aggressiveness": True, "max_daily_posts": 1},
            ),
        ),
        (
            "trend_activation",
            StrategyInput(
                account_id="acc_4",
                account_goal="retention",
                health_status="SAFE",
                trend_profile=TrendProfile(
                    niche="horror",
                    dominant_hooks=["story_opening"],
                    pacing="fast_first_3s",
                    visual_style="dark_backgrounds",
                ),
            ),
        ),
        (
            "hold_dominance",
            StrategyInput(
                account_id="acc_5",
                account_goal="retention",
                health_status="HOLD",
                recent_metrics_summary={"avg_completion_rate": 0.22, "publish_count": 10, "metrics_count": 10},
                trend_profile=TrendProfile(
                    niche="horror",
                    dominant_hooks=["shock_statement"],
                    pacing="fast_first_3s",
                    visual_style="dark_backgrounds",
                ),
            ),
        ),
    ]
    for case_id, qc_input in cases:
        result = service.generate(qc_input)
        examples.append(
            {
                "case_id": case_id,
                "input": qc_input.to_dict(),
                "result": result.to_dict(),
            }
        )
    return examples


def _asset_causality_examples(service: AssetSelectionAgentService) -> dict[str, object]:
    AssetSelector._global_video_signatures.clear()
    AssetSelector._global_failed_sequences_prevented.clear()
    common = {
        "niche": "horror",
        "topic": "sealed corridor warning",
        "trend_profile": TrendProfile(niche="horror", pacing="fast_first_3s", visual_style="dark_backgrounds"),
    }
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
            "payoff_category_changed": low.asset_selection.segments["payoff"].category != medium.asset_selection.segments["payoff"].category,
            "seed_changed": low.asset_selection.runtime_constraints.deterministic_seed != medium.asset_selection.runtime_constraints.deterministic_seed,
        },
    }


def _run_orchestrated_execution() -> dict[str, object]:
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
        execution = orchestrator.execute(
            CreativeOrchestratorInput(
                account_id="acc_strategy_v20_gate",
                niche="horror",
                topic="mirror corridor",
                publish_slot="2026-03-29T12:00:00Z",
            )
        )
        return execution.to_dict()


def main() -> None:
    _reset_audit_dir()
    strategy_service = StrategyAgentService()
    asset_service = AssetSelectionAgentService()

    strategy_examples = _strategy_case_examples(strategy_service)
    asset_examples = _asset_causality_examples(asset_service)
    execution = _run_orchestrated_execution()

    deterministic_input = StrategyInput(
        account_id="acc_det",
        account_goal="retention",
        health_status="SAFE",
        recent_metrics_summary={"avg_completion_rate": 0.31, "publish_count": 6, "metrics_count": 6},
        trend_profile=TrendProfile(niche="horror", dominant_hooks=["story_opening"], pacing="fast_first_3s", visual_style="dark_backgrounds"),
    )
    first = strategy_service.generate(deterministic_input).to_dict()
    second = strategy_service.generate(deterministic_input).to_dict()
    deterministic_consistency = first == second

    metrics_activation = next(item for item in strategy_examples if item["case_id"] == "metrics_activation")
    constraints_activation = next(item for item in strategy_examples if item["case_id"] == "constraint_activation")
    trend_activation = next(item for item in strategy_examples if item["case_id"] == "trend_activation")
    hold_case = next(item for item in strategy_examples if item["case_id"] == "hold_dominance")

    metrics = {
        "strategy_examples_count": len(strategy_examples),
        "metrics_activation_observed": metrics_activation["result"]["strategy_profile"]["hook_aggressiveness"] == "high"
        and metrics_activation["result"]["strategy_profile"]["variation_policy"] == "medium",
        "constraints_activation_observed": constraints_activation["result"]["strategy_profile"]["target_duration_range"] == "8-10s",
        "trend_activation_observed": trend_activation["result"]["strategy_profile"]["hook_aggressiveness"] == "high",
        "hold_dominance_observed": hold_case["result"]["strategy_profile"]["content_mode"] == "paused",
        "variation_policy_causality_observed": asset_examples["causality_observed"]["payoff_category_changed"]
        and asset_examples["causality_observed"]["seed_changed"],
        "deterministic_consistency": deterministic_consistency,
        "orchestrated_trend_passed_into_strategy": bool(
            execution.get("strategy", {}).get("decision_trace", {}).get("signals_seen", {}).get("trend_present")
        ),
    }

    block_summary = {
        "input_activation": {
            "metrics": metrics["metrics_activation_observed"],
            "constraints": metrics["constraints_activation_observed"],
            "trend": metrics["trend_activation_observed"],
        },
        "downstream_causality": {
            "variation_policy_asset_effect": metrics["variation_policy_causality_observed"],
        },
        "determinism": metrics["deterministic_consistency"],
        "orchestrator_integration": metrics["orchestrated_trend_passed_into_strategy"],
    }

    verdict = "GO" if all(bool(value) for value in metrics.values()) else "HOLD"
    final_verdict = {
        "verdict": verdict,
        "strategy_causal": bool(metrics["variation_policy_causality_observed"]),
        "inputs_activated": {
            "recent_metrics_summary": bool(metrics["metrics_activation_observed"]),
            "recommended_constraints": bool(metrics["constraints_activation_observed"]),
            "trend_profile": bool(metrics["trend_activation_observed"]),
        },
        "deterministic": bool(metrics["deterministic_consistency"]),
        "orchestrator_integration": bool(metrics["orchestrated_trend_passed_into_strategy"]),
        "main_failures": [],
        "next_action": "promote_strategy_v2_if_visual_validation_is_sufficient" if verdict == "GO" else "inspect_failed_activation_paths",
    }

    _write_json("decision_examples.json", {"strategy_examples": strategy_examples, "asset_examples": asset_examples})
    _write_json("execution_batch.json", {"executions": [execution]})
    _write_json("metrics.json", metrics)
    _write_json("block_summary.json", block_summary)
    _write_json("final_verdict.json", final_verdict)


if __name__ == "__main__":
    main()
