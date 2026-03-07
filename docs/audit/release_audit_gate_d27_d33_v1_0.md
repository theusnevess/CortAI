# CortAI - Release Audit Gate Completo

Versao: `v1.0`  
Aplica-se a: `CortAI >= D33`  
Uso: auditoria completa antes do piloto real D23

## Objetivo

Confirmar que o sistema esta:

- funcional
- consistente
- seguro
- observavel
- operavel
- pronto para o piloto real

## Regra de decisao

### GO

Somente se houver:

- 0 falhas em testes
- 0 regressões criticas
- 0 duplicacoes indevidas de estado
- 0 vazamentos de estado entre execucoes
- 0 vulnerabilidades conhecidas relevantes
- 0 erros operacionais sem explicacao
- 0 caminhos criticos fora do comportamento planejado

### NO-GO

Se aparecer qualquer um destes:

- `publish_record` duplicado sem justificativa
- publicacao falsa em `DELAY` ou `BLOCK`
- idempotencia quebrada
- inconsistencia entre log e indice
- scheduler duplicando tasks
- worker executando sem lease
- metricas nao persistindo
- alertas/SLO incoerentes
- endpoint critico indisponivel
- segredo exposto
- fallback quebrado
- evento obrigatorio nao emitido

## Escopo desta auditoria

### Nucleo funcional

- `D27` - Content Pipeline Automation
- `D28` - Platform Safety Layer
- `D29` - Creative Pack Generator
- `D30` - Platform Intelligence
- `D31` - Experiment Framework
- `D32` - Advanced Attribution
- `D33` - Metrics Collector

### Regressões obrigatorias

- `D3` - publish_records
- `D16 / D16.5 / D17` - event storage, index, hot store
- `D19` - SLO + alerting
- `D20` - distributed execution
- `D21` - distributed scheduler
- `D22` - external integration
- `D23` - rollout policy
- `D24 / D24.5` - operator console / actions
- `D26` - strategy observatory

## Parte 1 - Testes automatizados

### 1. Testes principais do bloco atual

```powershell
python -m unittest -q ^
  tests.test_content_pipeline_d27_unittest ^
  tests.test_platform_safety_d28_unittest ^
  tests.test_creative_pack_generator_d29_unittest ^
  tests.test_platform_intelligence_d30_unittest ^
  tests.test_experiment_framework_d31_unittest ^
  tests.test_content_attribution_d32_unittest ^
  tests.test_metrics_collector_d33_unittest
```

Criterio:

- tudo verde
- nenhum skip relevante

### 2. Regressões criticas

```powershell
python -m unittest -q ^
  tests.test_publish_records_d3_unittest ^
  tests.test_event_index_d16_unittest ^
  tests.test_event_append_write_through_d16_5_unittest ^
  tests.test_hot_storage_d17_unittest ^
  tests.test_slo_alerting_d19_unittest ^
  tests.test_distributed_execution_d20_unittest ^
  tests.test_distributed_scheduler_d21_unittest ^
  tests.test_external_platform_integration_d22_unittest ^
  tests.test_real_batch_rollout_d23_unittest ^
  tests.test_operator_console_d24_unittest ^
  tests.test_operator_actions_d24_5_unittest ^
  tests.test_strategy_observatory_d26_unittest
```

Criterio:

- 0 falhas
- 0 regressões de comportamento

### 3. Compilacao / sanidade de import

```powershell
Get-ChildItem backend/app/content/pipeline/*.py | ForEach-Object { python -m py_compile $_.FullName }
Get-ChildItem backend/app/safety/*.py | ForEach-Object { python -m py_compile $_.FullName }
Get-ChildItem backend/app/content/creative_pack/*.py | ForEach-Object { python -m py_compile $_.FullName }
Get-ChildItem backend/app/intelligence/*.py | ForEach-Object { python -m py_compile $_.FullName }
Get-ChildItem backend/app/experiments/*.py | ForEach-Object { python -m py_compile $_.FullName }
Get-ChildItem backend/app/attribution/*.py | ForEach-Object { python -m py_compile $_.FullName }
Get-ChildItem backend/app/metrics/*.py | ForEach-Object { python -m py_compile $_.FullName }
```

Criterio:

- 0 erros de sintaxe/import

## Parte 2 - Verificacoes funcionais manuais

### 4. Content Pipeline (D27)

Validar:

- creative_pack gera render_job
- TTS gera artefato
- render gera video e metadata
- publish gera publish_record
- retry funciona
- duplicidade vira `NOOP`

Checklist:

- [ ] `OUT/content/audio/` tem arquivo
- [ ] `OUT/content/video/` tem arquivo
- [ ] `OUT/content/metadata/` tem arquivo
- [ ] nomes coerentes com `render_job_id`

NO-GO se:

- TTS/render nao gerarem artefatos
- publish_record nao persistir
- duplicidade gerar duas publicacoes

### 5. Safety Layer (D28)

Validar:

