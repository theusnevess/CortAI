# Load Testing v1.0

## Objetivo

Medir, sob carga controlada:

- throughput
- latencia
- contencao por lease
- conflitos de idempotencia
- custo de fallback
- comportamento do pipeline em saturacao

Sem alterar contratos funcionais do sistema.

## Escopo

Entra:

- harness de carga para `window_pipeline`, `window_post_pipeline` e `/events`
- captura de metricas de latencia e throughput
- relatorio de saturacao em JSON e Markdown
- cenarios padrao de 10, 50 e 100 contas

Nao entra:

- tuning de banco
- autoscaling
- mudancas de arquitetura
- dashboards

## Metricas

Pipeline:

- `window_pipeline_latency_ms`
- `window_post_pipeline_latency_ms`

Query:

- `event_query_latency_ms`

Infra operacional:

- `lease_contention_rate`
- `idempotency_conflict_rate`
- `fallback_hit_rate`
- `error_rate`
- `throughput_ops_s`

## Cenarios

### load_10_accounts

- 10 contas
- 10 videos por conta
- 1 janela por conta
- burst leve de query

### load_50_accounts

- 50 contas
- 10 videos por conta
- 1 janela por conta
- burst medio de query

### load_100_accounts

- 100 contas
- 10 videos por conta
- 1 janela por conta
- burst mais alto de query
- rebuild opcional no final

### query_burst_fallback

- forca queda do hot store
- mede degradacao para indice/scanner

## Criterios GO/NO-GO

GO se:

- 0 corrupcao de dados
- 0 double-apply
- 0 snapshot inconsistente aceito
- query `/events` continua funcional sob burst
- fallback funciona sem quebra

NO-GO se:

- pipeline trava
- lease nao protege escrita
- patch duplica
- fallback perde consistencia
- query perde ordenacao ou paginacao

## Artefatos

O harness gera:

- `OUT/perf/load_test_report.json`
- `OUT/perf/load_test_report.md`

## Observacao arquitetural

`JSONL` continua sendo a verdade canonica.

O D18 mede comportamento sobre:

1. `JSONL`
2. indice SQLite
3. hot store

sem promover nenhuma dessas camadas derivadas a fonte de verdade.
