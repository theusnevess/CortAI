# P2 Results

## P2-B1 sintetico (Windows/Docker Desktop)

Objetivo:
- Executar uma validacao sintetica do fluxo de observabilidade e SLO quando nao ha runner externo disponivel.

Nao objetivo:
- Este fluxo nao substitui P2-B1 estrutural (runner separado do SUT).

Execucao:

```bash
python scripts/run_p2b1_synthetic.py --metric-date 2026-02-09 --base-url http://localhost:8000 --timing-minutes 60
```

Artefatos esperados (`.tmp_p2/`):
- `p2_a_summary_direct.csv` (3 endpoints x 3 Cs = 9 linhas de dados)
- `p2_a_summary_edge.csv` (3 endpoints x 3 Cs = 9 linhas de dados)
- `report_after_synth.json`
- `status_after_synth.json`

Validações obrigatorias:
- Agregacao diaria executada duas vezes sem duplicar `metrics_slo_alert`.
- Monotonicidade de latencia no CSV sintetico (`C1 < C2 < C5`) por endpoint.
- `report_after_synth.json` com:
  - `timing.events > 0`
  - `slo_daily.has_requests == true`
  - `bad_duration == 0`
  - `publish_receipts.path_leaks_30d == 0`

Observacao:
- Resultado sintetico e util para validar pipeline e contratos.
- Decisao estrutural de capacidade segue dependente de medicao com runner externo.

## P2-C2.1 pos-merge (runs read-path, C=2)

Objetivo:
- Validar impacto do read-path materializado de `/api/v1/metrics/runs` em C=2 apos merge.

Escopo da rodada:
- Endpoint: `/api/v1/metrics/runs?start_date=2026-02-11&end_date=2026-02-18&limit=200&offset=0`
- Cenario: C=2, 3 repeticoes, 60s por repeticao
- Caminhos: direct (`:8000`) e edge (`:8001`)
- Artefatos:
  - `.tmp_p2/p2_c21_runs_c2_postmerge.csv`
  - `.tmp_p2/p2_c21_runs_c2_postmerge_summary.json`

Resultado consolidado:

| path   | avg p90 | avg p99 | avg req/s | timeouts |
|--------|---------|---------|-----------|----------|
| direct | 853.07ms | 894.33ms | 2.42 | 0 |
| edge   | 855.64ms | 889.17ms | 2.40 | 0 |

Pivot server-side (`metrics_endpoint_timing`, janela curta):
- `runs_source=read_model`: `n=875`, `avg_db_queries=1.00`, `p95_db_us=1181.50`
- `runs_source=live`: `n=4`, `avg_db_queries=3.25`, `p95_db_us=9410.50`
- `db_pool_wait_us=0` (sem contencao de pool)

Interpretacao:
- O read-path de runs ficou efetivo e previsivel no servidor (predominio `read_model`).
- Houve reducao objetiva de cauda em relacao ao baseline anterior (~1108.82ms p99 direct para ~894.33ms, cerca de -19%).
- Mesmo com melhora de runs, C=2 permanece fora do SLO de latencia no ambiente atual.

Decisao:
- `safe_envelope_v2.0` permanece `C1`.
- P2-C2.1 foi eficaz para isolamento de leitura e custo DB de runs, mas nao alterou o limite estrutural de envelope.

## P2-C2.2 (async snapshot-first) - validacao funcional

Objetivo:
- remover agregacao live do request path de `overview` e `runs`, migrando `force_live` para enqueue assíncrono.

Implementado:
- `force_live=true` retorna `202 Accepted` (sem calcular no request).
- fila idempotente `metrics_read_refresh_jobs` (TTL + `job_key` unico).
- runner de refresh: `python scripts/run_read_refresh_jobs.py --limit 100`.
- request normal le somente snapshot; sem snapshot retorna `503 SnapshotMissing`.
- `status` expoe snapshot status/freshness e jobs enfileirados.

