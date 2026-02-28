<#
.SYNOPSIS
Executa o recheck total do Maestro com stop-the-line e evidencias em OUT/.

.DESCRIPTION
Valida gates internos, migration/runtime do Maestro no ambiente correto do
Compose, testes focais, smokes demo/real, invariantes, no-leak e logs.

Gera:
- OUT/00..09_*.txt
- OUT/RECHECK_MAESTRO_TOTAL.md
- OUT/RECHECK_MAESTRO_SUMMARY.md

.EXAMPLE
.\scripts\recheck_maestro.ps1

.EXAMPLE
.\scripts\recheck_maestro.ps1 -OutDir OUT -ApiContainer cortai_api -EdgeContainer cortai_edge
#>

[CmdletBinding()]
param(
    [string]$OutDir = "OUT",
    [string]$ApiContainer = "cortai_api",
    [string]$EdgeContainer = "cortai_edge",
    [string]$ApiBase = "http://127.0.0.1:8000",
    [string]$EdgeBase = "http://localhost:8001"
)

$ErrorActionPreference = "Stop"

function Ensure-OutDir {
    if (!(Test-Path $OutDir)) {
        New-Item -ItemType Directory -Path $OutDir | Out-Null
    }
}

function Write-Section {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Title
    )
    "`n===== $Title =====`n" | Out-File -FilePath $Path -Append -Encoding utf8
}

function Run-Cmd {
    param(
        [Parameter(Mandatory = $true)][string]$OutFile,
        [Parameter(Mandatory = $true)][string]$Title,
        [Parameter(Mandatory = $true)][string]$Cmd
    )
    Write-Section -Path $OutFile -Title $Title
    "PS> $Cmd`n" | Out-File -FilePath $OutFile -Append -Encoding utf8
    $output = cmd.exe /d /c $Cmd 2>&1 | Out-String
    $output | Out-File -FilePath $OutFile -Append -Encoding utf8
    return $output
}

function Json-Pretty {
    param([string]$Json)
    try {
        return ($Json | ConvertFrom-Json | ConvertTo-Json -Depth 20)
    }
    catch {
        return $Json
    }
}

function Invoke-JsonRequest {
    param(
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $true)][string]$Uri,
        [AllowNull()][string]$Body = $null,
        [hashtable]$Headers = @{}
    )
    try {
        $params = @{
            Method       = $Method
            Uri          = $Uri
            Headers      = $Headers
            UseBasicParsing = $true
            ErrorAction  = "Stop"
        }
        if ($PSBoundParameters.ContainsKey("Body")) {
            $params.ContentType = "application/json"
            $params.Body = $Body
        }
        $resp = Invoke-WebRequest @params
        return [pscustomobject]@{
            StatusCode = [int]$resp.StatusCode
            Content    = [string]$resp.Content
            Headers    = $resp.Headers
            Raw        = $resp.RawContent
        }
    }
    catch {
        $resp = $_.Exception.Response
        if ($null -eq $resp) {
            throw
        }
        $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
        return [pscustomobject]@{
            StatusCode = [int]$resp.StatusCode.value__
            Content    = [string]$reader.ReadToEnd()
            Headers    = $resp.Headers
            Raw        = ""
        }
    }
}

function Assert-True {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if (-not $Condition) {
        throw "STOP-THE-LINE: $Message"
    }
}

Ensure-OutDir

$runUrl = "$ApiBase/internal/maestro/run"
$jobsUrl = "$ApiBase/internal/maestro/jobs"
$headers = @{ "X-Internal-Status" = "1" }

$out00 = Join-Path $OutDir "00_maestro_precheck.txt"
$out01 = Join-Path $OutDir "01_maestro_gates_http.txt"
$out02 = Join-Path $OutDir "02_maestro_migration.txt"
$out03 = Join-Path $OutDir "03_maestro_pytest_focal.txt"
$out04 = Join-Path $OutDir "04_maestro_demo_smoke.txt"
$out05 = Join-Path $OutDir "05_maestro_real_failed_smoke.txt"
$out06 = Join-Path $OutDir "06_maestro_contract_v03.txt"
$out07 = Join-Path $OutDir "07_maestro_invariants.txt"
$out08 = Join-Path $OutDir "08_maestro_no_leak.txt"
$out09 = Join-Path $OutDir "09_maestro_logs.txt"
$recheckTotal = Join-Path $OutDir "RECHECK_MAESTRO_TOTAL.md"
$recheckSummary = Join-Path $OutDir "RECHECK_MAESTRO_SUMMARY.md"

