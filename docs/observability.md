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
- `CES_v3` e experimental.
- Novas formulas entram como novas versoes (`CES_v3`, `CES_v4`, ...).
- `ces_default_version` inicial: `CES_v1`.
- Campos top-level (`ces`, `ces_version`, `ces_reason`, `ces_components`, `budgets_used`) sempre refletem a versao default.
- `CES_v2` e `CES_v3` ficam disponiveis apenas em `ces_versions`, sem alterar o default.

Shape canonicamente exposto por item:
- `ces_default_version`
- `ces`
- `ces_version`
- `ces_reason`
- `ces_components`
- `budgets_used`
- `ces_versions` (`CES_v1`, `CES_v2`, `CES_v3`)

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

### CES_v3 (experimental)

CES_v3 usa os mesmos sinais de entrada do CES_v1/CES_v2 (`status`, `actions`, `latency`, `trunc`) e
mantem as mesmas restricoes de whitelist/elegibilidade:
- whitelist de acoes identica ao CES_v1
- `n >= 10` para acao participar de `S_latency`
- `unknown` excluido por design
- `total_runs = 0` => `ces = null` e `ces_reason = "no_runs"`

Diferenca principal:
- `S_latency` usa budget por acao com fonte `dynamic_baseline_14d`.
- Regra de budget no v3:
  - primeiro tenta `latency_dynamic_baseline[action].budget_ms` (source `dynamic_14d`);
  - sem baseline elegivel, faz fallback para budget fixo v1 (`fixed_v1`).

Politica:
- CES_v3 e experimental e fica disponivel somente em `ces_versions`.
- CES_v3 nao altera `ces_default_version` nem os campos top-level.

### Baseline dinamico de latencia (read-only)

Objetivo:
- Expor baseline dinamico por acao como telemetria auxiliar, sem alterar o score default.

Regra canonica:
- `B_a_dynamic = ceil(median(p95_ms_ultimos_14_dias) * 1.10)`.
- Considera somente acoes da whitelist CES.
- Considera somente dias com `total_runs > 0`.
- Considera somente amostras por acao com `n >= 10`.
- Exclui `unknown` por design.

Fallback:
- Sem historico elegivel para a acao, usa budget fixo v1 (`fallback_fixed_v1`).

Exposicao no endpoint:
- `latency_dynamic_baseline_window_days`
- `latency_dynamic_baseline` (por acao: `budget_ms`, `source`, `samples_used`)

Invariante:
- Baseline dinamico e read-only e nao altera `ces`, `ces_version` nem `ces_default_version`.

### Cognitive Efficiency Score - Run-level

Versao:
- `CES_run_v1` (congelado e imutavel).
- Mudancas futuras geram novas versoes (`CES_run_v2`, `CES_run_v3`, ...).

Fonte de verdade:
- Para cada `process_id`, usar o `cognitive_loop_finished` mais recente por `timestamp`.
- Evento de fechamento: `facts.event_type = "cognitive_loop_finished"`.
- Dedupe de emissao continua por `(process_id, source_outcome_id)`.

Componentes do `CES_run_v1`:
- `S_status` por tabela fixa:
  - `published=1.00`
  - `completed=0.98`
  - `truncated=0.70`
  - `failed=0.35`
  - `blocked=0.10`
  - `unknown=0.00`
- `S_actions = clamp((6 - A) / (6 - 1), 0, 1)`, com `A = actions_executed`.
  - Se `actions_executed` ausente: `A=0` e `S_actions=0` (fallback deterministico).
- `S_trunc = 0` quando `pipeline_status = truncated`, senao `1`.
- Latencia real por run:
  - Duracao por acao: `duration_ms = outcome.timestamp - decision.timestamp`.
  - Pareamento por `process_id` + `source_decision_id == decision_id`.
  - Em caso de multiplos outcomes para a mesma decision, usar o mais recente por timestamp.
  - Whitelist: `collect_video`, `extract_audio`, `segment_audio`, `transcribe_segments`, `write_artifact`, `publish_manifest`.
  - `unknown` e excluido por design.
  - Elegibilidade run-level: a acao entra no score quando `n >= 3` dentro do run.
  - Budgets fixos iniciais (ms):
    - `collect_video`: 20000
    - `extract_audio`: 5000
    - `segment_audio`: 8000
    - `transcribe_segments`: 30000
    - `write_artifact`: 3000
    - `publish_manifest`: 3000
  - Score por acao:
    - `ratio = p95_ms / budget_ms`
    - se `ratio <= 1`: `score_a = 1`
    - se `ratio > 1`: `score_a = clamp(1 - 0.7 * (ratio - 1), 0, 1)`
  - `S_latency` e media ponderada por `n` das acoes elegiveis.
  - Se nao houver acao elegivel:
    - `S_latency = 1.0`
    - `latency_measured = false`
    - `budgets_used = {}`
  - Auditoria read-only do calculo:
    - `latency_pairs_used`: pares `decision -> outcome` usados.
    - `latency_pairs_ignored`: pares ignorados (sem match, fora da whitelist, timestamp invalido).
    - `latency_pairs_inverted`: pares com `decision_ts > outcome_ts`.
  - `latency_pairs_*` nao alteram o score; sao apenas telemetria de auditoria.
  - Invariante esperado: `latency_pairs_inverted = 0`; se maior que zero, tratar como investigacao de clock drift/ordem de eventos.

Contrato operacional v1.2 (lean list / heavy debug):
- `GET /api/v1/metrics/runs` e endpoint de lista lean:
  - retorna apenas `process_id`, `timestamp_finished`, `pipeline_status`, `ces_run`,
    `ces_run_version`, `ces_run_reason`, `ces_run_components`, `latency_measured`,
    `latency_pairs_inverted`.
  - nao retorna campos pesados (`budgets_used`, `latency_pairs_used`, `latency_pairs_ignored`).
  - nao executa calculo de latencia real por acao (run-level pesado).
- `GET /api/v1/metrics/runs/{process_id}` permanece endpoint de debug heavy:
  - inclui `latency_breakdown` (budgets por acao), `latency_pairs_used/ignored/inverted`,
    `links`, `artifact_refs`, `last_error` sanitizado.

