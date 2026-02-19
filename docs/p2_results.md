# P2 Results

Objetivo do ciclo:
- Validar throughput/capacidade para decidir se `C2` e viavel com SLO atual sem alterar logica de endpoint.

Contexto de execucao:
- Runner: `DESKTOP-58M82LF` (co-localizado)
- SUT host: `localhost:8000` (direct) e `localhost:8001` (edge)
- API workers: `unknown` (na telemetria do script)
- Repeticoes por ponto: `3`
- Timeouts: `0` em todos os cenarios

## P2-A Summary (preenchido)

Arquivos fonte:
- `.tmp_p2/p2_a_summary_direct.csv`
- `.tmp_p2/p2_a_summary_edge.csv`
- `.tmp_p2/edge_logs_15m_tail400.txt`

### Resultado consolidado (mediana de 3 repeticoes)

| endpoint | C | direct p90/p99 | edge p90/p99 | rps direct (med) | rps edge (med) | timeouts |
|---|---:|---:|---:|---:|---:|---:|
| /api/v1/metrics/overview | 1 | 282.42 / 293.53 | 304.71 / 317.05 | 0.50 | 0.45 | 0 |
| /api/v1/metrics/overview | 2 | 546.08 / 553.77 | 574.65 / 603.12 | 0.50 | 0.50 | 0 |
| /api/v1/metrics/overview | 5 | 652.69 / 905.04 | 1242.16 / 1532.17 | 1.00 | 0.80 | 0 |
| /api/v1/metrics/runs | 1 | 289.21 / 303.67 | 305.50 / 324.74 | 2.05 | 2.00 | 0 |
| /api/v1/metrics/runs | 2 | 539.10 / 557.52 | 571.74 / 590.59 | 2.37 | 2.22 | 0 |
| /api/v1/metrics/runs | 5 | 663.37 / 705.18 | 1224.90 / 1820.21 | 5.00 | 3.67 | 0 |
| /api/v1/observability/report | 1 | 285.61 / 306.15 | 304.16 / 317.78 | 0.83 | 0.77 | 0 |
| /api/v1/observability/report | 2 | 543.08 / 560.12 | 570.94 / 586.73 | 0.83 | 0.83 | 0 |
| /api/v1/observability/report | 5 | 666.16 / 693.52 | 1265.01 / 1863.12 | 1.75 | 1.40 | 0 |

## Decisao

- `C2 possivel com SLO atual?` **Nao**
- Endpoint limitante: **/api/v1/metrics/overview** (principal), **/api/v1/metrics/runs** (co-limitante)
- Knob dominante observado: **throughput/infra path**, nao erro de aplicacao (`timeouts=0`)
- Proximo experimento recomendado (P2-B1): repetir matriz com **runner separado do SUT** para remover ruido de co-location e confirmar capacidade real de infra path.

## Evidencias anexadas

- CSV consolidado:
  - `.tmp_p2/p2_a_summary_direct.csv`
  - `.tmp_p2/p2_a_summary_edge.csv`
- Logs edge (15m):
  - `.tmp_p2/edge_logs_15m_tail400.txt`
- Comando de execucao:
  - `bash scripts/run_p2_matrix.sh http://127.0.0.1:8000`
  - `bash scripts/run_p2_matrix.sh http://127.0.0.1:8001`
