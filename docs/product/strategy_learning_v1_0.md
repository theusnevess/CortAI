# Strategy Learning v1.0

## Objetivo
Gerar patch conservador e reversível de estratégia por `(account_id, policy_stage, window_id)` usando apenas evidência real.

Sem LLM. Sem alteração de `policy_stage`. Sem relaxar gates constitucionais.

## Inputs canônicos
- `window_metrics` (D5)
- `real_batch_scorecard` (D7)
- `content_attribution[]` (D8)

## Output canônico
- `strategy_patch` append-only
- `proposal_summary`

## Escopo permitido (whitelist rígida)
Apenas overrides nas camadas:
1. `A1` preferences
2. `A4` defaults
3. `A5` rewrite defaults

Qualquer override fora de `A1/A4/A5` é ignorado com `SL_OVERRIDE_NOT_ALLOWED`.

## Heurística conservadora (determinística)
Patch ativo (`active=true`) apenas se:
- scorecard está verde (`status=STABLE`) E
- `videos_with_metrics >= min_videos_required` (v1.0: 5) E
- existe sinal consistente por feature (v1.0: >=60%)

Caso contrário:
- gera patch `NOOP` (`active=false`) com `reason_codes` explícitos.

## Persistência
- Path: `OUT/data/strategy_patches.jsonl`
- Chave lógica: `(account_id, window_id, policy_stage, patch_kind=STRATEGY_V1)`
- Idempotência:
  - payload igual => `NOOP`
  - payload diferente => `STRATEGY_PATCH_CONFLICT`

## Erros canônicos
- `SL_SCORECARD_MISSING`
- `SL_WINDOW_METRICS_MISSING`
- `SL_ATTRIBUTION_EMPTY`
- `SL_POLICY_STAGE_INVALID`

## Shape mínimo do patch
```json
{
  "patch_id": "sp_acc_ca_001_w_2026-03-02..._GROWTH",
  "account_id": "acc_ca_001",
  "window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
  "policy_stage": "GROWTH",
  "inputs": {
    "window_metrics_id": "wm_001",
    "scorecard_id": "sc_001",
    "attribution_count": 8
  },
  "overrides": {
    "a1_prefs_override": {},
    "a4_defaults_override": {},
    "a5_rewrite_defaults_override": {}
  },
  "active": false,
  "layers_applied": [],
  "reason_codes": ["INSUFFICIENT_VIDEOS"],
  "patch_kind": "STRATEGY_V1",
  "generated_at": "2026-03-05T03:00:00Z"
}
```
