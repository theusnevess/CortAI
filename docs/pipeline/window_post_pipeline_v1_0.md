# Window Post Pipeline v1.0 (D10)

## Objetivo
Orquestrar o caminho mínimo pós-janela:

`window_metrics -> scorecard -> attribution -> strategy_learning`

com guard obrigatório na entrada.

## Ordem rígida
1. Guard
2. Scorecard
3. Attribution
4. Strategy Learning

## Entradas
- `account_id`
- `window_id`
- `deps` (serviços injetáveis)

## Saídas
Resultado único com:
- status final
- status por etapa
- reason codes
- `op_key` de execução

## Invariantes
- Se `guard.blocked == true`, não executa scorecard/attribution/learning.
- Se scorecard não for gerado, não executa attribution/learning.
- Se attribution falhar por falta de métricas, não executa learning.
- Não aplica patch no registry (fora de escopo D10).

## Motivos de skip (mínimo v1.0)
- `CONSISTENCY_VIOLATION_BLOCKED`
- `SCORECARD_NOT_GENERATED`
- `ATTRIBUTION_METRICS_MISSING`

## Idempotência de execução
- `op_key` canônico: `D10:{account_id}:{window_id}`.
- Se a execução já existe para o mesmo `op_key`, retorna `NOOP_EXECUTION`.

## Fora de escopo
- Application do patch no registry.
- Updater/account mutation.
- Estratégias de concorrência avançadas (leases globais).
