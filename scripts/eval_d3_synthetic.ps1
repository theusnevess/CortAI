param(
  [string]$Dir = "OUT/D3",
  [string]$BaselineLabel = "D0b",
  [int]$P95HardMs = 300,
  [double]$RateHard = 0.001
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Parse-SummaryFile {
  param([string]$Path)

  if (-not (Test-Path $Path)) { throw "Missing summary file: $Path" }
  $lines = Get-Content -Raw -Path $Path -Encoding UTF8
  if ([string]::IsNullOrWhiteSpace($lines)) { throw "Empty summary file: $Path" }

  $kv = @{}
  foreach ($line in ($lines -split "`n")) {
    $trimmed = $line.Trim()
    if ($trimmed -eq "" -or -not ($trimmed -like "*=*")) { continue }
    $parts = $trimmed.Split("=", 2)
    $kv[$parts[0].Trim()] = $parts[1].Trim()
  }

  function Get-Int([string]$Key) {
    if (-not $kv.ContainsKey($Key)) { return $null }
    $value = $kv[$Key]
    if ([string]::IsNullOrWhiteSpace($value)) { return $null }
    return [int]$value
  }

  function Get-Double([string]$Key) {
    if (-not $kv.ContainsKey($Key)) { return $null }
    $value = $kv[$Key]
    if ([string]::IsNullOrWhiteSpace($value)) { return $null }
    return [double]$value
  }

  function Get-Str([string]$Key) {
    if (-not $kv.ContainsKey($Key)) { return $null }
    $value = $kv[$Key]
    if ([string]::IsNullOrWhiteSpace($value)) { return $null }
    return $value
  }

  return [pscustomobject]@{
    path = $Path
    day_label = Get-Str "day_label"
    status_public_5xx_count = Get-Int "status_public_5xx_count"
    status_public_5xx_rate = Get-Double "status_public_5xx_rate"
    status_public_p95_ms = Get-Int "status_public_p95_ms"
    webhook_sent = Get-Int "webhook_sent"
    webhook_success = Get-Int "webhook_success"
    webhook_error = Get-Int "webhook_error"
    webhook_error_rate = Get-Double "webhook_error_rate"
    webhook_p95_latency_ms = Get-Int "webhook_p95_latency_ms"
    webhook_last_error_status = Get-Str "webhook_last_error_status"
    webhook_last_error_ts = Get-Str "webhook_last_error_ts"
  }
}

function Evaluate-Day {
  param(
    [int]$BaselineP95,
    [object]$Summary
  )

  $reasons = New-Object System.Collections.Generic.List[string]
  $level = "OK"
  $rate = $Summary.status_public_5xx_rate
  $p95 = $Summary.status_public_p95_ms

  if ($rate -ne $null -and $rate -gt $RateHard) {
    $level = "PRE_NO_GO"
    $reasons.Add("status_public_5xx_rate=$rate > $RateHard")
  }
  if ($p95 -ne $null -and $p95 -gt $P95HardMs) {
    $level = "PRE_NO_GO"
    $reasons.Add("status_public_p95_ms=$p95 > $P95HardMs")
  }

  if ($level -ne "PRE_NO_GO" -and $p95 -ne $null) {
    $alertThreshold = [int](2 * $BaselineP95)
    if ($p95 -gt $alertThreshold) {
      $level = "ALERT"
      $reasons.Add("status_public_p95_ms=$p95 > 2x baseline ($alertThreshold)")
    }
  }

  $sent = $Summary.webhook_sent
  $success = $Summary.webhook_success
  $error = $Summary.webhook_error

  if ($sent -ne $null) {
    if ($success -ne $null -and $success -gt $sent) {
      $level = "PRE_NO_GO"
      $reasons.Add("webhook_success=$success > webhook_sent=$sent (incoherent)")
    }
    if ($error -ne $null -and $error -gt $sent) {
      $level = "PRE_NO_GO"
      $reasons.Add("webhook_error=$error > webhook_sent=$sent (incoherent)")
    }
    if ($success -ne $null -and $error -ne $null -and ($success + $error) -gt $sent) {
      $level = "PRE_NO_GO"
      $reasons.Add("webhook_success+webhook_error > webhook_sent (incoherent)")
    }
  }

  if ($sent -eq $null -or $sent -eq 0) {
    $reasons.Add("webhook not exercised (sent=0 or N/A) - not a failure by itself")
  }

  return [pscustomobject]@{
    day = $Summary.day_label
    level = $level
    reasons = $reasons
    p95 = $p95
    rate = $rate
  }
}

$baselinePath = Join-Path $Dir "$BaselineLabel`_summary.txt"
$d1Path = Join-Path $Dir "D1_summary.txt"
$d2Path = Join-Path $Dir "D2_summary.txt"
$d3Path = Join-Path $Dir "D3_summary.txt"

$baseline = Parse-SummaryFile $baselinePath
$d1 = Parse-SummaryFile $d1Path
$d2 = Parse-SummaryFile $d2Path
$d3 = Parse-SummaryFile $d3Path

$baselineP95 = $baseline.status_public_p95_ms
if ($baselineP95 -eq $null) {
  throw "Baseline missing status_public_p95_ms in $baselinePath"
}

$evals = @(
  Evaluate-Day -BaselineP95 $baselineP95 -Summary $d1
  Evaluate-Day -BaselineP95 $baselineP95 -Summary $d2
  Evaluate-Day -BaselineP95 $baselineP95 -Summary $d3
)

$alertDays = @($evals | Where-Object { $_.level -eq "ALERT" }).Count
$preNoGoDays = @($evals | Where-Object { $_.level -eq "PRE_NO_GO" }).Count

$final = "GO"
$finalReasons = New-Object System.Collections.Generic.List[string]
if ($preNoGoDays -gt 0) {
  $final = "NO_GO"
  $finalReasons.Add("At least one PRE_NO_GO day detected.")
}
elseif ($alertDays -ge 2) {
  $final = "NO_GO"
  $finalReasons.Add("ALERT repeated for 2+ days (p95 > 2x baseline).")
}
elseif ($alertDays -eq 1) {
  $final = "GO_WITH_ALERT"
  $finalReasons.Add("One ALERT day (p95 > 2x baseline) - monitor next run.")
}

Write-Output ""
Write-Output "=== D+3 Synthetic Evaluation (baseline=$BaselineLabel, baselineP95=$baselineP95 ms) ==="
foreach ($evaluation in $evals) {
  Write-Output ""
  Write-Output "[$($evaluation.day)] level=$($evaluation.level) p95=$($evaluation.p95)ms 5xx_rate=$($evaluation.rate)"
  foreach ($reason in $evaluation.reasons) {
    Write-Output " - $reason"
  }
}

Write-Output ""
Write-Output "=== FINAL VERDICT: $final ==="
foreach ($reason in $finalReasons) {
  Write-Output " - $reason"
}

$reportPath = Join-Path $Dir "D_SYNTH_verdict.txt"
$mdPath = Join-Path $Dir "D_SYNTH_verdict.md"

$txt = @()
$txt += "D+3 synthetic verdict"
$txt += "baseline=$BaselineLabel"
$txt += "baseline_p95_ms=$baselineP95"
foreach ($evaluation in $evals) {
  $txt += ""
  $txt += "$($evaluation.day)_level=$($evaluation.level)"
  $txt += "$($evaluation.day)_p95_ms=$($evaluation.p95)"
  $txt += "$($evaluation.day)_5xx_rate=$($evaluation.rate)"
  $txt += "$($evaluation.day)_reasons=" + ($evaluation.reasons -join " | ")
}
$txt += ""
$txt += "final_verdict=$final"
$txt += "final_reasons=" + ($finalReasons -join " | ")

$txt | Out-File -Encoding utf8 $reportPath

$md = @()
$md += "# D+3 Synthetic Verdict"
$md += ""
$md += "- Baseline: $BaselineLabel"
$md += "- Baseline p95: $baselineP95 ms"
$md += ""
foreach ($evaluation in $evals) {
  $md += "## $($evaluation.day)"
  $md += "- Level: $($evaluation.level)"
  $md += "- status_public_p95_ms: $($evaluation.p95)"
  $md += "- status_public_5xx_rate: $($evaluation.rate)"
  $md += ""
  $md += "Reasons:"
  foreach ($reason in $evaluation.reasons) {
    $md += "- $reason"
  }
  $md += ""
}
$md += "## Final"
$md += "- Verdict: $final"
foreach ($reason in $finalReasons) {
  $md += "- $reason"
}

$md | Out-File -Encoding utf8 $mdPath

Write-Output ""
Write-Output "Wrote:"
Write-Output " - $reportPath"
Write-Output " - $mdPath"