Validacao:
- `python -m pytest -q` -> `62 passed`.
- `tests/test_metrics_api.py` e `tests/test_status_api.py` cobrem:
  - `202 Accepted` com payload deterministico;
  - dedupe de enqueue por `job_key`;
  - `503 SnapshotMissing` sem snapshot;
  - leitura `200` apos processamento do runner;
  - telemetria com `snapshot_status`, `job_enqueued`, `job_key_hash`.
- Happy path operacional (`503 -> 202 -> runner -> 200`): ver `docs/observability.md`, secao `Happy path (snapshot-first) - 503 -> 202 -> runner -> 200`.

Decisao:
- C2.2 conclui a mudanca arquitetural de request path (snapshot-first).
- `safe_envelope_v2.0` permanece `C1` ate rodada estrutural P2-B1 com runner externo.

## P2-C2.3 (read-path split) - kickoff

Objetivo:
- isolar read-path em processo dedicado para reduzir contencao de throughput sob C=2.

Escopo:
- novo servico `read_api` com `metrics + observability/report + status`.
- edge roteia endpoints de leitura para `read_api`.
- API principal permanece como origem das rotas nao-read.

Gate de validacao:
- benchmark C=2 (3x60s) comparando p99 com baseline C2.2.
- criterio de impacto: queda >=20% em p99 (`overview` e `runs`) com `timeouts=0`.

## P2-C2.4 (diagnostico curto de anomalia db_us)

Objetivo:
- verificar se `db_us` alto observado em janela longa era gargalo SQL real.

Resultado:
- logs do edge com formato `rt/uct/uht` ativos.
- p95: `uct=0.0s`, `uht~1.118s`, `rt~1.104s` (TTFB domina; connect nao domina).
- top amostras com `db_us` alto em janela longa apareceram para:
  - `/api/v1/metrics/runs` (`query_fingerprint=limit=200&offset=0&range=8d`)
  - `/api/v1/observability/report` (modo lean default)
- `EXPLAIN (ANALYZE, BUFFERS)` das queries representativas permaneceu sub-ms.
- rodada curta C=2 (20s) confirmou `p99` ~1s+ com:
  - `timeouts=0`
  - `p95_db_us` novamente em poucos ms
  - `db_pool_wait_us=0`

Decisao:
- anomalia `db_us` classificada como ruido/contensao de runtime, nao `SQL slow` repetivel.
- `safe_envelope_v2.0` permanece `C1`.
- gate estrutural continua em `P2-B1` com runner externo.

## P2-B1 estrutural (runner externo GitHub Actions)

Objetivo:
- fechar o gate estrutural de capacidade com runner externo (fora do host do SUT).

Fonte de execucao:
- GitHub Actions (`ubuntu-latest`) com workflow manual `p2_b1_runner_external`.
- Artefatos:
  - `.tmp_p2/p2_a_summary_direct.csv`
  - `.tmp_p2/p2_a_summary_edge.csv`

Escopo da comparacao:
- Cenario: `C=2`, `3` repeticoes, `60s` por repeticao.
- Endpoints: `overview`, `runs`, `report`.
- Caminhos:
  - `direct` (API direta)
  - `edge` (proxy/read path)

Resultado consolidado (media das 3 repeticoes, C=2):

| path   | endpoint | avg p90 | avg p99 | avg req/s | timeouts |
|--------|----------|---------|---------|-----------|----------|
| direct | overview | 1123.33ms | 2503.33ms | 1.92 | 0 |
| direct | runs     | 1106.67ms | 1866.67ms | 1.98 | 0 |
| direct | report   | 1170.00ms | 1830.00ms | 1.89 | 0 |
| edge   | overview | 1273.33ms | 1660.00ms | 1.75 | 0 |
| edge   | runs     | 1146.67ms | 1496.67ms | 1.90 | 0 |
| edge   | report   | 1226.67ms | 1706.67ms | 1.83 | 0 |

Decisao:
- `P2-B1`: `PASS` (metodologia estrutural concluida).
- `safe_envelope_v2.0` (estrutural): `C1`.
- `C2`: `FAIL` por latencia de cauda (p99 acima do SLO), mesmo com `timeouts=0`.

Endpoint limitante:
- principal: `/api/v1/metrics/overview`
- co-limitante: `/api/v1/metrics/runs`

