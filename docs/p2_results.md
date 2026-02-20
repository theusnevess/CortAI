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
