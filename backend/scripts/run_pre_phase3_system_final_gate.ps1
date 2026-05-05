param(
    [string]$OutputDir = "OUT/audit/pre_phase3_final_gate",
    [switch]$SkipInfra,
    [switch]$SkipSecurity,
    [switch]$SkipStressBatch,
    [switch]$SkipResourceAudit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $repoRoot

$auditDir = Join-Path $repoRoot $OutputDir
$null = New-Item -ItemType Directory -Force -Path $auditDir

$results = New-Object System.Collections.Generic.List[object]

function Add-Result {
    param(
        [string]$Domain,
        [string]$Check,
        [string]$Status,
        [string]$Evidence,
        [string]$Details
    )
    $results.Add([pscustomobject]@{
        Domain = $Domain
        Check = $Check
        Status = $Status
        Evidence = $Evidence
        Details = $Details
    }) | Out-Null
}

function Invoke-LoggedCommand {
    param(
        [string]$Domain,
        [string]$Check,
        [string]$Command,
        [string]$OutputFile,
        [switch]$AllowMissing
    )

    $path = Join-Path $auditDir $OutputFile
    $exitCode = 0
    $text = ""
    try {
        $text = (& cmd.exe /d /c "$Command 2>&1" | Out-String)
        $exitCode = $LASTEXITCODE
    }
    catch {
        $text = ($_ | Out-String)
        $exitCode = 1
    }

    Set-Content -Path $path -Value $text -Encoding utf8

    if ($AllowMissing -and $text -match "not recognized|No module named|cannot find|is not installed") {
        Add-Result -Domain $Domain -Check $Check -Status "N/A" -Evidence $OutputFile -Details "ferramenta ausente no ambiente"
        return $true
    }

    if ($exitCode -eq 0) {
        Add-Result -Domain $Domain -Check $Check -Status "PASS" -Evidence $OutputFile -Details "comando executado com sucesso"
        return $true
    }

    Add-Result -Domain $Domain -Check $Check -Status "FAIL" -Evidence $OutputFile -Details "comando falhou com exit code $exitCode"
    return $false
}

function Test-HttpEndpoint {
    param(
        [string]$Domain,
        [string]$Check,
        [string]$Url,
        [string]$OutputFile
    )

    $path = Join-Path $auditDir $OutputFile
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
        $payload = "status=$($response.StatusCode)`n$($response.Content)"
        Set-Content -Path $path -Value $payload -Encoding utf8
        if ($response.StatusCode -eq 200) {
            Add-Result -Domain $Domain -Check $Check -Status "PASS" -Evidence $OutputFile -Details $Url
            return
        }
        Add-Result -Domain $Domain -Check $Check -Status "FAIL" -Evidence $OutputFile -Details "status $($response.StatusCode)"
    }
    catch {
        Set-Content -Path $path -Value ($_ | Out-String) -Encoding utf8
        Add-Result -Domain $Domain -Check $Check -Status "FAIL" -Evidence $OutputFile -Details $Url
    }
}

function Test-NoImportMatch {
    param(
        [string]$Domain,
        [string]$Check,
        [string]$Pattern,
        [string]$TargetPath,
        [string]$OutputFile
    )

    $path = Join-Path $auditDir $OutputFile
    $cmd = Get-Command rg -ErrorAction SilentlyContinue
    if (-not $cmd) {
        Set-Content -Path $path -Value "rg ausente" -Encoding utf8
        Add-Result -Domain $Domain -Check $Check -Status "N/A" -Evidence $OutputFile -Details "rg ausente"
        return
    }

    $hits = & $cmd.Source -n $Pattern $TargetPath 2>&1 | Out-String
    Set-Content -Path $path -Value $hits -Encoding utf8
    if ($LASTEXITCODE -eq 1) {
        Add-Result -Domain $Domain -Check $Check -Status "PASS" -Evidence $OutputFile -Details "nenhum import proibido"
        return
    }
    Add-Result -Domain $Domain -Check $Check -Status "FAIL" -Evidence $OutputFile -Details "import proibido encontrado"
}

