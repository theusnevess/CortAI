# CortAI - Analysis and Research Layer

Versao: `v1.0`  
Aplica-se a: `CortAI >= D33`  
Stage: `D34`

## Objetivo

Transformar artefatos ja produzidos pelo CortAI em sumarios uteis para decisao rapida apos o piloto, sem alterar o comportamento do sistema.

O D34 existe para reduzir o tempo entre:

- dado bruto
- insight consolidado
- decisao operacional ou estrategica

## Principios

- somente leitura
- somente agregacao deterministica
- inputs append-only
- outputs derivados
- nenhuma mutacao em `publish`, `safety`, `scheduler`, `metrics collector` ou `rollout`

## Fontes de dados

O D34 consome apenas artefatos ja existentes no sistema.

### Publish

- `publish_records`

### Metrics

- `video_metrics`

### Experiments

- `experiments`
- `experiment_assignments`
- `experiment_results`

### Attribution

- `hook_performance`
- `structure_performance`
- `duration_analysis`
- `pattern_performance`

### Intelligence

- `publish_windows`
- `pacing_profiles`
- `risk_profiles`
- `account_health`

### Safety

- `SAFETY/*` events
- cooldown history
- pacing delay history

## Saidas do D34

O D34 gera quatro sumarios principais.

### 1. Pilot Metrics Summary

Arquivo:

- `OUT/analysis/pilot_metrics_summary.json`

Responsabilidade:

- consolidar metricas gerais do piloto
- resumir desempenho por conta
- resumir desempenho por janela

Campos minimos esperados:

- `generated_at`
- `pilot_scope`
- `total_publish_records`
- `total_metrics_records`
- `accounts[]`
- `aggregate_views`
- `aggregate_watch_time`
- `aggregate_completion_rate`
- `aggregate_avg_watch_time`

### 2. Experiment Winners

Arquivo:

- `OUT/analysis/experiment_winners.json`

Responsabilidade:

- comparar variantes A/B
- apontar winner provisório por experimento
- registrar quando nao ha sinal suficiente

Campos minimos esperados:

- `generated_at`
- `experiments[]`
  - `experiment_id`
  - `scope`
  - `variant_a`
  - `variant_b`
  - `winner`
  - `winner_reason`
  - `confidence`
  - `evidence_count`

### 3. Hook Performance Summary

Arquivo:

- `OUT/analysis/hook_performance_summary.json`

Responsabilidade:

- consolidar performance por hook
- consolidar performance por estrutura
- consolidar performance por duracao

Campos minimos esperados:

- `generated_at`
- `hooks[]`
- `structures[]`
- `durations[]`
- `top_hook`
- `top_structure`
- `preferred_duration`

### 4. Account Health Summary

Arquivo:

- `OUT/analysis/account_health_summary.json`

Responsabilidade:

- consolidar saude operacional por conta
- resumir delays, cooldowns e risco
- indicar conta saudavel vs conta em observacao

Campos minimos esperados:

- `generated_at`
- `accounts[]`
  - `account_id`
  - `health_status`
  - `risk_level`
  - `cooldown_active`
  - `cooldown_count`
  - `pacing_delay_count`
  - `publish_block_count`
  - `notes[]`

## Regras de agregacao

### Determinismo

Mesma entrada logica deve produzir a mesma saida logica.

Isso implica:

- ordenacao estavel
- serializacao estavel
- ausencia de RNG
- ausencia de timestamp dinamico fora de `generated_at`

### Read-only

O D34 nunca deve:

- criar `publish_record`
- alterar estado de safety
- alterar scheduler
- alterar assignments de experimento
- alterar patch ou estrategia

### Tolerancia a dados incompletos

Se algum input estiver ausente:

- gerar sumario parcial ou vazio
- nao quebrar a execucao inteira
- explicitar ausencia de evidencia quando necessario

### Sem side effects no runtime

O D34 nao participa do caminho critico de execucao.

Ele opera fora de:

- `publish.py`
- `safety_gate.py`
- `scheduler`
- `worker execution`
- `metrics collector`

## Relacao com modulos existentes

### D30 - Platform Intelligence

O D34 le os outputs de inteligencia para:

- resumir janelas recomendadas
- resumir pacing recomendado
- resumir risco por conta

### D31 - Experiment Framework

O D34 usa assignments e resultados para:

- comparar A/B
- apontar winner provisório
- registrar experimentos sem sinal suficiente

### D32 - Advanced Attribution

O D34 usa attribution para:

- resumir hook vencedor
- resumir estrutura mais eficaz
- resumir duracao preferivel

### D26 - Strategy Observatory

O D34 gera outputs de analise que ajudam leitura operacional e estrategica, mas nao substitui o observatorio.

## Persistencia

A persistencia do D34 e em JSON derivado, sobrescrevivel por execucao do proprio sumario.

Diretorio:

- `OUT/analysis/`

Arquivos:

- `pilot_metrics_summary.json`
- `experiment_winners.json`
- `hook_performance_summary.json`
- `account_health_summary.json`

Observacao:

- os inputs seguem append-only
- os outputs do D34 sao snapshots derivados e reexecutaveis

## Casos de uso

Apos o piloto, o operador deve conseguir responder rapidamente:

- qual conta esta mais saudavel
- qual variante esta ganhando
- qual hook esta performando melhor
- qual estrutura segurou mais watch time
- qual faixa de duracao parece preferivel

## Fora de escopo

O D34 nao inclui:

- mutacao de pipeline
- winner selection automatica com rollout automatico
- engine estatistico avancado
- dashboard novo
- mudancas em `publish`, `safety`, `scheduler`, `rollout` ou `collector`

## Resultado esperado

Apos o D34, o CortAI ganha uma camada de analise e pesquisa que converte artefatos brutos em sumarios operacionais e estrategicos utilizaveis.
