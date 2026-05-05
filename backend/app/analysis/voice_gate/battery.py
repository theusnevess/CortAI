from __future__ import annotations

import json
import os
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

from app.analysis.voice_gate.metrics import (
    delivery_variance_score,
    duration_per_word,
    monotony_proxy_score,
    pause_distribution_from_voice_plan,
    segment_contrast_score,
)
from app.content.backgrounds.service import BackgroundGeneratorService
from app.content.pipeline.service import ContentPipelineService
from app.content.pipeline.tts import StubTtsAdapter
from app.content.pipeline.tts_router import TtsRouter
from app.creative.agents.account_health.service import AccountHealthAgentService
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.agents.learning.service import LearningAgentService
from app.creative.agents.script.models import ScriptAgentInput
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.strategy.service import StrategyAgentService
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.contracts.creative_pack import (
    ExperimentPlan,
    LearningInsights,
    StrategyProfile,
    TrendProfile,
    VoiceRuntimeConstraints,
)
from app.creative.experiments.service import ExperimentCapabilityService
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput


VOICE_BATTERY_CASES: list[dict[str, str]] = [
    {"category": "horror", "niche": "horror", "topic": "sealed evidence room whisper"},
    {"category": "horror", "niche": "horror", "topic": "autopsy room camera desync"},
    {"category": "horror", "niche": "horror", "topic": "midnight chapel ledger"},
    {"category": "horror", "niche": "horror", "topic": "rail tunnel warning"},
    {"category": "horror", "niche": "horror", "topic": "voice behind the fire exit"},
    {"category": "true_crime", "niche": "true_crime", "topic": "dispatcher tape reopened"},
    {"category": "true_crime", "niche": "true_crime", "topic": "sealed locker recorder"},
    {"category": "true_crime", "niche": "true_crime", "topic": "janitor witness statement"},
    {"category": "true_crime", "niche": "true_crime", "topic": "station intercom warning"},
    {"category": "true_crime", "niche": "true_crime", "topic": "missing witness transcript"},
    {"category": "investigative", "niche": "true_crime", "topic": "archive override on server 9"},
    {"category": "investigative", "niche": "true_crime", "topic": "contradictory evidence tape"},
    {"category": "investigative", "niche": "true_crime", "topic": "security log erased a minute"},
    {"category": "investigative", "niche": "true_crime", "topic": "sealed call transcript discrepancy"},
    {"category": "investigative", "niche": "true_crime", "topic": "camera blackout in sector 4"},
    {"category": "curiosity", "niche": "facts", "topic": "museum audio anomaly"},
    {"category": "curiosity", "niche": "facts", "topic": "archive page changed date"},
    {"category": "curiosity", "niche": "facts", "topic": "bunker map missing corridor"},
    {"category": "curiosity", "niche": "facts", "topic": "research log contradiction"},
    {"category": "curiosity", "niche": "facts", "topic": "urban legend tied to census record"},
    {"category": "dark_storytelling", "niche": "horror", "topic": "abandoned platform timetable"},
    {"category": "dark_storytelling", "niche": "horror", "topic": "elevator that reopened itself"},
    {"category": "dark_storytelling", "niche": "horror", "topic": "corridor blueprint from 1975"},
    {"category": "dark_storytelling", "niche": "horror", "topic": "night watch log with future date"},
    {"category": "dark_storytelling", "niche": "horror", "topic": "hospital wing sealed after 3 AM"},
]


VIDEO_BATCH_CASES: list[tuple[str, str, str]] = [
    ("acc_1", "horror", "sealed evidence room whisper"),
    ("acc_2", "true_crime", "dispatcher tape reopened"),
    ("acc_3", "facts", "archive page changed date"),
    ("acc_4", "horror", "hospital wing sealed after 3 AM"),
    ("acc_5", "true_crime", "missing witness transcript"),
]