### Run debug view

Endpoint read-only:
- `GET /api/v1/metrics/runs/{process_id}`

Contrato minimo:
- `run_summary` com status final, CES_run, componentes e auditoria de latencia (`latency_pairs_*`).
- `links` com `observation_id`, `source_outcome_id`, `source_decision_id`, `manifest_decision_id`, `publish_decision_id`.
- `artifact_refs` com `manifest_path` e `publish_receipt_id`.
- `last_error` sanitizado (`error_type`, `error_message` sem paths sensiveis).
- `latency_breakdown` somente para acoes whitelist.
- `missing_fields` quando algum dado opcional nao estiver disponivel.

Fonte de verdade:
- ultimo `cognitive_loop_finished` no Postgres para o `process_id`.

Pesos do `CES_run_v1`:
- `alpha=0.60` (status)
- `beta=0.15` (actions)
- `gamma=0.20` (latency)
- `delta=0.05` (trunc)

Formula:
- `CES_run_v1 = 100 * (alpha*S_status + beta*S_actions + gamma*S_latency + delta*S_trunc)`
- Clamp final em `[0, 100]`.

Casos ausentes:
- Se nao existir `cognitive_loop_finished` para o `process_id`: `ces_run = null`, `ces_run_reason = "missing_finished_observation"`.
- Se `pipeline_status` ausente no evento: `pipeline_status = "unknown"`, `ces_run = null`, `ces_run_reason = "missing_pipeline_status"`.

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
- `include_reasons` (bool, default `false`)
- `include_baseline` (bool, default `false`)

Contrato de alertas no overview:
- `alerted` e `alert_count` sempre presentes.
- `alert_reasons` sempre presente no shape:
  - default (`include_reasons=false`): `[]`
  - `include_reasons=true`: reasons deduplicadas/ordenadas.
- `latency_dynamic_baseline` sempre presente no shape:
  - default (`include_baseline=false`): `{}`
  - `include_baseline=true`: baseline por acao (`budget_ms`, `source`, `samples_used`).
- Fonte DB-first:
  - overview le `cognitive_metrics_daily` (incluindo `alert_count`/`alert_reasons` materializados no agregado diario)
  - nao executa lookup de alertas em `observations` durante a request
  - resposta usa cache read-only curto (TTL 10s) por query para reduzir p95 sob concorrencia

### GET /api/v1/metrics/alerts
Query params:
- `start_date` (YYYY-MM-DD)
- `end_date` (YYYY-MM-DD)
- `limit` (1..500)
- `offset` (>= 0)

### GET /api/v1/observability/report
Query params:
- `window_days` (default 7, max 30)
- `timing_minutes` (default 15, max 60)
- `limit_alerts` (default 200, max 500)
- `limit_receipts` (default 50, max 200)
- `include_worst_runs` (default `false`)
- `include_receipts` (default `false`)
- `include_alert_items` (default `false`)
- `limit_worst_runs` (default 20, max 200; usado quando `include_worst_runs=true`)

Contrato minimo:
- endpoint read-only que consolida o runbook operacional em JSON deterministico
- inclui blocos de versao, timing, slo_daily, slo_alerts, runs, publish_receipts, checks e status
- modo default e lean (blocos pesados ficam opt-in por query params `include_*`)
- `status`:
  - `FAIL` se check hard falhar (`timing_events_15m`, `daily_has_requests_7d`, `receipts_path_leaks_30d`)
  - `WARN` quando `include_worst_runs=true` e `runs.worst` estiver vazio
  - `PASS` caso contrario

Comparativo de modo de resposta:

| Bloco | Default (lean) | Heavy (opt-in) |
|---|---|---|
| `version`, `timing`, `slo_daily`, `checks`, `status` | sempre presente | sempre presente |
| `runs.worst` | `[]` (desativado por default) | preenchido com `include_worst_runs=true` |
| `slo_alerts.items` | `[]` (somente `count`) | preenchido com `include_alert_items=true` |
| `publish_receipts.errors_7d` e `publish_receipts.latest_7d` | `[]` | preenchidos com `include_receipts=true` |

Guardrails do endpoint:
- `window_days > 30` => `400` (`error_type=RangeTooLarge`, `window_days_requested`, `window_days_max`)
- `timing_minutes > 60` => `400` (`error_type=RangeTooLarge`, `timing_minutes_requested`, `timing_minutes_max`)
- `limit_alerts > 500` => `400` (`error_type=LimitTooHigh`, `limit_alerts_requested`, `limit_alerts_max`)
- `limit_receipts > 200` => `400` (`error_type=LimitTooHigh`, `limit_receipts_requested`, `limit_receipts_max`)
- `limit_worst_runs > 200` => `400` (`error_type=LimitTooHigh`, `limit_worst_runs_requested`, `limit_worst_runs_max`)
- `include_worst_runs=true` com `window_days > 7` => `400` (`error_type=RangeTooLarge`, `window_days_max_for_worst_runs`)

Otimizacoes v1.3.2 (sem mudanca de contrato):
- `version.alembic_head` usa cache in-memory curto (TTL 60s) para remover query fixa do request path.
- `publish_receipts.path_leaks_30d` usa cache in-memory curto (TTL 30s) para reduzir custo recorrente.
- `slo_daily.summary` passa a ser derivado de `slo_daily.items` em memoria (sem query adicional).
- Em ambiente de testes (`pytest`), caches locais sao desativados para manter casos deterministas.
- Meta medida em regime (cache aquecido): `p95_db_queries ~= 2` e `p95_db_us ~= 3-4ms` no caminho default lean.
- Comportamento de cold-start (apos restart): o `p95_db_us` pode subir temporariamente para a faixa de `~20-25ms`.

## Metrics SLO

Escopo operacional:
- Valido para ambiente normal, com banco saudavel.
- Exclui cenarios de debug pesado e consultas de range grande.

Endpoints cobertos:
- `GET /api/v1/metrics/runs`
- `GET /api/v1/metrics/runs/{process_id}`
- `GET /api/v1/metrics/overview`
- `GET /api/v1/observability/report`

