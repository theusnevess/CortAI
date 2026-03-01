# Scaling Memo v0.1

Objetivo: explicitar o que quebra primeiro quando o CortAI sair de processo único para múltiplas instâncias.

Hoje é process-local:
- `WebhookMetrics` in-memory
- caches in-memory do overview
- qualquer dedup em memória
- contadores agregados sem coordenação

Vai precisar virar compartilhado no futuro:
- métricas agregadas multi-processo
- storage de idempotency keys
- event log central
- trace propagation padronizada

Risco #1 em multi-instância:
- duplicação de eventos + inconsistência de métricas, porque cada instância observa só o próprio processo

Ordem provável de evolução:
1. padronizar envelope e catálogo
2. definir storage de idempotência
3. introduzir log/bus central
4. mover métricas críticas para backend compartilhado

Fora do v0.1:
- implementação do bus
- publish/consume real
- retry/backoff distribuído