- `ALLOW -> PUBLISH_DONE`
- `DELAY -> DELAYED`
- `BLOCK -> BLOCKED`
- `PUBLISH_RATE_LIMIT -> risco alto + cooldown`

Checklist:

- [ ] `DELAY` nao cria `publish_record`
- [ ] `BLOCK` nao cria `publish_record`
- [ ] cooldown persistido em `OUT/safety/`
- [ ] pacing persistido em `OUT/safety/`
- [ ] eventos `SAFETY/*` emitidos

NO-GO se:

- `DELAY` ou `BLOCK` gerarem publicacao
- state nao persistir
- risk detector nao alterar estado

### 6. Creative Pack Generator (D29)

Validar:

- `creative_pack_id` deterministico
- variacoes estaveis
- persistencia append-only
- `WRITTEN | NOOP | CONFLICT`

Checklist:

- [ ] `OUT/content/creative_packs/creative_packs.jsonl` existe
- [ ] mesma chave logica -> `NOOP`
- [ ] payload diferente -> `CONFLICT`

NO-GO se:

- ID nao for estavel
- store sobrescrever historico
- conflito passar silenciosamente

### 7. Platform Intelligence (D30)

Validar:

- recomendacoes geradas
- risco por conta gerado
- account health snapshot persistido
- nenhuma mutacao do caminho de execucao

Checklist:

- [ ] `OUT/intelligence/publish_windows.jsonl`
- [ ] `OUT/intelligence/pacing_profiles.jsonl`
- [ ] `OUT/intelligence/risk_profiles.jsonl`
- [ ] `OUT/intelligence/account_health.jsonl`

NO-GO se:

- nao persistir
- gerar resultado inconsistente para mesmo input
- tocar em `publish`/`scheduler`/`safety` diretamente

### 8. Experiment Framework (D31)

Validar:

- experimento criado
- assignment deterministico
- mesma entrada -> mesma variante
- append-only consistente

Checklist:

- [ ] `OUT/experiments/experiments.jsonl`
- [ ] `OUT/experiments/assignments.jsonl`
- [ ] `OUT/experiments/results.jsonl`

NO-GO se:

- assignment variar entre execucoes identicas
- duplicidade nao virar `NOOP`

### 9. Advanced Attribution (D32)

Validar:

- hook analysis
- structure analysis
- duration analysis
- integracao com experiment assignments

Checklist:

- [ ] `OUT/attribution/hook_performance.jsonl`
- [ ] `OUT/attribution/structure_performance.jsonl`
- [ ] `OUT/attribution/duration_analysis.jsonl`
- [ ] `OUT/attribution/pattern_performance.jsonl`

NO-GO se:

- recomputacao for instavel
- dados inconsistentes quebrarem API
- attribution ignorar experiment assignments

### 10. Metrics Collector (D33)

Validar:

- coleta real/stub bem-sucedida
- append-only
- idempotencia por bucket logico
- compatibilidade com publish_record

Checklist:

- [ ] `OUT/metrics/video_metrics.jsonl` existe
- [ ] primeira coleta persiste linha
- [ ] coleta duplicada da mesma janela vira `NOOP`
- [ ] `publish_id` e `video_id` coerentes

NO-GO se:

- coleta nao persistir
- duplicar a mesma coleta
- quebrar por publish inexistente sem erro explicito

## Parte 3 - Observabilidade e eventos

### 11. Event sanity

Verificar presenca de eventos minimos:

#### CONTENT

- [ ] `CONTENT/tts_started`
- [ ] `CONTENT/tts_completed`
- [ ] `CONTENT/render_started`
- [ ] `CONTENT/render_completed`
- [ ] `CONTENT/publish_started`
- [ ] `CONTENT/publish_completed`
- [ ] `CONTENT/pipeline_failed` quando aplicavel

#### SAFETY

- [ ] `SAFETY/pacing_delay`
- [ ] `SAFETY/publish_blocked`
- [ ] `SAFETY/risk_detected`
- [ ] `SAFETY/cooldown_started`

#### METRICS

- [ ] `METRICS/collection_started`
- [ ] `METRICS/collection_completed`
- [ ] `METRICS/collection_failed` quando aplicavel

NO-GO se:

- eventos criticos nao forem emitidos
- eventos divergirem do contrato congelado

### 12. Event query / trace

```powershell
python -m unittest -q ^
  tests.test_event_query_forensics_and_scanner_d13_unittest ^
  tests.test_event_query_trace_builder_d13_unittest ^
  tests.test_event_query_seek_pagination_d14_unittest ^
  tests.test_event_query_api_endpoint_d15_unittest
```

Criterio:

- paginacao estavel
- cursor integro
- trace funcional
- anti-scan preservado

NO-GO se:

- cursor duplicar/perder eventos
- forensics policy falhar
- `/events` quebrar

## Parte 4 - Runtime, workers, scheduler e rollout

### 13. Workers / leases / idempotencia

```powershell
python -m unittest -q ^
  tests.test_distributed_execution_d20_unittest ^
  tests.test_concurrency_failure_matrix_d12_unittest
```

