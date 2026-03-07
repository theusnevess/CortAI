# CortAI - Pilot Day GO / NO-GO Checklist

Versao: `v1.0`  
Aplica-se a: `CortAI >= D33`  
Uso: imediatamente antes de iniciar o piloto de 72h

## 1. Contas

- [ ] 3 contas aquecidas e elegiveis
- [ ] nenhuma conta com warning recente
- [ ] nenhuma conta em cooldown
- [ ] login funcional nas 3 contas

NO-GO se:

- menos de 3 contas elegiveis
- qualquer conta em cooldown

## 2. Sistema CortAI

Endpoints:

- `GET /health` -> `200`
- `GET /ready` -> `ready=true`

Payload esperado:

- `ready: true`
- `scheduler: ok`
- `workers >= 1`
- `queue: ok`
- `event_index: ok`
- `hot_store: ok`

NO-GO se:

- `/ready != 200`
- `ready=false`
- `queue != ok`

## 3. Pipeline de Conteudo

Dry-run minimo executado:

- [ ] `creative_pack` gerado
- [ ] render executado
- [ ] publish adapter respondeu
- [ ] `publish_record` persistido

NO-GO se:

- render falhar
- `publish_record` nao persistir

## 4. Safety Layer

Teste rapido executado:

- [ ] pacing violation simulado -> `DELAY`
- [ ] cooldown simulado -> `BLOCK`

NO-GO se:

- `safety_gate` nao interferir no publish

## 5. Metrics Collector

- [ ] worker ativo
- [ ] coleta agendada
- [ ] primeira coleta confirmada para 1 publish de teste

Arquivo esperado:

- `OUT/metrics/video_metrics.jsonl`

NO-GO se:

- metricas nao persistirem apos teste

## 6. Experiments

- [ ] experiment framework ativo
- [ ] variantes atribuidas
- [ ] experiment assignments persistidos

## 7. Observabilidade

Eventos esperados:

- `CONTENT/*`
- `SAFETY/*`
- `METRICS/*`

- [ ] console operacional visivel
- [ ] alertas configurados

## 8. Parametros do Piloto

Configuracao inicial:

- `accounts: 3`
- `posts_per_account_per_day: 2`
- `duration: 72h`
- `total_expected_posts: 12-18`

Pacing:

- `min_interval_between_posts: 120 min`
- `jitter: +-5-8 min`

## 9. Kill Switch

Teste obrigatorio:

- [ ] kill switch acionado em ambiente de teste
- [ ] novas tasks nao sao enfileiradas
- [ ] workers nao iniciam novos publishes apos o switch

## 10. Decisao Final

Se todas as caixas estiverem marcadas:

`GO`

Iniciar piloto D23.

## Condicoes de Abort

Abortar imediatamente se ocorrer:

- `ACCOUNT_RESTRICTED`
- `RATE_LIMIT` em multiplas contas
- `COOLDOWN > 24h`
- erro persistente de publish

Procedimento:

- acionar `kill switch rollout`

## Resumo

Esse checklist existe para responder apenas uma pergunta:

`Podemos iniciar o piloto agora sem risco operacional desnecessario?`
