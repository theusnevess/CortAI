# D32 - Advanced Content Performance Attribution v1.0

## Objetivo

Atribuir performance granular aos elementos do conteudo para explicar por que um video performa melhor ou pior.

Entidades analisadas:
- hook
- estrutura narrativa
- duracao
- padrao de conteudo

## Inputs

- `OUT/data/publish_records/publish_records.jsonl`
- `OUT/data/video_metrics/video_metrics.jsonl`
- `OUT/content/creative_packs/creative_packs.jsonl`
- `OUT/experiments/assignments.jsonl`

## Outputs

Persistencia em `OUT/attribution/`:
- `hook_performance.jsonl`
- `structure_performance.jsonl`
- `duration_analysis.jsonl`
- `pattern_performance.jsonl`

## Entidades de saida

### HookPerformance

- `hook_performance_id`
- `account_id`
- `publish_id`
- `creative_pack_id`
- `hook_key`
- `hook_type`
- `views`
- `completion_rate`
- `watch_3s_rate`
- `experiment_variant`
- `generated_at`

### StructurePerformance

- `structure_performance_id`
- `account_id`
- `publish_id`
- `creative_pack_id`
- `structure_key`
- `views`
- `completion_rate`
- `experiment_variant`
- `generated_at`

### DurationAnalysis

- `duration_analysis_id`
- `account_id`
- `publish_id`
- `creative_pack_id`
- `duration_s`
- `duration_bucket`
- `completion_rate`
- `dropoff_point`
- `generated_at`

### PatternPerformance

- `pattern_performance_id`
- `account_id`
- `publish_id`
- `creative_pack_id`
- `pattern_key`
- `views`
- `completion_rate`
- `experiment_variant`
- `generated_at`

## Regras

- analise deterministica
- append-only
- recomputacao identica -> `NOOP`
- payload diferente para a mesma chave -> `CONFLICT`
- nenhuma mutacao do pipeline

## Heuristicas v1.0

### Hook type

- `QUESTION`: hook termina ou contem `?`
- `LISTICLE`: hook contem numero inicial
- `CURIOSITY`: hook contem `por que`, `o que`, `como`
- `STATEMENT`: fallback

### Structure key

Derivada dos blocos presentes no `script_skeleton`, por exemplo:

`HOOK>SETUP>ANGLE>PAYOFF>CTA`

### Duration

Fonte preferencial:
- `publish_record.metadata.duration_s`
- fallback: `publish_record.metadata.effective_duration_s`
- fallback: `0`

Buckets:
- `SHORT` <= 30s
- `MEDIUM` <= 60s
- `LONG` > 60s

### Pattern key

- `FACT_LIST`
- `CURIOSITY_ARC`
- `STORY_BREAKDOWN`
- `GENERAL`

## Integracao

Consome:
- D29 (`creative_packs`)
- D31 (`experiment_assignments`)

Alimenta:
- D26 (observability)
- D30 (intelligence)
- Strategy Learning / analise manual

## Criterio de aceite

O D32 fecha se:
- analise de hook funciona
- analise de estrutura funciona
- analise de duracao funciona
- persistencia append-only funciona
- recomputacao eh deterministica
- assignment de experimento eh refletido quando presente