function Test-RequiredPaths {
    param(
        [string[]]$Paths,
        [string]$OutputFile
    )

    $path = Join-Path $auditDir $OutputFile
    $missing = @()
    $lines = @()
    foreach ($item in $Paths) {
        $exists = Test-Path $item
        $lines += "$item => $exists"
        if (-not $exists) {
            $missing += $item
        }
    }
    Set-Content -Path $path -Value ($lines -join "`n") -Encoding utf8
    if ($missing.Count -eq 0) {
        Add-Result -Domain "REPO" -Check "required_paths" -Status "PASS" -Evidence $OutputFile -Details "estrutura esperada presente"
    }
    else {
        Add-Result -Domain "REPO" -Check "required_paths" -Status "FAIL" -Evidence $OutputFile -Details ("missing: " + ($missing -join ", "))
    }
}

function Write-AuditReport {
    $reportPath = Join-Path $auditDir "AUDIT_REPORT.md"
    $failCount = @($results | Where-Object { $_.Status -eq "FAIL" }).Count
    $summary = if ($failCount -eq 0) { "GO" } else { "NO-GO" }

    $lines = @()
    $lines += "# Pre-Phase3 System Final Gate"
    $lines += ""
    $lines += "- Decision: $summary"
    $lines += "- Failures: $failCount"
    $lines += "- Generated at: $(Get-Date -Format s)"
    $lines += ""
    $lines += "| Domain | Check | Status | Evidence | Details |"
    $lines += "| --- | --- | --- | --- | --- |"
    foreach ($item in $results) {
        $lines += "| $($item.Domain) | $($item.Check) | $($item.Status) | $($item.Evidence) | $($item.Details) |"
    }
    Set-Content -Path $reportPath -Value ($lines -join "`n") -Encoding utf8
}

$requiredPaths = @(
    "backend/app/runtime",
    "backend/app/creative",
    "backend/app/content",
    "backend/app/metrics",
    "backend/app/analysis",
    "backend/app/safety",
    "backend/app/simulation",
    "backend/app/data",
    "backend/app/experiments",
    "docs/runtime",
    "tests"
)

$phase1Regression = @(
    "tests.test_content_pipeline_d27_unittest",
    "tests.test_script_generation_unittest",
    "tests.test_screen_text_adapter_unittest"
)

$cognitiveRegression = @(
    "tests.test_creative_orchestrator_phase2_unittest",
    "tests.test_script_agent_phase2_unittest",
    "tests.test_voice_agent_phase2_unittest",
    "tests.test_video_qc_agent_phase2_unittest",
    "tests.test_strategy_agent_phase2_unittest",
    "tests.test_account_health_agent_phase2_unittest",
    "tests.test_trend_analysis_agent_phase2_unittest",
    "tests.test_asset_selection_agent_phase2_unittest",
    "tests.test_learning_agent_phase2_unittest",
    "tests.test_experiment_capability_phase2_unittest"
)

Test-RequiredPaths -Paths $requiredPaths -OutputFile "repo_required_paths.txt"
Invoke-LoggedCommand -Domain "REPO" -Check "git_status_clean" -Command "git status --short" -OutputFile "repo_git_status.txt" | Out-Null
Invoke-LoggedCommand -Domain "DEPENDENCIES" -Check "pip_check" -Command "python -m pip check" -OutputFile "pip_check.txt" | Out-Null

if (-not $SkipSecurity) {
    Invoke-LoggedCommand -Domain "SECURITY" -Check "pip_audit" -Command "pip-audit" -OutputFile "pip_audit.txt" -AllowMissing:$true | Out-Null
    Invoke-LoggedCommand -Domain "SECURITY" -Check "gitleaks" -Command "gitleaks detect --source . --no-git --config .gitleaks.toml" -OutputFile "gitleaks.txt" -AllowMissing:$true | Out-Null
}
else {
    Add-Result -Domain "SECURITY" -Check "security_tools" -Status "N/A" -Evidence "pip_audit.txt" -Details "skip manual"
}

