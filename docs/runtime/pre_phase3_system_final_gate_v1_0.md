# Pre-Phase3 System Final Gate

Versao: 1.0  
Status: Aprovado para execucao  
Script: `backend/scripts/run_pre_phase3_system_final_gate.ps1`

## Objetivo
Executar uma auditoria total do sistema antes da abertura da proxima fase do CortAI.

O gate valida:

- integridade do repositorio
- dependencias
- seguranca
- compilacao global
- suite total de testes
- regressao relevante da Fase 1
- regressao da camada cognitiva da Fase 2
- smoke completo do fluxo cognitivo
- auditoria de fallbacks
- governanca de contratos
- batch basico de stress
- telemetria minima
- consistencia minima
- auditoria basica de recursos

## Saida
O gate materializa evidencia em:

- `OUT/audit/pre_phase3_final_gate/`

Arquivos principais:

- `AUDIT_REPORT.md`
- `repo_required_paths.txt`
- `repo_git_status.txt`
- `pip_check.txt`
- `pip_audit.txt`
- `gitleaks.txt`
- `py_compile_all.txt`
- `unittest_discover.txt`
- `phase1_regression.txt`
- `cognitive_regression.txt`
- `contract_schema.txt`
- `fallback_audit.txt`
- `full_smoke.txt`
- `stress_batch.txt`
- `resource_audit.txt`

## Comando padrao

```powershell
./backend/scripts/run_pre_phase3_system_final_gate.ps1
```

## Modo de validacao rapida do runner

```powershell
./backend/scripts/run_pre_phase3_system_final_gate.ps1 -SkipInfra -SkipSecurity -SkipStressBatch -SkipResourceAudit
```

Esse modo nao fecha o gate final do sistema. Ele serve apenas para validar o proprio runner e a materializacao de evidencias sem gastar tempo com os trechos mais lentos.

## Criterio de GO / NO-GO

- `GO` apenas se `FAILURES = 0`
- qualquer `FAIL` bloqueia a abertura da proxima fase

## Observacoes

- `pip-audit`, `gitleaks` e a auditoria basica de recursos aceitam `N/A` apenas quando a ferramenta nao existe no ambiente
- o batch de stress reutiliza `backend/scripts/run_local_d23_18_batch.py`
- o smoke completo valida o fluxo:

```text
Account Health
-> Trend Analysis
-> Learning
-> Strategy
-> Experiment
-> Asset Selection
-> Creative Orchestrator
-> Script
-> Voice
-> Content Pipeline
-> Video QC
```

## Resultado esperado
Quando esse gate fecha limpo, o sistema esta tecnicamente pronto para iniciar a proxima fase sem regressao evidente na Fase 1 ou na Fase 2.
