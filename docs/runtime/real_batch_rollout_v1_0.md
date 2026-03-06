# Real 72h Batch Production Rollout v1.0

## Objetivo

Executar o primeiro ciclo real de 72h em modo controlado.

O rollout desta etapa é:

- piloto
- pequeno
- allowlisted
- reversível

## Regras congeladas

- rollout começa com poucas contas
- scheduler só agenda contas allowlisted
- worker respeita kill switch e policy de rollout
- rollout desabilitado impede novas tasks
- kill switch impede novas execuções

## Critério GO do Batch-0

O batch piloto é válido se gerar:

- `window_metrics`
- `scorecard`
- `content_attribution`
- `strategy_patch`
- `patch_applied` ou `NOOP` legítimo

Sem:

- `double_apply`
- `snapshot_partial`
- alerta crítico
- conflict inesperado

## Critério NO-GO

Parar rollout se houver:

- `double_apply > 0`
- `snapshot_partial > 0`
- `event_query_error_rate` crítico
- `data_consistency_guard` bloqueando contas piloto sem justificativa

## Artefatos

Saída mínima:

- `OUT/rollout/pilot_rollout_report.md`
- `OUT/rollout/pilot_rollout_report.json`
- `OUT/rollout/pilot_batch_window_summary.json`
- `OUT/rollout/pilot_alerts.json`