SLO real (contrato):
- `/metrics/runs`: `p95 <= 150ms`, `p99 <= 300ms`, `error_rate <= 1%`
- `/metrics/runs/{process_id}`: `p95 <= 200ms`, `p99 <= 400ms`, `error_rate <= 1%`
- `/metrics/overview`: `p95 <= 120ms`, `p99 <= 250ms`, `error_rate <= 1%`
- `/observability/report`: `p95 <= 300ms`, `p99 <= 600ms`, `error_rate <= 1%`

Error budget diario:
- `error_budget = 1%` por endpoint/dia.
- `allowed_errors = count_requests * 0.01`.
- `estimated_errors = count_requests * error_rate`.
- `remaining_errors = allowed_errors - estimated_errors`.

Guardrails de entrada:
- `limit_max = 200` para endpoint run-level paginado.
- `range_max_days = 31` para endpoint run-level com janela de datas.

### Event Types de SLO

`metrics_endpoint_timing`:
- Telemetria append-only por request dos endpoints de metricas alvo.
- Shape minimo em `facts`:
  - `endpoint`
  - `method`
  - `status_code`
  - `duration_ms`
  - `duration_us` (alta resolucao para diagnostico sub-ms)
  - `queue_us` (tempo entre entrada ASGI e inicio do handler)
  - `handler_ms`
  - `server_total_ms`
  - `server_total_us`
  - `query_fingerprint`
  - `cache_hit` (quando aplicavel, ex.: `/metrics/overview`)
  - `cache_key_hash` (hash curto da chave canonica, quando aplicavel)
  - `process_id` (quando existir no path)
  - `metric_date` (YYYY-MM-DD)

Diagnostico de fila (v1.2.6):
- Para `/api/v1/metrics/overview`, comparar p95 client-side vs p95 server-side (`duration_ms`) com `cache_hit=true`.
- Priorizar `queue_us`/`server_total_us` para separar fila de execucao interna do handler.

`metrics_slo_alert`:
- Alerta diario de regressao de SLO por endpoint.
- Condicoes canonicas:
  - `p95_ms > slo_p95` ou
  - `p99_ms > slo_p99` ou
  - `error_rate > 0.01`
- Dedupe por `(metric_date, endpoint, reason)`.

### GET /api/v1/status

Query params:
- `window_days` (default 7, max 30)

Contrato minimo:
- endpoint read-only para status executivo de SLO.
- retorna `overall_status` (`PASS|WARN|FAIL`), `slo_status`, `error_budget_remaining`, `ces_trend_status`.
- `FAIL` quando algum endpoint com dados viola SLO.
- `WARN` quando faltam dados para endpoint coberto no periodo.

Guardrail:
- `window_days > 30` => `400` (`error_type=RangeTooLarge`, `window_days_requested`, `window_days_max`)

### CI performance gate (minimo)

Pipeline CI deve validar regressao basica de performance para `/api/v1/metrics/runs`:
- 5 warmups + 50 chamadas medidas
- gate minimo: `p95 <= 300ms`
- gate minimo: `error_rate <= 1%`

## Exemplos

```bash
curl -s "http://localhost:8000/api/v1/metrics/daily?start_date=2026-02-10&end_date=2026-02-10"
curl -s "http://localhost:8000/api/v1/metrics/overview?days=7"
curl -s "http://localhost:8000/api/v1/metrics/alerts?start_date=2026-02-10&end_date=2026-02-10"
```

## Evidencia operacional (smoke runtime)

Data UTC: `2026-02-16T21:55:01Z`
Commit: `3622bf2`

```json
{"process_id":"P_PUBLISH_FLOW2","pipeline_status":"completed","execution_status":"success","ces_run":98.8,"latency_measured":false,"latency_pairs":{"used":2,"ignored":0,"inverted":0},"source_outcome_id":"a45a3872-1a7d-496b-b160-296ec033121e","last_error":{"error_type":null,"error_message":null}}
{"process_id":"P_VIDEO_6c2ff2f2-f28a-4c9f-9d5d-b4640b31d427","pipeline_status":"published","execution_status":"success","ces_run":100.0,"latency_measured":false,"latency_pairs":{"used":6,"ignored":1,"inverted":0},"source_outcome_id":"dfc94ca4-a948-4387-8fe5-4016f2182138","last_error":{"error_type":null,"error_message":null}}
{"process_id":"P_BLOCKED_EVIDENCE_4b29ae9a","pipeline_status":"blocked","execution_status":"blocked","ces_run":31.0,"latency_measured":false,"latency_pairs":{"used":0,"ignored":1,"inverted":0},"source_outcome_id":"61d985e7-65aa-4795-a0f4-2c2a054b84ea","last_error":{"error_type":"ArtifactNotFound","error_message":"manifest nao encontrado: <path>/agent_output/MISSING_MANIFEST_6f586b602f8e4b3aa6bf662b145fde03.json"}}
```

## Evidencia operacional - /observability/report (v1.8.2)

Data UTC: `2026-02-17`

- `/health`: `status=ok`, `api_version=1.8.2`, `ces_default_version=CES_v1`
- Shape minimo do report: validado
- Guardrails validados:
  - `window_days=31` -> `400 RangeTooLarge` (`window_days_max=30`)
  - `timing_minutes=61` -> `400 RangeTooLarge` (`timing_minutes_max=60`)
  - `limit_alerts=501` -> `400 LimitTooHigh` (`limit_alerts_max=500`)
  - `limit_receipts=201` -> `400 LimitTooHigh` (`limit_receipts_max=200`)
- `checks`: 6 itens, todos com `id` e `pass`
- Timing sanity: `events=29`, `bad_duration=0`
- `slo_daily`: `has_requests=true`, `items_len=2`
- `publish_receipts.path_leaks_30d=0`
- `status=WARN` (contrato: `PASS|WARN|FAIL`)
- Self-observing: `events_before=34` -> `events_after=38` apos 3 chamadas

### Links

- PR `feat/observability-report`: `https://github.com/theusnevess/CortAI/pull/new/feat/observability-report`
- Runbook operacional v1.8.2: `https://github.com/theusnevess/CortAI/blob/v1.8.2/docs/runbook_operacional_v1.8.2.md`

