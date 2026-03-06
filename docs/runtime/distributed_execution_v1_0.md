# Distributed Execution v1.0

## Objetivo

Permitir que multiplos workers executem tarefas do CortAI preservando:

- exclusividade por lease
- idempotencia por `op_key`
- consistencia de snapshot
- corretude do patch loop
- observabilidade por worker

## Tipos de task

- `WINDOW_AGGREGATION`
- `WINDOW_POST_PIPELINE`
- `EVENT_INDEX_REBUILD`

## Lifecycle da task

Estados:

- `PENDING`
- `RUNNING`
- `SUCCEEDED`
- `FAILED`
- `NOOP`
- `BLOCKED`

Fluxo:

`queue -> worker -> lease -> op_key -> handler -> finalize`

## Retry policy

- `max_attempts = 3`
- retry apenas para falhas temporarias
- `CONFLICT`, `BLOCKED` e `NOOP` nao fazem retry

## Observabilidade minima

Cada execucao deve registrar:

- `worker_id`
- `pid`
- `hostname`
- `task_id`
- `op_key`

## Regra arquitetural

O D20 nao substitui D12.

O runtime distribuido apenas usa corretamente:

- `LeaseManager`
- `IdempotencyManager`
- snapshots e pipelines ja existentes

## Fora de escopo

- Redis / Celery / Kafka
- scheduler distribuido externo
- autoscaling
- orchestration multi-host completa