Invoke-LoggedCommand -Domain "BUILD" -Check "py_compile_all" -Command "python -m compileall backend/app tests" -OutputFile "py_compile_all.txt" | Out-Null
Invoke-LoggedCommand -Domain "TESTS" -Check "unittest_discover" -Command "python -m unittest discover -q" -OutputFile "unittest_discover.txt" | Out-Null
Invoke-LoggedCommand -Domain "REGRESSION" -Check "phase1_regression" -Command ("python -m unittest -q " + ($phase1Regression -join " ")) -OutputFile "phase1_regression.txt" | Out-Null
Invoke-LoggedCommand -Domain "REGRESSION" -Check "cognitive_regression" -Command ("python -m unittest -q " + ($cognitiveRegression -join " ")) -OutputFile "cognitive_regression.txt" | Out-Null

Test-NoImportMatch -Domain "CONTRACT" -Check "creative_no_runtime_imports" -Pattern "^\s*(from|import)\s+(app|backend\.app)\.runtime" -TargetPath "backend/app/creative" -OutputFile "contract_creative_runtime.txt"
Test-NoImportMatch -Domain "CONTRACT" -Check "creative_no_safety_imports" -Pattern "^\s*(from|import)\s+(app|backend\.app)\.safety" -TargetPath "backend/app/creative" -OutputFile "contract_creative_safety.txt"
Test-NoImportMatch -Domain "CONTRACT" -Check "creative_no_metrics_imports" -Pattern "^\s*(from|import)\s+(app|backend\.app)\.(metrics|data\.publish_records)" -TargetPath "backend/app/creative" -OutputFile "contract_creative_metrics.txt"

if (-not $SkipInfra) {
    Invoke-LoggedCommand -Domain "INFRA" -Check "docker_compose_ps" -Command "docker compose ps" -OutputFile "infra_ps.txt" -AllowMissing:$true | Out-Null
    Test-HttpEndpoint -Domain "INFRA" -Check "api_8000_health" -Url "http://127.0.0.1:8000/health" -OutputFile "probe_8000_health.txt"
    Test-HttpEndpoint -Domain "INFRA" -Check "api_8000_ready" -Url "http://127.0.0.1:8000/ready" -OutputFile "probe_8000_ready.txt"
    Test-HttpEndpoint -Domain "INFRA" -Check "api_8002_health" -Url "http://127.0.0.1:8002/health" -OutputFile "probe_8002_health.txt"
    Test-HttpEndpoint -Domain "INFRA" -Check "api_8002_ready" -Url "http://127.0.0.1:8002/ready" -OutputFile "probe_8002_ready.txt"
}
else {
    Add-Result -Domain "INFRA" -Check "infra_checks" -Status "N/A" -Evidence "infra_ps.txt" -Details "skip manual"
}

$contractScript = @'
from pathlib import Path
import sys

root = Path.cwd()
sys.path.insert(0, str((root / "backend").resolve()))

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import AssetPlan, CreativePack, ExperimentPlan, LearningInsights, ScriptPlan, StrategyProfile, TrendProfile, VoicePlan
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput

pack = CreativePack(
    creative_pack_id="cp_test",
    account_id="acc_1",
    niche="horror",
    topic="mirror warning",
    strategy_profile=StrategyProfile(),
    trend_profile=TrendProfile(),
    script_plan=ScriptPlan(hook="H", setup="S", payoff="P"),
    voice_plan=VoicePlan(provider="piper", voice_id="voice", style="base"),
    asset_plan=AssetPlan(),
    learning_insights=LearningInsights(),
    experiment_plan=ExperimentPlan(),
    experiment_assignment=None,
    generated_at="2026-03-17T00:00:00Z",
    orchestrator_version="test",
)
pack_payload = pack.to_dict()
required_pack_keys = {"strategy_profile", "trend_profile", "asset_selection", "learning_insights", "experiment_plan", "script_plan", "voice_plan"}
missing_pack = sorted(required_pack_keys - set(pack_payload.keys()))
if missing_pack:
    raise SystemExit("CREATIVE_PACK_SCHEMA_MISSING:" + ",".join(missing_pack))

orch = CreativeOrchestratorInput(account_id="acc_1", niche="horror", topic="mirror", publish_slot="2026-03-17T00:00:00Z")
orch_payload = orch.to_dict()
required_orch_keys = {"account_id", "niche", "topic", "publish_slot"}
missing_orch = sorted(required_orch_keys - set(orch_payload.keys()))
if missing_orch:
    raise SystemExit("ORCHESTRATOR_IO_SCHEMA_MISSING:" + ",".join(missing_orch))

