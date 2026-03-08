# CortAI - D23 Pilot Operator Index

Versao: `v1.0`  
Escopo: operacao do piloto real de 72h  
Aplica-se a: `CortAI >= D33`

## Objetivo

- centralizar todos os artefatos operacionais do piloto
- permitir execucao sem improviso
- reduzir tempo de decisao durante incidentes

## Estado do sistema

### Checkpoint congelado

- Tag: `cortai-pre-pilot-audit-2026-03-07`

### Status tecnico

- Engineering: `COMPLETE (D27-D33)`
- Audit Gate: `PASS`
- Operational Docs: `VERSIONED`
- Pilot: `READY (waiting accounts)`

## Sequencia operacional do piloto

Fluxo resumido:

- GO/NO-GO checklist
- Run pilot D23
- Monitor first 12 hours
- Operate remaining 72h
- Generate rollout artifacts
- Evaluate gate for D25

## Artefatos operacionais

### 1. Runbook completo

Arquivo:

- `docs/runtime/d23_pilot_runbook_v1_0.md`

Contem:

- sequencia completa de execucao
- rollback
- allowlist
- parametros do piloto
- criterios GO/NO-GO

Uso:

- referencia principal do operador

### 2. Operational Checklist

Arquivo:

- `docs/runtime/d23_pilot_operational_checklist_v1_0.md`

Contem:

- sequencia operacional detalhada
- checklist de execucao
- artefatos esperados

Uso:

- durante o piloto

### 3. GO / NO-GO Checklist

Arquivo:

- `docs/runtime/d23_pilot_day_go_no_go_checklist_v1_0.md`

Contem:

- verificacao final antes do piloto

Uso:

- imediatamente antes de iniciar o piloto

### 4. First 12 Hours Monitoring Map

Arquivo:

- `docs/runtime/d23_first_12_hours_monitoring_map_v1_0.md`

Contem:

- checkpoints de monitoramento
- sinais precoces de risco
- criterios de incidente

Uso:

- `T+0` ate `T+12h`

### 5. Pilot Learning Plan

Arquivo:

- `docs/runtime/d23_pilot_learning_plan_v1_0.md`

Contem:

- matriz de videos
- variaveis experimentais
- interpretacao de metricas
- leitura de sinais fracos

Uso:

- planejamento e analise do piloto

## Artefatos gerados pelo piloto

Apos execucao, devem existir:

- `OUT/rollout/pilot_rollout_report.json`
- `OUT/rollout/pilot_batch_window_summary.json`
- `OUT/rollout/pilot_alerts.json`
- `OUT/ops/slo_status.json`
- `OUT/ops/alerts.jsonl`

## Metricas monitoradas

Arquivo:

- `OUT/metrics/video_metrics.jsonl`

Campos principais:

- `views`
- `watch_time`
- `completion_rate`
- `avg_watch_time`
- `likes`
- `shares`
- `comments`

## Eventos esperados

### Content pipeline

- `CONTENT/tts_started`
- `CONTENT/tts_completed`
- `CONTENT/render_started`
- `CONTENT/render_completed`
- `CONTENT/publish_started`
- `CONTENT/publish_completed`

### Safety

- `SAFETY/pacing_delay`
- `SAFETY/publish_blocked`
- `SAFETY/risk_detected`

### Metrics

- `METRICS/collection_started`
- `METRICS/collection_completed`

## Condicoes de abort

Abortar piloto se ocorrer:

- `ACCOUNT_RESTRICTED`
- `REPEATED_PUBLISH_REJECTED`
- `RATE_LIMIT` em multiplas contas
- `COOLDOWN > 24h`

Procedimento:

- activate rollout kill switch
- pause scheduler
- investigate

## Criterio de sucesso do piloto

Apos `72h`:

- `publish success rate >= 95%`
- `0 contas restritas`
- metricas coletadas
- experimentos executados
- atribuicao funcional

Se atendido:

- abrir `D25 - Production Expansion`

## Operador responsavel

Preencher no momento do piloto:

- Operator: `____`
- Start time: `____`
- End time: `____`
- Accounts used: `____`

## Estrutura final de runtime docs

```text
docs/runtime/
 +- d23_pilot_runbook_v1_0.md
 +- d23_pilot_operational_checklist_v1_0.md
 +- d23_pilot_day_go_no_go_checklist_v1_0.md
 +- d23_first_12_hours_monitoring_map_v1_0.md
 +- d23_pilot_learning_plan_v1_0.md
 +- d23_pilot_operator_index_v1_0.md
```

## Beneficio desse indice

O operador precisa abrir apenas um documento:

- `d23_pilot_operator_index_v1_0.md`

E dali acessar tudo.
