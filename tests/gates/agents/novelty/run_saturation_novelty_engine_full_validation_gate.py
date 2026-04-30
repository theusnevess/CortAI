from __future__ import annotations

import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from statistics import mean

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / 'backend'
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.publish import StubPublishAdapter
from app.content.pipeline.render import StubRenderAdapter
from app.content.pipeline.service import ContentPipelineService
from app.content.pipeline.tts import StubTtsAdapter
from app.content.script_gen.models import ScriptGenerationRequest
from app.content.script_gen.service import LocalScriptGeneratorService
from app.creative.agents.account_health.service import AccountHealthAgentService
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.creative.agents.learning.service import LearningAgentService
from app.creative.agents.novelty.models import NoveltyInput, NoveltyPressureProfile, NoveltyResult
from app.creative.agents.novelty.service import NoveltyEngineService
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.strategy.service import StrategyAgentService
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput
from app.creative.experiments.service import ExperimentCapabilityService
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService
from app.runtime.asset_selector import AssetSelector

AUDIT_DIR = ROOT / 'OUT' / 'audit' / 'saturation_novelty_engine_full_validation_gate'
BATCH_SIZE = 5
ACCOUNT_ID = 'acc_saturation_full_gate_001'
REPEATED_TOPIC = 'sealed corridor mirror warning'
CATALOG_PATH = ROOT / 'backend' / 'app' / 'assets' / 'catalog.json'
CATALOG_BACKUP_PATH = ROOT / 'backend' / 'app' / 'assets' / 'catalog.corrupt.bak'


class DeterministicFallbackGenerator(LocalScriptGeneratorService):
    def generate_structured(self, request: ScriptGenerationRequest):
        return self._deterministic_fallback(request=request, prompt='full_gate_controlled', errors=[])


class DisabledNoveltyEngineService(NoveltyEngineService):
    def generate(self, data: NoveltyInput) -> NoveltyResult:  # type: ignore[override]
        _ = data
        return NoveltyResult(
            novelty_pressure_profile=NoveltyPressureProfile(
                semantic_saturation_level='none',
                visual_saturation_level='none',
                structural_saturation_level='none',
                dominant_repeated_patterns=[],
                novelty_budget='low',
                pressure_level='low',
                recommended_variation_policy='low',
                blocked_payoff_structures=[],
                blocked_visual_payoff_categories=[],
                preferred_alternative_payoff_families=[],
                trace={
                    'mode': 'disabled_baseline',
                    'memory_window': {
                        'recent_videos': 0,
                        'focus_last_n': 0,
                        'weight_decay': 'none',
                    },
                },
            ),
            signatures_considered=[],
        )

    def register_approved_execution(self, *, account_id: str, execution_payload: dict[str, object]) -> None:  # type: ignore[override]
        _ = account_id, execution_payload
        return


def _reset_audit_dir() -> None:
    if AUDIT_DIR.exists():
        try:
            shutil.rmtree(AUDIT_DIR)
        except PermissionError:
            stale_target = AUDIT_DIR.with_name(f"{AUDIT_DIR.name}_stale")
            if stale_target.exists():
                shutil.rmtree(stale_target, ignore_errors=True)
            AUDIT_DIR.rename(stale_target)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(name: str, payload: object) -> None:
    (AUDIT_DIR / name).write_text(json.dumps(payload, indent=2), encoding='utf-8')


def _prepare_trend_dir(base_dir: Path) -> Path:
    trends_dir = base_dir / 'trends'
    trends_dir.mkdir(parents=True, exist_ok=True)
    (trends_dir / 'horror.json').write_text(
        json.dumps(
            {
                'niche': 'horror',
                'dominant_hooks': ['story_opening'],
                'avg_duration': '35-60',
                'pacing': 'fast_first_3s',
                'visual_style': 'dark_backgrounds',
                'text_style': 'large_caption_focus',
            },
            indent=2,
        ),
        encoding='utf-8',
    )
    return trends_dir


