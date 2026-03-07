# D23 Pilot Runbook v1.0

## Objetivo

Executar o primeiro batch real de 72h em modo controlado, com risco contido e evidência operacional persistida.

Este runbook é obrigatório antes de abrir D25.

## Pré-condições

Antes de iniciar o piloto, confirmar:

- rollout habilitado
- kill switch desabilitado
- `/health` = `200`
- `/ready` = `200`
- scheduler ativo
- pelo menos 1 worker saudável
- integração externa do provider validada
- `publish_record` gravando corretamente
- `OUT/ops/slo_status.json` e `OUT/ops/alerts.jsonl` acessíveis
- `OUT/rollout/` com permissão de escrita

## Escopo do piloto

### Allowlist inicial

Rodar somente em contas explicitamente aprovadas.

Exemplo:

```json
[
  "acc_truecrime_001",
  "acc_truecrime_002",
  "acc_truecrime_003"
]
```

### Nicho inicial

- 1 macro-nicho
- 1 linha editorial
- 1 policy_stage por vez, preferencialmente `GROWTH`

### Volume inicial

Recomendação:

- 3 contas
- 3 a 5 conteúdos por conta
- 1 janela de 72h

## Checklist pré-run

### Sistema

- [ ] `GET /health` em `:8000` retorna `200`
- [ ] `GET /ready` em `:8000` retorna `200`
- [ ] `GET /health` em `:8002` retorna `200`
- [ ] `GET /ready` em `:8002` retorna `200`

### Rollout

- [ ] conta está na allowlist
- [ ] `policy_stage` permitido
- [ ] `operator_control.json` não está pausando rollout
- [ ] kill switch = `false`

### Conteúdo

- [ ] creative packs prontos
- [ ] pipeline D27 validado
- [ ] provider D22 autenticado
- [ ] `publish_record` funcionando

### Observabilidade

- [ ] console operacional acessível
- [ ] alertas do D19 visíveis
- [ ] `/api/v1/events` funcional
- [ ] event index/hot store operacionais

## Sequência operacional

### 1. Congelar a allowlist

Persistir as contas piloto para o rollout controlado.

### 2. Confirmar estado do controle operacional

Verificar:

- rollout ativo
- kill switch desligado
- nenhum alerta crítico aberto que bloqueie execução

### 3. Agendar a janela

Disparar o scheduler para criar:

- `WINDOW_AGGREGATION`
- `WINDOW_POST_PIPELINE`

Somente para as contas piloto.

### 4. Acompanhar execução no console

Observar:

- tasks em `RUNNING`
- tasks em `FAILED`
- tasks em `BLOCKED`
- progresso por `window_id`
- health do worker

### 5. Confirmar artifacts do batch

Ao fim da janela, confirmar que existem:

- `window_metrics`
- `scorecard`
- `content_attribution`
- `strategy_patch`
- `patch_applied` ou `NOOP` legítimo

### 6. Rodar evaluator de SLO

Gerar/atualizar:

- `OUT/ops/slo_status.json`
- `OUT/ops/alerts.jsonl`

### 7. Persistir artefatos do piloto

Gerar/atualizar:

- `OUT/rollout/pilot_rollout_report.json`
- `OUT/rollout/pilot_rollout_report.md`
- `OUT/rollout/pilot_batch_window_summary.json`
- `OUT/rollout/pilot_alerts.json`

## Critério GO do piloto

O piloto é considerado válido se, para as contas allowlisted:

- `window_metrics` existe
- `scorecard` existe
- `content_attribution` existe
- `strategy_patch` existe
- `patch_applied` é `APPLIED` ou `NOOP` legítimo
- nenhum `double_apply`
- nenhum `snapshot_partial`
- nenhum `conflict` inesperado
- nenhum alerta `CRITICAL` novo

## Critério NO-GO do piloto

Parar imediatamente o rollout se houver:

- `double_apply > 0`
- `snapshot_partial > 0`
- `strategy_patch_conflict` inesperado
- `event_query_error_rate` em nível crítico
- `data_consistency_guard` bloqueando conta piloto sem justificativa
- duplicação de `publish_record`

## Rollback procedure

### Caso de incidente operacional

1. acionar `pause-rollout`
2. se necessário, acionar kill switch
3. deixar workers finalizarem o que já está em execução
4. não agendar nova janela
5. preservar artifacts e eventos
6. abrir análise via:
   - console
   - `/api/v1/events`
   - alerts persistidos

### Caso de degradação de observabilidade

Se hot store ou index falhar:

- manter pipeline vivo
- usar fallback:
  - hot store -> index -> scanner
- não interromper batch só por degradação de leitura

## Checklist de observação no console

### Overview

- [ ] rollout enabled
- [ ] kill switch disabled
- [ ] p95 `/events` dentro do esperado
- [ ] fallback rate aceitável
- [ ] sem alertas críticos

### Windows / Batches

- [ ] `window_id` correto
- [ ] scorecard presente
- [ ] attribution presente
- [ ] patch status presente

### Tasks / Workers

- [ ] sem acúmulo anormal de `FAILED`
- [ ] sem acúmulo anormal de `BLOCKED`
- [ ] retries dentro do esperado

### Strategy Observatory

- [ ] patches visíveis
- [ ] timeline coerente
- [ ] impacto por janela calculado

## Artefatos esperados

### OUT/rollout

- `pilot_rollout_report.json`
- `pilot_rollout_report.md`
- `pilot_batch_window_summary.json`
- `pilot_alerts.json`

### OUT/ops

- `slo_status.json`
- `alerts.jsonl`

### OUT/data

- `publish_records/...`
- `strategy_patches.jsonl`
- `strategy_patch_applications.jsonl`

## Pós-run

Ao final do piloto:

1. consolidar evidência operacional
2. rodar auditoria focada do batch
3. classificar o resultado:
   - `GO`
   - `WARN`
   - `NO-GO`
4. somente com `GO` abrir D25