## Load Envelope v1.1 (baseline oficial)

Data UTC: `2026-02-18`

### Nota de ambiente: Docker Desktop + WSL2 (edge nao e fonte de verdade)

Quando o stack roda em Docker Desktop + WSL2 (`docker-desktop`), o proxy edge (Nginx) pode introduzir
latencia artificial de TTFB/queue que nao reflete o handler da API.

Regra canonica (importante):
- NAO calibrar SLO/envelope usando o caminho edge nesse ambiente.
- Para validacao local, use direct (`cortai_worker -> http://cortai_api:8000`) como referencia.
- Para envelope final e SLO "real", rode o benchmark em Linux nativo (VM/VPS/host), comparando direct vs edge.

Evidencia tipica do vies (sintoma):
- `upstream_connect_time ~ 0` e `upstream_header_time ~= request_time` altos no edge,
  enquanto `server_total_us` da API permanece baixo (cache-hit), indicando contensao/bridge fora do handler.

Perfil de carga:
- mix fixo: `/api/v1/metrics/runs` (60%), `/api/v1/observability/report` (25%), `/api/v1/metrics/overview` (15%)
- duracao por degrau: `60s`
- parametros fixos:
  - `/api/v1/metrics/runs?start_date=2026-02-11&end_date=2026-02-18&limit=200&offset=0`
  - `/api/v1/metrics/overview?days=7`
  - `/api/v1/observability/report?window_days=7&timing_minutes=15`

Snapshot de thresholds SLO usados no teste:
- `/api/v1/metrics/runs`: `p95 <= 150ms`, `p99 <= 300ms`, `error_rate <= 1%`
- `/api/v1/metrics/runs/{process_id}`: `p95 <= 200ms`, `p99 <= 400ms`, `error_rate <= 1%`
- `/api/v1/metrics/overview`: `p95 <= 120ms`, `p99 <= 250ms`, `error_rate <= 1%`
- `/api/v1/observability/report`: `p95 <= 300ms`, `p99 <= 600ms`, `error_rate <= 1%`

Resultado resumido:
- baseline p95:
  - runs `254.98ms`
  - report `113.67ms`
  - overview `91.16ms`
  - error_rate `0`
- degrau `C=1` p95:
  - runs `264.15ms` (`p99=306.06ms`)
  - report `121.5ms`
  - overview `102.37ms`
  - error_rate `0`
- degrau `C=5` p95:
  - runs `1053.9ms`
  - report `693.07ms`
  - overview `502.63ms`
  - error_rate `0`

Evidencia de observabilidade:
- `metrics_endpoint_daily` inclui os 3 endpoints do mix com `count_requests > 0`
- `metrics_slo_alert` emitido para `runs`, `report` e `overview`
- `timing.bad_duration = 0`

Conclusao operacional:
- safe envelope: `C=1`
- first violation: `C=5`
- violacao por latencia (SLO), nao por disponibilidade (sem 5xx)

## Envelope oficial v1.3 (Linux nativo)

Ambiente:
- Runner Linux nativo (fora Docker Desktop / WSL2)
- `wrk -t2 -c{1,2,5} -d60s --timeout 10s`
- Mix executado por endpoint isolado

Matriz consolidada:

| endpoint | C | p90 | p99 | req/s | timeouts |
|---|---:|---:|---:|---:|---:|
| overview | 1 | 218ms | 244ms | 4.73 | 0 |
| overview | 2 | 411ms | 451ms | 4.99 | 0 |
| overview | 5 | 823ms | 1.24s | 4.94 | 0 |
| runs | 1 | 231ms | 260ms | 4.49 | 0 |
| runs | 2 | 425ms | 451ms | 4.81 | 0 |
| runs | 5 | 1.26s | 1.68s | 4.79 | 0 |
| report | 1 | 241ms | 273ms | 4.26 | 0 |
| report | 2 | 433ms | 460ms | 4.69 | 0 |
| report | 5 | 866ms | 885ms | 4.73 | 0 |

Decisao:
- `safe_envelope_v1.3 = C1`

Justificativa:
- p90/p99 de `/metrics/overview` excede SLO ja em C1.
- Nenhum timeout ocorreu.
- Gargalo nao e handler (server-side sub-ms confirmado anteriormente).
- Limitacao atual e throughput do ambiente sob concorrencia >1.

Endpoint limitante:
- `/api/v1/metrics/overview`

## Stable Baseline Declaration - v1.9.x

A linha `v1.9.x` e considerada baseline estavel, auditavel e governada, com:
- Governanca de versao consistente (`/health` refletindo a versao operacional da release).
- Observabilidade completa em runtime (`timing`, `queue_us`, `db_us`, `server_total_us`).
- Endpoint `/api/v1/observability/report` em modo lean por default.
- Envelope oficial documentado e validado em Linux nativo.
- Sanitizacao validada (`path_leaks_30d = 0`).
- Sanidade de timing validada (`bad_duration = 0`).
- Telemetria append-only preservada.

A partir desta baseline:
- Mudancas estruturais devem abrir linha evolutiva explicita (ex.: v2.0).
- Ajustes de SLO/envelope devem ser deliberados, medidos e documentados.
- Evolucoes de performance devem manter rastreabilidade por evidencias runtime + pivot DB.

## Matriz P1 (workers x DB pool) - resultado e decisao (Linux nativo)

Objetivo:
- Validar se ajuste de process model (`API_WORKERS`) e DB pool (`DB_POOL_SIZE`) e suficiente para elevar o `safe_envelope v2.0` para `C=2` (mix 60/25/15), sem alterar logica dos endpoints.

Execucao:
- Artefato: `.tmp_matrix_p1/matrix_p1_summary.csv`
- Ambiente: Linux nativo
- Mix: `60/25/15`, duracao `60s` por degrau, timeout `10s`
- Concurrency avaliada: `C=2`
- Endpoints: `/api/v1/metrics/overview`, `/api/v1/metrics/runs`, `/api/v1/observability/report`