Observacao:
- o caminho `edge` reduziu parte da cauda vs `direct` em alguns cenarios, mas nao o suficiente para promover `C2`.

## P2-D Branch B (fail-fast/backpressure)

Ramo seguido:
- **B (local/externo com saturacao)**, pois a causa predominante permaneceu em contensao de runtime/path com penduramento ate timeout.

O que mudou:
- fail-fast em `force_live` (`429 Backpressure` / `503 QueueTimeout`).
- timeout interno por etapa:
  - `max_queue_wait_ms` no enfileiramento.
  - `max_exec_ms` no worker de refresh.
- status de job padronizado em timeout:
  - `queue_wait_timeout`
  - `exec_timeout`

Antes (exemplo de rodada estrutural sob saturacao, C=2):
- `direct` com timeouts > 0 e cauda em segundos.

Depois (comportamento esperado/validado em testes):
- saturacao retorna `429/503` rapidamente (sem hang silencioso).
- contratos deterministas mantidos (`error_type`, `scope`, `snapshot_status`, `retry_after_seconds`).
- telemetria com amostra de `queue_wait_ms` vs `exec_ms`.

Flags/configs adicionadas:
- `METRICS_READ_REFRESH_MAX_QUEUE_DEPTH`
- `METRICS_READ_REFRESH_MAX_RUNNING_JOBS`
- `METRICS_READ_REFRESH_MAX_QUEUE_WAIT_MS`
- `METRICS_READ_REFRESH_MAX_EXEC_MS`

## Declaracao final de envelope v2.0 (estrutural)

Fonte de verdade:
- `P2-B1` com runner externo (GitHub Actions) e artefatos de benchmark.

Decisao oficial:
- `safe_envelope_v2.0` (estrutural) = `C1`.
- `C2` = `FAIL` no SLO atual e classificado como `infra-bound` no ambiente avaliado.

Interpretacao consolidada:
- gargalo nao e `DB`, `pool`, `SQL`, `handler` ou `read-model`;
- a degradacao dominante aparece no infra-path/latencia externa (runner -> edge/direct -> SUT).

Politica operacional:
- nao promover `C2` neste ambiente.
- `C2` so pode ser reavaliado com infraestrutura dedicada (ex.: VPS/host sem tunel) ou revisao explicita de SLO.
- SLO operacional de `C1`: ver `docs/observability.md` na secao `SLO C1 (operacional)`.
- C1 Health Score (`PASS|WARN|FAIL`) e regras de leitura do summary: ver `docs/observability.md` na secao `C1 Health Score (PASS/WARN/FAIL)`.
- Warm-up pos-deploy do read-path: ver `docs/observability.md` na secao `Warm-up opcional no deploy (read-path)`.

## Regra de validade do benchmark externo (stop-the-line)

Uma rodada externa e invalida para promocao de envelope quando qualquer endpoint apresentar:
- `timeouts > 0`; ou
- `req/s < 1`.

Quando isso ocorrer:
- nao promover envelope;
- nao continuar tuning de app/edge com base nessa rodada;
- corrigir primeiro o ambiente/caminho de execucao (infra-path, tunel, rede, runner).

## Fase: C1 Health Score + Reliability Hardening - Status Final

Objetivo da fase:
- consolidar `C1` como estado operacional continuo (classificacao automatica + hardening de confiabilidade), sem perseguir throughput adicional.

Escopo entregue:
- stop-the-line no runner externo (`diag gate`);
- C1 Health Score engine + integracao no workflow;
- docs + runbook do C1 Health Score;
- hardening de refresh jobs (dedupe + atomic claim);
- warm-up opcional no deploy (read-path).

Garantias operacionais vigentes:
- benchmark invalido nao avanca para `formal`;
- classificacao automatica `PASS|WARN|FAIL` via `C1_HEALTH`;
- no maximo `1` refresh job ativo por `job_key` sob burst;
- runner seguro sob concorrencia (claim atomico, sem double-processing);
- warm-up reduz `SnapshotMissing` pos-deploy.

Pendencias conscientes:
- evidencia final do step `Evaluate C1 SLO` em host estavel (sem tunel) permanece pendente por limitacao de ambiente;
- `C2` permanece fora do escopo desta fase (continua `infra-bound` no ambiente atual).

