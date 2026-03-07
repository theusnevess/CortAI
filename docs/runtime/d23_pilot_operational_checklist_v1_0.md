# CortAI - Piloto Real D23

## Operational Checklist v1.0

Applies to:
- `CortAI >= D32`
- `Pilot stage: D23`
- `Accounts required: 3 warmed accounts`

## Objetivo

Validar comportamento real do sistema, medir performance inicial e coletar sinais para strategy learning sem colocar contas em risco.

## 1. Pre-run

### Contas

- [ ] 3 contas elegiveis
- [ ] aquecimento minimo concluido
- [ ] nenhuma conta com warning recente
- [ ] nenhuma conta em cooldown

### Sistema

- [ ] scheduler ativo
- [ ] workers ativos
- [ ] safety layer ativa
- [ ] experiment framework habilitado

### Endpoints

- [ ] `GET /health` -> `200`
- [ ] `GET /ready` -> `ready=true`

### Diretorios operacionais

- [ ] `OUT/content/`
- [ ] `OUT/safety/`
- [ ] `OUT/intelligence/`
- [ ] `OUT/experiments/`
- [ ] `OUT/attribution/`
- [ ] `OUT/rollout/`
- [ ] `OUT/ops/`

## 2. Parametros do piloto

Configuracao inicial recomendada:

- `accounts = 3`
- `posts_per_day_per_account = 2`
- `duration = 72h`
- `total_posts_expected = 12-18`

Pacing conservador:

- `min_interval_between_posts = 120 min`
- `max_posts_per_day = 3`

Jitter ativo:

- `publish_jitter = +-5-8 min`

## 3. Sequencia de execucao

1. habilitar rollout na allowlist
2. iniciar scheduler da janela
3. monitorar o primeiro ciclo de publish

A primeira publicacao eh a mais importante.

Verificar:

- [ ] publish ocorreu
- [ ] `publish_record` criado
- [ ] safety nao bloqueou
- [ ] metricas comecaram a chegar

## 4. Gate explicito de ingestao

Congelar o SLA operacional minimo:

- primeira evidencia de `publish_record`: ate `T+5 min`
- primeira evidencia de `video_metrics`: ate `T+6 h`

Se um desses limites estourar:

- [ ] abrir investigacao operacional
- [ ] verificar provider / ingestao / account state
- [ ] considerar pausa do piloto se houver repeticao

## 5. Monitoramento nas primeiras horas

### Pipeline

- [ ] `creative_pack` gerado
- [ ] render concluido
- [ ] publish concluido

### Safety

- [ ] pacing delays dentro do esperado
- [ ] nenhum cooldown inesperado
- [ ] nenhum risk signal critico

### Experimentos

- [ ] assignment correto
- [ ] variantes distribuidas

## 6. Alertas que exigem acao imediata

Parar o piloto se aparecer:

- `ACCOUNT_RESTRICTED`
- `REPEATED_PUBLISH_REJECTED`
- `RATE_LIMIT` em multiplas contas
- `COOLDOWN > 24h`

Acao:

- [ ] acionar `kill switch rollout`

## 7. Criterios de abort por tendencia

Abortar preventivamente se ocorrer qualquer um:

- `fallback_rate` anormal e crescente
- `publish success rate < 80%` nas primeiras 12h
- `cooldown_started` em 2 contas ou mais
- `risk_detected` recorrente sem recuperacao

Esses casos sao degradacao operacional, mesmo sem evento fatal unico.

## 8. Observacao durante as 72h

A cada janela observar:

### Performance

- views
- `watch_3s_rate`
- `completion_rate`

### Experimentos

- hook A vs B
- pacing A vs B

### Safety

- delays
- cooldowns
- jitter funcionando

## 9. Artefatos esperados

Ao final do piloto:

- `OUT/rollout/pilot_rollout_report.json`
- `OUT/rollout/pilot_batch_window_summary.json`
- `OUT/rollout/pilot_alerts.json`
- `OUT/ops/slo_status.json`
- `OUT/ops/alerts.jsonl`

## 10. Metricas minimas para considerar o piloto valido

O piloto nao busca viralizacao.

Ele busca:

- publicacao estavel
- contas sem restricao
- metricas chegando corretamente
- experimentos rodando
- atribuicao funcionando

## 11. Criterio GO para expansao

O piloto e considerado bem-sucedido se:

- `publish success rate >= 95%`
- `0 contas restritas`
- experimentos gerando dados
- pipeline sem falhas criticas

## 12. Pos-piloto

Executar:

- rollout summary
- experiment summary
- strategy learning review

Gerar:

- `OUT/rollout/pilot_summary.md`

## 13. O que nao esperar do piloto

Piloto nao e para:

- viralizar
- ganhar seguidores
- bater milhoes de views

Piloto e para:

- validar o sistema
- coletar sinais
- alimentar aprendizado

## Resumo operacional

Fluxo correto:

`aquecer contas -> executar piloto D23 -> validar comportamento real -> abrir D25`
