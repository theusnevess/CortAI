# Hot Storage v1.0

## Objetivo

Adicionar uma camada de hot storage consultavel para eventos, separada do log canonico append-only.

Arquitetura:

```text
append_event()
  -> JSONL (verdade canonica)
  -> SQLite index (aceleracao local)
  -> Hot Store (query operacional)
```

## Papeis

- `JSONL`: fonte de verdade.
- `event_index.sqlite3`: aceleracao local para consultas simples.
- `events_hot.sqlite3`: camada operacional para consultas mais pesadas.

## Invariantes

- O hot store nunca substitui o JSONL como verdade.
- Se houver divergencia, o rebuild parte sempre do JSONL.
- O fallback de consulta e obrigatorio:
  1. hot store
  2. indice SQLite
  3. scanner JSONL

## Armazenamento

- Caminho padrao: `OUT/hot_store/events_hot.sqlite3`
- Chave de idempotencia: `event_id`

## Writer

- Writer idempotente por `event_id`.
- Falha do hot store nao bloqueia o pipeline.
- Rebuild/replay a partir do log canonico continua disponivel.

## Out of scope

- dashboards
- auth/rbac
- analytics avancado
- distributed query
- materialized views complexas
