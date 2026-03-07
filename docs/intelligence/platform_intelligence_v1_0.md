# D30 - Platform Intelligence Layer v1.0

## Objetivo

Transformar sinais operacionais da plataforma em recomendacoes acionaveis, sem interferir diretamente na execucao.

Fluxo alvo:

`publish_records + video_metrics + safety_events -> platform intelligence outputs`

## Escopo

Entra:
- analise deterministica de janelas de publicacao
- recomendacao de pacing
- perfil de risco por conta
- snapshot de saude da conta
- persistencia append-only em `OUT/intelligence/`

Nao entra:
- alterar `publish.py`
- alterar `safety_gate`
- alterar scheduler
- alterar `publish_record`
- chamadas externas

## Inputs

- `OUT/data/publish_records/publish_records.jsonl`
- `OUT/data/video_metrics/video_metrics.jsonl`
- `OUT/events/events.jsonl` com familia `SAFETY/*`

## Outputs

### PublishWindowRecommendation

- `recommendation_id`
- `account_id`
- `generated_at`
- `best_publish_windows`
- `source_publish_count`
- `source_metric_count`

### PacingRecommendation

- `recommendation_id`
- `account_id`
- `generated_at`
- `recommended_min_interval_minutes`
- `recommended_max_posts_per_day`
- `recommended_max_posts_per_hour`
- `reason_codes`

### RiskProfile

- `profile_id`
- `account_id`
- `generated_at`
- `risk_level`
- `signal_counts`
- `latest_risk_ts`
- `reason_codes`

### AccountHealthSnapshot

- `snapshot_id`
- `account_id`
- `generated_at`
- `account_health`
- `avg_views`
- `avg_completion_rate`
- `publish_count`
- `risk_level`
- `reason_codes`

## Persistencia

Path base:

`OUT/intelligence/`

Arquivos:
- `publish_windows.jsonl`
- `pacing_profiles.jsonl`
- `risk_profiles.jsonl`
- `account_health.jsonl`

Semantica:
- append-only
- recomputacao identica -> `NOOP`
- payload diferente para mesma chave -> `CONFLICT`

## Regras de analise

### Publish windows

- agrupa publicacoes por hora UTC
- prioriza horas com melhor media de views e completion rate
- fallback sem metricas: usa frequencia de publicacao

### Pacing

- parte de baseline conservador
- degrada quando existem sinais `SAFETY/pacing_delay`, `SAFETY/risk_detected`, `SAFETY/cooldown_started`

### Risk profile

- considera apenas `SAFETY/*`
- deterministico por contagem e severidade

### Account health

- combina media de views, completion rate e risco
- classifica em `HEALTHY | WATCH | AT_RISK`

## Integracao

Conversa com:
- D28 (`SAFETY/*`)
- D26 (observabilidade estrategica)
- D21 (scheduler pode consumir as recomendacoes depois)

No v1.0 nao existe feedback automatico para scheduler ou publish.

## Criterio de aceite

O D30 fecha se:
- gera recomendacao de janela
- gera recomendacao de pacing
- detecta risco por conta
- produz snapshot de saude
- persiste append-only sem duplicacao em recomputacao identica
