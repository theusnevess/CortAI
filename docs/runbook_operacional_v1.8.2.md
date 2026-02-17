# CortAI - Runbook Operacional

Escopo: SLO + Guardrails + Timing + Runs + Receipts  
Versao alvo: >= v1.8.1  
Timezone padrao: UTC

## 0) Preflight (Contexto da Execucao)

Registrar manualmente antes de iniciar:

| Campo | Valor |
|---|---|
| `api_version` (`/health`) | |
| `ces_default_version` | |
| `git_tag` (se disponivel) | |
| `git_commit` (se disponivel) | |
| `alembic current` | |
| `generated_at_utc` | |

Comandos:

```bash
curl http://localhost:8000/health
docker exec -i cortai_api sh -lc "cd /app && alembic current"
```

### Opcional: modo automatizado via API

Endpoint read-only consolidado:

```bash
curl "http://localhost:8000/api/v1/observability/report?window_days=7&timing_minutes=15&limit_alerts=200&limit_receipts=50"
```

Leitura rapida:
- `status=PASS|WARN|FAIL`
- `checks[]` contem os mesmos criterios hard do runbook SQL
- `runs.worst` vazio gera `WARN` (nao `FAIL`) quando nao houver projecao de `ces_run`

## 1) Smoke HTTP (Contratos Publicos)

### 1.1 Health

Esperado:
- `status = ok`
- `api_version = 1.8.x`
- `ces_default_version = CES_v1`

### 1.2 Guardrails

Limit > 200:

```bash
curl ".../metrics/runs?start_date=2026-02-10&end_date=2026-02-11&limit=201"
```

Esperado:

```json
{
  "detail": {
    "error_type": "LimitTooHigh",
    "limit_requested": 201,
    "limit_max": 200
  }
}
```

Range > 31 dias:

```bash
curl ".../metrics/runs?start_date=2026-01-01&end_date=2026-04-01&limit=50"
```

Esperado:

```json
{
  "detail": {
    "error_type": "RangeTooLarge",
    "range_days": 91,
    "range_max": 31
  }
}
```

## 2) Telemetria Viva (ultimos 15 minutos)

```sql
SELECT
  COUNT(*) AS timing_events_15m,
  MIN(timestamp) AS min_ts,
  MAX(timestamp) AS max_ts
FROM observations
WHERE facts->>'event_type' = 'metrics_endpoint_timing'
  AND timestamp >= NOW() - INTERVAL '15 minutes';
```

PASS: `timing_events_15m > 0`

## 3) Sanity de duration_ms

```sql
SELECT COUNT(*) AS bad_duration
FROM observations
WHERE facts->>'event_type'='metrics_endpoint_timing'
  AND timestamp >= NOW() - INTERVAL '15 minutes'
  AND (
    (facts->>'duration_ms') IS NULL OR
    (facts->>'duration_ms') = '' OR
    (facts->>'duration_ms')::numeric < 0
  );
```

PASS: `bad_duration = 0`

## 4) SLO Diario por Endpoint (7 dias)

```sql
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
```

Criterios:
- pelo menos 1 endpoint com `count_requests > 0`
- `p95_ms` e `p99_ms` preenchidos

## 5) Dedupe explicito (metrics_endpoint_daily)

```sql
SELECT metric_date, endpoint, COUNT(*) AS n
FROM metrics_endpoint_daily
WHERE metric_date >= (CURRENT_DATE - INTERVAL '14 days')::date
GROUP BY 1,2
HAVING COUNT(*) > 1;
```

PASS: `0 linhas`

## 6) SLO Alerts (14 dias)

```sql
SELECT
  timestamp,
  process_id,
  facts->>'metric_date' AS metric_date,
  facts->>'endpoint' AS endpoint,
  facts->'reasons' AS reasons
FROM observations
WHERE facts->>'event_type' = 'metrics_slo_alert'
  AND timestamp >= NOW() - INTERVAL '14 days'
ORDER BY timestamp DESC;
```

Criterios:
- `reasons` coerente com `p95/p99/error_rate`
- sem duplicacao por `(metric_date, endpoint, reason)`

## 7) Top 20 Piores Runs (2 dias)

```sql
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
  NULLIF(facts->>'ces_run','')::numeric AS ces_run
FROM finished
WHERE rn = 1
  AND NULLIF(facts->>'ces_run','') IS NOT NULL
ORDER BY ces_run ASC
LIMIT 20;
```

PASS:
- `ces_run` numerico
- ordenacao ascendente coerente

## 8) Distribuicao de erros publish_receipts (7 dias)

```sql
SELECT
  COALESCE(error_type,'unknown') AS error_type,
  COUNT(*) AS n
FROM publish_receipts
WHERE created_at >= NOW() - INTERVAL '7 days'
  AND pipeline_status IN ('blocked','failed')
GROUP BY 1
ORDER BY n DESC;
```

## 9) Auditoria de Sanitizacao (30 dias)

```sql
SELECT COUNT(*) AS error_message_path_leaks_30d
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
```

PASS: `error_message_path_leaks_30d = 0`

## 10) Resumo 7 dias por endpoint

```sql
SELECT
  endpoint,
  SUM(count_requests) AS total_requests_7d,
  AVG(p95_ms) AS avg_p95_ms_7d,
  AVG(error_rate) AS avg_error_rate_7d
FROM metrics_endpoint_daily
WHERE metric_date >= (CURRENT_DATE - INTERVAL '7 days')::date
GROUP BY endpoint
ORDER BY total_requests_7d DESC;
```

## Template de Evidencia Operacional

```text
CortAI Observability Report - vX.Y.Z
Generated at: <UTC>

Health:
- api_version:
- ces_default_version:

Timing (15m):
- timing_events_15m:
- bad_duration:

SLO Daily:
- endpoints ativos:

Alerts:
- count_last_14d:

Receipts:
- blocked/failed_last_7d:
- path_leaks_30d:

Status Final: PASS | WARN | FAIL
Observacoes:
```

## Criterios Globais de PASS

- telemetria viva
- `duration_ms` valido
- `metrics_endpoint_daily` populado
- sem duplicacao por endpoint/dia
- alertas idempotentes
- sanitizacao integra
- `ces_run` numerico quando presente
