# Data Consistency Guard v1.0

## Objetivo
Bloquear estados impossíveis antes de scorecard e attribution.

Regra constitucional:
- nunca corrigir silenciosamente;
- checks com `BLOCK` impedem continuidade do pipeline.

## API canônica
`run_data_consistency_guard(account_id, window_id, deps) -> GuardResult`

## Catálogo mínimo (v1.0)

### VCG_001 (BLOCK)
Todo `video_id` presente em `video_metrics` da janela deve existir em `publish_records` da mesma conta/janela.

### VCG_002 (SOFT/SKIP)
Todo `publish_record.job_id` da janela deve existir em `job_spec`.
- Se repositório de `job_spec` não estiver disponível: `SKIPPED_NOT_AVAILABLE`.

### VCG_003 (BLOCK)
`window_metrics.videos_considered == count(publish_records in window)`.

### VCG_004 (BLOCK)
Quando `window_metrics` trouxer campos derivados:
- `videos_with_metrics + videos_missing_metrics == videos_considered`.

### VCG_005 (CATALOGADO)
Scorecard e Attribution devem usar o mesmo `window_id`.
No v1.0 o check fica disponível no catálogo e pode ser avaliado quando os ids forem fornecidos em `deps`.

## Erros canônicos
- `CONSISTENCY_VIOLATION_BLOCKED`
- `CONSISTENCY_DEPENDENCY_MISSING`

## Saída auditável
Resultado pode ser persistido em:
`OUT/guards/data_consistency/<account_id>/<window_id>.json`
