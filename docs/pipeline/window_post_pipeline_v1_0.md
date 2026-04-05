# Window Post Pipeline v1.0 (D10)

## Objetivo
Orquestrar o caminho minimo pos-janela:

`window_metrics -> scorecard -> attribution -> strategy_learning`

com guard obrigatorio na entrada.

## Boundary de attribution
- O root canonico do subsystem de Content Performance Attribution e `backend/app/product/attribution/`.
- O trilho `backend/app/attribution/` permanece apenas como legado analitico / suporte nao canonico.
- O `D10` deve consumir o path canonico quando houver wiring concreto do servico de attribution.

## Ordem rigida
1. Guard
2. Scorecard
3. Attribution
4. Strategy Learning

## Entradas
- `account_id`
- `window_id`
- `deps` (servicos injetaveis)

## Saidas
Resultado unico com:
- status final
- status por etapa
- reason codes
- `op_key` de execucao

## Invariantes
- Se `guard.blocked == true`, nao executa scorecard/attribution/learning.
- Se scorecard nao for gerado, nao executa attribution/learning.
- Se attribution falhar por falta de metricas, nao executa learning.
- Nao aplica patch no registry (fora de escopo D10).

## Motivos de skip (minimo v1.0)
- `CONSISTENCY_VIOLATION_BLOCKED`
- `SCORECARD_NOT_GENERATED`
- `ATTRIBUTION_METRICS_MISSING`

## Idempotencia de execucao
- `op_key` canonico: `D10:{account_id}:{window_id}`.
- Se a execucao ja existe para o mesmo `op_key`, retorna `NOOP_EXECUTION`.

## Fora de escopo
- Application do patch no registry.
- Updater/account mutation.
- Estrategias de concorrencia avancadas (leases globais).