Checklist operacional P1 (PASS/FAIL):
- PASS: `timeouts=0` em todos os combos.
- PASS: `db_pool_wait_us=0` em todos os combos (sem contention de pool).
- FAIL: `safe_envelope_v2.0 = C2` nao atingido (latencia acima do SLO).
- PASS: endpoint limitante identificado de forma consistente: `/api/v1/metrics/overview`.

Winner P1 (melhor equilibrio geral):
- Config vencedora: `API_WORKERS=2`, `DB_POOL_SIZE=10`.
- Motivo: melhor equilibrio de `p90/p99` entre `overview/runs/report`, mantendo DB estavel e sem timeouts.

Resultados (C=2, winner):
- `/api/v1/metrics/overview`: `p90 587.3ms`, `p99 640.73ms`
- `/api/v1/metrics/runs`: `p90 600.26ms`, `p99 668.0ms`
- `/api/v1/observability/report`: `p90 572.5ms`, `p99 635.95ms`

Telemetria (p95):
- `queue_us` (`overview/runs`): `~1289us / ~1268us`
- `db_us` (`overview/runs/report`): `~8096us / ~6784us / ~6739us`
- `db_queries`: `2` (`overview/runs`), `3` (`report`)

Decisao P1:
- Conclusao: P1 confirma que `workers/pool` nao sao o gargalo dominante para viabilizar `C=2` com os SLOs atuais.
- `queue_us` baixo (ordem de `~1-2ms p95`) e `db_pool_wait_us=0` indicam ausencia de contencao de pool/fila interna.
- Mesmo assim, a latencia cliente (`p90/p99`) permanece alta e viola SLO em todos os combos.
- Endpoint limitante principal: `/api/v1/metrics/overview`, com `/metrics/runs` tambem acima do SLO no mesmo patamar.

Proximo passo canonico (P2):
- Seguir para P2 (throughput/process model/infra path) sem mexer em logica de endpoint.
- Alternativamente, revisao deliberada dos SLOs alvo para `C=2` (decisao de produto/operacao).

## P2-B1 sintetico (Windows/Docker Desktop)

Escopo:
- Validar pipeline de observabilidade (timing -> agregacao -> alerta -> report/status).
- Gerar artefatos equivalentes ao P2-B1 sem depender de runner externo.

Limite metodologico (obrigatorio):
- Este metodo **nao e validacao estrutural de infra path**.
- Este metodo **valida pipeline de observabilidade + SLO/alerts + envelope logico**.
- Decisao estrutural de capacidade (`safe_envelope_v2.0` definitivo) continua dependente de runner externo.

Comando de execucao:

```bash
python scripts/run_p2b1_synthetic.py --metric-date 2026-02-09 --base-url http://localhost:8000 --timing-minutes 60
```

Artefatos gerados em `.tmp_p2/`:
- `p2_a_summary_direct.csv`
- `p2_a_summary_edge.csv`
- `report_after_synth.json`
- `status_after_synth.json`

Checks esperados do script:
- `report.timing.events > 0`
- `report.slo_daily.has_requests == true`
- `report.slo_alerts.count > 0` quando ha breach
- `bad_duration == 0`
- `path_leaks_30d == 0`

## P2-B2.3a - Edge/Keepalive/Backlog (C=2, 3 reps, 60s)

Escopo:
- Ambiente local atual.
- Paths: direct (`:8000`) e edge (`:8001`).
- Objetivo: verificar se tuning de edge aproxima `C=2` dos SLOs sem alterar logica de endpoint.

Artefatos:
- `.tmp_p2/p2_b2_3a_baseline_direct.csv`
- `.tmp_p2/p2_b2_3a_baseline_edge.csv`
- `.tmp_p2/p2_b2_3a_keepalive_off_edge.csv`
- `.tmp_p2/p2_b2_3a_keepalive_on_edge.csv`
- `.tmp_p2/p2_b2_3a_buffering_on_edge.csv`
- `.tmp_p2/p2_b2_3a_buffering_off_edge.csv`
- `.tmp_p2/p2_b2_3a_workerconn4096_edge.csv`
- `.tmp_p2/edge_logs_15m_tail400.txt`
- `.tmp_p2/edge_p95_on.json`
- `.tmp_p2/p2_b2_3a_server_pivot.json`

Preflight:
- `/health`: `status=ok`, `api_version=1.9.6`.
- `/api/v1/observability/report`: `bad_duration=0`, `path_leaks_30d=0`.

Diagnostico de edge (logs):
- `p95_uct=0.0s`
- `p95_uht~=0.815s`
- `p95_rt~=0.812s`
- Interpretacao: TTFB domina; connect nginx->api nao e o gargalo.

A/B keepalive OFF vs ON (p99, edge):
- `overview`: `829.59ms -> 800.37ms` (`-3.52%`)
- `runs`: `787.70ms -> 805.60ms` (`+2.27%`)
- `report`: `799.69ms -> 834.41ms` (`+4.34%`)
- Resultado: **FAIL** (criterio de ganho `>=20%` nao atingido).

A/B buffering ON vs OFF:
- Resultado: **FAIL** (ganho inconsistente e regressao em `report`).

Capacidade edge (`worker_connections 4096`):
- Resultado: **FAIL** (sem melhora consistente; regressao em parte dos cenarios).
- Mantido `worker_connections=8192` no estado final local.

Decisao P2-B2.3a:
- **FAIL** para objetivo de aproximar `C=2` do SLO via tuning de edge.
- Melhor equilibrio local entre testadas: `keepalive OFF + proxy_buffering OFF + worker_connections=8192` (sem ganho suficiente para promocao de envelope).
- Endpoint limitante: `/api/v1/metrics/overview` (principal), com `/api/v1/metrics/runs` como co-limitante.

Proxima etapa canonica:
- Avancar para **P2-B2.3b** (infra/OS/backlog/limits): backlog/accept queue, `ulimit`/sockets, portas efemeras/TIME_WAIT, tuning de accept loop, e validacao final com runner separado para decisao estrutural.

## P2-B2.3b - Infra/OS Path (Backlog, Sockets, Accept Loop)

Escopo:
- Ambiente Linux (preferencialmente runner separado).
- Objetivo: validar se gargalo `C=2` esta na camada OS/socket/accept e nao no app/DB/edge tuning.

