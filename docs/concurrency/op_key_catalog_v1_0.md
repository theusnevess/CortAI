# OP Key Catalog v1.0

## Objetivo
Congelar formato de chaves idempotentes para operacoes criticas.

## Formato
`{OP}:{account_id}:{window_id}`

Operacoes que exigem stage:
`SPA:{account_id}:{window_id}:{stage}`

## Catalogo
- `AGG:{account_id}:{window_id}`
- `SC:{account_id}:{window_id}`
- `ATTR:{account_id}:{window_id}`
- `SL:{account_id}:{window_id}`
- `SPA:{account_id}:{window_id}:{stage}`
- `UPD:{account_id}:{window_id}`

## Regras
1. Mesmo `op_key` + mesmo `payload_hash` => `NOOP`.
2. Mesmo `op_key` + hash diferente => `CONFLICT`.
3. Operacao so finaliza apos `finalize_op`.
4. Toda reserva/finalizacao emite evento de auditoria.