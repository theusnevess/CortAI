param(
    [string]$OutputDir = "OUT/audit/voice_agent_excellence_gate",
    [switch]$SkipVideoBatch,
    [string]$PrimaryProvider = "piper",
    [string]$VoiceId = "",
    [string]$KokoroModelPath = "",
    [string]$KokoroVoicesPath = "",
    [string]$KokoroDevice = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $repoRoot
$auditDir = Join-Path $repoRoot $OutputDir
$null = New-Item -ItemType Directory -Force -Path $auditDir

if ($PrimaryProvider -eq "kokoro") {
    $env:CORTAI_PREMIUM_TTS_PROVIDER = "kokoro"
    if ([string]::IsNullOrWhiteSpace($VoiceId)) {
        $env:CORTAI_PREMIUM_TTS_VOICE = "af_heart"
    } else {
        $env:CORTAI_PREMIUM_TTS_VOICE = $VoiceId
    }
    if (-not [string]::IsNullOrWhiteSpace($KokoroModelPath)) {
        $env:CORTAI_KOKORO_MODEL_PATH = $KokoroModelPath
    }
    if (-not [string]::IsNullOrWhiteSpace($KokoroVoicesPath)) {
        $env:CORTAI_KOKORO_VOICES_PATH = $KokoroVoicesPath
    }
    if (-not [string]::IsNullOrWhiteSpace($KokoroDevice)) {
        $env:CORTAI_KOKORO_DEVICE = $KokoroDevice
    }
} else {
    Remove-Item Env:CORTAI_PREMIUM_TTS_PROVIDER -ErrorAction SilentlyContinue
    Remove-Item Env:CORTAI_PREMIUM_TTS_VOICE -ErrorAction SilentlyContinue
}

$scriptPath = Join-Path $auditDir "voice_gate_runner.py"
$scriptBody = @'
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

root = Path.cwd()
sys.path.insert(0, str((root / 'backend').resolve()))

from app.analysis.voice_gate.battery import run_video_batch, run_voice_battery
from app.analysis.voice_gate.evaluator import evaluate_gate

output_dir = Path(sys.argv[1]).resolve()
skip_video_batch = sys.argv[2].lower() == 'true'
output_dir.mkdir(parents=True, exist_ok=True)

battery = run_voice_battery(output_dir=output_dir)
video_batch = {"rows": []} if skip_video_batch else run_video_batch(output_dir=output_dir)
evaluation = evaluate_gate(battery=battery, video_batch=video_batch)

voice_rows = battery["rows"]
fallback_cases = battery["fallback_cases"]
video_rows = video_batch["rows"]

def write_json(name: str, payload: object) -> None:
    (output_dir / name).write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

write_json("voice_battery_25.json", {
    "status": "PASS" if evaluation["status"] == "GO" else "FAIL",
    "metrics": evaluation["summary"],
    "rows": voice_rows,
})
write_json("video_batch_5.json", {
    "status": "PASS" if all(row.get("pipeline_status") == "READY" and row.get("video_qc_status") == "APPROVE" for row in video_rows) else "FAIL",
    "rows": video_rows,
})
write_json("fallback_trace.json", {"rows": fallback_cases})
write_json("delivery_profile_summary.json", {
    "styles": sorted({row["voice_plan"]["style"] for row in voice_rows}),
    "providers_requested": evaluation["summary"]["requested_counts"],
    "providers_executed": evaluation["summary"]["provider_counts"],
    "delivery_variance_score": evaluation["summary"]["delivery_variance_score"],
    "primary_provider": os.getenv("CORTAI_PREMIUM_TTS_PROVIDER", "piper"),
})
write_json("latency_summary.json", evaluation["operational_checks"])
write_json("segment_pause_analysis.json", {
    "avg_pause_after_hook": evaluation["summary"]["avg_pause_after_hook"],
    "avg_pause_before_payoff": evaluation["summary"]["avg_pause_before_payoff"],
    "rows": [
        {
            "case_id": row["case_id"],
            "pause_after_hook": row["pause_after_hook"],
            "pause_after_setup": row["pause_after_setup"],
            "pause_before_payoff": row["pause_before_payoff"],
        }
        for row in voice_rows
    ],
})
write_json("monotony_proxy_analysis.json", {
    "avg_monotony_proxy": evaluation["summary"]["avg_monotony_proxy"],
    "avg_segment_contrast": evaluation["summary"]["avg_segment_contrast"],
    "rows": [
        {
            "case_id": row["case_id"],
            "monotony_proxy_score": row["monotony_proxy_score"],
            "segment_contrast_score": row["segment_contrast_score"],
        }
        for row in voice_rows
    ],
})

report_lines = [
    "# Voice Agent Excellence Gate",
    "",
    "## Gate verdict",
    evaluation["status"],
    "",
    "## Failures",
]
if evaluation["failures"]:
    report_lines.extend([f"- {item}" for item in evaluation["failures"]])
else:
    report_lines.append("- none")
report_lines.extend(["", "## Warnings"])
if evaluation["warnings"]:
    report_lines.extend([f"- {item}" for item in evaluation["warnings"]])
else:
    report_lines.append("- none")
report_lines.extend([
    "",
    "## Evidence",
    "- `voice_battery_25.json`",
    "- `video_batch_5.json`",
    "- `fallback_trace.json`",
    "- `delivery_profile_summary.json`",
    "- `latency_summary.json`",
    "- `segment_pause_analysis.json`",
    "- `monotony_proxy_analysis.json`",
    "",
    "## Architecture checks",
])
for key, value in evaluation["architecture_checks"].items():
    report_lines.append(f"- {key}: {value}")
report_lines.extend(["", "## Perceptual checks"])
for key, value in evaluation["perceptual_checks"].items():
    report_lines.append(f"- {key}: {value}")
report_lines.extend(["", "## Operational checks"])
for key, value in evaluation["operational_checks"].items():
    report_lines.append(f"- {key}: {value}")
report_lines.extend([
    "",
    "## Executive conclusion",
    "The gate is measuring whether the repaired voice control path is both operationally real and perceptibly useful.",
    f"Decision: {evaluation['status']}",
])
(output_dir / "AUDIT_REPORT.md").write_text("\n".join(report_lines), encoding="utf-8")
print(evaluation["status"])
'@

Set-Content -Path $scriptPath -Value $scriptBody -Encoding utf8

try {
    $output = (& python $scriptPath $auditDir ($SkipVideoBatch.ToString()) 2>&1 | Out-String)
    $exitCode = $LASTEXITCODE
} catch {
    $output = ($_ | Out-String)
    $exitCode = 1
}

Set-Content -Path (Join-Path $auditDir "voice_gate_runner.log") -Value $output -Encoding utf8
if ($exitCode -ne 0) {
    Write-Host "NO-GO"
    exit $exitCode
}

$decision = ($output.Trim().Split("`n") | Select-Object -Last 1).Trim()
Write-Host $decision
if ($decision -eq "GO") { exit 0 }
exit 1
