# D12 Concurrency Hardening v1.0

## Objetivo
Garantir exclusividade de escrita, idempotencia e snapshot atomico por janela para evitar double-apply, escrita fora de ordem e estado parcial.

## Escopo v1.0
- Leases por conta e por janela.
- Catalogo de op_key para operacoes criticas.
- Reserva idempotente por op_key + payload hash.
- Snapshot atomico da janela antes do fluxo D10.

## Invariantes
1. Um writer por chave (`account_id` ou `account_id+window_id`).
2. Operacoes criticas protegidas por `op_key`.
3. Pipeline de janela executa sob `LEASE_WINDOW`.
4. Toda violacao gera evento com `reason_code`.
5. `BLOCK` quando ha risco de drift.

## Leases
- `LEASE_ACCOUNT:{account_id}`
- `LEASE_WINDOW:{account_id}:{window_id}`

## Regras de lease
- Lease expirada bloqueia escrita.
- Renovacao falha se owner mudou.
- Release de lease inexistente nao quebra execucao.

## Integracao com D10
1. `window_pipeline` adquire `LEASE_WINDOW`.
2. Reserva `AGG:{account_id}:{window_id}`.
3. Gera snapshot atomico e persiste.
4. Executa D10 usando snapshot imutavel.

## Resultado esperado
Execucao deterministica, sem aplicacao duplicada e com trilha auditavel por `account_id`, `window_id` e `op_key`.