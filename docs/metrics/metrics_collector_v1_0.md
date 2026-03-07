# D33 - Metrics Collector v1.0

## Objetivo

Coletar metricas reais de performance dos videos para alimentar:

- D30 - Platform Intelligence
- D31 - Experiment Framework
- D32 - Advanced Attribution
- D26 - Strategy Observatory

Sem alterar o caminho de publish.

## Fluxo

`Platform API -> Metrics Collector Worker -> Normalized Metrics Model -> OUT/metrics/video_metrics.jsonl`

## Persistencia

Arquivo:

`OUT/metrics/video_metrics.jsonl`

Semantica:
- append-only
- idempotencia por `(publish_id, collected_at_bucket)`
- mesma coleta -> `NOOP`
- payload diferente na mesma chave -> `CONFLICT`

## Modelo canônico

### VideoMetricsRecord

- `metrics_id`
- `publish_id`
- `account_id`
- `video_id`
- `views`
- `likes`
- `comments`
- `shares`
- `watch_time_total`
- `avg_watch_time`
- `completion_rate`
- `view_3s_rate`
- `view_5s_rate`
- `collected_at`
- `collected_at_bucket`
- `age_hours`
- `provider`

## Frequencia recomendada

- primeiras 24h: a cada 30 min
- 24h-72h: a cada 2h
- acima de 72h: diario

## Eventos

- `METRICS/collection_started`
- `METRICS/collection_completed`
- `METRICS/collection_failed`
- `METRICS/api_rate_limited`

## Retry policy

- `max_attempts = 3`
- retry apenas para:
  - timeout
  - rate limit
  - erro 5xx transitório

## Integracao

Input obrigatorio:
- `publish_record`

O collector nao inventa video fora de `publish_record`.

## Criterio de aceite

O D33 fecha se:
- coleta normal funciona
- idempotencia funciona
- erro de API e retry funcionam
- persistencia append-only funciona
- integracao com `publish_record` esta confirmada