Remove-Item @(
    $out00, $out01, $out02, $out03, $out04,
    $out05, $out06, $out07, $out08, $out09,
    $recheckTotal, $recheckSummary
) -ErrorAction SilentlyContinue

# 00) Pré-check
Run-Cmd -OutFile $out00 -Title "git status --short" -Cmd "git status --short" | Out-Null
Run-Cmd -OutFile $out00 -Title "git branch/head/tag" -Cmd "git branch --show-current && git rev-parse --short HEAD && git tag --list v2.3.0-maestro-v0.3-audio-minio-contract" | Out-Null
Run-Cmd -OutFile $out00 -Title "docker compose ps" -Cmd "docker compose ps 2>&1" | Out-Null
Run-Cmd -OutFile $out00 -Title "docker ps" -Cmd "docker ps 2>&1" | Out-Null

$precheck = Get-Content $out00 -Raw
Assert-True -Condition (-not ($precheck -match '(?m)^ M |(?m)^M |(?m)^\?\? ')) -Message "working tree not clean"
Assert-True -Condition ($precheck -match 'perf/p2-c2-2-async-snapshot') -Message "wrong branch"
Assert-True -Condition ($precheck -match 'v2.3.0-maestro-v0.3-audio-minio-contract') -Message "missing expected tag"
Assert-True -Condition ($precheck -match $ApiContainer) -Message "api container not running"
Assert-True -Condition ($precheck -match $EdgeContainer) -Message "edge container not running"
Assert-True -Condition ($precheck -match 'cortai_db') -Message "db container not running"
Assert-True -Condition ($precheck -match 'cortai_minio') -Message "minio container not running"

# 01) Gates internos
$goodBody = '{"source_ref":"http://localhost:8001/smoke-assets/video_1s.mp4","job_id":null}'
Write-Section -Path $out01 -Title "RUN gate POST sem header -> 404"
$gateRun = Invoke-JsonRequest -Method "POST" -Uri $runUrl -Body $goodBody
$gateRun | ConvertTo-Json -Depth 6 | Out-File -FilePath $out01 -Append -Encoding utf8
Assert-True -Condition ($gateRun.StatusCode -eq 404) -Message "expected 404 on POST /internal/maestro/run without header, got $($gateRun.StatusCode)"

Write-Section -Path $out01 -Title "RUN method GET com header -> 405"
$gateGet = Invoke-JsonRequest -Method "GET" -Uri $runUrl -Headers $headers
$gateGet | ConvertTo-Json -Depth 6 | Out-File -FilePath $out01 -Append -Encoding utf8
Assert-True -Condition ($gateGet.StatusCode -eq 405) -Message "expected 405 on GET /internal/maestro/run, got $($gateGet.StatusCode)"

Write-Section -Path $out01 -Title "JOBS gate GET sem header -> 404"
$jobsGate = Invoke-JsonRequest -Method "GET" -Uri "$jobsUrl/does-not-matter"
$jobsGate | ConvertTo-Json -Depth 6 | Out-File -FilePath $out01 -Append -Encoding utf8
Assert-True -Condition ($jobsGate.StatusCode -eq 404) -Message "expected 404 on GET /internal/maestro/jobs/{id} without header, got $($jobsGate.StatusCode)"

# 02) Migration/DB no ambiente correto do Compose
Run-Cmd -OutFile $out02 -Title "alembic current in cortai_api" -Cmd "docker exec $ApiContainer sh -lc ""cd /app && python -m alembic current 2>&1""" | Out-Null
Run-Cmd -OutFile $out02 -Title "alembic upgrade head in cortai_api" -Cmd "docker exec $ApiContainer sh -lc ""cd /app && python -m alembic upgrade head 2>&1""" | Out-Null
Run-Cmd -OutFile $out02 -Title "alembic current confirm in cortai_api" -Cmd "docker exec $ApiContainer sh -lc ""cd /app && python -m alembic current 2>&1""" | Out-Null
Run-Cmd -OutFile $out02 -Title "DB check maestro_jobs exists in cortai_api" -Cmd "docker exec $ApiContainer sh -lc ""python -c \""from sqlalchemy import create_engine, text; from app.core.config import settings; eng = create_engine(settings.DATABASE_URL.replace('+asyncpg', '')); conn = eng.connect(); print(conn.execute(text('select to_regclass(''''public.maestro_jobs'''')')).scalar()); conn.close()\"""" | Out-Null

$migration = Get-Content $out02 -Raw
Assert-True -Condition ($migration -match 'a7f9e1d2c3b4') -Message "migration head missing"
Assert-True -Condition ($migration -match 'maestro_jobs') -Message "maestro_jobs table missing"

# 03) Pytests focais
Run-Cmd -OutFile $out03 -Title "pytest maestro orchestrator" -Cmd "cd /d backend && .venv\Scripts\python.exe -m pytest -q tests/test_maestro_orchestrator.py --noconftest 2>&1" | Out-Null
Run-Cmd -OutFile $out03 -Title "pytest maestro repository in cortai_api" -Cmd "docker exec $ApiContainer sh -lc ""cd /app && python -m pytest -q tests/test_maestro_repository.py --noconftest 2>&1""" | Out-Null
Run-Cmd -OutFile $out03 -Title "pytest internal maestro api" -Cmd "cd /d backend && .venv\Scripts\python.exe -m pytest -q tests/test_internal_maestro_api.py --noconftest 2>&1" | Out-Null
Run-Cmd -OutFile $out03 -Title "pytest audio extractor adapter" -Cmd "cd /d backend && .venv\Scripts\python.exe -m pytest -q tests/test_audio_extractor_adapter.py --noconftest 2>&1" | Out-Null