Criterio de sucesso:
- ganho `>=15-20%` em `p99` no `C=2` sem alterar logica de endpoint
- `timeouts=0`
- `bad_duration=0`
- `db_pool_wait_us=0`

1) Backlog efetivo (listen / accept queue)
- Checklist:
  - `ss -ltnp | grep 8000`
  - verificar `Recv-Q` vs `Send-Q`
  - verificar `net.core.somaxconn`
  - verificar `net.ipv4.tcp_max_syn_backlog`
- Teste:
  - aumentar `somaxconn=4096`
  - aumentar `tcp_max_syn_backlog=4096`
  - reiniciar edge + api
  - rodar `C=2` (3 reps, 60s)
- PASS se:
  - `p99` reduzir `>=15%`
  - `Recv-Q` nao saturar sob carga

2) File descriptors (`ulimit`)
- Checklist:
  - `ulimit -n`
  - `cat /proc/<nginx_pid>/limits`
  - `cat /proc/<uvicorn_pid>/limits`
- Teste:
  - ajustar para `>=65535`
  - reexecutar `C=2`
- PASS se:
  - `p99` reduzir `>=15%`
  - nenhum erro de socket

3) TIME_WAIT / portas efemeras
- Checklist:
  - `ss -s`
  - `net.ipv4.ip_local_port_range`
  - `net.ipv4.tcp_tw_reuse`
- Teste:
  - expandir port range (ex.: `10000-65000`)
  - habilitar `tcp_tw_reuse=1`
  - reexecutar `C=2`
- PASS se:
  - `p99` reduzir `>=15%`
  - `TIME_WAIT` nao crescer descontroladamente

4) Accept loop tuning (nginx / uvicorn)
- Edge:
  - `multi_accept on;`
  - `reuseport on;`
- API:
  - testar com:
    - `workers=2` (baseline)
    - `workers=2 + --loop uvloop` (se aplicavel)
    - `workers=2 + --http httptools`
- PASS se:
  - `p99` reduzir `>=15%`
  - latencia mais estavel (menor variancia)

Artefatos obrigatorios:
- `.tmp_p2/p2_b2_3b_summary.csv`
- `.tmp_p2/p2_b2_3b_sysctl.txt`
- `.tmp_p2/p2_b2_3b_ss.txt`
- (se edge) logs com `rt/uct/uht`

Decisao P2-B2.3b:
- se nenhum ajuste infra produzir ganho `>=15-20%` em `C=2`:
  - concluir que `C=2` esta acima do envelope estrutural do ambiente atual
  - `safe_envelope_v2.0` permanece `C1`
  - proximo passo real passa a ser:
    - revisao deliberada de SLO, ou
    - mudanca de arquitetura (P2-C)

## P2-C - Architecture Path (caso P2-B2.3b nao atinja meta)

Escopo:
- Aplicavel somente se `P2-B2.3b` (infra/OS) nao produzir ganho `>=15-20%` em `p99` (`C=2`).
- Objetivo: revisar arquitetura para tornar `C=2` estruturalmente viavel sem degradar governanca/observabilidade.

Estado de entrada:
- `timeouts=0`
- `db_pool_wait_us=0`
- edge tuning nao resolve
- infra/OS tuning nao resolve
- limitantes: `/api/v1/metrics/overview` (principal), `/api/v1/metrics/runs` (co)

1) Opcao A - Revisao deliberada de SLO (envelope realista)
- Acao:
  - formalizar que `C2` excede envelope estrutural do ambiente atual
  - ajustar SLO para:
    - `C1` como envelope oficial
    - `C2` como best-effort nao contratual
- Criterio:
  - evidencia consolidada `P2-A + P2-B2.3a + P2-B2.3b`
- Impacto:
  - nenhuma alteracao arquitetural
  - mantem simplicidade operacional

2) Opcao B - Materializacao/cache estrutural (read path)
- Objetivo:
  - reduzir TTFB no `/metrics/overview` e `/metrics/runs`
- Possiveis intervencoes:
  - snapshot diario materializado (job assincrono)
  - cache Redis para overview (TTL curto)
  - pre-agregacao de metricas (write-time, nao read-time)
  - separar read-model (CQRS leve)
- Criterio de sucesso:
  - `p99 C=2 < 400ms` (ou meta definida)
  - `db_queries` estaveis
  - `bad_duration=0`

3) Opcao C - Separacao de servico (read API isolada)
- Acao:
  - separar endpoints de leitura pesada em servico dedicado
  - API principal mantem status/health/observability leve
- Objetivo:
  - isolar throughput read path
  - permitir tuning dedicado (workers, cache, autoscale)
- Criterio:
  - `C2` passa SLO com arquitetura segmentada

4) Opcao D - Ajuste de modelo de execucao
- Intervencoes possiveis:
  - async full-stack real (sem bloqueios sincronos residuais)
  - `uvloop` obrigatorio
  - HTTP server diferente (ex.: hypercorn/uvicorn config otimizada)
  - HTTP/2 (se edge suportar)

Decisao P2-C:
- Escolher exatamente uma:
  - revisao de SLO (operacional)
  - cache/materializacao (arquitetura leve)
  - servico dedicado read-path
  - mudanca de modelo de execucao

Observacao canonica:
- Se `P2-B2.3b` falhar:
  - concluir que gargalo e estrutural do ambiente/process model atual
  - `safe_envelope_v2.0` permanece `C1`
  - `C2` so passa com intervencao arquitetural deliberada

## P2-C - Kickoff (com gate explicito)

Premissas (gate):
- `safe_envelope_v2.0` (operacional) = `C1`
- `safe_envelope_v2.0` (estrutural) = `pending` (P2-B1 runner externo)
- Qualquer melhoria em P2-C deve:
  - manter `timeouts = 0`
  - manter `bad_duration = 0`
  - manter `path_leaks_30d = 0`
  - manter `db_pool_wait_us = 0` (ou evidenciar por que subiu)
- Sem mudanca de logica/contrato dos endpoints (apenas read-path/materializacao/cache/infra do read).

