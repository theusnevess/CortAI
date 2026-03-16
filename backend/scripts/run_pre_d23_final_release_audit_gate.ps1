param(
    [string]$OutputDir = "OUT/audit/pre_d23_final_gate",
    [switch]$SkipInfra,
    [switch]$SkipSecurity,
    [switch]$SkipVideoQc
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

    if ($AllowMissing -and $text -match "not recognized|No module named|cannot find") {
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

function Write-AuditReport {
    $reportPath = Join-Path $auditDir "AUDIT_REPORT.md"
    $failCount = @($results | Where-Object { $_.Status -eq "FAIL" }).Count
    $summary = if ($failCount -eq 0) { "GO" } else { "NO-GO" }

    $lines = @()
    $lines += "# Pre-D23 Final Release Audit Gate"
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

$unitTests = @(
    "tests.test_content_pipeline_d27_unittest",
    "tests.test_platform_safety_d28_unittest",
    "tests.test_creative_pack_generator_d29_unittest",
    "tests.test_platform_intelligence_d30_unittest",
    "tests.test_experiment_framework_d31_unittest",
    "tests.test_content_attribution_d32_unittest",
    "tests.test_metrics_collector_d33_unittest",
    "tests.test_analysis_research_layer_d34_unittest",
    "tests.test_offline_simulation_engine_d37_unittest",
    "tests.test_data_consistency_checker_d38_unittest",
    "tests.test_script_generation_unittest",
    "tests.test_screen_text_adapter_unittest",
    "tests.test_publish_records_d3_unittest",
    "tests.test_real_batch_rollout_d23_unittest"
)

$smokeTests = @(
    @{ Domain = "SMOKE"; Check = "scheduler_runtime_d23"; Test = "tests.test_real_batch_rollout_d23_unittest" },
    @{ Domain = "SMOKE"; Check = "safety_gate_d28"; Test = "tests.test_platform_safety_d28_unittest" },
    @{ Domain = "SMOKE"; Check = "pipeline_d27"; Test = "tests.test_content_pipeline_d27_unittest" },
    @{ Domain = "SMOKE"; Check = "publish_records"; Test = "tests.test_publish_records_d3_unittest" },
    @{ Domain = "SMOKE"; Check = "metrics_collector"; Test = "tests.test_metrics_collector_d33_unittest" }
)

Invoke-LoggedCommand `
    -Domain "BUILD" `
    -Check "py_compile" `
    -Command "python -m compileall backend/app" `
    -OutputFile "py_compile.txt" | Out-Null

Invoke-LoggedCommand `
    -Domain "TESTS" `
    -Check "unit_tests" `
    -Command ("python -m unittest -q " + ($unitTests -join " ")) `
    -OutputFile "unit_tests.txt" | Out-Null

Invoke-LoggedCommand `
    -Domain "TESTS" `
    -Check "regression_tests" `
    -Command "python -m unittest -q tests.test_script_generation_unittest tests.test_screen_text_adapter_unittest tests.test_content_pipeline_d27_unittest" `
    -OutputFile "regression_tests.txt" | Out-Null

Test-NoImportMatch `
    -Domain "CONTRACT" `
    -Check "pipeline_no_runtime_imports" `
    -Pattern "^\s*(from|import)\s+(app|backend\.app)\.runtime" `
    -TargetPath "backend/app/content/pipeline" `
    -OutputFile "contract_pipeline_runtime.txt"

Test-NoImportMatch `
    -Domain "CONTRACT" `
    -Check "pipeline_no_safety_imports" `
    -Pattern "^\s*(from|import)\s+(app|backend\.app)\.safety" `
    -TargetPath "backend/app/content/pipeline" `
    -OutputFile "contract_pipeline_safety.txt"

Test-NoImportMatch `
    -Domain "CONTRACT" `
    -Check "analysis_no_runtime_or_pipeline_imports" `
    -Pattern "^\s*(from|import)\s+(app|backend\.app)\.(runtime|content\.pipeline)" `
    -TargetPath "backend/app/analysis" `
    -OutputFile "contract_analysis_imports.txt"

if (-not $SkipInfra) {
    Invoke-LoggedCommand `
        -Domain "INFRA" `
        -Check "docker_compose_ps" `
        -Command "docker compose ps" `
        -OutputFile "infra_health.txt" `
        -AllowMissing:$true | Out-Null

    Test-HttpEndpoint -Domain "INFRA" -Check "api_8000_health" -Url "http://127.0.0.1:8000/health" -OutputFile "probe_8000_health.txt"
    Test-HttpEndpoint -Domain "INFRA" -Check "api_8000_ready" -Url "http://127.0.0.1:8000/ready" -OutputFile "probe_8000_ready.txt"
    Test-HttpEndpoint -Domain "INFRA" -Check "api_8002_health" -Url "http://127.0.0.1:8002/health" -OutputFile "probe_8002_health.txt"
    Test-HttpEndpoint -Domain "INFRA" -Check "api_8002_ready" -Url "http://127.0.0.1:8002/ready" -OutputFile "probe_8002_ready.txt"
}
else {
    Add-Result -Domain "INFRA" -Check "infra_checks" -Status "N/A" -Evidence "infra_health.txt" -Details "skip manual"
}

if (-not $SkipSecurity) {
    Invoke-LoggedCommand `
        -Domain "SECURITY" `
        -Check "pip_check" `
        -Command "python -m pip check" `
        -OutputFile "security_scan.txt" | Out-Null

    Invoke-LoggedCommand `
        -Domain "SECURITY" `
        -Check "pip_audit" `
        -Command "pip-audit" `
        -OutputFile "pip_audit.txt" `
        -AllowMissing:$true | Out-Null

    Invoke-LoggedCommand `
        -Domain "SECURITY" `
        -Check "gitleaks" `
        -Command "gitleaks detect --source . --no-git --config .gitleaks.toml" `
        -OutputFile "gitleaks.txt" `
        -AllowMissing:$true | Out-Null
}
else {
    Add-Result -Domain "SECURITY" -Check "security_scans" -Status "N/A" -Evidence "security_scan.txt" -Details "skip manual"
}

$smokeLog = Join-Path $auditDir "smoke_runtime_checks.txt"
$smokeLines = @()
foreach ($smoke in $smokeTests) {
    $cmd = "python -m unittest -q $($smoke.Test)"
    $output = ""
    $exitCode = 0
    try {
        $output = (& cmd.exe /d /c "$cmd 2>&1" | Out-String)
        $exitCode = $LASTEXITCODE
    }
    catch {
        $output = ($_ | Out-String)
        $exitCode = 1
    }
    $smokeLines += "## $($smoke.Check)"
    $smokeLines += $output
    if ($exitCode -eq 0) {
        Add-Result -Domain $smoke.Domain -Check $smoke.Check -Status "PASS" -Evidence "smoke_runtime_checks.txt" -Details $smoke.Test
    }
    else {
        Add-Result -Domain $smoke.Domain -Check $smoke.Check -Status "FAIL" -Evidence "smoke_runtime_checks.txt" -Details $smoke.Test
    }
}
Set-Content -Path $smokeLog -Value ($smokeLines -join "`n") -Encoding utf8

if (-not $SkipVideoQc) {
    $videoQcScript = @'
from pathlib import Path
import json
import sys

root = Path.cwd()
sys.path.insert(0, str((root / "backend").resolve()))

from app.content.pipeline.models import ExecutionEnvelope
from app.content.pipeline.publish import StubPublishAdapter
from app.content.pipeline.render import StubRenderAdapter
from app.content.pipeline.service import ContentPipelineService
from app.content.pipeline.tts import StubTtsAdapter

audit_dir = root / "OUT" / "audit" / "pre_d23_final_gate"
content_dir = audit_dir / "content_qc"
event_path = audit_dir / "events" / "events.jsonl"

service = ContentPipelineService(
    tts_adapter=StubTtsAdapter(base_dir=content_dir),
    render_adapter=StubRenderAdapter(base_dir=content_dir),
    publish_adapter=StubPublishAdapter(),
    event_path=event_path,
)

scripts = [
    "Someone wrote on the mirror. Who left the warning? The door wouldn't open.",
    "The red phone started ringing again. No one could explain why it had power. A voice whispered an empty room number.",
    "One timetable kept changing after midnight. No employee admitted touching it. Final departure to a station that never existed.",
]

results = []
for index, script in enumerate(scripts, start=1):
    envelope = ExecutionEnvelope(
        job_id=f"job_qc_{index}",
        account_id="acc_qc",
        creative_pack_id=f"cp_qc_{index}",
        publish_slot=f"2026-03-15T1{index}:00:00Z",
        experiment_variant="A",
    )
    result = service.execute(envelope, script_text=script, caption="caption", hashtags=["#qc"])
    render_job_id = result["result"]["render_job_id"]
    metadata_path = content_dir / "metadata" / f"{render_job_id}.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    cues = metadata["subtitle_cues"]
    if metadata["render_duration_s"] < 8.0:
        raise SystemExit(f"render_duration_s below minimum for {render_job_id}")
    if not Path(metadata["audio_path"]).exists():
        raise SystemExit(f"missing audio for {render_job_id}")
    if len(cues) != 3:
        raise SystemExit(f"expected 3 cues for {render_job_id}")
    if any(not cue["text"].strip() for cue in cues):
        raise SystemExit(f"empty cue for {render_job_id}")
    if any(cue["start"] >= cue["end"] for cue in cues):
        raise SystemExit(f"invalid cue timing for {render_job_id}")
    results.append({
        "render_job_id": render_job_id,
        "video_path": result["result"]["artifacts"]["video"],
        "audio_path": result["result"]["artifacts"]["audio"],
        "timings": metadata["timings"],
        "subtitle_cues": cues,
    })

(audit_dir / "video_batch_qc.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print("PASS")
'@
    $videoQcPath = Join-Path $auditDir "video_qc_runner.py"
    Set-Content -Path $videoQcPath -Value $videoQcScript -Encoding utf8
    Invoke-LoggedCommand `
        -Domain "VIDEO" `
        -Check "video_batch_qc" `
        -Command "python `"$videoQcPath`"" `
        -OutputFile "video_batch_qc.txt" | Out-Null
}
else {
    Add-Result -Domain "VIDEO" -Check "video_batch_qc" -Status "N/A" -Evidence "video_batch_qc.txt" -Details "skip manual"
}

$consistencyScript = @'
from pathlib import Path
import sys

root = Path.cwd()
sys.path.insert(0, str((root / "backend").resolve()))

from app.analysis.consistency.service import DataConsistencyCheckerService

audit_dir = root / "OUT" / "audit" / "pre_d23_final_gate"
service = DataConsistencyCheckerService(analysis_dir=audit_dir)
summary = service.generate_consistency_report()
print(summary.status)
'@
$consistencyPath = Join-Path $auditDir "consistency_runner.py"
Set-Content -Path $consistencyPath -Value $consistencyScript -Encoding utf8
Invoke-LoggedCommand `
    -Domain "CONSISTENCY" `
    -Check "consistency_report" `
    -Command "python `"$consistencyPath`"" `
    -OutputFile "consistency_runner.txt" | Out-Null

if (Test-Path (Join-Path $auditDir "consistency_check.json")) {
    Add-Result -Domain "CONSISTENCY" -Check "consistency_json_present" -Status "PASS" -Evidence "consistency_check.json" -Details "materialized"
}
else {
    Add-Result -Domain "CONSISTENCY" -Check "consistency_json_present" -Status "FAIL" -Evidence "consistency_check.json" -Details "missing"
}

if (Test-Path (Join-Path $auditDir "consistency_check.md")) {
    Add-Result -Domain "CONSISTENCY" -Check "consistency_md_present" -Status "PASS" -Evidence "consistency_check.md" -Details "materialized"
}
else {
    Add-Result -Domain "CONSISTENCY" -Check "consistency_md_present" -Status "FAIL" -Evidence "consistency_check.md" -Details "missing"
}

Write-AuditReport

$failCount = @($results | Where-Object { $_.Status -eq "FAIL" }).Count
if ($failCount -gt 0) {
    Write-Host "Pre-D23 final audit gate: NO-GO ($failCount FAIL)" -ForegroundColor Red
    exit 1
}

Write-Host "Pre-D23 final audit gate: GO" -ForegroundColor Green
