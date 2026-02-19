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

## P2-A (Throughput) - Resultado e Decisao (runner co-localizado)

Escopo:
- Script: `scripts/run_p2_matrix.sh`
- Artefatos:
  - `.tmp_p2/p2_a_summary_direct.csv`
  - `.tmp_p2/p2_a_summary_edge.csv`
  - `.tmp_p2/edge_logs_15m_tail400.txt`
- Repeticoes: 3 por ponto
- Concurrency: C=1, C=2, C=5
- Resultado operacional: `timeouts=0` em todos os cenarios

Resumo (mediana das 3 repeticoes):

| path | C | overview p90/p99 | runs p90/p99 | report p90/p99 |
|---|---:|---:|---:|---:|
| direct (:8000) | 1 | 282.42 / 293.53 | 289.21 / 303.67 | 285.61 / 306.15 |
| direct (:8000) | 2 | 546.08 / 553.77 | 539.10 / 557.52 | 543.08 / 560.12 |
| direct (:8000) | 5 | 652.69 / 905.04 | 663.37 / 705.18 | 666.16 / 693.52 |
| edge (:8001) | 1 | 304.71 / 317.05 | 305.50 / 324.74 | 304.16 / 317.78 |
| edge (:8001) | 2 | 574.65 / 603.12 | 571.74 / 590.59 | 570.94 / 586.73 |
| edge (:8001) | 5 | 1242.16 / 1532.17 | 1224.90 / 1820.21 | 1265.01 / 1863.12 |

Decisao P2-A:
- `safe_envelope_v2.0 = C1`
- `C2` nao atende SLO atual (latencia muito acima dos limites, mesmo sem timeouts).
- Endpoint limitante principal: `/api/v1/metrics/overview`.
- Co-limitante: `/api/v1/metrics/runs`.
- Observacao: execucao co-localizada (runner e SUT no mesmo host); decisao definitiva de infra path requer runner separado (P2-B1).
