# Content Attribution v1.0

## Objetivo
Conectar de forma determinística os artefatos canônicos para formar o dataset de attribution:

`job_id -> publish_id/video_id -> video_metrics -> window_id -> scorecard`.

Esta camada não faz aprendizado. Apenas constrói e persiste o registro estruturado.

## Decisões congeladas (v1.0)

### 1) Métricas ausentes
- Se não existir métrica real para o vídeo: attribution não é gerado.
- Erro canônico: `ATTRIBUTION_METRICS_MISSING`.

### 2) Idempotência
- Chave canônica: `publish_id`.
- Motivo: representa a entidade real de publicação e evita ambiguidade em reupload.

## Fluxo canônico
```text
job_id
  -> publish_record (D3)
  -> publish_id / video_id
  -> video_metrics (D4)
  -> window_metrics (D5)
  -> scorecard (D7)
  -> content_attribution (D8)
```

## Shape canônico mínimo
```json
{
  "attribution_id": "attr_pub_20260305_001",
  "account_id": "acc_ca_001",
  "publish_id": "pub_20260305_001",
  "video_id": "vid_abc123",
  "job_id": "job_789",
  "window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
  "policy_stage": "GROWTH",
  "hook_strategy": "open_loop_shock",
  "dominant_failure_reason": null,
  "effective_duration_s": 33,
  "rare_fact_placement_s": 18,
  "human_patch_detected": false,
  "views": 1200,
  "retention_3s": 0.46,
  "completion_rate": 0.31,
  "likes": 150,
  "follows": 18,
  "rpm": 0.84,
  "captured_at": "2026-03-05T00:02:00Z",
  "generated_at": "2026-03-05T00:05:00Z"
}
```

## Campos obrigatórios
- `attribution_id`
- `account_id`
- `publish_id`
- `video_id`
- `job_id`
- `window_id`
- `policy_stage`
- `hook_strategy`
- `effective_duration_s`
- `rare_fact_placement_s`
- `human_patch_detected`
- `views`
- `retention_3s`
- `completion_rate`
- `captured_at`
- `generated_at`

## Campos opcionais
- `dominant_failure_reason`
- `likes`
- `follows`
- `rpm`

## Invariantes
- `retention_3s` em `[0, 1]`.
- `completion_rate` em `[0, 1]`.
- `views >= 0`.
- `effective_duration_s > 0`.
- `rare_fact_placement_s >= 0`.
- `rare_fact_placement_s <= effective_duration_s`.
- `publish_id` obrigatório para idempotência.

## Fora de escopo (v1.0)
- Ranking de estratégias.
- Aprendizado adaptativo.
- Mutação de policy/account registry.