def run_voice_battery(*, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    router = TtsRouter(tts_adapter=StubTtsAdapter(base_dir=output_dir / "voice_battery_workspace"))
    script_agent = ScriptAgentService()
    voice_agent = VoiceAgentService()
    rows: list[dict[str, Any]] = []

    for index, case in enumerate(VOICE_BATTERY_CASES, start=1):
        script_result = script_agent.generate(
            ScriptAgentInput(
                account_id=f"acc_{index:02d}",
                niche=case["niche"],
                topic=case["topic"],
                strategy_profile=StrategyProfile(),
                trend_profile=TrendProfile(niche=case["niche"], dominant_hooks=["question"], pacing="fast_first_3s"),
                learning_insights=LearningInsights(recommendations=["favor contrastive delivery"]),
                experiment_plan=ExperimentPlan(
                    experiment_id="voice_gate",
                    variant_id="A",
                    variant_type="voice_delivery",
                    variant_params={},
                    fallback_used=False,
                ),
            )
        )
        voice_result = voice_agent.resolve(
            account_id=f"acc_{index:02d}",
            niche=case["niche"],
            script_plan=script_result.script_plan,
            strategy_profile=StrategyProfile(),
        )
        started = time.perf_counter()
        router_result = router.generate_audio(
            script_text=script_result.script_plan.narration_text(),
            voice_plan=voice_result.voice_plan,
            language="en",
            render_job_id=f"voice_gate_{index:02d}",
            attempt_count=1,
        )
        elapsed = round(time.perf_counter() - started, 3)
        pauses = pause_distribution_from_voice_plan(voice_result.voice_plan)
        row = {
            "case_id": f"case_{index:02d}",
            "category": case["category"],
            "niche": case["niche"],
            "topic": case["topic"],
            "script_plan": script_result.script_plan.to_dict(),
            "voice_plan": voice_result.voice_plan.to_dict(),
            "provider_requested": router_result.trace.provider_requested,
            "provider_executed": router_result.trace.provider_executed,
            "fallback_used": router_result.trace.fallback_used,
            "fallback_reason": router_result.trace.fallback_reason,
            "tts_latency_seconds": router_result.trace.latency_s or elapsed,
            "audio_duration_seconds": router_result.trace.audio_duration_s,
            "hook_duration": _segment_value(router_result.trace.segment_durations, 0),
            "setup_duration": _segment_value(router_result.trace.segment_durations, 1),
            "payoff_duration": _segment_value(router_result.trace.segment_durations, 2),
            "pause_after_hook": pauses["pause_after_hook"],
            "pause_after_setup": pauses["pause_after_setup"],
            "pause_before_payoff": pauses["pause_before_payoff"],
        }
        row["duration_per_word"] = duration_per_word(
            text=script_result.script_plan.narration_text(),
            duration_s=row["audio_duration_seconds"],
        )
        row["segment_duration_variation"] = _segment_duration_variation(router_result.trace.segment_durations)
        row["pause_distribution"] = pauses
        row["segment_contrast_score"] = segment_contrast_score(voice_result.voice_plan)
        row["monotony_proxy_score"] = monotony_proxy_score(
            voice_plan=voice_result.voice_plan,
            segment_durations=list(router_result.trace.segment_durations),
        )
        rows.append(row)

    fallback_case = _run_forced_fallback_case(router=router, voice_agent=voice_agent, script_agent=script_agent)
    return {
        "rows": rows,
        "fallback_cases": [fallback_case],
        "delivery_variance_score": delivery_variance_score(rows),
    }


def run_video_batch(*, output_dir: Path) -> dict[str, Any]:
    workspace = output_dir / "video_batch_workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    _seed_workspace(workspace)
    pipeline = ContentPipelineService(event_path=workspace / "events" / "events.jsonl")
    orchestrator = CreativeOrchestratorService(
        pipeline_service=pipeline,
        account_health_agent=AccountHealthAgentService(),
        trend_analysis_agent=TrendAnalysisAgentService(trends_dir=workspace / "trends"),
        learning_agent=LearningAgentService(
            default_publish_records_path=workspace / "data" / "publish_records.jsonl",
            default_video_metrics_path=workspace / "metrics" / "video_metrics.jsonl",
            default_analysis_dir=workspace / "analysis",
            default_output_path=workspace / "learning" / "learning_insights.json",
        ),
        strategy_agent=StrategyAgentService(),
        experiment_capability=ExperimentCapabilityService(
            default_config_path=workspace / "experiments" / "experiment_config.json",
            default_output_path=workspace / "experiments" / "experiment_plan.json",
            default_experiments_path=workspace / "experiments" / "experiments.jsonl",
            default_assignments_path=workspace / "experiments" / "assignments.jsonl",
            default_results_path=workspace / "experiments" / "results.jsonl",
        ),
        asset_selection_agent=AssetSelectionAgentService(
            background_service=BackgroundGeneratorService(local_assets_dir=(Path.cwd() / "assets" / "backgrounds").resolve())
        ),
        script_agent=ScriptAgentService(),
        voice_agent=VoiceAgentService(),
        video_qc_agent=VideoQcAgentService(),
        event_emitter=CreativeEventEmitter(event_path=workspace / "events" / "creative_events.jsonl"),
    )

    rows: list[dict[str, Any]] = []
    for index, (account_id, niche, topic) in enumerate(VIDEO_BATCH_CASES, start=1):
        started = time.perf_counter()
        execution = orchestrator.execute(
            CreativeOrchestratorInput(
                account_id=account_id,
                niche=niche,
                topic=topic,
                publish_slot=f"2026-03-18T1{index}:00:00Z",
            )
        )
        elapsed = round(time.perf_counter() - started, 3)
        tts_trace = execution.pipeline_output["result"].get("tts_trace", {})
        rows.append(
            {
                "account_id": account_id,
                "niche": niche,
                "topic": topic,
                "pipeline_status": execution.pipeline_output["result"]["status"],
                "video_qc_status": execution.video_qc.status if execution.video_qc else None,
                "provider_requested": tts_trace.get("provider_requested", ""),
                "provider_executed": tts_trace.get("provider_executed", ""),
                "fallback_used": tts_trace.get("fallback_used", False),
                "fallback_reason": tts_trace.get("fallback_reason", ""),
                "tts_latency_seconds": tts_trace.get("latency_s"),
                "audio_duration_seconds": tts_trace.get("audio_duration_s"),
                "script_generation_mode": execution.creative_pack.script_plan.generation_mode if execution.creative_pack else "",
                "voice_style": execution.creative_pack.voice_plan.style if execution.creative_pack else "",
                "hook": execution.creative_pack.script_plan.hook if execution.creative_pack else "",
                "payoff": execution.creative_pack.script_plan.payoff if execution.creative_pack else "",
                "pipeline_execution_time": elapsed,
            }
        )
    return {"rows": rows}


def _run_forced_fallback_case(*, router: TtsRouter, voice_agent: VoiceAgentService, script_agent: ScriptAgentService) -> dict[str, Any]:
    script_result = script_agent.generate(
        ScriptAgentInput(
            account_id="acc_fallback",
            niche="horror",
            topic="forced provider fallback case",
            strategy_profile=StrategyProfile(),
            trend_profile=TrendProfile(niche="horror"),
            learning_insights=LearningInsights(),
            experiment_plan=ExperimentPlan(experiment_id="voice_gate", variant_id="fallback", variant_type="voice_delivery"),
        )
    )
    voice_result = voice_agent.resolve(
        account_id="acc_fallback",
        niche="horror",
        script_plan=script_result.script_plan,
        strategy_profile=StrategyProfile(),
    )
    forced_plan = replace(
        voice_result.voice_plan,
        provider="elevenlabs",
        runtime_constraints=VoiceRuntimeConstraints(
            allow_provider_fallback=True,
            fallback_order=["elevenlabs", "piper"],
        ),
    )
    router_result = router.generate_audio(
        script_text=script_result.script_plan.narration_text(),
        voice_plan=forced_plan,
        language="en",
        render_job_id="voice_gate_fallback",
        attempt_count=1,
    )
    return {
        "provider_requested": router_result.trace.provider_requested,
        "provider_executed": router_result.trace.provider_executed,
        "fallback_used": router_result.trace.fallback_used,
        "fallback_reason": router_result.trace.fallback_reason,
    }


def _seed_workspace(workspace: Path) -> None:
    for path in (
        workspace / "trends",
        workspace / "data",
        workspace / "metrics",
        workspace / "analysis",
        workspace / "experiments",
        workspace / "learning",
        workspace / "events",
    ):
        path.mkdir(parents=True, exist_ok=True)
    (workspace / "trends" / "horror.json").write_text(
        json.dumps(
            {
                "niche": "horror",
                "dominant_hooks": ["question", "shock_statement"],
                "avg_duration": "35-60",
                "pacing": "fast_first_3s",
                "visual_style": "dark_backgrounds",
                "text_style": "large_caption_focus",
            },
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    (workspace / "trends" / "true_crime.json").write_text(
        json.dumps(
            {
                "niche": "true_crime",
                "dominant_hooks": ["story_opening", "shock_statement"],
                "avg_duration": "35-55",
                "pacing": "fast_first_3s",
                "visual_style": "investigation_dark",
                "text_style": "large_caption_focus",
            },
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    (workspace / "trends" / "facts.json").write_text(
        json.dumps(
            {
                "niche": "facts",
                "dominant_hooks": ["question", "story_opening"],
                "avg_duration": "30-45",
                "pacing": "fast_first_3s",
                "visual_style": "archive_dark",
                "text_style": "large_caption_focus",
            },
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    (workspace / "data" / "publish_records.jsonl").write_text(
        "\n".join(
            json.dumps({"account_id": f"acc_{idx}", "publish_id": f"pub_{idx:03d}", "niche": niche}, ensure_ascii=True)
            for idx, niche in enumerate(["horror", "true_crime", "facts", "horror", "true_crime"], start=1)
        ),
        encoding="utf-8",
    )
    (workspace / "metrics" / "video_metrics.jsonl").write_text(
        "\n".join(
            json.dumps(
                {
                    "account_id": f"acc_{idx}",
                    "views": 150 + idx * 40,
                    "completion_rate": 0.55 + idx * 0.03,
                    "duration_s": 9.0 + idx * 0.2,
                },
                ensure_ascii=True,
            )
            for idx in range(1, 6)
        ),
        encoding="utf-8",
    )
    (workspace / "analysis" / "hook_performance_summary.json").write_text(
        json.dumps({"hooks": [{"hook_style": "question"}, {"hook_style": "story_opening"}]}, ensure_ascii=True),
        encoding="utf-8",
    )
    (workspace / "experiments" / "experiment_config.json").write_text(
        json.dumps(
            {
                "name": "voice_agent_excellence",
                "scope": "CREATIVE_PACK",
                "variant_a": {"variant_type": "voice_delivery", "style": "baseline"},
                "variant_b": {"variant_type": "voice_delivery", "style": "contrastive"},
                "status": "ACTIVE",
            },
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )


def _segment_value(values: list[float], index: int) -> float:
    if index >= len(values):
        return 0.0
    return round(float(values[index]), 3)


def _segment_duration_variation(values: list[float]) -> float:
    from app.analysis.voice_gate.metrics import segment_duration_variation

    return segment_duration_variation(values)
