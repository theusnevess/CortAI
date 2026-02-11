# Contrato de Observabilidade (CortAI)

Este documento define o contrato mínimo de observabilidade append-only do pipeline cognitivo.
O consumo é read-only a partir de JSONL/Observations; o destino é aggregate-only no Postgres.
Não há heurística nem lógica de decisão neste contrato.

## Eventos

### cognitive_loop_finished
Fonte: Observations (JSONL + Postgres `observations`).

Fatos obrigatórios:
- `event_type`
- `execution_status`
- `pipeline_status` (`completed` | `failed` | `blocked` | `truncated`)
- `termination_reason` (quando existir)
- `actions_executed`
- `last_action_type`
- `terminated`

Proibido em `facts`:
- Campos de caminho/path (ex.: `raw_video_minio_path`, `audio_local_path`)

### cognitive_metrics_alert
Fonte: agregação de telemetria.

Fatos obrigatórios:
- `event_type`
- `metric_date` (YYYY-MM-DD)
- `reasons` (lista de strings)
- `total_runs`, `failed_runs`, `blocked_runs`
- `failed_ratio`, `threshold`

Fatos opcionais:
- `action_type`
- `p95_ms`, `threshold_ms`, `n`

## Saída do pipeline

`write_artifact` gera um manifest determinístico em `storage/agent_output/<decision_id>.json` com:
- `process_id`, `decision_id`
- `pipeline_status`, `termination_reason`
- `segments_count`, `transcriptions_count`
- `artifact_paths.manifest_path`
- `artifacts.raw_video_minio_path`, `artifacts.audio_local_path`
- `created_at`

## Regras de dedupe

Agregação de telemetria:
- Uma linha por `metric_date` em `cognitive_metrics_daily` (upsert).

Emissão de alertas:
- Um alerta por `metric_date` para razões-base.

Emissão de loop finalizado:
- Um `cognitive_loop_finished` por `(process_id, source_outcome_id)`.
- Se `run_loop` receber um processo já terminado, usa stop reason `already_terminated` e tenta emitir uma vez.
- Se o par já existir, a emissão é ignorada (dedupe).

## Variáveis de ambiente

Telemetria:
- `COGNITIVE_LOOP_MAX_STEPS` (padrão: 10)

Alertas:
- `COGNITIVE_ALERT_MAX_PER_DAY` (padrão: 5)
- `COGNITIVE_ALERT_P95_TRANSCRIBE_MS` (padrão: 60000)
- `COGNITIVE_ALERT_P95_COLLECT_MS` (padrão: 90000)
- `COGNITIVE_ALERT_P95_EXTRACT_MS` (padrão: 30000)
- `COGNITIVE_ALERT_P95_SEGMENT_MS` (padrão: 30000)

## Endpoints da API

### GET /api/v1/metrics/daily
Query params:
- `start_date` (YYYY-MM-DD)
- `end_date` (YYYY-MM-DD)
- `days` (1..365)

### GET /api/v1/metrics/overview
Query params:
- `start_date` (YYYY-MM-DD)
- `end_date` (YYYY-MM-DD)
- `days` (1..365)

### GET /api/v1/metrics/alerts
Query params:
- `start_date` (YYYY-MM-DD)
- `end_date` (YYYY-MM-DD)
- `limit` (1..500)
- `offset` (>= 0)

## Exemplos

```bash
curl -s "http://localhost:8000/api/v1/metrics/daily?start_date=2026-02-10&end_date=2026-02-10"
curl -s "http://localhost:8000/api/v1/metrics/overview?days=7"
curl -s "http://localhost:8000/api/v1/metrics/alerts?start_date=2026-02-10&end_date=2026-02-10"
```
