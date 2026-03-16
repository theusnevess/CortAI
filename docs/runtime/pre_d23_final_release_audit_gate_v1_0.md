# Pre-D23 Final Release Audit Gate v1.0

## Objetivo

Executar um gate final pre-D23 com evidencia materializada em:

- `OUT/audit/pre_d23_final_gate/`

O gate e orientado a `GO/NO-GO`.

## Script

- `backend/scripts/run_pre_d23_final_release_audit_gate.ps1`

## Saidas geradas

- `OUT/audit/pre_d23_final_gate/AUDIT_REPORT.md`
- `OUT/audit/pre_d23_final_gate/unit_tests.txt`
- `OUT/audit/pre_d23_final_gate/regression_tests.txt`
- `OUT/audit/pre_d23_final_gate/py_compile.txt`
- `OUT/audit/pre_d23_final_gate/infra_health.txt`
- `OUT/audit/pre_d23_final_gate/security_scan.txt`
- `OUT/audit/pre_d23_final_gate/smoke_runtime_checks.txt`
- `OUT/audit/pre_d23_final_gate/video_batch_qc.txt`
- `OUT/audit/pre_d23_final_gate/consistency_check.json`
- `OUT/audit/pre_d23_final_gate/consistency_check.md`

## Uso recomendado

### Execucao completa

```powershell
./backend/scripts/run_pre_d23_final_release_audit_gate.ps1
```

### Execucao sem infra local

Uso apenas para validar o script ou trabalhar fora do ambiente completo.

```powershell
./backend/scripts/run_pre_d23_final_release_audit_gate.ps1 -SkipInfra
```

### Execucao sem ferramentas externas de seguranca

Uso apenas quando `pip-audit` ou `gitleaks` nao estiverem instalados.

```powershell
./backend/scripts/run_pre_d23_final_release_audit_gate.ps1 -SkipSecurity
```

## O que o gate verifica

### Build

- `python -m compileall backend/app`

### Testes

- `D27`
- `D28`
- `D29`
- `D30`
- `D31`
- `D32`
- `D33`
- `D34`
- `D37`
- `D38`
- regressao de `screen_text`
- regressao de `script_generation`
- `publish_records`
- `D23 rollout`

### Contratos

- `pipeline` sem import de `runtime`
- `pipeline` sem import de `safety`
- `analysis` sem import de `runtime` ou `content.pipeline`

### Infra

- `docker compose ps`
- `:8000/health`
- `:8000/ready`
- `:8002/health`
- `:8002/ready`

### Seguranca

- `python -m pip check`
- `pip-audit`
- `gitleaks`

Ferramentas ausentes sao marcadas como `N/A` com justificativa.

### Smoke operacional

- `scheduler/runtime D23`
- `safety D28`
- `pipeline D27`
- `publish_records`
- `metrics_collector`

### Video QC

O gate gera um batch curto de QC com `3` videos e valida:

- artefatos reais
- `render_duration_s >= 8.0`
- `3` cues
- timings validos
- cues nao vazios

### Consistency

Materializa:

- `consistency_check.json`
- `consistency_check.md`

## Regra de decisao

### GO

Somente se o `AUDIT_REPORT.md` fechar sem nenhum `FAIL`.

### NO-GO

Qualquer `FAIL` bloqueia o D23.

## Leitura do relatorio

O `AUDIT_REPORT.md` traz:

- dominio
- check
- status
- evidencia
- detalhe

Status validos:

- `PASS`
- `FAIL`
- `N/A`

`N/A` so e aceitavel quando houver justificativa operacional real.