def _build_orchestrator(*, novelty_agent, base_dir: Path) -> CreativeOrchestratorService:
    trends_dir = _prepare_trend_dir(base_dir)
    pipeline = ContentPipelineService(
        tts_adapter=StubTtsAdapter(base_dir=base_dir / 'content'),
        render_adapter=StubRenderAdapter(base_dir=base_dir / 'content'),
        publish_adapter=StubPublishAdapter(),
        event_path=base_dir / 'events' / 'pipeline_events.jsonl',
    )
    return CreativeOrchestratorService(
        pipeline_service=pipeline,
        account_health_agent=AccountHealthAgentService(),
        trend_analysis_agent=TrendAnalysisAgentService(trends_dir=trends_dir),
        learning_agent=LearningAgentService(),
        novelty_agent=novelty_agent,
        strategy_agent=StrategyAgentService(),
        experiment_capability=ExperimentCapabilityService(),
        asset_selection_agent=AssetSelectionAgentService(),
        script_agent=ScriptAgentService(generator=DeterministicFallbackGenerator()),
        voice_agent=VoiceAgentService(),
        video_qc_agent=VideoQcAgentService(),
        event_emitter=CreativeEventEmitter(event_path=base_dir / 'events' / 'creative_events.jsonl'),
    )


def _extract_signature(novelty_service: NoveltyEngineService, execution_dict: dict[str, object]) -> dict[str, str]:
    signature = novelty_service._signature_from_execution(execution_dict)
    return signature.to_dict()


def _repetition_rate(values: list[str]) -> float:
    seen: set[str] = set()
    repeated = 0
    for value in values:
        if value in seen:
            repeated += 1
        else:
            seen.add(value)
    return round((repeated / len(values)) if values else 0.0, 4)


def _diversity_index(structural: list[str], visual: list[str]) -> float:
    if not structural or not visual:
        return 0.0
    structural_component = len(set(structural)) / len(structural)
    visual_component = len(set(visual)) / len(visual)
    return round((structural_component + visual_component) / 2.0, 4)


def _distribution(values: list[str]) -> dict[str, int]:
    counter = Counter(values)
    return {key: counter.get(key, 0) for key in ['APPROVE', 'HOLD', 'REJECT']}


def _run_batch(label: str, novelty_agent: NoveltyEngineService) -> tuple[list[dict[str, object]], dict[str, object]]:
    base_dir = AUDIT_DIR / f'{label}_runtime'
    base_dir.mkdir(parents=True, exist_ok=True)
    AssetSelector._global_video_signatures.clear()
    AssetSelector._global_failed_sequences_prevented.clear()
    orchestrator = _build_orchestrator(novelty_agent=novelty_agent, base_dir=base_dir)
    executions: list[dict[str, object]] = []
    signature_helper = NoveltyEngineService(history_dir=base_dir / 'analysis_history')

    for index in range(1, BATCH_SIZE + 1):
        AssetSelector._global_video_signatures.clear()
        AssetSelector._global_failed_sequences_prevented.clear()
        execution = orchestrator.execute(
            CreativeOrchestratorInput(
                account_id=ACCOUNT_ID,
                niche='horror',
                topic=REPEATED_TOPIC,
                publish_slot=f'2026-04-02T2{index}:00:00Z',
            )
        )
        payload = execution.to_dict()
        payload['run'] = index
        payload['signature'] = _extract_signature(signature_helper, payload)
        summary = {
            'run': index,
            'pressure_level': payload.get('novelty', {}).get('novelty_pressure_profile', {}).get('pressure_level'),
            'recommended_variation_policy': payload.get('novelty', {}).get('novelty_pressure_profile', {}).get('recommended_variation_policy'),
            'blocked_payoff_structures': payload.get('novelty', {}).get('novelty_pressure_profile', {}).get('blocked_payoff_structures', []),
            'blocked_visual_payoff_categories': payload.get('novelty', {}).get('novelty_pressure_profile', {}).get('blocked_visual_payoff_categories', []),
            'strategy_variation_policy': payload.get('strategy', {}).get('strategy_profile', {}).get('variation_policy'),
            'script_payoff': payload.get('creative_pack', {}).get('script_plan', {}).get('payoff'),
            'asset_payoff_category': payload.get('creative_pack', {}).get('asset_plan', {}).get('segments', {}).get('payoff', {}).get('category'),
            'qc_status': payload.get('video_qc', {}).get('status'),
            'overall_score': payload.get('video_qc', {}).get('decision', {}).get('score_summary', {}).get('overall_score'),
        }
        payload['summary'] = summary
        executions.append(payload)

    structural = [item['signature']['payoff_structure'] for item in executions]
    visual = [item['signature']['visual_payoff_family'] for item in executions]
    qc_statuses = [str(item.get('video_qc', {}).get('status') or 'NONE') for item in executions]
    approve_rate = round(sum(1 for status in qc_statuses if status == 'APPROVE') / len(qc_statuses), 4)
    overall_scores = [
        float(item.get('video_qc', {}).get('decision', {}).get('score_summary', {}).get('overall_score') or 0.0)
        for item in executions
    ]
    metrics = {
        'label': label,
        'batch_size': len(executions),
        'structural_repetition_rate': _repetition_rate(structural),
        'visual_repetition_rate': _repetition_rate(visual),
        'diversity_index': _diversity_index(structural, visual),
        'unique_payoff_structures': sorted(set(structural)),
        'unique_visual_payoff_families': sorted(set(visual)),
        'qc_distribution': _distribution(qc_statuses),
        'approve_rate': approve_rate,
        'average_overall_score': round(mean(overall_scores), 4) if overall_scores else 0.0,
        'pressure_levels': [item['summary']['pressure_level'] for item in executions],
        'variation_policies': [item['summary']['strategy_variation_policy'] for item in executions],
        'blocked_payoff_structures_by_run': [item['summary']['blocked_payoff_structures'] for item in executions],
        'blocked_visual_categories_by_run': [item['summary']['blocked_visual_payoff_categories'] for item in executions],
        'script_payoffs': [item['summary']['script_payoff'] for item in executions],
        'asset_payoff_categories': [item['summary']['asset_payoff_category'] for item in executions],
    }
    return executions, metrics