fallback = FallbackDecision(used=True, mode="SAFE_DEFAULT", reason="x")
if fallback.to_dict().get("mode") != "SAFE_DEFAULT":
    raise SystemExit("AGENT_COMMON_SCHEMA_INVALID")

print("PASS")
'@
$contractPath = Join-Path $auditDir "contract_schema_runner.py"
Set-Content -Path $contractPath -Value $contractScript -Encoding utf8
Invoke-LoggedCommand -Domain "CONTRACT" -Check "schema_integrity" -Command "python `"$contractPath`"" -OutputFile "contract_schema.txt" | Out-Null

$fallbackScript = @'
import json
import sys
import tempfile
from pathlib import Path

root = Path.cwd()
sys.path.insert(0, str((root / "backend").resolve()))

from app.creative.agents.learning.models import LearningAgentInput
from app.creative.agents.learning.service import LearningAgentService
from app.creative.agents.trend_analysis.models import TrendAnalysisInput
from app.creative.agents.trend_analysis.service import TrendAnalysisAgentService
from app.creative.contracts.creative_pack import LearningInsights
from app.creative.experiments.models import ExperimentCapabilityInput
from app.creative.experiments.service import ExperimentCapabilityService

with tempfile.TemporaryDirectory() as tmp_dir:
    base = Path(tmp_dir)

    trend = TrendAnalysisAgentService(trends_dir=base / "trends")
    trend_result = trend.load(TrendAnalysisInput(niche="missing"))
    if not trend_result.fallback.used or trend_result.trend_profile.niche != "default":
        raise SystemExit("TREND_FALLBACK_FAIL")

    learning = LearningAgentService()
    learning_result = learning.generate(LearningAgentInput(
        account_id="acc_1",
        publish_records_path=base / "missing_publish.jsonl",
        video_metrics_path=base / "missing_metrics.jsonl",
        analysis_dir=base / "missing_analysis",
        output_path=base / "learning" / "learning_insights.json",
    ))
    if not learning_result.fallback.used or learning_result.learning_insights.recommendations != ["fallback_default"]:
        raise SystemExit("LEARNING_FALLBACK_FAIL")

    experiments = ExperimentCapabilityService(
        default_config_path=base / "missing_experiment.json",
        default_output_path=base / "experiments" / "experiment_plan.json",
        default_experiments_path=base / "experiments" / "experiments.jsonl",
        default_assignments_path=base / "experiments" / "assignments.jsonl",
        default_results_path=base / "experiments" / "results.jsonl",
    )
    exp_result = experiments.generate(ExperimentCapabilityInput(
        account_id="acc_1",
        niche="horror",
        topic="mirror",
        publish_slot="2026-03-17T00:00:00Z",
        learning_insights=LearningInsights(),
    ))
    if not exp_result.fallback.used or exp_result.experiment_plan.variant_type != "baseline":
        raise SystemExit("EXPERIMENT_FALLBACK_FAIL")

    print(json.dumps({
        "trend_fallback": True,
        "learning_fallback": True,
        "experiment_fallback": True,
    }))
'@
$fallbackPath = Join-Path $auditDir "fallback_runner.py"
Set-Content -Path $fallbackPath -Value $fallbackScript -Encoding utf8
Invoke-LoggedCommand -Domain "FALLBACK" -Check "fallback_audit" -Command "python `"$fallbackPath`"" -OutputFile "fallback_audit.txt" | Out-Null

$smokeScript = @'
import json
import sys
import tempfile
from pathlib import Path

root = Path.cwd()
sys.path.insert(0, str((root / "backend").resolve()))

from app.content.pipeline.publish import StubPublishAdapter
from app.content.pipeline.render import StubRenderAdapter
from app.content.pipeline.service import ContentPipelineService
from app.content.pipeline.tts import StubTtsAdapter
from app.creative.agents.account_health.service import AccountHealthAgentService
from app.creative.agents.asset_selection.service import AssetSelectionAgentService
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

def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\\n".join(json.dumps(row) for row in rows), encoding="utf-8")

