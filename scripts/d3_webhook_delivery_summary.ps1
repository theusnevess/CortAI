param(
  [Parameter(Mandatory = $true)]
  [ValidateSet("D1", "D2", "D3")]
  [string]$DayLabel,

  [Parameter(Mandatory = $true)]
  [string]$ReceiverLogPath,

  [string]$OutDir = "OUT/D3",
  [string]$ApiContainer = "cortai_api",
  [string]$ReceiverPostPattern = "WEBHOOK POST",
  [string]$ApiErrorPattern = "public_status_webhook_(failed|error)|webhook.*(failed|error)|Webhook.*(failed|error)",
  [int]$WindowHours = 24
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function StopLine([string]$Message) {
  Write-Error $Message
  exit 1
}

function TryParseLineTs([string]$Line) {
  if ([string]::IsNullOrWhiteSpace($Line)) {
    return $null
  }

  $patterns = @(
    '^\s*---\s*(?<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)',
    '^(?<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)',
    '^(?<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
  )

  foreach ($pattern in $patterns) {
    $match = [regex]::Match($Line, $pattern)
    if (-not $match.Success) {
      continue
    }

    $rawTs = $match.Groups["ts"].Value
    [DateTimeOffset]$dto = [DateTimeOffset]::MinValue
    if ([DateTimeOffset]::TryParse($rawTs, [ref]$dto)) {
      return $dto.UtcDateTime
    }
    [DateTime]$dt = [DateTime]::MinValue
    if ([DateTime]::TryParse($rawTs, [ref]$dt)) {
      return $dt.ToUniversalTime()
    }
  }

  return $null
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$summaryPath = Join-Path $OutDir ("{0}_webhook_delivery_summary.txt" -f $DayLabel)
$tsNow = (Get-Date).ToUniversalTime()
$windowStart = $tsNow.AddHours(-1 * $WindowHours)

if (-not (Test-Path $ReceiverLogPath)) {
  StopLine "STOP: Receiver log nao encontrado em: $ReceiverLogPath"
}

$lines = Get-Content -Path $ReceiverLogPath -ErrorAction Stop
$bounded = $true
$receiverLines = New-Object System.Collections.Generic.List[string]
$currentEntry = New-Object System.Collections.Generic.List[string]
$currentTs = $null

foreach ($line in $lines) {
  if ($currentEntry.Count -eq 0 -and [string]::IsNullOrWhiteSpace($line)) {
    continue
  }

  $lineTs = TryParseLineTs $line

  if ($lineTs -ne $null) {
    if ($currentEntry.Count -gt 0) {
      if ($currentTs -ne $null -and $currentTs -ge $windowStart -and $currentTs -le $tsNow) {
        $receiverLines.Add(($currentEntry -join "`n"))
      }
      $currentEntry.Clear()
    }
    $currentTs = $lineTs
    $currentEntry.Add($line)
    continue
  }

  if ($currentEntry.Count -eq 0) {
    $bounded = $false
    break
  }

  $currentEntry.Add($line)
}

if ($bounded -and $currentEntry.Count -gt 0) {
  if ($currentTs -ne $null -and $currentTs -ge $windowStart -and $currentTs -le $tsNow) {
    $receiverLines.Add(($currentEntry -join "`n"))
  }
}

if (-not $bounded) {
  $receiverScope = "unbounded_total"
  $deliveries = @($lines | Select-String -Pattern $ReceiverPostPattern).Count
}
else {
  $receiverScope = "window_last_${WindowHours}h"
  $deliveries = @($receiverLines | Select-String -Pattern $ReceiverPostPattern).Count
}

$sinceArg = ("{0}h" -f $WindowHours)
$apiLogs = & cmd /c "docker logs $ApiContainer --since $sinceArg 2>&1"
if ($LASTEXITCODE -ne 0) {
  StopLine "STOP: Falhou docker logs $ApiContainer --since $sinceArg"
}

$apiWebhookErrors = @($apiLogs | Select-String -Pattern $ApiErrorPattern).Count

$verdict = "OK"
$notes = New-Object System.Collections.Generic.List[string]

if ($apiWebhookErrors -gt 0) {
  $verdict = "PRE_NO_GO"
  $notes.Add("api_webhook_errors_detected=$apiWebhookErrors")
}

if ($deliveries -eq 0) {
  if ($verdict -eq "OK") {
    $verdict = "ALERT"
  }
  $notes.Add("deliveries_zero_in_scope")
}

@"
D+3 webhook delivery summary
day_label=$DayLabel
now=$($tsNow.ToString("s"))
window_hours=$WindowHours
window_start=$($windowStart.ToString("s"))
receiver_log_path=$ReceiverLogPath
receiver_scope=$receiverScope
receiver_post_pattern=$ReceiverPostPattern
deliveries_count=$deliveries
api_container=$ApiContainer
api_error_pattern=$ApiErrorPattern
api_webhook_error_count=$apiWebhookErrors
verdict=$verdict
notes=$($notes -join ";")
"@ | Set-Content -Path $summaryPath -Encoding UTF8

Write-Host "WROTE: $summaryPath"
Write-Host "verdict=$verdict deliveries=$deliveries api_errors=$apiWebhookErrors scope=$receiverScope"
exit 0