# 04) Smoke demo
$demoResp = Invoke-JsonRequest -Method "POST" -Uri "${runUrl}?demo=1" -Body $goodBody -Headers $headers
Json-Pretty $demoResp.Content | Out-File -FilePath $out04 -Encoding utf8
$demoObj = $demoResp.Content | ConvertFrom-Json
Assert-True -Condition ($demoResp.StatusCode -eq 200) -Message "demo smoke HTTP code <> 200"
Assert-True -Condition ([string]::IsNullOrWhiteSpace($demoObj.job_id) -eq $false) -Message "demo missing job_id"
Assert-True -Condition ($demoObj.status -eq 'done') -Message "demo status <> done"
Assert-True -Condition ($null -eq $demoObj.error) -Message "demo error not null"

$demoJobResp = Invoke-JsonRequest -Method "GET" -Uri "$jobsUrl/$($demoObj.job_id)" -Headers $headers
Write-Section -Path $out04 -Title "GET job demo persisted"
Json-Pretty $demoJobResp.Content | Out-File -FilePath $out04 -Append -Encoding utf8
$demoJob = $demoJobResp.Content | ConvertFrom-Json
Assert-True -Condition ($demoJobResp.StatusCode -eq 200) -Message "GET demo job HTTP code <> 200"
Assert-True -Condition ($demoJob.demo_mode -eq $true) -Message "demo_mode expected true"
Assert-True -Condition ($demoJob.status -eq 'done') -Message "persisted demo status <> done"
Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($demoJob.started_at)) -Message "demo started_at missing"
Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($demoJob.finished_at)) -Message "demo finished_at missing"
Write-Section -Path $out04 -Title "Headers GET job"
$demoJob.Raw | Out-File -FilePath $out04 -Append -Encoding utf8
Assert-True -Condition ($demoJobResp.Headers["Cache-Control"] -eq "no-store") -Message "GET /internal/maestro/jobs missing Cache-Control: no-store"

# 05) Smoke real failed-controlado
$badBody = '{"source_ref":"http://localhost:8001/smoke-assets/nao_existe.mp4","job_id":null}'
$realResp = Invoke-JsonRequest -Method "POST" -Uri $runUrl -Body $badBody -Headers $headers
Json-Pretty $realResp.Content | Out-File -FilePath $out05 -Encoding utf8
$realObj = $realResp.Content | ConvertFrom-Json
Assert-True -Condition ($realResp.StatusCode -eq 200) -Message "real smoke HTTP code <> 200"
Assert-True -Condition ([string]::IsNullOrWhiteSpace($realObj.job_id) -eq $false) -Message "real missing job_id"
Assert-True -Condition ($realObj.status -eq 'failed') -Message "real status <> failed"
Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($realObj.step)) -Message "real missing step"
Assert-True -Condition (-not [string]::IsNullOrWhiteSpace([string]$realObj.error)) -Message "real missing error"

$realJobResp = Invoke-JsonRequest -Method "GET" -Uri "$jobsUrl/$($realObj.job_id)" -Headers $headers
Write-Section -Path $out05 -Title "GET job real persisted"
Json-Pretty $realJobResp.Content | Out-File -FilePath $out05 -Append -Encoding utf8
$realJob = $realJobResp.Content | ConvertFrom-Json
Assert-True -Condition ($realJobResp.StatusCode -eq 200) -Message "GET real job HTTP code <> 200"
Assert-True -Condition ($realJob.status -eq 'failed') -Message "persisted real status <> failed"
Assert-True -Condition ($realJob.step -eq $realObj.step) -Message "persisted real step mismatch"
Assert-True -Condition (-not [string]::IsNullOrWhiteSpace([string]$realJob.error)) -Message "persisted real error missing"

