# Distributed Scheduler v1.0

## Objetivo

Planejar, enfileirar e disparar tasks de forma continua, previsivel e auditavel.

O scheduler:

- gera planos deterministas
- decide `scheduled_for`
- enfileira tasks
- nunca executa a task diretamente

## Tipos de schedule

- `EVERY_72H`
- `DAILY`
- `MANUAL`

## Regras congeladas

- mesma janela + mesma task = `NOOP`
- mesma chave logica com payload diferente = `CONFLICT`
- scheduler nao executa task
- scheduler apenas planeja e enfileira

## Chave de idempotencia

`op_key`

Exemplos:

- `AGG:{account_id}:{window_id}`
- `D10:{account_id}:{window_id}`
- `IDX_REBUILD:{account_id}:{date}`

## Observabilidade minima

Toda task agendada carrega:

- `task_id`
- `task_type`
- `account_id`
- `window_id`
- `scheduled_for`
- `op_key`
- `scheduler_id`

## Janela principal

Para `EVERY_72H`:

- o scheduler gera `WINDOW_AGGREGATION`
- e tambem `WINDOW_POST_PIPELINE`
- ambos para a mesma janela

## Fora de escopo

- cron real
- scheduler distribuido multi-host
- persistencia da fila em banco externo
- priorizacao dinamica