Status final:
- `safe_envelope_v2.0` (estrutural): `C1`
- Fase `C1 Premium`: `CLOSED`

Proxima evolucao:
- deliberada e separada desta fase (infra dedicada para reavaliar `C2`, ou metricas runtime embutidas).

## Recheck Final - GO

Referencia de fix do bloqueante:
- `832100d` (`docs/perf` na trilha do fix de guardrail `429 RateLimited` deterministico; runtime validado apos rebuild local)

Resumo (10 linhas):
1. Recheck final executado localmente com evidencias em `OUT/RECHECK_REPORT.md`.
2. Suite completa no container: `75 passed`.
3. `force_live` retorna `202` padronizado em `overview` e `runs`.
4. Segunda chamada `force_live` no cooldown retorna `429 RateLimited` deterministico (`overview` e `runs`).
5. Runner de refresh processa fila e `GET` sem `force_live` retorna `200` para `overview` e `runs`.
6. `ETag` + `304 Not Modified` validados em `overview` e `runs`.
7. `nginx -t` OK e logs do edge com `rt/uct/uht` confirmados.
8. Hardening de refresh jobs validado por testes de concorrencia (`dedupe` + `atomic claim`).
9. Workflow/tooling/scripts/docs sanity: PASS (`diag gate`, `best-effort artifacts`, `C1 Health Score`, stop-the-line, happy path).
10. GO/NO-GO final: `GO`.

Decisao final:
- `GO`
- `safe_envelope_v2.0` (estrutural) = `C1`
- fase `C1 Premium + Health Score + Hardening`: encerrada

Nota (nao bloqueante):
- working tree local permaneceu suja por artefatos/experimentos (`.tmp_*`, `OUT/`, `docker-compose.netem.yml`, `infra/nginx/default.conf`);
- classificado como higiene local, sem evidencia de bug/regressao do sistema, e nao deve ser mergeado sem ticket explicito.

## Recheck rapido pos-fix - GO (Runtime Visibility validada)

Data:
- `2026-02-24`

Contexto:
- pos-fix de governanca de versao (`DEFAULT_APP_VERSION`), rebootstrap sequencial e validacao controlada de `c1_health` no `/status` (gate restrito).

Resultado:
- `GO`

Checks executados (stop-the-line):
1. Edge / nginx config
   - `nginx -t` (`cortai_edge`): `PASS`
2. Read-path warm-up
   - `scripts/warmup_read_path.sh` (`cortai_api`): `PASS`
   - `overview_get_http=200`
   - `runs_get_http=200`
   - `jobs_queued_count=0`
3. Guardrail anti-burst (`force_live`)
   - `PASS` (key nova no edge)
   - `overview?days=6`: `202 -> 429 RateLimited`
   - `runs?...end_date=2026-02-19...`: `202 -> 429 RateLimited`
4. ETag / `304`
   - `PASS` (edge)
   - `200` com `ETag`
   - `304 Not Modified` com `If-None-Match`
5. Runtime C1 Health Score (`/status`, gate ON)
   - `PASS`
   - `enabled=true`, `version=v1.1`
   - `score`, `rows[]`, `reasons[]`, `meta` presentes

Nota (cache TTL):
- com `api_workers=2`, o cache e por processo; `2` chamadas seguidas podem nao mostrar `cached=true`;
- loop curto confirmou cache hit (`cached=false -> cached=true`).

Governanca / versao (pos-fix):
- drift encerrado: `/health` em `:8000` e `:8001` retorna `api_version=1.9.9`
- commit aplicado: `1bb5beb` (`chore(version): bump DEFAULT_APP_VERSION to 1.9.9`)

Observacao operacional (runbook):
- ordem sequencial de rebootstrap evita `502` no edge:
  1. `api/read_api` primeiro
  2. `edge` por ultimo

Nota de ambiente (nao versionada):
- `EXPOSE_C1_HEALTH_STATUS=1` foi habilitado localmente no `docker-compose.yml` apenas para validacao;
- nao commitado (config de ambiente).
