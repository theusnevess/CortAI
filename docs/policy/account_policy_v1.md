# Account Policy Spec v1.0

## Objetivo
Definir resolucao de stage por conta de forma simples, deterministica e auditavel.

## Enum fechado
- `GROWTH`
- `MONETIZATION`
- `RECOVERY`

## Precedencia efetiva
`RECOVERY > MONETIZATION > GROWTH`

## Regras v1.0 (congeladas)
1. Dados insuficientes:
   - Se `videos_last_10_count < 10` -> `GROWTH`.
2. Recovery:
   - Se `videos_last_10_count >= 10` e `avg_3s_retention_last_10 < 0.35` -> `RECOVERY`.
3. Monetization:
   - Se `followers >= 10000` e `avg_rpm_last_10 >= target_rpm` -> `MONETIZATION`.
4. Default:
   - Caso contrario -> `GROWTH`.

## Frequencia de atualizacao
- Atualizacao por janela de 72h.

## Invariantes
- Resolver puro: sem IO, sem env, sem log.
- Stage sempre pertence ao enum fechado.
- Fallback de dados insuficientes sempre retorna `GROWTH`.

## Policy composition (v1.0)
- `compose_policy(account_id, metrics, target_rpm)`:
  - Resolve stage via `resolve_policy(...)`.
  - Aplica `DEFAULT_POLICY_BY_STAGE_v1.0[stage]`.
  - Retorna policy completa com:
    - `stage`
    - `targets`
    - `constraints`
    - `metrics_window.updated_at`
    - `metrics_window.videos_considered`

## Out of scope (este PR)
- Injeção no runner antes de A1.
- Integracao com governanca do runner.

## Tracking
- TODO: Runner injection pending: requires strike-team stack present on remote base.