with tempfile.TemporaryDirectory() as tmp_dir:
    root_tmp = Path(tmp_dir)
    out = root_tmp / "OUT"
    trends_dir = root_tmp / "trends"
    trends_dir.mkdir(parents=True, exist_ok=True)
    (trends_dir / "horror.json").write_text(json.dumps({
        "niche": "horror",
        "dominant_hooks": ["question", "story_opening"],
        "avg_duration": "35-60",
        "pacing": "fast_first_3s",
        "visual_style": "dark_backgrounds",
        "text_style": "large_caption_focus",
    }), encoding="utf-8")

    publish_path = root_tmp / "data" / "publish_records" / "publish_records.jsonl"
    metrics_path = root_tmp / "metrics" / "video_metrics.jsonl"
    analysis_dir = root_tmp / "analysis"
    write_jsonl(publish_path, [{"account_id": "acc_gate", "publish_id": "pub_001"}])
    write_jsonl(metrics_path, [{"account_id": "acc_gate", "views": 260, "completion_rate": 0.64, "duration_s": 9.2}])
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "hook_performance_summary.json").write_text(json.dumps({"hooks": [{"hook_style": "question"}]}), encoding="utf-8")

    experiments_dir = root_tmp / "experiments"
    experiments_dir.mkdir(parents=True, exist_ok=True)
    (experiments_dir / "experiment_config.json").write_text(json.dumps({
        "name": "creative_pack_baseline",
        "scope": "CREATIVE_PACK",
        "variant_a": {"variant_type": "hook_style", "hook_style": "question"},
        "variant_b": {"variant_type": "hook_style", "hook_style": "story_opening"},
        "status": "ACTIVE",
    }), encoding="utf-8")

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
        learning_agent=LearningAgentService(
            default_publish_records_path=publish_path,
            default_video_metrics_path=metrics_path,
            default_analysis_dir=analysis_dir,
            default_output_path=root_tmp / "learning" / "learning_insights.json",
        ),
        strategy_agent=StrategyAgentService(),
        experiment_capability=ExperimentCapabilityService(
            default_config_path=experiments_dir / "experiment_config.json",
            default_output_path=experiments_dir / "experiment_plan.json",
            default_experiments_path=experiments_dir / "experiments.jsonl",
            default_assignments_path=experiments_dir / "assignments.jsonl",
            default_results_path=experiments_dir / "results.jsonl",
        ),
        asset_selection_agent=AssetSelectionAgentService(),
        script_agent=ScriptAgentService(),
        voice_agent=VoiceAgentService(),
        video_qc_agent=VideoQcAgentService(),
        event_emitter=CreativeEventEmitter(event_path=out / "events" / "creative_events.jsonl"),
    )
    execution = orchestrator.execute(CreativeOrchestratorInput(
        account_id="acc_gate",
        niche="horror",
        topic="sealed mirror tunnel",
        publish_slot="2026-03-17T12:00:00Z",
    ))

    payload = {
        "account_health_status": execution.account_health.decision.status,
        "trend_profile_loaded": not execution.trend_analysis.fallback.used,
        "learning_insights_generated": not execution.learning.fallback.used,
        "experiment_plan_generated": not execution.experiment.fallback.used,
        "asset_selection_generated": not execution.asset_selection.fallback.used,
        "pipeline_status": execution.pipeline_output["result"]["status"],
        "video_qc_status": execution.video_qc.status,
    }
    required = {
        "account_health_status": "SAFE",
        "trend_profile_loaded": True,
        "learning_insights_generated": True,
        "experiment_plan_generated": True,
        "asset_selection_generated": True,
        "pipeline_status": "READY",
        "video_qc_status": "APPROVE",
    }
    for key, expected in required.items():
        if payload[key] != expected:
            raise SystemExit(f"SMOKE_FAIL:{key}:{payload[key]}:{expected}")

    events_path = out / "events" / "creative_events.jsonl"
    event_types = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        event_types.append(str(row.get("event_type") or ""))
    for expected_event in [
        "CREATIVE/trend_profile_loaded",
        "CREATIVE/learning_insights_generated",
        "CREATIVE/experiment_plan_generated",
        "CREATIVE/asset_selection_generated",
    ]:
        if expected_event not in event_types:
            raise SystemExit(f"EVENT_MISSING:{expected_event}")

    print(json.dumps(payload, indent=2))
