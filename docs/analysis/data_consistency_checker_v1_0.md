# Data Consistency Checker v1.0

## Scope

`D38 — Data Consistency Checker v1.0` adiciona uma camada read-only para validar integridade entre os artefatos do piloto e do learning loop.

O checker existe para responder apenas:

- os artefatos estao consistentes?
- se nao estiverem, onde esta a quebra?

## Goals

- detectar inconsistencias silenciosas antes e durante o piloto
- gerar saida objetiva `OK / FAIL`
- expor contagens claras por check
- nao modificar nenhum artefato existente

## Out of Scope

- nenhum auto-fix
- nenhum fallback magico
- nenhuma mutacao de dados
- nenhuma alteracao em:
  - `publish`
  - `safety`
  - `scheduler`
  - `metrics collector`
  - `rollout`

## Inputs

Fontes de dados lidas:

- `publish_records`
- `video_metrics`
- `experiments`
- `experiment assignments`
- `experiment results`
- `creative_packs`
- artefatos de `analysis`

## Checks

Checks minimos do v1.0:

1. todo `publish_record` esperado tem `video_metrics`
2. todo `video_metrics` referencia `publish_record` existente
3. todo `experiment assignment` referencia experimento existente
4. todo resultado de experimento referencia assignment existente
5. todo `creative_pack_id` usado em `publish_record.metadata` existe
6. todo artefato de `analysis` e derivavel dos inputs presentes

## Output Files

Saidas derivadas:

- `OUT/analysis/consistency_check.json`
- `OUT/analysis/consistency_check.md`

## Output Contract

Modelo minimo:

- `status: OK | FAIL`
- `generated_at`
- `checks`
- `summary_counts`

Cada item em `checks` deve conter, no minimo:

- `check_id`
- `status`
- `expected`
- `found`
- `missing_count`
- `notes`

## Rules

- somente leitura
- mesma entrada produz a mesma saida funcional
- diferencas aceitas apenas em `generated_at`
- falhas devem ser explicitas e contaveis
- ausencia parcial de dados deve gerar `FAIL` ou resultado vazio coerente, nunca reparo silencioso

## OK / FAIL Semantics

`OK`:

- todos os checks executados passaram
- nenhuma referencia critica ausente

`FAIL`:

- pelo menos um check falhou
- a saida deve indicar claramente qual relacao esta inconsistente

## Operator Usage

O checker deve ser seguro para uso:

- antes do piloto
- durante as primeiras 12h
- ao final das 72h

## Invariants

- sem side effects
- sem escrita fora de `OUT/analysis/`
- sem alterar inputs append-only
- sem dependencia de servicos externos

