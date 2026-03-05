# Window Metrics Aggregation v1.0

## Objetivo
Gerar `window_metrics` determinísticos (janela de 72h) a partir de `publish_records` (D3) + `video_metrics` (D4).

## Fluxo canônico
```text
job_id
  -> publish_record (D3)
  -> video_id
  -> video_metrics (D4)
  -> window_aggregation (D5)
  -> window_metrics
```

## Shape canônico
```json
{
  "window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
  "account_id": "acc_ca_001",
  "videos_considered": 3,
  "avg_views": 200.0,
  "avg_retention_3s": 0.45,
  "avg_completion_rate": 0.31,
  "avg_rpm": 0.72,
  "total_views": 600,
  "total_follows": 9,
  "computed_at": "2026-03-05T00:10:00Z"
}
```

## Campos mínimos
- `window_id: str`
- `account_id: str`
- `videos_considered: int`
- `avg_views: float`
- `avg_retention_3s: float | null`
- `avg_completion_rate: float | null`
- `avg_rpm: float | null`
- `total_views: int`
- `total_follows: int | null`
- `computed_at: str`

## Invariantes
- `window_id` é obrigatório.
- `videos_considered >= 0`.
- `total_views >= 0`.
- Médias `avg_*` são calculadas apenas com valores não nulos.
- `window_id` usa formato `w_<start_iso>_<end_iso>`.

## Persistência e idempotência (v1.0)
- Store append-only em `OUT/data/window_metrics.jsonl`.
- Chave canônica de idempotência: `(account_id, window_id)`.
- Mesmo conteúdo: `NOOP`.
- Conteúdo diferente para a mesma chave: erro explícito.
