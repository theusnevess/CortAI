$ErrorActionPreference = "Stop"

$auditDir = Join-Path "OUT/audit" "pre_d23_full_gate"
New-Item -ItemType Directory -Force -Path $auditDir | Out-Null

$script:Failures = New-Object System.Collections.Generic.List[string]
$script:NotInBase = New-Object System.Collections.Generic.List[string]
$script:Passes = New-Object System.Collections.Generic.List[string]

if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) { return }
        $parts = $line -split "=", 2
        if ($parts.Count -eq 2) {
            [System.Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim())
        }
    }
}

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "==== $Title ===="
}

function Add-Pass {
    param([string]$Message)
    $script:Passes.Add($Message) | Out-Null
    Write-Host "PASS: $Message"
}

function Add-Failure {
    param([string]$Message)
    $script:Failures.Add($Message) | Out-Null
    Write-Host "FAIL: $Message"
}

function Add-NotInBase {
    param([string]$Message)
    $script:NotInBase.Add($Message) | Out-Null
    Write-Host "NOT_IN_BASE: $Message"
}

function Write-LogHeader {
    param(
        [string]$Path,
        [string]$Title,
        [string]$Command
    )
    @"
TITLE: $Title
COMMAND: $Command
TIMESTAMP: $(Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")

"@ | Set-Content -Path $Path -Encoding UTF8
}

function Invoke-LoggedCommand {
    param(
        [string]$Title,
        [string]$Command,
        [string]$OutFile
    )
    Write-Host $Title
    Write-LogHeader -Path $OutFile -Title $Title -Command $Command
    try {
        $oldPref = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $output = & ([scriptblock]::Create($Command)) 2>&1
        $exitCode = $LASTEXITCODE
        $ErrorActionPreference = $oldPref
        if ($null -ne $output) {
            $output | Tee-Object -FilePath $OutFile -Append | Out-Host
        }
        if ($exitCode -ne 0) {
            Add-Failure "$Title exited with code $exitCode"
            return $false
        }
        Add-Pass $Title
        return $true
    } catch {
        $_ | Out-String | Tee-Object -FilePath $OutFile -Append | Out-Host
        Add-Failure "$Title threw: $($_.Exception.Message)"
        return $false
    }
}

function Invoke-UnittestModule {
    param(
        [string]$TestFile,
        [string]$ModuleName,
        [string]$OutFile,
        [bool]$Required = $true
    )
    if (-not (Test-Path $TestFile)) {
        $message = "$ModuleName ($TestFile) not present in this base"
        Write-LogHeader -Path $OutFile -Title "unittest $ModuleName" -Command "python -m unittest -q $ModuleName"
        "NOT_IN_BASE: $message" | Add-Content -Path $OutFile -Encoding UTF8
        if ($Required) {
            Add-NotInBase $message
        } else {
            Add-Pass "optional not-in-base: $message"
        }
        return $false
    }
    return (Invoke-LoggedCommand -Title "unittest $ModuleName" -Command "python -m unittest -q $ModuleName" -OutFile $OutFile)
}

function Invoke-HttpCheck {
    param(
        [string]$Url,
        [string]$Label,
        [string]$OutFile
    )
    Write-Host $Label
    Write-LogHeader -Path $OutFile -Title $Label -Command "Invoke-WebRequest $Url"
    try {
        $resp = Invoke-WebRequest $Url -UseBasicParsing
        "STATUS=$($resp.StatusCode)" | Add-Content -Path $OutFile -Encoding UTF8
        if ($resp.Content) {
            $resp.Content | Add-Content -Path $OutFile -Encoding UTF8
        }
        if ($resp.StatusCode -ne 200) {
            Add-Failure "$Label returned status $($resp.StatusCode)"
            return $false
        }
        Add-Pass $Label
        return $true
    } catch {
        $_.Exception.Message | Add-Content -Path $OutFile -Encoding UTF8
        Add-Failure "$Label failed: $($_.Exception.Message)"
        return $false
    }
}

function Assert-ReadyPayload {
    param(
        [string]$Path,
        [string]$Label
    )
    if (-not (Test-Path $Path)) {
        Add-Failure "$Label payload file missing"
        return
    }
    try {
        $raw = Get-Content $Path -Raw
        $jsonStart = $raw.IndexOf("{")
        if ($jsonStart -lt 0) {
            Add-Failure "$Label payload does not contain JSON"
            return
        }
        $payload = ($raw.Substring($jsonStart) | ConvertFrom-Json)
        $payloadOk = (
            $payload.ready -eq $true -and
            $payload.scheduler -eq "ok" -and
            [int]$payload.workers -ge 1 -and
            $payload.queue -eq "ok" -and
            $payload.event_index -eq "ok" -and
            $payload.hot_store -eq "ok"
        )
        if ($payloadOk) {
            Add-Pass "$Label payload"
        } else {
            Add-Failure "$Label payload missing expected readiness fields"
        }
    } catch {
        Add-Failure "$Label payload parse failed: $($_.Exception.Message)"
    }
}

function Write-AuditReport {
    param([string]$Status)

    $notInBaseBlock = if ($script:NotInBase.Count -gt 0) {
        ($script:NotInBase | ForEach-Object { "- $_" }) -join "`n"
    } else {
        "- none"
    }
    $failureBlock = if ($script:Failures.Count -gt 0) {
        ($script:Failures | ForEach-Object { "- $_" }) -join "`n"
    } else {
        "- none"
    }
    $passBlock = if ($script:Passes.Count -gt 0) {
        ($script:Passes | ForEach-Object { "- $_" }) -join "`n"
    } else {
        "- none"
    }

    @"
# Pre-D23 Full Gate

- Status: $Status
- Generated at: $(Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")
- Evidence dir: `$auditDir`
- Passed checks: $($script:Passes.Count)
- Failed checks: $($script:Failures.Count)
- Not-in-base items: $($script:NotInBase.Count)

## Failures
$failureBlock

## Not In Base
$notInBaseBlock

## Passed Checks
$passBlock

## Notes
- Not-in-base items are informational for this branch and do not block PASS.
- Failures represent problems in code, infra, security, or evidence that this branch actually supports.
"@ | Set-Content -Path (Join-Path $auditDir "AUDIT_REPORT.md") -Encoding UTF8
}

$contentPipelineInBase = (Test-Path "tests/test_content_pipeline_d27_unittest.py") -or ((Get-ChildItem "backend/app/content/pipeline" -File -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0)
$safetyInBase = (Test-Path "tests/test_platform_safety_d28_unittest.py") -or ((Get-ChildItem "backend/app/safety" -File -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0)
$analysisInBase = Test-Path "tests/test_analysis_research_layer_d34_unittest.py"

Write-Section "CORTAI PRE-D23 FULL GATE"

Write-Section "1. TESTES UNITARIOS E REGRESSOES"
$unitLog = Join-Path $auditDir "unit_and_regression_tests.txt"
"Pre-D23 unit and regression gate`nGenerated at: $(Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")`n" | Set-Content -Path $unitLog -Encoding UTF8
$testGroups = @(
    @{ File = "tests/test_content_pipeline_d27_unittest.py"; Module = "tests.test_content_pipeline_d27_unittest"; Required = $true },
    @{ File = "tests/test_platform_safety_d28_unittest.py"; Module = "tests.test_platform_safety_d28_unittest"; Required = $true },
    @{ File = "tests/test_creative_pack_generator_d29_unittest.py"; Module = "tests.test_creative_pack_generator_d29_unittest"; Required = $true },
    @{ File = "tests/test_platform_intelligence_d30_unittest.py"; Module = "tests.test_platform_intelligence_d30_unittest"; Required = $true },
    @{ File = "tests/test_experiment_framework_d31_unittest.py"; Module = "tests.test_experiment_framework_d31_unittest"; Required = $true },
    @{ File = "tests/test_content_attribution_d32_unittest.py"; Module = "tests.test_content_attribution_d32_unittest"; Required = $true },
    @{ File = "tests/test_metrics_collector_d33_unittest.py"; Module = "tests.test_metrics_collector_d33_unittest"; Required = $true },
    @{ File = "tests/test_analysis_research_layer_d34_unittest.py"; Module = "tests.test_analysis_research_layer_d34_unittest"; Required = $true },
    @{ File = "tests/test_content_template_library_d36_unittest.py"; Module = "tests.test_content_template_library_d36_unittest"; Required = $true },
    @{ File = "tests/test_offline_simulation_engine_d37_unittest.py"; Module = "tests.test_offline_simulation_engine_d37_unittest"; Required = $true },
    @{ File = "tests/test_data_consistency_checker_d38_unittest.py"; Module = "tests.test_data_consistency_checker_d38_unittest"; Required = $true },
    @{ File = "tests/test_publish_records_d3_unittest.py"; Module = "tests.test_publish_records_d3_unittest"; Required = $true },
    @{ File = "tests/test_event_index_d16_unittest.py"; Module = "tests.test_event_index_d16_unittest"; Required = $true },
    @{ File = "tests/test_event_query_forensics_and_scanner_d13_unittest.py"; Module = "tests.test_event_query_forensics_and_scanner_d13_unittest"; Required = $true },
    @{ File = "tests/test_event_query_trace_builder_d13_unittest.py"; Module = "tests.test_event_query_trace_builder_d13_unittest"; Required = $true },
    @{ File = "tests/test_event_query_seek_pagination_d14_unittest.py"; Module = "tests.test_event_query_seek_pagination_d14_unittest"; Required = $true },
    @{ File = "tests/test_event_query_api_endpoint_d15_unittest.py"; Module = "tests.test_event_query_api_endpoint_d15_unittest"; Required = $true },
    @{ File = "tests/test_operator_console_d24_unittest.py"; Module = "tests.test_operator_console_d24_unittest"; Required = $true },
    @{ File = "tests/test_operator_actions_d24_5_unittest.py"; Module = "tests.test_operator_actions_d24_5_unittest"; Required = $true },
    @{ File = "tests/test_strategy_observatory_d26_unittest.py"; Module = "tests.test_strategy_observatory_d26_unittest"; Required = $true }
)
foreach ($group in $testGroups) {
    $safeName = ($group.Module -replace "[^A-Za-z0-9_.-]", "_")
    $outFile = Join-Path $auditDir "$safeName.txt"
    Invoke-UnittestModule -TestFile $group.File -ModuleName $group.Module -OutFile $outFile -Required $group.Required | Out-Null
    Get-Content $outFile | Add-Content -Path $unitLog -Encoding UTF8
    "`n-----`n" | Add-Content -Path $unitLog -Encoding UTF8
}

Write-Section "2. COMPILACAO"
Invoke-LoggedCommand `
    -Title "py_compile backend/app/**/*.py" `
    -Command 'Get-ChildItem backend/app -Recurse -Filter *.py | ForEach-Object { python -m py_compile $_.FullName }' `
    -OutFile (Join-Path $auditDir "py_compile.txt") | Out-Null

Write-Section "3. INFRA E RUNTIME"
Invoke-HttpCheck -Url "http://localhost:8000/health" -Label "8000 /health" -OutFile (Join-Path $auditDir "health_8000.txt") | Out-Null
Invoke-HttpCheck -Url "http://localhost:8000/ready" -Label "8000 /ready" -OutFile (Join-Path $auditDir "ready_8000.txt") | Out-Null
Invoke-HttpCheck -Url "http://localhost:8002/health" -Label "8002 /health" -OutFile (Join-Path $auditDir "health_8002.txt") | Out-Null
Invoke-HttpCheck -Url "http://localhost:8002/ready" -Label "8002 /ready" -OutFile (Join-Path $auditDir "ready_8002.txt") | Out-Null
Assert-ReadyPayload -Path (Join-Path $auditDir "ready_8000.txt") -Label "8000 /ready"
Assert-ReadyPayload -Path (Join-Path $auditDir "ready_8002.txt") -Label "8002 /ready"

Invoke-LoggedCommand `
    -Title "postgres connectivity" `
    -Command 'docker exec cortai_db psql -U cortai_app -d cortai -c "SELECT current_user, current_database();"' `
    -OutFile (Join-Path $auditDir "postgres_check.txt") | Out-Null
Invoke-LoggedCommand `
    -Title "redis auth" `
    -Command "docker exec cortai_redis redis-cli -a $env:REDIS_PASSWORD ping" `
    -OutFile (Join-Path $auditDir "redis_check.txt") | Out-Null
Invoke-LoggedCommand `
    -Title "minio readwrite" `
    -Command "docker exec cortai_minio /bin/sh -lc ""mc alias set cortai http://127.0.0.1:9000 $env:MINIO_ROOT_USER $env:MINIO_ROOT_PASSWORD >/dev/null; mc ls cortai""" `
    -OutFile (Join-Path $auditDir "minio_check.txt") | Out-Null

Write-Section "4. SEGURANCA"
Invoke-LoggedCommand -Title "pip-audit" -Command "pip-audit" -OutFile (Join-Path $auditDir "pip_audit.txt") | Out-Null
Invoke-LoggedCommand -Title "pip check" -Command "pip check" -OutFile (Join-Path $auditDir "pip_check.txt") | Out-Null
if (Get-Command gitleaks -ErrorAction SilentlyContinue) {
    Invoke-LoggedCommand -Title "gitleaks" -Command "gitleaks detect --source . -v" -OutFile (Join-Path $auditDir "gitleaks.txt") | Out-Null
} else {
    Write-LogHeader -Path (Join-Path $auditDir "gitleaks.txt") -Title "gitleaks" -Command "gitleaks detect --source . -v"
    "FAIL: gitleaks command not found" | Add-Content -Path (Join-Path $auditDir "gitleaks.txt") -Encoding UTF8
    Add-Failure "gitleaks command not found"
}

$configChecks = @()
if ($env:DB_USER -eq "cortai_app" -and $env:DB_NAME -eq "cortai") { $configChecks += "postgres dedicated user/db ok" } else { Add-Failure "Postgres env not using dedicated user/db" }
if ($env:MINIO_ROOT_USER -and $env:MINIO_ROOT_USER -ne "minioadmin") { $configChecks += "minio dedicated credentials ok" } else { Add-Failure "MinIO still using default user" }
if ($env:REDIS_URL -match "^redis://:.+@") { $configChecks += "redis auth configured" } else { Add-Failure "Redis URL missing auth" }
if ($configChecks.Count -gt 0) {
    $configChecks | Set-Content -Path (Join-Path $auditDir "config_hardening.txt") -Encoding UTF8
    Add-Pass "config hardening checks"
}

Write-Section "5. CONSISTENCIA E GOVERNANCA"
$consistencyTestOut = Join-Path $auditDir "consistency_report.txt"
Invoke-UnittestModule -TestFile "tests/test_data_consistency_checker_d38_unittest.py" -ModuleName "tests.test_data_consistency_checker_d38_unittest" -OutFile $consistencyTestOut -Required $true | Out-Null
if (Test-Path "OUT/analysis/consistency_check.json") {
    Copy-Item "OUT/analysis/consistency_check.json" (Join-Path $auditDir "consistency_check.json") -Force
    Add-Pass "consistency_check.json present"
} else {
    Add-Failure "OUT/analysis/consistency_check.json not found"
}
if (Test-Path "OUT/analysis/consistency_check.md") {
    Copy-Item "OUT/analysis/consistency_check.md" (Join-Path $auditDir "consistency_check.md") -Force
    Add-Pass "consistency_check.md present"
} else {
    Add-Failure "OUT/analysis/consistency_check.md not found"
}

Write-Section "6. TELEMETRIA E EVENTOS"
$eventSanityPath = Join-Path $auditDir "event_sanity.txt"
$eventHits = @{
    "CONTENT/tts_started" = (rg -n "CONTENT/tts_started" tests backend/app | Measure-Object -Line).Lines
    "CONTENT/tts_completed" = (rg -n "CONTENT/tts_completed" tests backend/app | Measure-Object -Line).Lines
    "CONTENT/render_started" = (rg -n "CONTENT/render_started" tests backend/app | Measure-Object -Line).Lines
    "CONTENT/render_completed" = (rg -n "CONTENT/render_completed" tests backend/app | Measure-Object -Line).Lines
    "CONTENT/publish_manifest_created" = (rg -n "CONTENT/publish_manifest_created" tests backend/app | Measure-Object -Line).Lines
    "CONTENT/pipeline_failed" = (rg -n "CONTENT/pipeline_failed" tests backend/app | Measure-Object -Line).Lines
    "SAFETY/pacing_delay" = (rg -n "SAFETY/pacing_delay" tests backend/app | Measure-Object -Line).Lines
    "SAFETY/publish_blocked" = (rg -n "SAFETY/publish_blocked" tests backend/app | Measure-Object -Line).Lines
    "SAFETY/risk_detected" = (rg -n "SAFETY/risk_detected" tests backend/app | Measure-Object -Line).Lines
    "SAFETY/cooldown_started" = (rg -n "SAFETY/cooldown_started" tests backend/app | Measure-Object -Line).Lines
    "METRICS/collection_started" = (rg -n "METRICS/collection_started" tests backend/app | Measure-Object -Line).Lines
    "METRICS/collection_completed" = (rg -n "METRICS/collection_completed" tests backend/app | Measure-Object -Line).Lines
    "METRICS/collection_failed" = (rg -n "METRICS/collection_failed" tests backend/app | Measure-Object -Line).Lines
}
$eventHits.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Name): $($_.Value)" } | Set-Content -Path $eventSanityPath -Encoding UTF8
foreach ($entry in $eventHits.GetEnumerator()) {
    if ($entry.Value -gt 0) {
        Add-Pass "event contract evidence for $($entry.Key)"
    } else {
        $isContentEvent = $entry.Key.StartsWith("CONTENT/")
        $isSafetyBlocked = $entry.Key -eq "SAFETY/publish_blocked"
        if (($isContentEvent -and -not $contentPipelineInBase) -or ($isSafetyBlocked -and -not $safetyInBase)) {
            Add-NotInBase "event contract evidence not applicable in this base for $($entry.Key)"
        } else {
            Add-Failure "event contract evidence missing for $($entry.Key)"
        }
    }
}

Write-Section "7. COGNICAO E LEARNING LOOP"
$analysisOutputs = @(
    "OUT/analysis/pilot_metrics_summary.json",
    "OUT/analysis/experiment_winners.json",
    "OUT/analysis/hook_performance_summary.json",
    "OUT/analysis/account_health_summary.json"
)
$analysisLog = Join-Path $auditDir "analysis_outputs.txt"
$analysisLines = foreach ($path in $analysisOutputs) {
    if (Test-Path $path) {
        Add-Pass "$path present"
        "PRESENT: $path"
    } else {
        if ($analysisInBase) {
            Add-Failure "$path missing"
            "FAIL: $path"
        } else {
            Add-NotInBase "$path not required in this base"
            "NOT_IN_BASE: $path"
        }
    }
}
$analysisLines | Set-Content -Path $analysisLog -Encoding UTF8

Write-Section "8. DRY RUN DE 1 VIDEO"
$dryRunOut = Join-Path $auditDir "dry_run_one_video.txt"
if (Test-Path "tests/test_content_pipeline_d27_unittest.py") {
    Invoke-LoggedCommand -Title "dry-run one video (D27 suite)" -Command "python -m unittest -q tests.test_content_pipeline_d27_unittest" -OutFile $dryRunOut | Out-Null
} else {
    Write-LogHeader -Path $dryRunOut -Title "dry-run one video" -Command "python -m unittest -q tests.test_content_pipeline_d27_unittest"
    "NOT_IN_BASE: tests/test_content_pipeline_d27_unittest.py not present in this base" | Add-Content -Path $dryRunOut -Encoding UTF8
    Add-NotInBase "dry-run harness not in this base: tests/test_content_pipeline_d27_unittest.py"
}

Write-Section "9. ARTEFATOS ESPERADOS"
$artifactLog = Join-Path $auditDir "artifact_presence.txt"
$artifactChecks = @(
    "OUT/content",
    "OUT/analysis",
    "OUT/simulation",
    "OUT/metrics",
    "OUT/ops"
)
$artifactLines = foreach ($path in $artifactChecks) {
    if (Test-Path $path) {
        Add-Pass "$path present"
        "PRESENT: $path"
    } else {
        Add-Failure "$path missing"
        "FAIL: $path"
    }
}
$artifactLines | Set-Content -Path $artifactLog -Encoding UTF8

Write-Section "10. VEREDITO FINAL"
$status = if ($script:Failures.Count -eq 0) { "PASS" } else { "NO-GO" }
Write-AuditReport -Status $status

Write-Host ""
Write-Host "==== PRE-D23 FULL GATE $status ===="
Write-Host "Evidence: $auditDir"
Write-Host "Passed checks: $($script:Passes.Count)"
Write-Host "Failed checks: $($script:Failures.Count)"
Write-Host "Not-in-base items: $($script:NotInBase.Count)"

if ($status -ne "PASS") {
    exit 1
}
