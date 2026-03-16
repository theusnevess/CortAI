# Content Template Library v1.0

## Scope

`D36 — Content Template Library v1.0` adiciona uma biblioteca estruturada de templates para alimentar o `CreativePackGenerator`.

Esta camada padroniza texto-base de:

- hooks
- estrutura narrativa
- pacing de roteiro
- CTA

## Goals

- aumentar consistencia dos `creative_packs`
- reduzir variacao ruim entre geracoes
- permitir selecao deterministica por tipo
- preparar variacoes controladas antes do piloto real

## Out of Scope

- nenhuma alteracao em `publish`
- nenhuma alteracao em `safety`
- nenhuma alteracao em `scheduler`
- nenhuma alteracao em `metrics`
- nenhuma chamada de API externa
- nenhuma mutacao do pipeline de conteudo

## Template Types

Tipos canonicos suportados no v1.0:

- `HOOK_QUESTION`
- `HOOK_CURIOUS_STATEMENT`
- `HOOK_REVEAL`
- `HOOK_CONTRAST`
- `HOOK_COUNTDOWN`

## Template Structure

Cada template representa um texto-base reutilizavel com esta estrutura logica:

1. `hook`
2. `setup`
3. `tension`
4. `reveal`
5. `cta`

Os campos textuais ficam organizados como:

- `hook_pattern`
- `body_pattern`
- `cta_pattern`

## Invariants

- templates sao deterministicos
- templates nao chamam servicos externos
- templates apenas geram texto-base
- templates sao usados apenas pelo `CreativePackGenerator`
- mesma entrada de selecao deve produzir a mesma ordem de templates
- variacoes simples devem ser estaveis por indice

## Persistence

Persistencia append-only em:

- `OUT/content/templates/templates.jsonl`

## Data Model

Modelo minimo:

- `template_id`
- `template_type`
- `structure`
- `hook_pattern`
- `body_pattern`
- `cta_pattern`
- `tags`
- `created_at`

## Service Responsibilities

A biblioteca deve expor:

- `list_templates()`
- `get_template(template_id)`
- `select_templates_by_type(template_type)`
- `generate_template_variations(template_id, count)`

## Deterministic Selection

Regras:

- a selecao por tipo deve preservar ordenacao estavel
- a geracao de variacoes nao usa RNG global
- o indice da variacao controla a saida

## Future Integration

Integracao prevista com:

- `D29 — Creative Pack Generator`

A integracao futura deve:

- escolher templates por tipo e contexto
- montar hooks e estruturas mais consistentes
- continuar sem tocar no runtime critico

