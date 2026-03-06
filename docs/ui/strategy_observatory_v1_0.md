# D26 - Strategy Observatory v1.0

## Objetivo

Tornar o learning loop legível para operador sem alterar a lógica de aprendizado.

O observatório deve mostrar:

- patches gerados
- patches aplicados
- impacto por janela
- evolução temporal da estratégia

## Fonte de dados

O D26 é somente leitura e usa artefatos já existentes:

- `OUT/data/strategy_patches.jsonl`
- `OUT/data/strategy_patch_applications.jsonl`
- `OUT/data/scorecards.jsonl`
- `OUT/data/window_metrics.jsonl`

Quando algum artefato não existir, a API deve responder com listas vazias em vez de quebrar.

## Entidades exibidas

### Patch

- `patch_id`
- `account_id`
- `window_id`
- `policy_stage`
- `reason_code`
- `created_at`
- `status`

Status canônicos:

- `generated`
- `applied`
- `noop`
- `conflict`
- `reverted`

### Impacto

Cada patch deve expor:

- `window_id_before`
- `window_id_after`
- `scorecard_delta`

O delta é calculado como:

`valor_after - valor_before`

Sem heurística sofisticada no v1.0.

### Timeline

Linha temporal por conta:

- `window_id`
- `patch_id`
- `policy_stage`
- `status`
- `reason_code`
- `created_at`

## Endpoints

- `GET /api/v1/ops/strategy/patches`
- `GET /api/v1/ops/strategy/patch/{patch_id}`
- `GET /api/v1/ops/strategy/impact`
- `GET /api/v1/ops/strategy/timeline`

## Regras

- read-only obrigatório
- nenhuma mutação de patch ou policy
- patch inexistente deve falhar explicitamente
- dados inconsistentes devem degradar para campos nulos, nunca derrubar a API inteira

## Out of Scope

- edição manual de estratégia
- rollback manual de patch
- mudança no learner
- algoritmos novos de impacto
