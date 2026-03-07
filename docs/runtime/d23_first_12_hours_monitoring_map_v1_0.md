# CortAI - First 12 Hours Monitoring Map

Versao: `v1.0`  
Aplica-se a: `CortAI >= D33`  
Uso: monitoramento intensivo apos inicio do piloto D23

## Objetivo

- detectar risco de conta cedo
- confirmar funcionamento do pipeline real
- validar coleta de metricas
- observar sinais iniciais de aprendizado

## T+10 minutos - checkpoint critico

Confirmar imediatamente apos o primeiro publish:

- [ ] `publish_record` escrito
- [ ] evento `CONTENT/publish_completed` emitido
- [ ] ausencia de `SAFETY/publish_blocked`

Arquivos esperados:

- `OUT/data/publish_records.jsonl`
- `OUT/content/video/<render_job_id>.mp4`

Se falhar:

- [ ] abrir incidente operacional
- [ ] nao esperar T+30

## T+30 minutos

Confirmar integridade do loop.

Pipeline:

- [ ] proxima task agendada
- [ ] workers ativos

Eventos esperados:

- `CONTENT/*`
- `SAFETY/*`

## T+60 minutos - checkpoint de metricas

Confirmar ingestao inicial.

Arquivo:

- `OUT/metrics/video_metrics.jsonl`

Criterio congelado:

- se nenhuma linha aparecer ate `T+60 min` -> abrir incidente operacional

Isso indica problema em:

- metrics collector
- platform API
- persistencia

## 1-3 horas

Agora observar sinais de seguranca e estabilidade.

Verificar eventos:

- `SAFETY/pacing_delay`
- `SAFETY/risk_detected`

Esses sao normais.

Alerta se aparecer:

- `SAFETY/publish_blocked`

## 3-6 horas

Primeiros sinais de performance.

### Sistema vivo

- `views > 0`
- `watch_time > 0`

Significa:

- conteudo indexado
- pipeline funcional

### Sinal inicial bom

- `completion_rate > 20%`

Nao e obrigatorio no piloto, mas e bom indicador.

## 6-12 horas

Confirmar aprendizado do sistema.

Arquivos esperados:

- `OUT/experiments/`
- `OUT/intelligence/`
- `OUT/attribution/`

Isso valida:

- D30 intelligence
- D31 experiments
- D32 attribution

## Sinais de risco precoce

Abortar piloto se ocorrer:

- `ACCOUNT_RESTRICTED`
- `REPEATED_PUBLISH_REJECTED`
- `RATE_LIMIT` em multiplas contas
- `COOLDOWN > 24h`

Procedimento:

- acionar `kill switch rollout`

## Artefatos esperados ate T+12h

Confirmar presenca de:

- `OUT/content/`
- `OUT/metrics/video_metrics.jsonl`
- `OUT/experiments/`
- `OUT/intelligence/`
- `OUT/attribution/`
- `OUT/safety/`

## Criterio de piloto saudavel nas primeiras 12h

Confirmar:

- pipeline executou
- publicacao real ocorreu
- metricas chegaram
- experimentos distribuiram
- safety nao bloqueou contas

Se todos verdadeiros:

- piloto esta saudavel

## Resumo

Esse mapa existe para responder:

`Nas primeiras 12 horas, o piloto esta vivo, seguro e produzindo aprendizado?`