Objetivo P2-C (mensuravel):
- Tornar `C2` viavel sob SLO atual em Linux nativo (rodada estrutural posterior), reduzindo latencia do read-path para:
  - `p99 C2 <= SLO` por endpoint (`overview/runs/report`)
  - com `db_us` e `queue_us` previsiveis e baixos

### Metricas-alvo e hard checks

Hard checks (nao pode piorar):
- `timeouts = 0` (direct e edge)
- `error_rate = 0` (ou `<= SLO`, se aplicavel)
- `bad_duration = 0`
- `path_leaks_30d = 0`
- `db_pool_wait_us p95 = 0` (ou justificativa + fix)

Alvos de performance:
- `/metrics/overview` em `C2`: `p99` dentro do SLO
- `/metrics/runs` em `C2`: `p99` dentro do SLO
- `/observability/report` (default lean) em `C2`: `p99` dentro do SLO

Instrumentacao obrigatoria para P2-C:
- Pivot por endpoint no timing: `queue_us`, `handler_us`, `db_us`, `db_queries`, `db_pool_wait_us`, `server_total_us`
- Pivot por caminho (direct vs edge): `rt/uct/uht` (edge logs)
- Evidencia do read-path por request (fonte DB/materializado/cache em facts)

### Escolha de trilha (sem mudar logica de endpoint)

Trilha C1 - Materializacao/Cache (recomendado primeiro):
- Definir read models minimos por endpoint:
  - `overview_read_model` (agregado pronto)
  - `runs_read_model` (lista latest per process_id ja otimizada)
  - `report_read_model` (default lean mantendo `db_queries <= 4`)
- Estrategia de atualizacao:
  - job periodico (ex.: 1-5 min) ou trigger/append-only (se aplicavel)
- Contrato de consistencia:
  - `freshness_seconds` exposto em `/status` (somente leitura)
- Guardrails:
  - fallback para DB on-demand desligado por default
- Migracoes + indices:
  - indices alinhados com top queries do read model

Criterio de saida da Trilha C1:
- `db_queries` por endpoint em `C2` previsivel e baixo (ex.: 0-2)
- `db_us` reduzido e estavel
- `queue_us` sem explosao por saturacao do read-path

Trilha C2 - Servico read-path (se C1 nao bastar):
- Novo servico `metrics-read` (mesmo repo/compose)
- API principal consome read-service (HTTP interno) ou mesmo DB/read model
- Rate limits e timeouts internos definidos
- Observabilidade por hop (timing no chamador e no servico)

Criterio de saida da Trilha C2:
- Latencia C2 dentro do SLO com isolamento de recursos
- Evidencia de contensao de processo/loop (nao DB)

### DoD P2-C

Para fechar PR de P2-C:
- Sem mudanca de contrato publico
- Testes verdes (suite completa)
- Documentacao atualizada em `docs/observability.md`
- Tabela de evidencia (`C=1/2/5`) + pivots (`queue_us/db_us/db_queries`)
- Execucao local (operacional) demonstra melhoria vs baseline
- Sem regressao em `/observability/report` (`db_queries <= 4` e `p95_db_us` baixo em steady-state)

Gate estrutural (fora do DoD do PR, obrigatorio para promover envelope):
- Rodar P2-B1 com runner externo e atualizar decisao estrutural

### P2-C2.2 (async snapshot-first)

Objetivo:
- remover agregacao live do request path de `/api/v1/metrics/overview` e `/api/v1/metrics/runs`.

Contrato C2.2:
- `force_live=true` nao calcula no request.
- `force_live=true` retorna HTTP `202 Accepted` e enfileira refresh idempotente.
- request normal (sem `force_live`) le somente snapshot do read model.
- sem snapshot, retorna HTTP `503` com erro deterministico `SnapshotMissing`.

Fila de refresh:
- tabela `metrics_read_refresh_jobs` com `job_key` unico por (`endpoint`, `query_key`).
- enqueue com `INSERT ... ON CONFLICT DO NOTHING` e TTL (`expires_at`).
- `job_key = sha256(endpoint + query_key_canonica)`.
- runner minimo: `python scripts/run_read_refresh_jobs.py --limit 100`.

Payload esperado para `force_live=true`:
```json
{
  "snapshot_status": "queued",
  "correlation_id": "<job_key_hash>",
  "scope": "overview",
  "retry_after_seconds": 5
}
```

Notas:
- `correlation_id` = hash seguro do job (`job_key_hash`), sem expor `query_key`.
- `scope` canonico: `overview` ou `runs`.

Headers canonicos de envelope/degradacao:
- `X-Envelope: C1`
- `X-Reason: throughput_path` (quando degradado)
- `Retry-After: <segundos>` para respostas `202 Accepted` e `503 SnapshotMissing`

Cache de edge (P2-D2, SLO-aware delivery):
- aplicado apenas em `GET /api/v1/metrics/overview` e `GET /api/v1/metrics/runs`
- bypass canonico: `force_live=true` (`proxy_cache_bypass`/`proxy_no_cache`)
- TTLs no edge:
  - `200`: `10s`
  - `503 SnapshotMissing`: `1s` (amortecer thundering herd)
  - `202` e `429`: `0s` (nao cachear)
- stale policy: `stale-while-revalidate` com `proxy_cache_background_update on`
- header diagnostico no edge: `X-Edge-Cache: HIT|MISS|BYPASS|EXPIRED`

Revalidacao HTTP (P2-D3):
- backend (`overview`/`runs`) expõe `ETag` deterministico por versao de snapshot.
- requests com `If-None-Match` retornam `304 Not Modified` quando o snapshot nao mudou.
- edge ativa `proxy_cache_revalidate on` para aproveitar revalidacao condicional no upstream.
- `ETag` nao e emitido em `202 Accepted` nem em `503 SnapshotMissing`.

Erro deterministico sem snapshot:
```json
{
  "detail": {
    "snapshot_status": "missing",
    "scope": "overview",
    "next_action": "force_live",
    "estimated_ready_seconds": 5
  }
}
```

Notas:
- `scope` canonico: `overview` ou `runs`.
- `Retry-After` usa a mesma fonte de `estimated_ready_seconds`.

### Happy path (snapshot-first) - 503 -> 202 -> runner -> 200

