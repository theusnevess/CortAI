# Publish Record Spec v1.0

## Objetivo
Definir o artefato canonico que liga publicacao real ao motor de geracao:
`job_id -> video_id`.

## Shape canonico
```json
{
  "publish_id": "pub_20260304_0001",
  "account_id": "acc_ca_001",
  "job_id": "job_123",
  "video_id": "vid_abc",
  "platform": "tiktok",
  "publish_mode": "auto",
  "status": "posted",
  "published_at": "2026-03-04T18:00:00Z",
  "created_at": "2026-03-04T18:00:00Z",
  "metadata": {}
}
```

## Enums fechados
- `platform`: `tiktok | youtube_shorts | instagram_reels`
- `publish_mode`: `auto | manual | replay`
- `status`: `posted | failed | blocked`

## Invariantes
- `publish_id` e obrigatorio e unico.
- `video_id` valido nao pode existir sem `job_id`.
- Para `(job_id, account_id, platform)`, no maximo 1 registro `status=posted`.
- Escrita e append-only no log JSONL.

## API minima (v1.0)
- `write_publish_record(record)` grava registro validado.
- `get_by_job(job_id, account_id, platform)` consulta por job.
- `get_by_video(video_id, account_id, platform)` consulta por video.
