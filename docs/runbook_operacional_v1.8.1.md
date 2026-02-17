Runbook Operacional - CortAI v1.8.1 (Metrics SLO + Guardrails + Timing)

Versao: v1.8.1
Timezone padrao: UTC
Escopo: validar que a observabilidade de metricas esta viva, consistente e auditavel apos release.

0) Preflight (HTTP)

0.1 Healthcheck (versao e CES default)

PASS se:

status=ok

api_version=1.8.1

ces_default_version=CES_v1

Exemplo:

GET /health

0.2 Guardrails do endpoint de runs

PASS se:

/metrics/runs?limit=201 retorna 400 com LimitTooHigh

/metrics/runs com range > 31 dias retorna 400 com RangeTooLarge

Criterios:

detail.error_type == "LimitTooHigh"

detail.limit_requested e int

detail.limit_max == 200

E:

detail.error_type == "RangeTooLarge"

detail.range_days e int

detail.range_max == 31

1) Smoke HTTP (gera telemetria de timing)

Execute pelo menos uma vez cada endpoint:

1. GET /api/v1/metrics/overview?days=7

2. GET /api/v1/metrics/runs?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&limit=50&offset=0

3. GET /api/v1/metrics/runs/{process_id} (use um process_id real do /runs)

Objetivo: garantir que metrics_endpoint_timing esta sendo emitido em Observations e persistido (JSONL + Postgres).

2) SQL Bundle - Observability Report (v1.8.1)

Rode em Postgres (UTC).
Obs: publish_receipts.pipeline_status e o campo canonico.

2.0 Header / Contexto

SELECT
  NOW() AT TIME ZONE 'UTC' AS generated_at_utc,
  CURRENT_DATE AS current_date_utc;

2.1 Telemetria viva (ultimos 15 min): metrics_endpoint_timing

SELECT
  COUNT(*) AS timing_events_15m,
  MIN(timestamp) AS min_ts,
  MAX(timestamp) AS max_ts
FROM observations
WHERE facts->>'event_type' = 'metrics_endpoint_timing'
  AND timestamp >= NOW() - INTERVAL '15 minutes';

2.2 Timing por endpoint + sanity de duration (ultimos 15 min)

SELECT
  facts->>'endpoint' AS endpoint,
  facts->>'method' AS method,
  facts->>'status_code' AS status_code,
  COUNT(*) AS n_events,
  MIN((facts->>'duration_ms')::numeric) AS min_ms,
  MAX((facts->>'duration_ms')::numeric) AS max_ms
FROM observations
WHERE facts->>'event_type' = 'metrics_endpoint_timing'
  AND timestamp >= NOW() - INTERVAL '15 minutes'
GROUP BY 1,2,3
ORDER BY endpoint, status_code;

2.3 Dedupe de timing (nao pode haver 2 eventos "iguais" por request)

SELECT
  COUNT(*) AS duplicated_events
FROM (
  SELECT
    facts->>'endpoint' AS endpoint,
    facts->>'method' AS method,
    facts->>'timestamp' AS req_ts,
    COUNT(*) AS n
  FROM observations
  WHERE facts->>'event_type' = 'metrics_endpoint_timing'
    AND timestamp >= NOW() - INTERVAL '15 minutes'
  GROUP BY 1,2,3
  HAVING COUNT(*) > 1
) t;

2.4 Ultimos 7 dias: SLO diario por endpoint

SELECT
  metric_date,
  endpoint,
  count_requests,
  p50_ms,
  p95_ms,
  p99_ms,
  error_rate
FROM metrics_endpoint_daily
WHERE metric_date >= (CURRENT_DATE - INTERVAL '7 days')::date
ORDER BY metric_date ASC, endpoint ASC;

2.5 Pior dia por endpoint (ultimos 14 dias)

SELECT DISTINCT ON (endpoint)
  endpoint,
  metric_date,
  count_requests,
  p95_ms,
  p99_ms,
  error_rate
FROM metrics_endpoint_daily
WHERE metric_date >= (CURRENT_DATE - INTERVAL '14 days')::date
ORDER BY endpoint, p95_ms DESC, error_rate DESC, metric_date DESC;

2.6 SLO Alerts (ultimos 14 dias)

SELECT
  timestamp,
  process_id,
  facts->>'metric_date' AS metric_date,
  facts->>'endpoint' AS endpoint,
  facts->'reasons' AS reasons,
  facts
FROM observations
WHERE facts->>'event_type' = 'metrics_slo_alert'
  AND timestamp >= NOW() - INTERVAL '14 days'
ORDER BY timestamp DESC
LIMIT 200;

2.7 Top 20 piores runs (CES_run) - ultimos 2 dias (cast seguro)

