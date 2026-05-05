param(
    [string]$OutputDir = "OUT/audit/script_agent_excellence_gate",
    [switch]$SkipScriptBattery,
    [switch]$SkipVideoBatch
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $repoRoot
$auditDir = Join-Path $repoRoot $OutputDir
$null = New-Item -ItemType Directory -Force -Path $auditDir
$results = New-Object System.Collections.Generic.List[object]

function Add-Result {
    param([string]$Domain,[string]$Check,[string]$Status,[string]$Evidence,[string]$Details)
    $results.Add([pscustomobject]@{Domain=$Domain;Check=$Check;Status=$Status;Evidence=$Evidence;Details=$Details}) | Out-Null
}

function Invoke-LoggedCommand {
    param([string]$Domain,[string]$Check,[string]$Command,[string]$OutputFile)
    $path = Join-Path $auditDir $OutputFile
    try {
        $text = (& cmd.exe /d /c "$Command 2>&1" | Out-String)
        $exitCode = $LASTEXITCODE
    } catch {
        $text = ($_ | Out-String)
        $exitCode = 1
    }
    Set-Content -Path $path -Value $text -Encoding utf8
    if ($exitCode -eq 0) {
        Add-Result -Domain $Domain -Check $Check -Status "PASS" -Evidence $OutputFile -Details "comando executado com sucesso"
    } else {
        Add-Result -Domain $Domain -Check $Check -Status "FAIL" -Evidence $OutputFile -Details "comando falhou com exit code $exitCode"
    }
}

function Invoke-PythonAudit {
    param([string]$Domain,[string]$Check,[string]$ScriptBody,[string]$JsonOutputFile,[string]$LogOutputFile)
    $scriptPath = Join-Path $auditDir ($Check + ".py")
    $jsonPath = Join-Path $auditDir $JsonOutputFile
    $logPath = Join-Path $auditDir $LogOutputFile
    Set-Content -Path $scriptPath -Value $ScriptBody -Encoding utf8
    try {
        $text = (& python $scriptPath $jsonPath 2>&1 | Out-String)
        $exitCode = $LASTEXITCODE
    } catch {
        $text = ($_ | Out-String)
        $exitCode = 1
    }
    Set-Content -Path $logPath -Value $text -Encoding utf8
    if ($exitCode -ne 0) {
        Add-Result -Domain $Domain -Check $Check -Status "FAIL" -Evidence $LogOutputFile -Details "python audit falhou com exit code $exitCode"
        return
    }
    $payload = Get-Content -Raw -Path $jsonPath | ConvertFrom-Json
    Add-Result -Domain $Domain -Check $Check -Status ([string]$payload.status) -Evidence $JsonOutputFile -Details ([string]$payload.summary)
}

function Write-AuditReport {
    $reportPath = Join-Path $auditDir "AUDIT_REPORT.md"
    $failCount = @($results | Where-Object { $_.Status -eq "FAIL" }).Count
    $warnCount = @($results | Where-Object { $_.Status -eq "WARN" }).Count
    $summary = if ($failCount -eq 0) { "GO" } else { "NO-GO" }
    $lines = @(
        "# Script Agent Excellence Gate",
        "",
        "- Decision: $summary",
        "- Failures: $failCount",
        "- Warnings: $warnCount",
        "- Generated at: $(Get-Date -Format s)",
        "",
        "| Domain | Check | Status | Evidence | Details |",
        "| --- | --- | --- | --- | --- |"
    )
    foreach ($item in $results) {
        $lines += "| $($item.Domain) | $($item.Check) | $($item.Status) | $($item.Evidence) | $($item.Details) |"
    }
    Set-Content -Path $reportPath -Value ($lines -join "`n") -Encoding utf8
    return $failCount
}

$compileTargets = @(
    "backend/app/content/script_gen/models.py",
    "backend/app/content/script_gen/service.py",
    "backend/app/content/screen_text/service.py",
    "backend/app/creative/agents/script/models.py",
    "backend/app/creative/agents/script/service.py",
    "backend/app/creative/orchestrator/service.py"
)
$unitSuites = @(
    "tests.test_script_generation_unittest",
    "tests.test_script_agent_phase2_unittest",
    "tests.test_screen_text_adapter_unittest"
)
$cognitiveSuites = @(
    "tests.test_creative_orchestrator_phase2_unittest",
    "tests.test_phase2_block1_smoke_unittest",
    "tests.test_phase2_block2_smoke_unittest",
    "tests.test_phase2_block3_smoke_unittest",
    "tests.test_phase2_block4_smoke_unittest"
)

Invoke-LoggedCommand -Domain "BUILD" -Check "py_compile_script_agent" -Command ("python -m py_compile " + ($compileTargets -join " ")) -OutputFile "py_compile_script_agent.txt"
Invoke-LoggedCommand -Domain "TESTS" -Check "script_agent_unit_tests" -Command ("python -m unittest -q " + ($unitSuites -join " ")) -OutputFile "script_agent_unit_tests.txt"
Invoke-LoggedCommand -Domain "TESTS" -Check "script_agent_cognitive_regression" -Command ("python -m unittest -q " + ($cognitiveSuites -join " ")) -OutputFile "script_agent_cognitive_regression.txt"

$contextAudit = @"
from __future__ import annotations
import json, sys
from pathlib import Path
root = Path.cwd(); sys.path.insert(0, str((root / 'backend').resolve()))
from app.content.script_gen.models import ScriptGenerationContext, ScriptGenerationRequest
from app.content.script_gen.service import LocalScriptGeneratorService
from app.creative.contracts.creative_pack import ExperimentPlan, LearningInsights, StrategyProfile, TrendProfile
out = Path(sys.argv[1]); svc = LocalScriptGeneratorService()
base = ScriptGenerationContext(account_id='acc', niche='horror', topic='sealed evidence room', account_health_status='SAFE', strategy_profile=StrategyProfile(), trend_profile=TrendProfile(niche='horror', dominant_hooks=['question'], pacing='fast_first_3s', visual_style='dark_backgrounds'), learning_insights=LearningInsights(recommended_hook_type='question', recommendations=['prefer witness phrasing']), experiment_plan=ExperimentPlan(experiment_id='exp', variant_id='A', variant_type='narrative_mode', variant_params={'narrative_mode':'witness_report'}, fallback_used=False))
variants = {
    'base': base,
    'strategy': ScriptGenerationContext(account_id=base.account_id, niche=base.niche, topic=base.topic, account_health_status=base.account_health_status, strategy_profile=StrategyProfile(content_mode='conservative', hook_aggressiveness='low', target_duration_range='8-10s'), trend_profile=base.trend_profile, learning_insights=base.learning_insights, experiment_plan=base.experiment_plan),
    'trend': ScriptGenerationContext(account_id=base.account_id, niche=base.niche, topic=base.topic, account_health_status=base.account_health_status, strategy_profile=base.strategy_profile, trend_profile=TrendProfile(niche='horror', dominant_hooks=['shock_statement'], pacing='fast_first_3s', visual_style='dark_backgrounds'), learning_insights=base.learning_insights, experiment_plan=base.experiment_plan),
    'learning': ScriptGenerationContext(account_id=base.account_id, niche=base.niche, topic=base.topic, account_health_status=base.account_health_status, strategy_profile=base.strategy_profile, trend_profile=base.trend_profile, learning_insights=LearningInsights(recommended_hook_type='story_opening', recommendations=['favor concrete timestamp']), experiment_plan=base.experiment_plan),
    'experiment': ScriptGenerationContext(account_id=base.account_id, niche=base.niche, topic=base.topic, account_health_status=base.account_health_status, strategy_profile=base.strategy_profile, trend_profile=base.trend_profile, learning_insights=base.learning_insights, experiment_plan=ExperimentPlan(experiment_id='exp', variant_id='B', variant_type='narrative_mode', variant_params={'narrative_mode':'official_warning'}, fallback_used=False)),
}
outputs = {k: svc.generate_structured(ScriptGenerationRequest(context=v)).to_dict() for k, v in variants.items()}
base_script = json.dumps(outputs['base']['script_plan'], sort_keys=True)
changed = [k for k in ('strategy','trend','learning','experiment') if json.dumps(outputs[k]['script_plan'], sort_keys=True) != base_script]
out.write_text(json.dumps({'status': 'PASS' if len(changed)==4 else 'FAIL', 'summary': f'context changed output in {len(changed)}/4 controlled variants', 'changed_variants': changed, 'outputs': outputs}, ensure_ascii=True, indent=2), encoding='utf-8')
"@
Invoke-PythonAudit -Domain "QUALITY" -Check "context_influence_audit" -ScriptBody $contextAudit -JsonOutputFile "context_influence_audit.json" -LogOutputFile "context_influence_audit.log"

$parsingAudit = @"
from __future__ import annotations
import json, sys
from pathlib import Path
root = Path.cwd(); sys.path.insert(0, str((root / 'backend').resolve()))
from app.content.script_gen.models import ScriptGenerationContext, ScriptGenerationRequest
from app.content.script_gen.service import LocalScriptGeneratorService
from app.creative.contracts.creative_pack import ExperimentPlan, LearningInsights, StrategyProfile, TrendProfile
out = Path(sys.argv[1]); svc = LocalScriptGeneratorService(); req = ScriptGenerationRequest(context=ScriptGenerationContext(account_id='acc', niche='true_crime', topic='sealed tape recorder', strategy_profile=StrategyProfile(), trend_profile=TrendProfile(niche='true_crime', dominant_hooks=['story_opening']), learning_insights=LearningInsights(recommendations=['favor recovered evidence']), experiment_plan=ExperimentPlan(experiment_id='exp', variant_id='A', variant_type='narrative_mode', variant_params={'narrative_mode':'procedural_anomaly'}, fallback_used=False)))
cases = {
    'json_direct': '{"narrative_mode":"procedural_anomaly","hook":"A recorder started inside evidence lockup","setup":"The playback began before police touched the shelf","payoff":"It named a detective buried twelve years earlier"}',
    'json_fenced': '```json\n{"narrative_mode":"official_warning","hook":"The warning arrived after the station shut","setup":"Every camera failed before the second knock","payoff":"The sealed exit opened into a condemned shaft"}\n```',
    'json_with_noise': 'Result follows:\n{"narrative_mode":"hidden_truth","hook":"The archive page changed after midnight","setup":"Each copy removed the same witness signature","payoff":"The replacement date was printed next year"}\nend',
    'sentence_fallback': 'Police reopened the room. The recorder switched on before contact. It named a dead officer from 2011.',
}
parsed, failed = {}, []
for name, raw in cases.items():
    try:
        parsed[name] = svc._parse_structured_response(raw, request=req).to_dict()
    except Exception as exc:
        failed.append(f'{name}: {exc}')
out.write_text(json.dumps({'status': 'PASS' if not failed else 'FAIL', 'summary': 'structured parser accepted 4/4 representative cases' if not failed else '; '.join(failed), 'parsed': parsed, 'failed': failed}, ensure_ascii=True, indent=2), encoding='utf-8')
"@
Invoke-PythonAudit -Domain "ROBUSTNESS" -Check "structured_parsing_audit" -ScriptBody $parsingAudit -JsonOutputFile "structured_parsing_audit.json" -LogOutputFile "structured_parsing_audit.log"
$fallbackAudit = @"
from __future__ import annotations
import json, sys
from pathlib import Path
root = Path.cwd(); sys.path.insert(0, str((root / 'backend').resolve()))
from app.content.script_gen.models import ScriptGenerationContext, ScriptGenerationRequest
from app.content.script_gen.service import LocalScriptGeneratorService, ScriptGenerationError
from app.creative.contracts.creative_pack import ExperimentPlan, LearningInsights, StrategyProfile, TrendProfile
out = Path(sys.argv[1]); svc = LocalScriptGeneratorService(); req = ScriptGenerationRequest(context=ScriptGenerationContext(account_id='acc', niche='history', topic='archive entry erased itself', strategy_profile=StrategyProfile(), trend_profile=TrendProfile(niche='history', dominant_hooks=['story_opening']), learning_insights=LearningInsights(recommendations=['favor contradiction']), experiment_plan=ExperimentPlan(experiment_id='exp', variant_id='A', variant_type='narrative_mode', variant_params={'narrative_mode':'contradiction_timeline'}, fallback_used=False)))
orig_groq = svc._generate_with_groq; orig_ollama = svc._generate_with_ollama

def fail_groq(*, prompt, request, provider_attempt_trace=()): raise ScriptGenerationError('simulated groq outage')
def fail_ollama(*, prompt, request, provider_attempt_trace=()): raise ScriptGenerationError('simulated ollama outage')
def fake_ollama(*, prompt, request, provider_attempt_trace=()):
    return svc._build_response(request=request, prompt=prompt, raw_output='{"narrative_mode":"contradiction_timeline","hook":"The archive entry changed after sealing","setup":"A clerk found tomorrow printed in the ledger","payoff":"The final page listed witnesses not born yet"}', provider='ollama', model='test-ollama')
svc._generate_with_groq = fail_groq
svc._generate_with_ollama = fake_ollama
ollama_response = svc.generate_structured(req)
svc._generate_with_ollama = fail_ollama
deterministic_response = svc.generate_structured(req)
svc._generate_with_groq = orig_groq; svc._generate_with_ollama = orig_ollama
ok = ollama_response.script_plan.generation_mode.endswith('_structured') and deterministic_response.script_plan.generation_mode == 'fallback_contextual' and 'NOBODY COULD EXPLAIN IT' not in deterministic_response.script_plan.payoff.upper()
out.write_text(json.dumps({'status': 'PASS' if ok else 'FAIL', 'summary': 'groq->ollama and ollama->deterministic fallback paths remained valid', 'checks': {'ollama_fallback_mode': ollama_response.script_plan.generation_mode, 'deterministic_fallback_mode': deterministic_response.script_plan.generation_mode, 'deterministic_payoff': deterministic_response.script_plan.payoff}}, ensure_ascii=True, indent=2), encoding='utf-8')
"@
Invoke-PythonAudit -Domain "ROBUSTNESS" -Check "fallback_path_audit" -ScriptBody $fallbackAudit -JsonOutputFile "fallback_path_audit.json" -LogOutputFile "fallback_path_audit.log"

if (-not $SkipScriptBattery) {
    $scriptBattery = @"
from __future__ import annotations
import json, re, statistics, sys, time
from collections import Counter
from pathlib import Path
root = Path.cwd(); sys.path.insert(0, str((root / 'backend').resolve()))
from app.content.script_gen.models import ScriptGenerationContext, ScriptGenerationRequest
from app.content.script_gen.service import ANTI_CLICHE_PHRASES, LocalScriptGeneratorService
from app.creative.contracts.creative_pack import ExperimentPlan, LearningInsights, StrategyProfile, TrendProfile
out = Path(sys.argv[1]); svc = LocalScriptGeneratorService()
scenarios = [('horror','sealed evidence room','witness_report'),('horror','radio whisper behind the wall','recovered_recording'),('horror','midnight fire exit warning','official_warning'),('horror','stairwell number changed overnight','contradiction_timeline'),('horror','last train voice note','urban_legend_fragment'),('horror','chapel ledger hidden page','hidden_truth'),('horror','autopsy room camera desync','procedural_anomaly'),('true_crime','sealed locker recorder','procedural_anomaly'),('true_crime','missing witness transcript','hidden_truth'),('true_crime','station intercom warning','official_warning'),('true_crime','evidence tape contradiction','contradiction_timeline'),('true_crime','dispatcher call recovered','recovered_recording'),('true_crime','janitor witness statement','witness_report'),('facts','archive page changed date','contradiction_timeline'),('facts','bunker map missing corridor','hidden_truth'),('facts','official memo reversed timeline','official_warning'),('facts','museum audio anomaly','recovered_recording'),('facts','research log contradiction','procedural_anomaly'),('facts','urban legend tied to census record','urban_legend_fragment'),('facts','survivor notebook testimony','witness_report')]
scripts, latencies = [], []
for idx, (niche, topic, mode) in enumerate(scenarios):
    req = ScriptGenerationRequest(context=ScriptGenerationContext(account_id=f'acc_{idx:02d}', niche=niche, topic=topic, account_health_status='SAFE', strategy_profile=StrategyProfile(), trend_profile=TrendProfile(niche=niche, dominant_hooks=['question' if idx % 2 == 0 else 'shock_statement'], pacing='fast_first_3s', visual_style='dark_backgrounds'), learning_insights=LearningInsights(recommended_hook_type='question' if idx % 3 else 'story_opening', recommendations=['favor concrete timestamp', 'avoid generic endings']), experiment_plan=ExperimentPlan(experiment_id='exp_battery', variant_id='A' if idx % 2 == 0 else 'B', variant_type='narrative_mode', variant_params={'narrative_mode': mode}, fallback_used=False)))
    started = time.perf_counter(); response = svc.generate_structured(req); latencies.append(time.perf_counter() - started)
    attempt_trace = list(response.provider_attempt_trace)
    groq_failures = [item for item in attempt_trace if item.startswith('groq[')]
    scripts.append({
        'niche': niche,
        'topic': topic,
        'provider': response.provider_used,
        'narrative_mode': response.payload.narrative_mode,
        'hook': response.script_plan.hook,
        'setup': response.script_plan.setup,
        'payoff': response.script_plan.payoff,
        'provider_attempt_trace': attempt_trace,
        'groq_to_ollama_reason': '; '.join(groq_failures) if response.provider_used == 'ollama' and groq_failures else '',
    })
    time.sleep(0.2)
joined_upper = [' '.join([i['hook'], i['setup'], i['payoff']]).upper() for i in scripts]
cliche_hits = sum(1 for text in joined_upper if any(phrase in text for phrase in ANTI_CLICHE_PHRASES))
weak_payoff_hits = sum(1 for i in scripts if re.search(r'\b(SOMETHING WAS WRONG|NOBODY COULD EXPLAIN IT|NOBODY EVER FOUND OUT WHY)\b', i['payoff'].upper()))
distinct_hooks = len({i['hook'] for i in scripts}); distinct_modes = len({i['narrative_mode'] for i in scripts}); providers = dict(Counter(i['provider'] for i in scripts))
groq_to_ollama_count = sum(1 for i in scripts if i['groq_to_ollama_reason'])
reasons = []
if len(scripts) != 20: reasons.append('battery did not produce 20 scripts')
if cliche_hits > 3: reasons.append(f'cliche_hits={cliche_hits}')
if weak_payoff_hits > 2: reasons.append(f'weak_payoff_hits={weak_payoff_hits}')
if distinct_hooks < 16: reasons.append(f'distinct_hooks={distinct_hooks}')
if distinct_modes < 5: reasons.append(f'distinct_modes={distinct_modes}')
out.write_text(json.dumps({'status': 'PASS' if not reasons else 'FAIL', 'summary': '20-script battery met diversity and anti-cliche thresholds' if not reasons else '; '.join(reasons), 'metrics': {'script_count': len(scripts), 'distinct_hooks': distinct_hooks, 'distinct_modes': distinct_modes, 'cliche_hits': cliche_hits, 'weak_payoff_hits': weak_payoff_hits, 'provider_counts': providers, 'groq_to_ollama_count': groq_to_ollama_count, 'avg_latency_s': round(statistics.mean(latencies), 3), 'p95_latency_s': round(sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)], 3)}, 'scripts': scripts}, ensure_ascii=True, indent=2), encoding='utf-8')
"@
    Invoke-PythonAudit -Domain "QUALITY" -Check "script_battery_20" -ScriptBody $scriptBattery -JsonOutputFile "script_battery_20.json" -LogOutputFile "script_battery_20.log"
} else {
    Add-Result -Domain "QUALITY" -Check "script_battery_20" -Status "N/A" -Evidence "script_battery_20.json" -Details "skip manual"
}
if (-not $SkipVideoBatch) {
    $videoBatch = @"
from __future__ import annotations
import json, os, statistics, sys, time
from pathlib import Path
root = Path.cwd(); sys.path.insert(0, str((root / 'backend').resolve()))
from app.content.pipeline.service import ContentPipelineService
from app.creative.agents.account_health.service import AccountHealthAgentService
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
from app.content.backgrounds.service import BackgroundGeneratorService
from app.creative.agents.learning.service import LearningAgentService
from app.creative.agents.script.service import ScriptAgentService
from app.creative.agents.strategy.service import StrategyAgentService
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.experiments.service import ExperimentCapabilityService
from app.creative.orchestrator.events import CreativeEventEmitter
from app.creative.orchestrator.service import CreativeOrchestratorService
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput
out = Path(sys.argv[1]).resolve(); work = (out.parent / 'video_batch_workspace').resolve(); work.mkdir(parents=True, exist_ok=True)
ffmpeg_dir = Path(r'C:\ffmpeg\ffmpeg-8.0.1-essentials_build\bin')
if ffmpeg_dir.exists(): os.environ['PATH'] = str(ffmpeg_dir) + os.pathsep + os.environ.get('PATH', '')
trends = work / 'trends'; trends.mkdir(parents=True, exist_ok=True)
(trends / 'horror.json').write_text(json.dumps({'niche':'horror','dominant_hooks':['question','shock_statement'],'avg_duration':'35-60','pacing':'fast_first_3s','visual_style':'dark_backgrounds','text_style':'large_caption_focus'}), encoding='utf-8')
(trends / 'true_crime.json').write_text(json.dumps({'niche':'true_crime','dominant_hooks':['story_opening','shock_statement'],'avg_duration':'35-55','pacing':'fast_first_3s','visual_style':'investigation_dark','text_style':'large_caption_focus'}), encoding='utf-8')
(trends / 'facts.json').write_text(json.dumps({'niche':'facts','dominant_hooks':['question','story_opening'],'avg_duration':'30-45','pacing':'fast_first_3s','visual_style':'archive_dark','text_style':'large_caption_focus'}), encoding='utf-8')
data_dir = work / 'data'; metrics_dir = work / 'metrics'; analysis_dir = work / 'analysis'; exp_dir = work / 'experiments'; learning_dir = work / 'learning'; events_dir = work / 'events'
for item in (data_dir, metrics_dir, analysis_dir, exp_dir, learning_dir, events_dir): item.mkdir(parents=True, exist_ok=True)
(data_dir / 'publish_records.jsonl').write_text('\n'.join(json.dumps({'account_id': f'acc_{idx}', 'publish_id': f'pub_{idx:03d}', 'niche': niche}) for idx, niche in enumerate(['horror','true_crime','facts','horror','true_crime'], start=1)), encoding='utf-8')
(metrics_dir / 'video_metrics.jsonl').write_text('\n'.join(json.dumps({'account_id': f'acc_{idx}', 'views': 150 + idx * 40, 'completion_rate': 0.55 + idx * 0.03, 'duration_s': 9.0 + idx * 0.2}) for idx in range(1, 6)), encoding='utf-8')
(analysis_dir / 'hook_performance_summary.json').write_text(json.dumps({'hooks':[{'hook_style':'question'},{'hook_style':'story_opening'}]}, ensure_ascii=True), encoding='utf-8')
(exp_dir / 'experiment_config.json').write_text(json.dumps({'name':'script_agent_excellence','scope':'CREATIVE_PACK','variant_a':{'variant_type':'narrative_mode','narrative_mode':'witness_report'},'variant_b':{'variant_type':'narrative_mode','narrative_mode':'official_warning'},'status':'ACTIVE'}, ensure_ascii=True), encoding='utf-8')
pipeline = ContentPipelineService(event_path=events_dir / 'events.jsonl')
orchestrator = CreativeOrchestratorService(pipeline_service=pipeline, account_health_agent=AccountHealthAgentService(), trend_analysis_agent=TrendAnalysisAgentService(trends_dir=trends), learning_agent=LearningAgentService(default_publish_records_path=data_dir / 'publish_records.jsonl', default_video_metrics_path=metrics_dir / 'video_metrics.jsonl', default_analysis_dir=analysis_dir, default_output_path=learning_dir / 'learning_insights.json'), strategy_agent=StrategyAgentService(), experiment_capability=ExperimentCapabilityService(default_config_path=exp_dir / 'experiment_config.json', default_output_path=exp_dir / 'experiment_plan.json', default_experiments_path=exp_dir / 'experiments.jsonl', default_assignments_path=exp_dir / 'assignments.jsonl', default_results_path=exp_dir / 'results.jsonl'), asset_selection_agent=AssetSelectionAgentService(background_service=BackgroundGeneratorService(local_assets_dir=(root / 'assets' / 'backgrounds').resolve())), script_agent=ScriptAgentService(), voice_agent=VoiceAgentService(), video_qc_agent=VideoQcAgentService(), event_emitter=CreativeEventEmitter(event_path=events_dir / 'creative_events.jsonl'))
runs = [('acc_1','horror','sealed evidence room whisper'),('acc_2','true_crime','dispatcher tape reopened'),('acc_3','facts','archive page changed date'),('acc_4','horror','station corridor warning'),('acc_5','true_crime','dead detective voice print')]
results, durations = [], []
for idx, (account_id, niche, topic) in enumerate(runs, start=1):
    started = time.perf_counter(); execution = orchestrator.execute(CreativeOrchestratorInput(account_id=account_id, niche=niche, topic=topic, publish_slot=f'2026-03-17T1{idx}:00:00Z')); elapsed = time.perf_counter() - started; durations.append(elapsed)
    results.append({'account_id': account_id, 'niche': niche, 'topic': topic, 'pipeline_status': execution.pipeline_output['result']['status'], 'video_qc_status': execution.video_qc.status if execution.video_qc else None, 'script_generation_mode': execution.creative_pack.script_plan.generation_mode if execution.creative_pack else None, 'voice_provider': execution.creative_pack.voice_plan.provider if execution.creative_pack else None, 'hook': execution.creative_pack.script_plan.hook if execution.creative_pack else None, 'payoff': execution.creative_pack.script_plan.payoff if execution.creative_pack else None, 'elapsed_s': round(elapsed, 3)})
pass_count = sum(1 for item in results if item['pipeline_status'] == 'READY' and item['video_qc_status'] == 'APPROVE'); distinct_hooks = len({item['hook'] for item in results if item['hook']})
reasons = []
if len(results) != 5: reasons.append('video batch did not execute 5 runs')
if pass_count < 4: reasons.append(f'only {pass_count}/5 videos reached READY+APPROVE')
if distinct_hooks < 4: reasons.append(f'distinct video hooks={distinct_hooks}')
out.write_text(json.dumps({'status': 'PASS' if not reasons else 'FAIL', 'summary': '5-video batch met readiness and diversity thresholds' if not reasons else '; '.join(reasons), 'metrics': {'video_count': len(results), 'pass_count': pass_count, 'distinct_hooks': distinct_hooks, 'avg_elapsed_s': round(statistics.mean(durations), 3) if durations else 0.0, 'max_elapsed_s': round(max(durations), 3) if durations else 0.0}, 'results': results}, ensure_ascii=True, indent=2), encoding='utf-8')
"@
    Invoke-PythonAudit -Domain "QUALITY" -Check "video_batch_5" -ScriptBody $videoBatch -JsonOutputFile "video_batch_5.json" -LogOutputFile "video_batch_5.log"
} else {
    Add-Result -Domain "QUALITY" -Check "video_batch_5" -Status "N/A" -Evidence "video_batch_5.json" -Details "skip manual"
}

$failCount = Write-AuditReport
if ($failCount -eq 0) { Write-Host "GO"; exit 0 }
Write-Host "NO-GO"; exit 1
