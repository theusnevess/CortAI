# Script Agent Excellence Gate

Versao: 1.0  
Status: Aprovado para execucao  
Script: `backend/scripts/run_script_agent_excellence_gate.ps1`

## Objetivo
Executar um gate de excelencia especifico do `Script Agent` antes de liberar o proximo gargalo criativo da Fase 2.5.

O gate valida se o agente:

- usa contexto cognitivo real
- gera copy perceptivelmente melhor
- preserva a melhora ate o video final
- continua operacionalmente confiavel

## Escopo
O runner cobre:

- compilacao do `Script Agent` e adjacentes alterados
- testes unitarios do `Script Agent`
- regressao cognitiva minima com `Creative Orchestrator` e smokes dos blocos 1 a 4
- influencia real de `strategy_profile`, `trend_profile`, `learning_insights` e `experiment_plan`
- robustez do parsing estruturado
- cadeia de fallback `Gemini -> Ollama -> fallback deterministico`
- bateria de 20 roteiros para anti-cliche e diversidade
- lote de 5 videos reais para impacto perceptivel e estabilidade

## Evidencia gerada
O gate materializa evidencia em:

- `OUT/audit/script_agent_excellence_gate/`

Arquivos principais:

- `AUDIT_REPORT.md`
- `py_compile_script_agent.txt`
- `script_agent_unit_tests.txt`
- `script_agent_cognitive_regression.txt`
- `context_influence_audit.json`
- `structured_parsing_audit.json`
- `fallback_path_audit.json`
- `script_battery_20.json`
- `video_batch_5.json`

## Comando padrao

```powershell
./backend/scripts/run_script_agent_excellence_gate.ps1
```

## Modo de validacao rapida do runner

```powershell
./backend/scripts/run_script_agent_excellence_gate.ps1 -SkipScriptBattery -SkipVideoBatch
```

Esse modo nao fecha o gate de excelencia. Ele serve apenas para validar o runner e a materializacao de evidencia sem executar as baterias mais caras.

## Criterio de GO / NO-GO

- `GO` apenas se `FAILURES = 0`
- qualquer `FAIL` bloqueia a liberacao do proximo agente

Thresholds minimos embutidos no runner:

- contexto precisa alterar `4/4` variantes controladas
- parser estruturado precisa aceitar os `4` casos representativos
- fallback precisa fechar `Gemini -> Ollama` e `Ollama -> fallback deterministico`
- bateria de 20 roteiros:
  - `20` roteiros gerados
  - `distinct_hooks >= 16`
  - `distinct_modes >= 5`
  - `cliche_hits <= 3`
  - `weak_payoff_hits <= 2`
- lote de 5 videos:
  - `5` execucoes
  - pelo menos `4/5` com `pipeline_status = READY` e `video_qc_status = APPROVE`
  - `distinct_hooks >= 4`

## Interpretacao
Quando esse gate fecha limpo, o `Script Agent` deixa de estar apenas integrado e passa a estar validado como componente criativo liberavel.
