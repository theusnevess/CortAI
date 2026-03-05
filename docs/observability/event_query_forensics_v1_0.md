# Event Query & Forensics v1.0

## Problema
O sistema emite eventos em multiplas trilhas JSONL, mas ainda nao possui uma camada de consulta estruturada para investigacao operacional e forense.

## Objetivos
Permitir consultas deterministicas e somente leitura por:
- `account_id`
- `window_id`
- `job_id`
- `publish_id`
- `op_key`
- `event_type`
- `timestamp_range`

## Fontes de eventos
A camada D13 consulta dados existentes, sem alterar storage:
- `OUT/events/*.jsonl`
- `OUT/data/*.jsonl`
- `OUT/audit/*.jsonl`

## Tipos de eventos relevantes
- `PIPE/*`
- `LOCK/*`
- `IDEMPOTENCY/*`
- `SC/*`
- `ATTR/*`
- `SL/*`
- `REG/*`

## Queries minimas
| Query | Descricao |
|---|---|
| `get_events_by_account` | Lista eventos por conta |
| `get_events_by_window` | Reconstrui execucao da janela |
| `get_events_by_op_key` | Rastreia operacao idempotente |
| `get_pipeline_trace` | Monta trilha canonica do pipeline |

## Exemplo de trace
`window_pipeline -> AGG -> SC -> ATTR -> SL -> SPA`

## Invariantes
1. Somente leitura.
2. Sem modificacao de eventos de origem.
3. Sem alteracao de pipeline de negocio.
4. Consultas deterministicas com filtros explicitos.

## Estrutura inicial de modulos
```text
backend/app/observability/event_query/
  __init__.py
  models.py
  query_service.py
  indexer.py
  errors.py
```

## Fora de escopo (D13.1)
- Wiring no runtime.
- Index persistente.
- API publica.
- Replay automatico.

## Proximos passos
- D13.2: scanner JSONL + filtros.
- D13.3: builder de pipeline trace.
- D13.4: testes e casos forenses.
