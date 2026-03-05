# Video Metrics Ingestion Spec v1.0

## Objetivo
Definir ingestao canonica de metricas reais por video, com chave deterministica de deduplicacao e precedencia de fonte.

## Shape canonico
```json
{
  "video_id": "vid_abc",
  "account_id": "acc_ca_001",
  "captured_at": "2026-03-04T18:00:00Z",
  "captured_window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
  "source_kind": "PLATFORM_ANALYTICS",
  "views": 12345,
  "retention_3s": 0.46,
  "completion_rate": 0.31,
  "likes": 245,
  "follows": 27,
  "rpm": 0.92,
  "ingested_at": "2026-03-04T18:02:00Z"
}
```

## Campos obrigatorios
- `video_id`
- `account_id`
- `captured_at` (ISO8601 UTC)
- `captured_window_id`
- `source_kind`
- `views`
- `ingested_at` (ISO8601 UTC)

## Enum fechado de source_kind
- `PLATFORM_ANALYTICS`
- `SCRAPED_ANALYTICS`
- `MANUAL_ENTRY`

## Invariantes
- `views >= 0`
- `0 <= retention_3s <= 1` quando nao nulo
- `0 <= completion_rate <= 1` quando nao nulo
- `captured_window_id` obrigatorio
- `source_kind` obrigatorio e fechado

## Dedup key canonica
`(account_id, video_id, captured_window_id)`

## Precedencia de fonte
1. `PLATFORM_ANALYTICS`
2. `SCRAPED_ANALYTICS`
3. `MANUAL_ENTRY`

## Regras
- Fonte pior para mesma dedup key: `NOOP`.
- Fonte melhor para mesma dedup key: atualiza best atual sem remover historico append-only.
