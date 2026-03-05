# Strategy Patch Application v1.0

## Objetivo
Aplicar `strategy_patch` (D9) ao Account Registry de forma determinística, auditável, idempotente e reversível.

## Pipeline lógico
```text
strategy_patch
  -> whitelist_validation
  -> stage_match_check
  -> merge_registry_config
  -> persist_patch_application
  -> emit_audit_event
```

## Regras congeladas

### Whitelist rígida
Somente camadas permitidas:
- `A1`
- `A4`
- `A5`

Exemplos permitidos:
- `A1.topic_bias`
- `A4.hook_style`
- `A5.rewrite_flags`

Proibido:
- `policy_stage`
- `allocation`
- `retention_floor`
- `max_retry`

### Idempotência
Chave lógica:
- `(account_id, window_id, policy_stage)`

Resultado:
- inexistente -> `APPLY`
- payload igual -> `NOOP`
- payload diferente -> `CONFLICT`

### Stage mismatch
Se `patch.policy_stage != account_policy.stage`:
- `NOOP`
- sem aplicação de override

### Rollback
Rollback automático quando:
- patch ativo
- `next_window_scorecard.performance_color == RED`

Ação:
- remove `strategy_overrides.active`
- emite `SL/strategy_patch_rolled_back`

## Merge determinístico de configuração
Ordem fixa:
1. `defaults_by_stage`
2. `account_policy`
3. `strategy_overrides.active`

## Persistência
- `OUT/data/strategy_patch_applications.jsonl`
- append-only

## Eventos
- `SL/strategy_patch_applied`
- `SL/strategy_patch_noop`
- `SL/strategy_patch_conflict`
- `SL/strategy_patch_rolled_back`

Payload mínimo:
- `account_id`
- `window_id`
- `policy_stage`
- `patch_id`
- `timestamp`