Validar:

- [ ] dois workers nao executam a mesma task ao mesmo tempo
- [ ] retry nao duplica efeito
- [ ] lease expirada aborta corretamente
- [ ] `op_key` duplicado -> `NOOP` ou `CONFLICT` correto

NO-GO se:

- double execution
- task duplicada
- lease bypass

### 14. Scheduler

```powershell
python -m unittest -q tests.test_distributed_scheduler_d21_unittest
```

Validar:

- [ ] janelas planejadas corretamente
- [ ] scheduler restart nao duplica task
- [ ] multiplas contas geram filas independentes

NO-GO se:

- scheduler criar task duplicada
- `window_id` inconsistente
- enqueue nao for idempotente

### 15. Rollout / allowlist / kill switch

```powershell
python -m unittest -q tests.test_real_batch_rollout_d23_unittest
```

Validar:

- [ ] allowlist bloqueia conta nao elegivel
- [ ] kill switch impede novas tasks
- [ ] worker respeita rollout policy
- [ ] artifacts do piloto sao produzidos no fluxo de teste

NO-GO se:

- rollout ignorar allowlist
- kill switch nao tiver efeito real

## Parte 5 - Operator layer

### 16. Console / Operator Actions / Strategy Observatory

```powershell
python -m unittest -q ^
  tests.test_operator_console_d24_unittest ^
  tests.test_operator_actions_d24_5_unittest ^
  tests.test_strategy_observatory_d26_unittest
```

Validar:

- [ ] console e read-only onde deve ser
- [ ] actions exigem reason
- [ ] requeue idempotente
- [ ] ack de alerta auditavel
- [ ] observatory liga patch -> window -> scorecard

NO-GO se:

- console expuser mutation indevida
- operator action contornar policy
- observatory quebrar vinculacao de dados

## Parte 6 - Infra, endpoints e probes

### 17. Health / Ready

Validar live:

- [ ] `GET /health` em `:8000` -> `200`
- [ ] `GET /ready` em `:8000` -> `200`
- [ ] `GET /health` em `:8002` -> `200`
- [ ] `GET /ready` em `:8002` -> `200`

Payload minimo esperado em `/ready`:

- [ ] `ready: true`
- [ ] `scheduler: ok`
- [ ] `workers >= 1`
- [ ] `queue: ok`
- [ ] `event_index: ok`
- [ ] `hot_store: ok`

NO-GO se:

- `/ready` nao responder `200`
- payload indicar componente critico indisponivel

## Parte 7 - Seguranca

### 18. Dependencias

```powershell
pip-audit
pip check
```

Criterio:

- [ ] sem vulnerabilidades conhecidas relevantes
- [ ] sem conflitos de dependencia

NO-GO se:

- vulnerabilidade alta/critica conhecida
- conflito de dependencia que possa quebrar runtime

### 19. Secrets / gitleaks

```powershell
gitleaks detect --source . -v
```

Validar:

- [ ] 0 leaks novos
- [ ] fingerprints historicos aceitos documentados
- [ ] nenhum token atual exposto

NO-GO se:

- segredo novo em `HEAD`
- segredo real exposto sem rotacao/aceitacao formal

## Parte 8 - Evidencias e artefatos

### 20. Diretorios que devem existir

Confirmar:

- [ ] `OUT/content/`
- [ ] `OUT/safety/`
- [ ] `OUT/intelligence/`
- [ ] `OUT/experiments/`
- [ ] `OUT/attribution/`
- [ ] `OUT/metrics/`
- [ ] `OUT/ops/`
- [ ] `OUT/rollout/` se houver execucao piloto/operacional simulada

NO-GO se:

- modulo persiste em lugar errado
- artefatos criticos nao forem produzidos

## Parte 9 - Relatorio da auditoria

### 21. Gerar evidencias

Salvar em:

- `OUT/audit/D27_D33/`

Arquivos minimos:

- `AUDIT_REPORT.md`
- `pytest_d27_d33.txt`
- `content_artifacts_check.txt`
- `safety_artifacts_check.txt`
- `intelligence_artifacts_check.txt`
- `metrics_artifacts_check.txt`
- `event_sanity.txt`
- `infra_health.txt`
- `security_scan.txt`
- `py_compile.txt`

## Estrutura do veredito final

Se tudo passar:

- Gate de codigo: `PASS`
- Gate operacional: `PASS`
- Gate de seguranca: `PASS`
- Gate para prosseguir: `GO`

Se qualquer ponto critico falhar:

- Gate de codigo: `PASS/FAIL`
- Gate operacional: `PASS/FAIL`
- Gate de seguranca: `PASS/FAIL`
- Gate para prosseguir: `NO-GO`

## Leitura final correta

Se esse checklist ficar verde, voce podera dizer com confianca:

- o CortAI esta integralmente conforme o planejado
- a base tecnica esta consistente
- a operacao esta segura
- o sistema esta pronto para o piloto real
- o que resta e apenas a condicao externa das contas