Obs: so funciona se o cognitive_loop_finished estiver projetando ces_run em facts.
WITH finished AS (
  SELECT
    process_id,
    timestamp,
    facts,
    ROW_NUMBER() OVER (PARTITION BY process_id ORDER BY timestamp DESC) AS rn
  FROM observations
  WHERE facts->>'event_type' = 'cognitive_loop_finished'
    AND timestamp >= NOW() - INTERVAL '2 days'
)
SELECT
  process_id,
  timestamp AS finished_ts,
  COALESCE(facts->>'pipeline_status', 'unknown') AS pipeline_status,
  facts->>'execution_status' AS execution_status,
  facts->>'ces_run_version' AS ces_run_version,
  NULLIF(facts->>'ces_run','')::numeric AS ces_run,
  NULLIF(facts->'ces_run_components'->>'status','')::numeric AS s_status,
  NULLIF(facts->'ces_run_components'->>'actions','')::numeric AS s_actions,
  NULLIF(facts->'ces_run_components'->>'latency','')::numeric AS s_latency,
  NULLIF(facts->'ces_run_components'->>'trunc','')::numeric AS s_trunc,
  facts->>'ces_run_reason' AS ces_run_reason
FROM finished
WHERE rn = 1
  AND NULLIF(facts->>'ces_run','') IS NOT NULL
ORDER BY ces_run ASC
LIMIT 20;

2.8 publish_receipts: distribuicao de erros (ultimos 7 dias) com NULL visivel

SELECT
  COALESCE(error_type, 'unknown') AS error_type,
  COUNT(*) AS n
FROM publish_receipts
WHERE created_at >= NOW() - INTERVAL '7 days'
  AND pipeline_status IN ('blocked','failed')
GROUP BY 1
ORDER BY n DESC;

2.9 publish_receipts: ultimos 50 blocked/failed (ultimos 7 dias)

SELECT
  process_id,
  publish_decision_id,
  manifest_decision_id,
  pipeline_status,
  error_type,
  error_message,
  created_at
FROM publish_receipts
WHERE created_at >= NOW() - INTERVAL '7 days'
  AND pipeline_status IN ('blocked','failed')
ORDER BY created_at DESC
LIMIT 50;

2.10 Auditoria de sanitizacao (30 dias): vazamento de paths/artefatos em error_message

SELECT
  COUNT(*) AS error_message_path_leaks_30d
FROM publish_receipts
WHERE created_at >= NOW() - INTERVAL '30 days'
  AND (
    error_message ILIKE '%/tmp%' OR
    error_message ILIKE '%storage/%' OR
    error_message ILIKE '%videos-raw%' OR
    error_message ILIKE '%.mp4%' OR
    error_message ILIKE '%.wav%' OR
    error_message ILIKE '%.json%' OR
    error_message ILIKE '%agent_output%'
  );

2.11 Resumo final (ultimos 7 dias): volume e qualidade por endpoint

SELECT
  endpoint,
  SUM(count_requests) AS total_requests_7d,
  AVG(p95_ms) AS avg_p95_ms_7d,
  AVG(error_rate) AS avg_error_rate_7d
FROM metrics_endpoint_daily
WHERE metric_date >= (CURRENT_DATE - INTERVAL '7 days')::date
GROUP BY endpoint
ORDER BY total_requests_7d DESC;

3) Checklist PASS/FAIL (com base no bundle)

3.1 Timing / Telemetria

PASS se timing_events_15m > 0

PASS se o query 2.2 mostra os 3 endpoints:

/api/v1/metrics/runs

/api/v1/metrics/runs/{process_id}

/api/v1/metrics/overview

PASS se min_ms > 0 e max_ms > 0

PASS se duplicated_events = 0

3.2 Agregacao diaria SLO

PASS se 2.4 retorna linhas nos ultimos 7 dias

PASS se existe pelo menos 1 endpoint com count_requests > 0 nos ultimos 7 dias

PASS se nao ha duplicacao por (metric_date, endpoint) (implicito pela tabela + idempotencia do job)

3.3 Sanitizacao publish_receipts

PASS se error_message_path_leaks_30d = 0

3.4 Alertas SLO

PASS se, quando existirem alertas (2.6), reasons forem coerentes com:

p95_ms, p99_ms e/ou error_rate

PASS se nao existir duplicacao logica por (metric_date, endpoint, reason) (dedupe)

3.5 CES_run report

PASS se 2.7 retorna ces_run numerico

OK se vazio quando cognitive_loop_finished ainda nao projeta ces_run em facts (nao e falha do SLO)

4) Template de evidencia operacional (para anexar em PR/Issue)

Preencha:

generated_at_utc: <resultado do 2.0>

timing_events_15m: <resultado do 2.1>

duplicated_events: <resultado do 2.3>

endpoints vistos (2.2): <lista>

metrics_endpoint_daily linhas 7d: <quantidade>

pelo menos 1 endpoint count_requests>0: <sim/nao>

error_message_path_leaks_30d: <resultado do 2.10>

SLO alerts ultimos 14d: <0 / N + resumo reasons>

Top worst runs: <0 / N + motivo>
