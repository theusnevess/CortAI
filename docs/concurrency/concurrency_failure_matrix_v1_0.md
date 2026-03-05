# Concurrency Failure Matrix v1.0

## Objetivo
Definir respostas canonicas para falhas de concorrencia em D12.

## Matriz

| Caso | Deteccao | Acao | Severidade | reason_code |
|---|---|---|---|---|
| Double-apply com mesmo op_key e hash diferente | `idempotency_check_or_reserve` | BLOCK | HIGH | `IDEMPOTENCY_CONFLICT` |
| Lease negada (owner ativo) | `acquire_lease` | BLOCK | MEDIUM | `LEASE_DENIED` |
| Lease expirada antes de write | validacao de lease handle | BLOCK | HIGH | `LEASE_EXPIRED` |
| Snapshot ausente para executar D10 | precondicao no pipeline | BLOCK | HIGH | `SNAPSHOT_MISSING` |
| Snapshot parcial/invalido | validacao de schema/hash | BLOCK | HIGH | `SNAPSHOT_INVALID` |
| Reexecucao com mesmo op_key e hash igual | idempotency store | NOOP | LOW | `IDEMPOTENCY_NOOP` |
| Release apos expiracao | release defensivo | DEGRADE | LOW | `LEASE_RELEASE_AFTER_EXPIRY` |

## Regras de decisao
- BLOCK: risco de drift ou verdade parcial.
- DEGRADE: erro sem impacto na verdade final.
- NOOP: repeticao segura detectada por hash igual.