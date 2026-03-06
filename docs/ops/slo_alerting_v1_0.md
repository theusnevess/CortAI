# SLO + Alerting v1.0

## Objetivo

Transformar as metricas do D18 em limites operacionais claros:

- SLOs
- SLIs
- error budget
- thresholds de alerta
- acoes operacionais minimas

## SLOs congelados

### Event Query

- `event_query_p95_ms`
- `event_query_error_rate`
- `event_query_fallback_rate`

### Pipeline

- `window_pipeline_success_rate`
- `window_post_pipeline_success_rate`

### Concorrencia

- `lease_denied_rate`
- `double_apply_count`
- `snapshot_partial_count`

### Learning / Patch

- `strategy_patch_conflict_rate`

## Thresholds v1.0

### CRITICAL imediato

- `double_apply_count > 0`
- `snapshot_partial_count > 0`
- `event_query_error_rate >= 0.05`

### WARN

- `event_query_p95_ms >= 250`
- `event_query_fallback_rate >= 0.10`
- `strategy_patch_conflict_rate >= 0.02`
- `lease_denied_rate >= 0.05`

### Error budget

`event_query_error_rate`

- alvo: `99.5%` de disponibilidade
- budget: `0.5%`
- budget consumido `>= 100%` gera alerta persistente

## Severidades e acoes

- `INFO` -> `OBSERVE`
- `WARN` -> `DEGRADE`
- `CRITICAL` -> `BLOCK`

## Artefatos

O D19 persiste:

- `OUT/ops/alerts.jsonl`
- `OUT/ops/slo_status.json`

## Regra arquitetural

O D19 nao altera contrato do pipeline.

Ele apenas:

1. avalia metricas
2. classifica severidade
3. gera alertas acionaveis
4. persiste estado operacional
