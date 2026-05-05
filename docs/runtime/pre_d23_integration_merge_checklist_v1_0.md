# Pre-D23 Integration Merge Checklist v1.0

## Escopo

Checklist obrigatorio para integracao das branches:
- `D34 Analysis Layer`
- `D28 Safety Layer`
- `D27 Content Pipeline`

Objetivo: garantir compatibilidade com o runtime atual antes da execucao do `D23`.

## Bloqueadores Absolutos

1. `D27` importando qualquer modulo de `runtime`
2. `D27` chamando `safety` diretamente
3. `D27` escrevendo `publish_record` diretamente
4. `D28` reagendando job; `safety` deve apenas decidir
5. `D34` escrevendo fora de `OUT/analysis/*`
6. Ausencia de idempotencia baseada em `publish_key`

## Contratos de Execucao

### 7. Orquestracao

- `runtime` e `scheduler` chamam `pipeline`
- `pipeline` nao agenda tarefas
- `pipeline` nao cria jobs
- `pipeline` nao chama `scheduler` nem `executor`

Imports proibidos dentro de:
- `backend/app/content/pipeline/`
- `backend/app/safety/`
- `backend/app/analysis/`

Imports que nao devem aparecer:
- `from backend.app.runtime.scheduler import ...`
- `from backend.app.runtime.executor import ...`
- `from backend.app.runtime.rollout import ...`

### 8. Autoridade de decisao

- `D28` decide `ALLOW`, `DELAY` ou `BLOCK`
- `pipeline` executa somente se autorizado
- `runtime` chama `safety.evaluate()`

Fluxo permitido:
- `runtime -> safety -> decision -> runtime -> pipeline`

Fluxo proibido:
- `pipeline -> safety`
- `pipeline -> runtime.policy`

### 9. Fonte de verdade

- `runtime` e a autoridade de `scheduling`
- `safety` e a autoridade de `decision`
- `pipeline` e a autoridade de `content generation`
- `publish_record` e a autoridade de `publish state`
- `metrics_collector` e a autoridade de `metrics`
- `analysis layer` e a autoridade de `analysis`

Se algum modulo novo:
- sobrescreve `publish_record`
- altera metricas
- altera estado do `scheduler`

o merge deve ser rejeitado.

## Pipeline (D27)

### 10. Execucao pura

`pipeline` deve ser executavel sob um `ExecutionEnvelope`.

Campos minimos esperados:
- `job_id`
- `account_id`
- `creative_pack_id`
- `publish_slot`
- `experiment_variant`

`pipeline` nao pode:
- ler fila
- escrever estado global
- agendar jobs
- alterar cooldown

`pipeline` pode apenas:
- gerar conteudo
- gerar `publish_manifest`
- emitir eventos `CONTENT/*`
- retornar resultado

### 11. Contrato de retorno

`pipeline.execute(...)` deve retornar um objeto explicito com, no minimo:
- `status`
- `publish_manifest`
- `artifacts`
- `events_emitted`

Nenhum resultado implicito via side effect solto.

### 12. Tratamento de falhas

Falhas em `tts` ou `render` devem:
- emitir `CONTENT/pipeline_failed`
- produzir `status` terminal consistente
- nunca gerar `publish_record` parcial

### 13. Paths e filesystem

`pipeline` pode escrever somente em:
- `OUT/content/audio/`
- `OUT/content/video/`
- `OUT/content/metadata/`

Nenhum path fora de `OUT/`.

## Eventos Canonicos

`pipeline` deve emitir:
- `CONTENT/tts_started`
- `CONTENT/tts_completed`
- `CONTENT/render_started`
- `CONTENT/render_completed`
- `CONTENT/publish_manifest_created`
- `CONTENT/pipeline_failed`

`safety` deve emitir:
- `SAFETY/publish_allowed`
- `SAFETY/publish_delayed`
- `SAFETY/publish_blocked`

`runtime` nao deve emitir eventos de conteudo.

## Contrato de Manifest

`pipeline` deve produzir um `PublishManifest` com:
- `publish_id`
- `account_id`
- `video_path`
- `caption`
- `hashtags`
- `scheduled_time`

Confirmacoes obrigatorias:
- `runtime` consome o manifest
- `pipeline` nao escreve `publish_record` diretamente

## Idempotencia

Chave obrigatoria:

`publish_key = account_id + creative_pack_id + publish_slot`

Se existir `publish_record` com essa chave:
- a execucao deve retornar `NOOP`

Revisar especificamente:
- geracao de artefatos
- criacao de `publish_record`
- ausencia de duplicacao de publish

## Analysis Layer (D34)

Confirmar que `analysis` e read-only.

Nao pode haver:
- escrita em `publish_record`
- escrita em `metrics`
- escrita em `runtime`

`analysis` so pode:
- ler
- agregar
- gerar snapshots

Saidas permitidas:
- `OUT/analysis/*`

## Dependencias Proibidas

Arquitetura permitida:

`runtime -> safety -> pipeline -> content tools`

`pipeline` nao pode importar:
- `runtime`
- `rollout`
- `scheduler`

`analysis` nao pode importar:
- `pipeline`
- `runtime`

## Procedimento de Integracao

Aplicar o checklist separadamente para cada merge:

1. `D34`
2. `D28`
3. `D27`

Nunca validar apenas apos todos os merges.

## Teste Minimo Obrigatorio Apos Merge

### 1. Gate pesado

Executar:

`scripts/run_pre_d23_full_gate.ps1`

### 2. Geracao real de video

Artefatos esperados:
- `OUT/content/video/*.mp4`
- `OUT/content/audio/*.wav`

### 3. Eventos de pipeline

Eventos esperados:
- `CONTENT/tts_started`
- `CONTENT/render_completed`
- `CONTENT/publish_manifest_created`

### 4. Safety funcionando

Eventos esperados:
- `SAFETY/publish_allowed`
- ou `SAFETY/publish_blocked`

## Criterio Final de Aprovacao

O merge e aceito somente se:
- `pipeline` executa sob `ExecutionEnvelope`
- `safety` decide `ALLOW`, `DELAY` ou `BLOCK`
- `runtime` agenda
- idempotencia funciona
- eventos sao emitidos corretamente
- geracao real de video funciona
- `gate` completo fecha em `PASS`
