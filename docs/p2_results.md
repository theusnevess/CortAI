# P2 Results (Template)

Objetivo do ciclo:
- Validar throughput/capacidade para decidir se `C2` e viavel com SLO atual sem alterar logica de endpoint.

Contexto de execucao:
- Runner:
- SUT host:
- API workers:
- Janela:
- Repeticoes por ponto:
- Ferramenta:

## P2-A Summary

Arquivo fonte:
- `.tmp_p2/p2_a_summary.csv`

Colunas:
- `endpoint, C, repeat, p90_ms, p99_ms, rps, timeouts, runner, sut_host, api_workers`

### Resultado consolidado

| endpoint | C | p90 (mediana das repeticoes) | p99 (mediana das repeticoes) | rps (mediana) | timeouts (total) |
|---|---:|---:|---:|---:|---:|
| /api/v1/metrics/overview |  |  |  |  |  |
| /api/v1/metrics/runs |  |  |  |  |  |
| /api/v1/observability/report |  |  |  |  |  |

## Decisao

- `C2 possivel com SLO atual?`:
- Endpoint limitante:
- Knob dominante observado (workers / keep-alive / backlog / client pool / infra path):
- Proximo experimento recomendado:

## Evidencias anexadas

- CSV consolidado:
- Comando de execucao:
- Hash/branch:
