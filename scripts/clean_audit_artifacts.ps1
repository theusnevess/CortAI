<#
.SYNOPSIS
Limpa artefatos locais de auditoria/recheck sem tocar em arquivos versionados.

.DESCRIPTION
Remove diretórios e arquivos temporários gerados por:
- OUT/
- .tmp_*
- backend/.tmp_p2
- .tmp_p2_*

Suporta -WhatIf para simulação segura.

.EXAMPLE
.\scripts\clean_audit_artifacts.ps1 -WhatIf

.EXAMPLE
.\scripts\clean_audit_artifacts.ps1
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param()

Write-Host "== CortAI Audit Artifact Cleanup ==" -ForegroundColor Cyan

$paths = @(
    "OUT",
    ".tmp_*",
    "backend\.tmp_p2",
    ".tmp_p2_*"
)

foreach ($path in $paths) {
    $resolved = Get-ChildItem -Path $path -Force -ErrorAction SilentlyContinue

    if ($resolved) {
        foreach ($item in $resolved) {
            if ($PSCmdlet.ShouldProcess($item.FullName, "Remove")) {
                Remove-Item -Recurse -Force $item.FullName -ErrorAction SilentlyContinue
                Write-Host "Removed: $($item.FullName)" -ForegroundColor Yellow
            }
        }
    }
}

Write-Host "Cleanup complete." -ForegroundColor Green
