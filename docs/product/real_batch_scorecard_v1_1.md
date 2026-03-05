# Real Batch Scorecard v1.1

## Objetivo
Gerar automaticamente um scorecard analítico por janela (`window_id`) com base em `window_metrics`, bloqueando execução quando o `data_consistency_guard` apontar violação estrutural.

## Fluxo canônico
```text
publish_records (D3)
  -> video_metrics (D4)
  -> window_metrics (D5)
  -> data_consistency_guard (D6)
  -> real_batch_scorecard (D7)
```

## Shape canônico
```json
{
  "account_id": "acc_ca_001",
  "window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
  "videos_considered": 12,
  "avg_views": 823.2,
  "avg_retention_3s": 0.43,
  "avg_completion_rate": 0.29,
  "avg_rpm": 0.76,
  "status": "OPTIMIZE",
  "recommendation": "OTIMIZAR_HOOKS",
  "generated_at": "2026-03-05T02:00:00Z"
}
```

## Campos mínimos
- `account_id: str`
- `window_id: str`
- `videos_considered: int`
- `avg_views: float`
- `avg_retention_3s: float | null`
- `avg_completion_rate: float | null`
- `avg_rpm: float | null`
- `status: STABLE | OPTIMIZE | RECOVERY`
- `recommendation: str`
- `generated_at: str`

## Regras de geração (v1.1)
- `RECOVERY` quando `avg_retention_3s < 0.35`.
- `OPTIMIZE` quando retenção não cai em `RECOVERY`, mas desempenho ainda pede ajuste.
- `STABLE` quando lote está saudável.

## Integração com Guard (obrigatória)
- Se `guard.blocked == true`: não gerar scorecard.
- Erro canônico: `CONSISTENCY_VIOLATION_BLOCKED`.

## Persistência e idempotência
- Store append-only: `OUT/data/scorecards.jsonl`.
- Chave canônica: `(account_id, window_id)`.
- Mesmo payload: `NOOP`.
- Payload diferente para mesma chave: erro explícito.
