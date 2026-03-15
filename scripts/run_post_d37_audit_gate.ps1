Write-Host "==== CORTAI RELEASE AUDIT GATE POS-D37 ===="

Write-Host "`n1. TESTES DO BLOCO NOVO"
python -m unittest -q tests.test_offline_simulation_engine_d37_unittest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m unittest -q tests.test_data_consistency_checker_d38_unittest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n2. REGRESSOES DO LEARNING LOOP"
python -m unittest -q tests.test_experiment_framework_d31_unittest tests.test_content_attribution_d32_unittest tests.test_metrics_collector_d33_unittest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (Test-Path "tests/test_analysis_research_layer_d34_unittest.py") {
    Write-Host "Rodando testes do D34"
    python -m unittest -q tests.test_analysis_research_layer_d34_unittest
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "`n3. COMPILACAO"
Get-ChildItem backend/app/simulation/*.py | ForEach-Object {
    python -m py_compile $_.FullName
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
Get-ChildItem backend/app/analysis/consistency/*.py | ForEach-Object {
    python -m py_compile $_.FullName
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "`n4. INFRA CHECK"
$infraOk = $true
try {
    $health8000 = Invoke-WebRequest http://localhost:8000/health -UseBasicParsing
    $ready8000 = Invoke-WebRequest http://localhost:8000/ready -UseBasicParsing
    Write-Host "8000 OK"
} catch {
    Write-Host "8000 FAIL"
    $infraOk = $false
}

try {
    $health8002 = Invoke-WebRequest http://localhost:8002/health -UseBasicParsing
    $ready8002 = Invoke-WebRequest http://localhost:8002/ready -UseBasicParsing
    Write-Host "8002 OK"
} catch {
    Write-Host "8002 FAIL"
    $infraOk = $false
}

if (-not $infraOk) { exit 1 }

Write-Host "`n5. SEGURANCA"
Write-Host "pip-audit"
pip-audit
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "pip check"
pip check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "gitleaks"
if (Get-Command gitleaks -ErrorAction SilentlyContinue) {
    gitleaks detect --source . -v
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} else {
    Write-Host "gitleaks FAIL: comando nao encontrado"
    exit 1
}

Write-Host "`n==== AUDIT GATE EXECUTADO ===="
Write-Host "Se tudo PASS, criar a tag:"
Write-Host "git tag -a cortai-pre-pilot-final -m 'CortAI final pre-pilot checkpoint'"
Write-Host "git push origin cortai-pre-pilot-final"

