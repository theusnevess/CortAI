# Contrato de Observabilidade (CortAI)

Este documento define o contrato minimo de observabilidade append-only do pipeline cognitivo.
O consumo e read-only a partir de JSONL/Observations; o destino e aggregate-only no Postgres.
Nao ha heuristica nem logica de decisao neste contrato.

## Eventos

### cognitive_loop_finished
Fonte: Observations (JSONL + Postgres `observations`).

Fatos obrigatorios:
- `event_type`
- `execution_status`
- `pipeline_status` (`completed` | `failed` | `blocked` | `truncated` | `published`)
- `termination_reason` (quando existir)
- `actions_executed`
- `last_action_type`
- `terminated`

Proibido em `facts`:
- Campos de caminho/path (ex.: `raw_video_minio_path`, `audio_local_path`, `manifest_path`)

### cognitive_metrics_alert
Fonte: agregacao de telemetria.

Fatos obrigatorios:
- `event_type`
- `metric_date` (YYYY-MM-DD)
- `reasons` (lista de strings)
- `total_runs`, `failed_runs`, `blocked_runs`
- `failed_ratio`, `threshold`

Fatos opcionais:
- `action_type`
- `p95_ms`, `threshold_ms`, `n`
- `ces_version`, `window_days`, `required_bad_days`, `bad_days_in_window`, `days_with_runs_in_window`, `ces_samples`

Reasons canonicamente suportados:
- `blocked_runs`
- `failed_ratio`
- `ces_regression:CES_v1`

## Saida do pipeline

`write_artifact` gera um manifest deterministico em `storage/agent_output/<decision_id>.json` com:
- `process_id`, `decision_id`
- `pipeline_status`, `termination_reason`
- `segments_count`, `transcriptions_count`
- `artifact_paths.manifest_path`
- `artifacts.raw_video_minio_path`, `artifacts.audio_local_path`
- `created_at`

`publish_manifest` consome apenas o manifest (manifest-only) via `decision_id`.

## Receipt de publicacao

A auditoria de publish e persistida em `publish_receipts` com idempotencia por
`publish_decision_id`.

Campos principais:
- `publish_decision_id` (chave unica)
- `process_id`
- `manifest_decision_id`
- `pipeline_status` (`published` | `blocked` | `failed`)
- `execution_status` (`success` | `blocked` | `failed`)
- `target`
- `external_post_id` (quando existir)
- `error_type`, `error_message` (sem paths)
- `published_at`, `created_at`, `updated_at`

## Regras de dedupe

Agregacao de telemetria:
- Uma linha por `metric_date` em `cognitive_metrics_daily` (upsert).

Emissao de alertas:
- Dedupe por (`metric_date`, `reason`).
- Pode haver mais de um alerta por dia quando os motivos forem diferentes.

Emissao de loop finalizado:
- Um `cognitive_loop_finished` por `(process_id, source_outcome_id)`.
- Se `run_loop` receber um processo ja terminado, usa `stop_reason=already_terminated` e tenta emitir uma vez.
- Se o par ja existir, a emissao e ignorada (dedupe).

## Cognitive Efficiency Score (CES)

### CES Versions

Regra de versionamento:
- `CES_v1` e congelado e imutavel.
- `CES_v2` e congelado e imutavel.
- Novas formulas entram como novas versoes (`CES_v3`, `CES_v4`, ...).
- `ces_default_version` inicial: `CES_v1`.
- Campos top-level (`ces`, `ces_version`, `ces_reason`, `ces_components`, `budgets_used`) sempre refletem a versao default.
- `CES_v2` fica disponivel em `ces_versions`, sem alterar o default.

Shape canonicamente exposto por item:
- `ces_default_version`
- `ces`
- `ces_version`
- `ces_reason`
- `ces_components`
- `budgets_used`
- `ces_versions` (`CES_v1`, `CES_v2`)

### CES_v1

Acoes canonicamente consideradas no `S_latency` e em `budgets_used`:
- `collect_video`
- `extract_audio`
- `segment_audio`
- `transcribe_segments`
- `write_artifact`
- `publish_manifest`

Elegibilidade:
- A acao entra no latency score apenas quando `n >= 10`.

Regra:
- `unknown` e excluido por design do latency score e de `budgets_used`.
- `unknown` pode aparecer em `latency_by_action` (telemetria bruta), mas nao participa de `S_latency`, pesos `n_a`, budgets `B_a` ou do CES.

Regra de dia sem execucao:
- Se `total_runs = 0`, retorna `ces = null` e `ces_reason = "no_runs"`.

### CES_v2

CES_v2 usa os mesmos sinais de entrada do CES_v1 (`status`, `actions`, `latency`, `trunc`) e
mantem as mesmas restricoes de whitelist/elegibilidade:
- whitelist de acoes identica ao CES_v1
- `n >= 10` para acao participar de `S_latency`
- `unknown` excluido por design
- `total_runs = 0` => `ces = null` e `ces_reason = "no_runs"`

Diferenca principal:
- `S_latency` usa penalizacao suave por excesso relativo ao budget da acao.
- Para cada acao elegivel:
  - `budget_ms = ceil(p95_ms * 1.10)`
  - `ratio = p95_ms / budget_ms`
  - `score_a = 1` quando `ratio <= 1`
  - `score_a = clamp(1 - k * (ratio - 1), 0, 1)` quando `ratio > 1` (com `k = 0.7`)
  - `S_latency` e a media ponderada por `n` das acoes elegiveis.

Politica:
- CES_v2 nao altera CES_v1; apenas expande a leitura em `ces_versions`.

### CES Window Counter

`summary.ces_bad_days_in_window`:
- Numero de dias ruins dentro da janela `COGNITIVE_ALERT_CES_WINDOW_DAYS`.
- Dia ruim: `ces` (versao default) `< COGNITIVE_ALERT_CES_THRESHOLD`.
- `ces_window_effective_days` conta apenas dias validos (`ces != null` e `ces_reason != "no_runs"`).
- Exclui dias com `ces = null` (`ces_reason = "no_runs"`).
- Nao e persistido; e calculado dinamicamente no endpoint.
- Usa a mesma regra base do alerta `ces_regression:CES_v1`.

Campos de janela expostos no `summary`:
- `ces_window_days`
- `ces_window_effective_days`
- `ces_threshold`
- `ces_bad_days_required`
- `ces_bad_days_in_window`
- `ces_bad_days_ratio`

Regra de ratio:
- `ces_bad_days_ratio = ces_bad_days_in_window / ces_window_effective_days` quando `effective_days > 0`.
- `ces_bad_days_ratio = null` quando `effective_days = 0`.

## Variaveis de ambiente

Telemetria:
- `COGNITIVE_LOOP_MAX_STEPS` (padrao: 10)

Alertas:
- `COGNITIVE_ALERT_MAX_PER_DAY` (padrao: 5)
- `COGNITIVE_ALERT_P95_TRANSCRIBE_MS` (padrao: 60000)
- `COGNITIVE_ALERT_P95_COLLECT_MS` (padrao: 90000)
- `COGNITIVE_ALERT_P95_EXTRACT_MS` (padrao: 30000)
- `COGNITIVE_ALERT_P95_SEGMENT_MS` (padrao: 30000)
- `COGNITIVE_ALERT_CES_ENABLED` (padrao: 1)
- `COGNITIVE_ALERT_CES_THRESHOLD` (padrao: 85)
- `COGNITIVE_ALERT_CES_BAD_DAYS` (padrao: 3)
- `COGNITIVE_ALERT_CES_WINDOW_DAYS` (padrao: 7)

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