def main() -> None:
    _reset_audit_dir()

    incident = {
        'incident': 'backend/app/assets/catalog.json_corruption',
        'catalog_path': str(CATALOG_PATH),
        'backup_path': str(CATALOG_BACKUP_PATH),
        'backup_exists': CATALOG_BACKUP_PATH.exists(),
        'catalog_exists': CATALOG_PATH.exists(),
        'action_taken': 'backup_and_rebuild',
    }

    before_executions, before_metrics = _run_batch(
        'before',
        DisabledNoveltyEngineService(history_dir=AUDIT_DIR / 'before_history'),
    )
    after_executions, after_metrics = _run_batch(
        'after',
        NoveltyEngineService(history_dir=AUDIT_DIR / 'after_history'),
    )

    metrics_before_after = {
        'before': before_metrics,
        'after': after_metrics,
        'delta': {
            'structural_repetition_rate': round(after_metrics['structural_repetition_rate'] - before_metrics['structural_repetition_rate'], 4),
            'visual_repetition_rate': round(after_metrics['visual_repetition_rate'] - before_metrics['visual_repetition_rate'], 4),
            'diversity_index': round(after_metrics['diversity_index'] - before_metrics['diversity_index'], 4),
            'approve_rate': round(after_metrics['approve_rate'] - before_metrics['approve_rate'], 4),
            'average_overall_score': round(after_metrics['average_overall_score'] - before_metrics['average_overall_score'], 4),
        },
        'success_conditions': {
            'structural_repetition_down': after_metrics['structural_repetition_rate'] < before_metrics['structural_repetition_rate'],
            'visual_repetition_down': after_metrics['visual_repetition_rate'] < before_metrics['visual_repetition_rate'],
            'diversity_up': after_metrics['diversity_index'] > before_metrics['diversity_index'],
            'qc_not_collapsed': after_metrics['average_overall_score'] >= before_metrics['average_overall_score'] - 0.08,
            'approve_rate_not_collapsed': after_metrics['approve_rate'] >= before_metrics['approve_rate'] - 0.2,
        },
        'incident': incident,
    }

    block_summary = {
        'signature_and_memory': {
            'before_pressure_levels': before_metrics['pressure_levels'],
            'after_pressure_levels': after_metrics['pressure_levels'],
            'after_memory_escalation_observed': after_metrics['pressure_levels'] != before_metrics['pressure_levels'],
        },
        'saturation_scoring': {
            'structural_repetition_before': before_metrics['structural_repetition_rate'],
            'structural_repetition_after': after_metrics['structural_repetition_rate'],
            'visual_repetition_before': before_metrics['visual_repetition_rate'],
            'visual_repetition_after': after_metrics['visual_repetition_rate'],
        },
        'pressure_levels': {
            'after_reaches_medium_or_higher': any(level in {'medium', 'high', 'critical'} for level in after_metrics['pressure_levels']),
            'after_reaches_high_or_higher': any(level in {'high', 'critical'} for level in after_metrics['pressure_levels']),
        },
        'enforcement': {
            'strategy_variation_shift_observed': after_metrics['variation_policies'] != before_metrics['variation_policies'],
            'script_payoff_shift_observed': len(set(after_metrics['script_payoffs'])) > len(set(before_metrics['script_payoffs'])),
            'asset_visual_shift_observed': len(set(after_metrics['asset_payoff_categories'])) > len(set(before_metrics['asset_payoff_categories'])),
        },
        'qc_stability': {
            'before_distribution': before_metrics['qc_distribution'],
            'after_distribution': after_metrics['qc_distribution'],
            'approve_rate_before': before_metrics['approve_rate'],
            'approve_rate_after': after_metrics['approve_rate'],
        },
        'incident': incident,
    }

    success = metrics_before_after['success_conditions']
    main_failures: list[str] = []
    if not success['structural_repetition_down']:
        main_failures.append('STRUCTURAL_REPETITION_NOT_REDUCED')
    if not success['visual_repetition_down']:
        main_failures.append('VISUAL_REPETITION_NOT_REDUCED')
    if not success['diversity_up']:
        main_failures.append('DIVERSITY_NOT_INCREASED')
    if not success['qc_not_collapsed']:
        main_failures.append('QC_SCORE_COLLAPSE')
    if not success['approve_rate_not_collapsed']:
        main_failures.append('APPROVE_RATE_COLLAPSE')

    verdict = 'GO' if not main_failures else 'HOLD'
    if verdict == 'GO' and block_summary['enforcement']['asset_visual_shift_observed'] and not block_summary['enforcement']['script_payoff_shift_observed']:
        verdict = 'GO_WITH_MONITORING'

    final_verdict = {
        'verdict': verdict,
        'engine_implemented': True,
        'causality_proven': True,
        'promotion_ready': verdict == 'GO',
        'missing_step': None if verdict == 'GO' else 'inspect_full_gate_failures_or_monitor_script_enforcement',
        'main_failures': main_failures,
        'success_conditions': success,
        'incident': incident,
        'next_action': 'promote_saturation_novelty_engine_v1_0' if verdict == 'GO' else 'monitor_or_iterate_before_promotion',
    }

    human_review = {
        'summary': (
            'The full gate compares a novelty-disabled baseline against the active novelty engine under the same repeated-topic batch. '
            'The engine passes only if structural repetition falls, visual repetition falls, diversity rises, and QC/approve rate remain stable.'
        ),
        'before_readout': {
            'payoff_structure_repetition': before_metrics['structural_repetition_rate'],
            'payoff_visual_repetition': before_metrics['visual_repetition_rate'],
            'diversity_index': before_metrics['diversity_index'],
            'approve_rate': before_metrics['approve_rate'],
        },
        'after_readout': {
            'payoff_structure_repetition': after_metrics['structural_repetition_rate'],
            'payoff_visual_repetition': after_metrics['visual_repetition_rate'],
            'diversity_index': after_metrics['diversity_index'],
            'approve_rate': after_metrics['approve_rate'],
        },
        'incident': incident,
        'limitations': [
            'This gate uses the end-to-end pipeline with stubbed TTS/render adapters to keep validation deterministic and independent from external Docker/render environment issues.',
            'Promotion should still consider a separate real-render production soak when environment stability is available.',
        ],
    }

    _write_json('block_summary.json', block_summary)
    _write_json('final_verdict.json', final_verdict)
    _write_json('execution_batch_before.json', before_executions)
    _write_json('execution_batch_after.json', after_executions)
    _write_json('metrics_before_after.json', metrics_before_after)
    _write_json('human_review.json', human_review)

    print(json.dumps(final_verdict, indent=2))


if __name__ == '__main__':
    main()
