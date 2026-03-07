# D31 - Experiment Framework v1.0

## Objetivo

Permitir experimentacao controlada e auditavel de:

- creative packs
- hook styles
- pacing profiles
- publish windows

Sem alterar diretamente o pipeline de execucao.

## Escopo

Entra:
- entidade `Experiment`
- assignment deterministico A/B
- persistencia append-only de experimentos, assignments e resultados
- resolucao de variante para D29/D30/D26

Nao entra:
- engine estatistico avancado
- selecao automatica de vencedor
- rollout automatico do vencedor
- mutacao de policy
- mais de 2 variantes

## Entidades

### Experiment

- `experiment_id`
- `name`
- `scope`
- `variant_a`
- `variant_b`
- `status`
- `created_at`

Scopes permitidos no v1.0:
- `CREATIVE_PACK`
- `HOOK_STYLE`
- `PACING_PROFILE`
- `PUBLISH_WINDOW`

Status permitidos no v1.0:
- `DRAFT`
- `ACTIVE`
- `PAUSED`
- `ARCHIVED`

### ExperimentAssignment

- `assignment_id`
- `experiment_id`
- `subject_key`
- `variant`
- `assigned_at`

### ExperimentResult

- `result_id`
- `experiment_id`
- `subject_key`
- `variant`
- `window_id`
- `metrics`
- `recorded_at`

## Assignment

Assignment eh deterministico:

`hash(subject_key + experiment_id) % 2`

Saida:
- `A`
- `B`

Sem RNG global.

## Persistencia

Base:

`OUT/experiments/`

Arquivos:
- `experiments.jsonl`
- `assignments.jsonl`
- `results.jsonl`

Semantica:
- append-only
- mesmo payload -> `NOOP`
- payload diferente na mesma chave logica -> `CONFLICT`

## Integracao

Pode ser consumido por:
- D29 (`creative_pack` variation)
- D30 (`pacing` e `publish_window` recommendation)
- D26 (comparacao por janela)

No v1.0 o framework nao altera execucao sozinho.

## Invariantes

- experimentos nao mutam pipeline
- assignment eh estavel para o mesmo input
- comparabilidade por janela e preservada
- toda decisao de variante eh auditavel

## Criterio de aceite

O D31 fecha se:
- experimento pode ser criado
- assignment eh deterministico
- mesma entrada gera mesma variante
- persistencia append-only funciona
- duplicidade vira `NOOP`
- conflito vira `CONFLICT`