```bash
# 1) GET normal (snapshot ausente -> 503)
curl -sS "http://localhost:8000/api/v1/metrics/overview?days=7"
curl -sS "http://localhost:8000/api/v1/metrics/runs?start_date=2026-02-13&end_date=2026-02-20&limit=50&offset=0"

# 2) Enfileira refresh (202 queued + correlation_id)
curl -sS "http://localhost:8000/api/v1/metrics/overview?days=7&force_live=true"
curl -sS "http://localhost:8000/api/v1/metrics/runs?start_date=2026-02-13&end_date=2026-02-20&limit=50&offset=0&force_live=true"

# 3) Processa fila de refresh (runner)
python scripts/run_read_refresh_jobs.py --limit 100

# 4) GET normal (200 com snapshot)
curl -sS "http://localhost:8000/api/v1/metrics/overview?days=7"
curl -sS "http://localhost:8000/api/v1/metrics/runs?start_date=2026-02-13&end_date=2026-02-20&limit=50&offset=0"
```

Exemplo `503 SnapshotMissing` (overview/runs):
```json
{"detail":{"snapshot_status":"missing","scope":"overview","next_action":"force_live","estimated_ready_seconds":5}}
```

Exemplo `202 Accepted` (overview/runs):
```json
{"snapshot_status":"queued","correlation_id":"a1b2c3d4","scope":"overview","retry_after_seconds":5}
```

Nota operacional:
- repita o `GET` (ou consulte `/api/v1/status`) ate `freshness_seconds ~ 0` ou ate a resposta virar `200`.

Status/read-path:
- `GET /api/v1/status` expoe:
  - `read_path.overview_snapshot_status`
  - `read_path.overview_last_refreshed_at`
  - `read_path.overview_freshness_seconds`
  - `read_path.runs_snapshot_status`
  - `read_path.runs_last_refreshed_at`
  - `read_path.runs_freshness_seconds`
  - `read_path.runs_key_count`
  - `read_path.jobs_queued_count`

Telemetria:
- `metrics_endpoint_timing` mantem `db_us`, `db_queries`, `db_pool_wait_us`, `queue_us`, `server_total_us`.
- adiciona `snapshot_status`.
- para `202`, adiciona `job_enqueued` e `job_key_hash`.
- `overview_source` e `runs_source` continuam para auditoria do read-path.

Invariantes preservados:
- `bad_duration=0`
- `path_leaks_30d=0`
- `db_pool_wait_us=0` no steady-state observado

### P2-C2.3 (split leve do read-path)

Objetivo:
- isolar throughput de leitura em processo dedicado (`read_api`) sem alterar logica de endpoint.

Wiring:
- novo app: `app.read_main:app` com routers read-only:
  - `/api/v1/metrics/*`
  - `/api/v1/observability/report`
  - `/api/v1/status`
  - `/health`
- novo servico compose: `read_api` (porta host `8002`).
- edge roteia:
  - `/api/v1/metrics/*` -> `cortai_read_api`
  - `/api/v1/observability/report` -> `cortai_read_api`
  - `/api/v1/status` e `/health` -> `cortai_read_api`
  - restante -> `cortai_api`

Status operacional:
- `/api/v1/status` inclui bloco `read_api`:
  - `enabled`
  - `up`
  - `base_url`

### Nota de anomalia (db_us)

Em janelas longas, pode aparecer `db_us` alto em `metrics_endpoint_timing` sem reproduzir em SQL:
- amostras pontuais mostraram `db_us` alto em `/metrics/runs` e `/observability/report`;
- `EXPLAIN (ANALYZE, BUFFERS)` das queries equivalentes permaneceu sub-ms;
- pivots curtos voltaram para `p95_db_us` em poucos ms, com `db_pool_wait_us=0`.

Regra operacional:
- nao tratar `db_us` alto isolado como `SQL slow` sem repetibilidade em rodada curta + `EXPLAIN`.
- priorizar correlacao com `rt/uct/uht` no edge para diagnostico de TTFB/infra-path.

### P2-D Branch B (fail-fast/backpressure)

Objetivo:
- eliminar request pendurado ate timeout de cliente sob saturacao de fila/worker.

Flags de controle:
- `METRICS_READ_REFRESH_MAX_QUEUE_DEPTH` (default `20`)
- `METRICS_READ_REFRESH_MAX_RUNNING_JOBS` (default `4`)
- `METRICS_READ_REFRESH_MAX_QUEUE_WAIT_MS` (default `1500`)
- `METRICS_READ_REFRESH_MAX_EXEC_MS` (default `5000`)

Comportamento:
- `force_live=true` em `overview/runs`:
  - `429 Backpressure` quando fila/worker passam do limite.
  - `503 QueueTimeout` quando enfileiramento excede `max_queue_wait_ms`.
- worker de refresh:
  - marca `failed` com `queue_wait_timeout` quando job envelhece na fila.
  - marca `failed` com `exec_timeout` quando execucao excede `max_exec_ms`.

Telemetria:
- `metrics_endpoint_timing` inclui `queue_wait_ms` e `exec_ms` no caminho de `force_live`.

Seguranca:
- resposta de erro continua minima/deterministica.
- sem vazamento de paths internos.

### Envelope v2.0 (declaracao estrutural final)

Fonte de verdade:
- `P2-B1` com runner externo (GitHub Actions), fora do host do SUT.

Decisao:
- `safe_envelope_v2.0` (estrutural) = `C1`.
- `C2` falha no SLO atual e fica classificado como `infra-bound` no ambiente atual.

Leitura consolidada:
- nao ha evidencia de gargalo dominante em `DB`, `pool`, `SQL` ou `handler`;
- o limitante observado esta no infra-path/latencia externa (runner/rede/tunel/camada de entrega).

### Regra de validade de benchmark (stop-the-line)

Uma rodada externa nao pode ser usada para promover envelope quando qualquer endpoint apresentar:
- `timeouts > 0`; ou
- `req/s < 1`.

Nesses casos:
- tratar a rodada como invalida para promocao;
- nao continuar tuning de app/edge com base nela;
- corrigir primeiro o ambiente de execucao (runner/rede/tunel/infra-path).
