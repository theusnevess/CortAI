# Checklist de PR - Observability / Publish

## 0) Contexto
- Objetivo do PR:
- Escopo (arquivos/areas tocadas):
- Invariantes respeitados: append-only, sem heuristica, facts sem paths.

## A) Migracoes / Banco
- [ ] `alembic upgrade head` executado sem erro
- [ ] `alembic current` aponta para `head`
- [ ] Sanity de tabela/indice novo (quando aplicavel)

Evidencias:
- `alembic upgrade head`:
- `alembic current`:

## B) Testes (Contrato API)
- [ ] `python -m pytest -q` passou
- [ ] Cobertura dos contratos:
  - [ ] `/metrics/daily`
  - [ ] `/metrics/overview`
  - [ ] `/metrics/alerts`
  - [ ] guardrails/dedupe

Comando:
`docker exec -i cortai_api sh -lc "cd /app && python -m pytest -q"`

Resultado:

## C) Smoke Telemetria (dia vazio)
- [ ] `aggregate_daily_metrics('2099-01-01')` com `status=done`
- [ ] Totais zerados
- [ ] Sem `cognitive_metrics_alert` no dia

Comando:
`docker exec -i cortai_worker python -c "from app.tasks.collector_tasks import aggregate_daily_metrics; r=aggregate_daily_metrics('2099-01-01'); assert r['status']=='done'; assert r['total_runs']==0; print('SMOKE_OK')"`

Query:
```sql
SELECT COUNT(*)
FROM observations
WHERE facts->>'event_type'='cognitive_metrics_alert'
  AND facts->>'metric_date'='2099-01-01';
```

## D) Contrato cognitive_loop_finished
- [ ] Termina e emite em cenarios observaveis
- [ ] `pipeline_status` valido
- [ ] Dedupe por `(process_id, source_outcome_id)`
- [ ] Sem paths em `facts`

## E) Manifest (write_artifact)
- [ ] `<decision_id>.json` existe
- [ ] Schema objetivo valido
- [ ] Observation sem paths

## F) Manifest-only Consumer (publish_manifest)
- [ ] Consumidor le apenas manifest
- [ ] `ArtifactNotFound` -> blocked
- [ ] `ArtifactInvalid` -> failed
- [ ] Sucesso com `last_action_type=publish_manifest`

## G) Publish Receipts (A-F)
- [ ] A) publish observado
- [ ] B/C) sem duplicata por `publish_decision_id`
- [ ] D) sem vazamento de path em `error_message`
- [ ] E) blocked/failed com `error_type` e `error_message`
- [ ] F) vinculo com manifest valido

Queries:
```sql
SELECT publish_decision_id, COUNT(*)
FROM publish_receipts
GROUP BY publish_decision_id
HAVING COUNT(*) > 1;
```

```sql
SELECT *
FROM publish_receipts
WHERE error_message ~ '(/tmp|storage|videos-raw|\\.mp4|\\.wav)'
LIMIT 20;
```

## H) Runtime / Operacao
- [ ] `git status` limpo
- [ ] `docker compose ps` com API/worker/beat up
- [ ] Sem `OutcomeMismatch` em logs do worker

## I) Notas de risco
- Backward-compatible:
- Requer restart:
- Downtime de migracao:
- Variaveis novas:
