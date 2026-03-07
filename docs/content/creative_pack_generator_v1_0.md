# D29 - Creative Pack Generator v1.0

## Objetivo

Gerar `creative_pack` de forma deterministica e auditavel a partir de um tema/oportunidade, sem alterar o caminho de `publish`.

Fluxo alvo:

`theme/opportunity -> creative_pack -> content pipeline -> publish`

## Escopo

Entra:
- geracao automatica de `creative_pack`
- hook candidates
- script skeleton
- angle
- title
- hashtags
- CTA
- variacoes por conta e `policy_stage`
- respeito a `account_policy` e `strategy_patch`
- persistencia append-only

Nao entra:
- alteracao do `publish.py`
- alteracao do `safety_gate`
- alteracao do scheduler/workers/rollout

## Contratos

### CreativePack

- `creative_pack_id`
- `account_id`
- `policy_stage`
- `theme`
- `variation_index`
- `angle`
- `title`
- `hook_candidates`
- `script_skeleton`
- `hashtags`
- `cta`
- `strategy_patch_id | null`
- `generated_at`

### Regras

- `creative_pack_id` eh deterministico
- mesma entrada logica gera `NOOP`
- payload diferente com mesma chave gera `CONFLICT`
- variacoes sao estaveis por `variation_index`
- `strategy_patch` so influencia quando `active=true`

## Persistencia

Path canonico:

`OUT/content/creative_packs/creative_packs.jsonl`

Semantica:
- append-only
- `WRITTEN | NOOP | CONFLICT`

## Integracao com strategy/policy

Inputs relevantes:
- `account_policy.stage`
- `account_policy.config`
- `strategy_patch.overrides`

Whitelisted:
- `a1_prefs_override`
- `a4_defaults_override`
- `a5_rewrite_defaults_override`

Exemplos de impacto:
- `a1_prefs_override.prefer_angles` influencia `angle`
- `a1_prefs_override.niches_boost` influencia hashtags
- `a4_defaults_override.force_number` influencia `title`
- `a4_defaults_override.increase_tension` influencia `hook_candidates`
- `a4_defaults_override.hook_style` influencia o tipo de hook
- `a5_rewrite_defaults_override.cta_style` influencia `cta`

## Eventos

Nao obrigatorios no v1.0.

Auditoria minima eh garantida pela persistencia append-only.

## Criterio de aceite

O D29 fecha se:
- gera `creative_pack` consistente
- variacoes sao estaveis
- `account_policy` e `strategy_patch` influenciam a saida sem quebrar determinismo
- persistencia idempotente funciona
