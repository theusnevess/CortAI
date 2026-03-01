param(
  [string]$OutDir = "OUT/D3",
  [string]$DayLabel = "D0",
  [string]$ApiContainer = "cortai_api",
  [string]$StatusPublicUri = "http://localhost:8001/api/v1/status/public",
  [string]$OverviewUri = "http://127.0.0.1:8000/api/v1/observability/overview",
  [int]$SampleCount = 100,
  [int]$TimeoutSec = 5,
  [switch]$UseOverviewGate = $true
)

$ErrorActionPreference = "Stop"

function Get-P95 {
  param([long[]]$Values)
  if (-not $Values -or $Values.Count -eq 0) { return $null }
  $sorted = $Values | Sort-Object
  $rank = [int][Math]::Ceiling(0.95 * $sorted.Count)
  $index = [Math]::Max(0, [Math]::Min($sorted.Count - 1, $rank - 1))
  return [int]$sorted[$index]
}

function Get-RunPrefix {
  param([string]$Label)
  if ($Label -eq "D0") { return "01" }
  return $Label
}

function Get-OverviewPrefix {
  param([string]$Label)
  if ($Label -eq "D0") { return "02" }
  return $Label
}

function Invoke-OverviewRequest {
  param(
    [string]$Uri,
    [int]$TimeoutSec,
    [bool]$UseGate
  )
  $headers = @{}
  if ($UseGate) {
    $headers["X-Internal-Status"] = "1"
  }
  return Invoke-WebRequest -UseBasicParsing -Uri $Uri -Headers $headers -TimeoutSec $TimeoutSec
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$statusPrefix = Get-RunPrefix -Label $DayLabel
$overviewPrefix = Get-OverviewPrefix -Label $DayLabel
$statusCsv = Join-Path $OutDir ("{0}_status_public_100.csv" -f $statusPrefix)
$overviewJson = Join-Path $OutDir ("{0}_overview.json" -f $overviewPrefix)
$summaryTxt = Join-Path $OutDir ("{0}_summary.txt" -f $DayLabel)

if ($DayLabel -eq "D0") {
  $envPresence = Join-Path $OutDir "00_env_presence.txt"
  $envOutput = docker exec $ApiContainer sh -lc "python - <<'PY'
import os
print('STATUS_WEBHOOK_URL_SET=', bool(os.getenv('STATUS_WEBHOOK_URL')))
print('STATUS_WEBHOOK_SECRET_SET=', bool(os.getenv('STATUS_WEBHOOK_SECRET')))
PY"
  if ($LASTEXITCODE -ne 0) {
    throw "STOP-THE-LINE: failed to capture webhook env presence from $ApiContainer"
  }
  $envOutput | Out-File -Encoding utf8 $envPresence
}

$results = for ($i = 0; $i -lt $SampleCount; $i++) {
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $StatusPublicUri -TimeoutSec $TimeoutSec
    $code = [int]$r.StatusCode
  }
  catch {
    $code = 0
  }
  finally {
    $sw.Stop()
  }

  [pscustomobject]@{
    i = $i
    code = $code
    ms = [int]$sw.ElapsedMilliseconds
  }
}

$results | Export-Csv -NoTypeInformation -Encoding utf8 $statusCsv

$overviewResp = Invoke-OverviewRequest -Uri $OverviewUri -TimeoutSec $TimeoutSec -UseGate:$UseOverviewGate
$overviewResp.Content | Out-File -Encoding utf8 $overviewJson
$overview = $overviewResp.Content | ConvertFrom-Json

$sampleRows = @($results)
$fiveXxCount = @($sampleRows | Where-Object { $_.code -ge 500 -and $_.code -lt 600 }).Count
$fiveXxRate = if ($sampleRows.Count -gt 0) { [math]::Round($fiveXxCount / $sampleRows.Count, 6) } else { 0.0 }
$statusP95 = Get-P95 -Values @($sampleRows | ForEach-Object { [long]$_.ms })

$webhook = $overview.webhook
$webhookSent = if ($null -ne $webhook) { [int]$webhook.sent } else { $null }
$webhookSuccess = if ($null -ne $webhook) { [int]$webhook.success } else { $null }
$webhookError = if ($null -ne $webhook) { [int]$webhook.error } else { $null }
$webhookErrorRate = if ($null -ne $webhook) { [double]$webhook.error_rate } else { $null }
$webhookP95 = if ($null -ne $webhook) { $webhook.p95_latency_ms } else { $null }
$webhookLastErrorStatus = if ($null -ne $webhook) { $webhook.last_error_status } else { $null }
$webhookLastErrorTs = if ($null -ne $webhook) { $webhook.last_error_ts } else { $null }

$summary = @"
D+3 summary
day_label=$DayLabel
status_public_uri=$StatusPublicUri
overview_uri=$OverviewUri
sample_count=$SampleCount
status_public_5xx_count=$fiveXxCount
status_public_5xx_rate=$fiveXxRate
status_public_p95_ms=$statusP95
webhook_sent=$webhookSent
webhook_success=$webhookSuccess
webhook_error=$webhookError
webhook_error_rate=$webhookErrorRate
webhook_p95_latency_ms=$webhookP95
webhook_last_error_status=$webhookLastErrorStatus
webhook_last_error_ts=$webhookLastErrorTs
"@

$summary | Out-File -Encoding utf8 $summaryTxt

Write-Host "D+3 snapshot complete"
Write-Host " - $statusCsv"
Write-Host " - $overviewJson"
Write-Host " - $summaryTxt"
