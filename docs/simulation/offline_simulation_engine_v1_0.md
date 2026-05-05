# Offline Simulation Engine v1.0

## Scope

`D37 — Offline Simulation Engine v1.0` adiciona uma camada offline para simular o ciclo de aprendizagem do CortAI sem usar contas reais e sem publicar nada.

Fluxo simulado:

- `publish_records`
- `video_metrics`
- `experiment_results`
- inputs derivados para `analysis`

## Goals

- validar `D31`, `D32`, `D34` e `D38` com dados sintéticos
- exercitar cenarios de aprendizado antes do piloto real
- aumentar confianca nos fluxos de analise e consistencia
- evitar gasto de videos reais para debug funcional

## Out of Scope

- nenhuma publicacao real
- nenhuma chamada externa
- nenhuma alteracao em:
  - `publish`
  - `scheduler`
  - `workers`
  - `safety`
  - `metrics collector`
  - `rollout`

## Outputs

Outputs append-only previstos em `OUT/simulation/`:

- `simulated_publish_records.jsonl`
- `simulated_video_metrics.jsonl`
- `simulated_experiment_results.jsonl`
- `simulation_run_summary.json`

## Input Shape

O engine aceita apenas configuracao offline, por exemplo:

- `simulation_run_id`
- `account_ids`
- `videos_per_account`
- `experiment_variants`
- `seed`

## Data Model

Modelos minimos:

- `SimulatedPublishRecord`
- `SimulatedVideoMetrics`
- `SimulatedExperimentResult`
- `SimulationRunSummary`

## Invariants

- mesma entrada e mesmo seed produzem a mesma saida funcional
- ids sao determinísticos por `simulation_run_id + index`
- referencias internas precisam ser coerentes
- nenhum side effect fora de `OUT/simulation/`
- nenhum artefato real de runtime pode ser alterado

## Publish Simulation

O simulador de publish deve gerar registros equivalentes a `publish_records`, contendo pelo menos:

- `publish_id`
- `account_id`
- `video_id`
- `creative_pack_id`
- `platform`
- `status`

## Metrics Simulation

O simulador de métricas deve gerar registros equivalentes a `video_metrics`, contendo pelo menos:

- `publish_id`
- `account_id`
- `video_id`
- `views`
- `avg_watch_time`
- `completion_rate`
- `view_3s_rate`
- `view_5s_rate`
- `collected_at_bucket`

## Experiment Simulation

O simulador de experimentos deve gerar resultados coerentes com variantes atribuidas, contendo pelo menos:

- `experiment_id`
- `assignment_id`
- `variant`
- `supporting_metric`
- `winner_hint`

## Runner Responsibilities

O runner deve:

1. gerar publishes simulados
2. gerar métricas simuladas coerentes
3. gerar resultados de experimento coerentes
4. persistir os outputs
5. produzir um `simulation_run_summary`

## Integration Expectations

Os dados simulados devem ser consumiveis por:

- `D34 — Analysis & Research Layer`
- `D38 — Data Consistency Checker`

Sem adapters especiais ou mutacoes no runtime critico.