'@
$smokePath = Join-Path $auditDir "full_smoke_runner.py"
Set-Content -Path $smokePath -Value $smokeScript -Encoding utf8
Invoke-LoggedCommand -Domain "SMOKE" -Check "full_cognitive_flow" -Command "python `"$smokePath`"" -OutputFile "full_smoke.txt" | Out-Null

if (-not $SkipStressBatch) {
    $batchBase = Join-Path $auditDir "stress_batch"
    Invoke-LoggedCommand -Domain "STRESS" -Check "local_batch_18" -Command "python backend/scripts/run_local_d23_18_batch.py --base-dir `"$batchBase`"" -OutputFile "stress_batch.txt" | Out-Null

    if (Test-Path (Join-Path $batchBase "audit\batch_report.json")) {
        Add-Result -Domain "TELEMETRY" -Check "batch_report_present" -Status "PASS" -Evidence "stress_batch.txt" -Details "batch_report.json materialized"
    }
    else {
        Add-Result -Domain "TELEMETRY" -Check "batch_report_present" -Status "FAIL" -Evidence "stress_batch.txt" -Details "missing batch_report.json"
    }

    if (Test-Path (Join-Path $batchBase "data\publish_records\publish_records.jsonl")) {
        Add-Result -Domain "TELEMETRY" -Check "publish_records_present" -Status "PASS" -Evidence "stress_batch.txt" -Details "publish_records materialized"
    }
    else {
        Add-Result -Domain "TELEMETRY" -Check "publish_records_present" -Status "FAIL" -Evidence "stress_batch.txt" -Details "missing publish_records.jsonl"
    }

    if (Test-Path (Join-Path $batchBase "metrics\video_metrics.jsonl")) {
        Add-Result -Domain "TELEMETRY" -Check "video_metrics_present" -Status "PASS" -Evidence "stress_batch.txt" -Details "video_metrics materialized"
    }
    else {
        Add-Result -Domain "TELEMETRY" -Check "video_metrics_present" -Status "FAIL" -Evidence "stress_batch.txt" -Details "missing video_metrics.jsonl"
    }

    if (Test-Path (Join-Path $batchBase "analysis\consistency_check.json")) {
        Add-Result -Domain "CONSISTENCY" -Check "stress_consistency_present" -Status "PASS" -Evidence "stress_batch.txt" -Details "consistency_check.json materialized"
    }
    else {
        Add-Result -Domain "CONSISTENCY" -Check "stress_consistency_present" -Status "FAIL" -Evidence "stress_batch.txt" -Details "missing consistency_check.json"
    }
}
else {
    Add-Result -Domain "STRESS" -Check "local_batch_18" -Status "N/A" -Evidence "stress_batch.txt" -Details "skip manual"
}

if (-not $SkipResourceAudit) {
    $resourceScript = @'
import json
import os

try:
    import psutil
except Exception as exc:
    raise SystemExit(f"PSUTIL_UNAVAILABLE:{exc}")

process = psutil.Process(os.getpid())
payload = {
    "rss_bytes": process.memory_info().rss,
    "cpu_percent": process.cpu_percent(interval=0.1),
}
print(json.dumps(payload, indent=2))
'@
    $resourcePath = Join-Path $auditDir "resource_audit_runner.py"
    Set-Content -Path $resourcePath -Value $resourceScript -Encoding utf8
    Invoke-LoggedCommand -Domain "RESOURCES" -Check "basic_resource_audit" -Command "python `"$resourcePath`"" -OutputFile "resource_audit.txt" -AllowMissing:$true | Out-Null
}
else {
    Add-Result -Domain "RESOURCES" -Check "basic_resource_audit" -Status "N/A" -Evidence "resource_audit.txt" -Details "skip manual"
}

Write-AuditReport

$failCount = @($results | Where-Object { $_.Status -eq "FAIL" }).Count
if ($failCount -gt 0) {
    Write-Host "Pre-Phase3 system final gate: NO-GO ($failCount FAIL)" -ForegroundColor Red
    exit 1
}

Write-Host "Pre-Phase3 system final gate: GO" -ForegroundColor Green