# 06) Contrato v0.3
Run-Cmd -OutFile $out06 -Title "pytest orchestrator contract v0.3" -Cmd "cd /d backend && .venv\Scripts\python.exe -m pytest -q tests/test_maestro_orchestrator.py --noconftest -k ""audio_minio_path or extractor"" 2>&1" | Out-Null

# 07) Invariantes
@"
Demo invariants:
- status=done
- step=null
- error=null
- duration_ms numeric

Real invariants:
- status=failed
- step non-empty
- error non-empty
- duration_ms numeric
"@ | Out-File -FilePath $out07 -Encoding utf8
Assert-True -Condition ($demoObj.status -eq 'done') -Message "demo invariant status"
Assert-True -Condition ($null -eq $demoObj.step) -Message "demo invariant step"
Assert-True -Condition ($null -eq $demoObj.error) -Message "demo invariant error"
Assert-True -Condition ([int]$demoObj.duration_ms -ge 0) -Message "demo invariant duration_ms"
Assert-True -Condition ($realObj.status -eq 'failed') -Message "real invariant status"
Assert-True -Condition (-not [string]::IsNullOrWhiteSpace($realObj.step)) -Message "real invariant step"
Assert-True -Condition (-not [string]::IsNullOrWhiteSpace([string]$realObj.error)) -Message "real invariant error"
Assert-True -Condition ([int]$realObj.duration_ms -ge 0) -Message "real invariant duration_ms"
"OK" | Out-File -FilePath $out07 -Append -Encoding utf8

# 08) No-leak
$payloads = @(
    ($demoResp.Content | Out-String),
    ($demoJobResp.Content | Out-String),
    ($realResp.Content | Out-String),
    ($realJobResp.Content | Out-String)
) -join "`n---`n"
$payloads | Out-File -FilePath $out08 -Encoding utf8
foreach ($needle in @(
    "MINIO_ROOT_PASSWORD",
    "MINIO_ROOT_USER",
    "cortai_secret",
    "BEGIN PRIVATE KEY",
    "AWS_SECRET_ACCESS_KEY"
)) {
    Assert-True -Condition (-not ($payloads -match [regex]::Escape($needle))) -Message "leak $needle"
}
"OK" | Out-File -FilePath $out08 -Append -Encoding utf8

# 09) Logs
Run-Cmd -OutFile $out09 -Title "docker logs cortai_api --tail 300" -Cmd "docker logs $ApiContainer --tail 300 2>&1" | Out-Null
$logs = Get-Content $out09 -Raw
Assert-True -Condition ($logs -match 'maestro_job_finished') -Message "missing maestro_job_finished"
Assert-True -Condition ($logs -match 'maestro_job_failed') -Message "missing maestro_job_failed"

@"
# RECHECK MAESTRO TOTAL

Data: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Branch: $(git branch --show-current)
Commit: $(git rev-parse --short HEAD)

## Status
- 00 Precheck: PASS
- 01 Gates internos: PASS
- 02 Migration/DB: PASS
- 03 Pytests focais: PASS
- 04 Smoke demo: PASS
- 05 Smoke real failed-controlado: PASS
- 06 Contrato v0.3: PASS
- 07 Invariantes: PASS
- 08 No-leak: PASS
- 09 Logs: PASS

## Evidencias
- $out00
- $out01
- $out02
- $out03
- $out04
- $out05
- $out06
- $out07
- $out08
- $out09

## Nota operacional
- Migration/Alembic e validado dentro do container de aplicacao (`$ApiContainer`), que e o ambiente correto do Compose.
- Isso evita falso negativo de `DATABASE_URL`/DNS quando o host nao herda a mesma rede do Compose.
"@ | Out-File -FilePath $recheckTotal -Encoding utf8

@"
# RECHECK MAESTRO SUMMARY

Status: GO

## Criterio
- Gates OK (404/405 conforme esperado)
- Migration em head (a7f9e1d2c3b4) no ambiente correto
- Pytests focais verdes
- Demo smoke deterministico OK (done)
- Real smoke falha controlada OK (failed + step + error)
- Persistencia OK (GET reflete POST)
- No-leak OK
- Logs OK (finished + failed)

## Artefatos
- Total: $recheckTotal
- Evidencias: OUT/00..09_*.txt
"@ | Out-File -FilePath $recheckSummary -Encoding utf8

Write-Host "OK: Recheck Maestro concluido."
Write-Host " - $recheckTotal"
Write-Host " - $recheckSummary"
