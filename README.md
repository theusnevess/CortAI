# CortAI

CortAI e um sistema de geracao de conteudo short-form com runtime controlado, pipeline auditavel e baseline operacional validada localmente.

O projeto saiu do estado de prototipo tecnico e hoje possui:

- runtime distribuido
- scheduler e planner
- safety layer
- content pipeline com audio, video e metadata
- publish manifest e publish record canonico
- metrics collector
- analysis layer
- consistency checker
- batch local validado

## Status

- Fase 1: concluida
- Fase 2: especificacao congelada para implementacao

Documentos principais:

- `docs/runtime/phase1_completion_report_v1_0.md`
- `docs/runtime/phase2_definition_report_v1_0.md`
- `docs/runtime/phase2_implementation_map_v1_0.md`
- `docs/runtime/pre_d23_final_release_audit_gate_v1_0.md`

## Objetivo do Projeto

O objetivo do CortAI e operar um loop completo de geracao e avaliacao de conteudo:

```text
scheduler
-> runtime
-> safety
-> content pipeline
-> publish manifest
-> publish_record
-> metrics collector
-> analysis
-> consistency validation
```

Na Fase 1, o foco foi provar que esse loop funciona de forma automatizada, consistente e auditavel.

Na Fase 2, o foco passa a ser a camada cognitiva:

- contexto de tendencia
- estrategia por conta
- geracao de script orientada por retencao
- selecao de voz
- selecao de assets
- video QC
- learning loop

## Arquitetura Atual

Camadas principais:

- `backend/app/runtime/`
  - executor
  - worker
  - scheduler
  - rollout
- `backend/app/content/`
  - pipeline
  - script generation
  - screen text
  - backgrounds
- `backend/app/safety/`
- `backend/app/analysis/`
- `backend/app/creative/`
  - reservado para a implementacao da Fase 2

Persistencia e artefatos:

- `OUT/`
- `assets/`
- `tools/`

Documentacao operacional:

- `docs/runtime/`

Scripts operacionais:

- `backend/scripts/run_pre_d23_final_release_audit_gate.ps1`
- `backend/scripts/run_local_d23_18_batch.py`

## O que foi validado na Fase 1

Infraestrutura:

- PostgreSQL
- Redis
- MinIO
- Docker Compose
- probes de health/readiness

Pipeline operacional:

- `ExecutionEnvelope`
- `PipelineResult`
- `PublishManifest`
- videos reais `1080x1920`
- audio presente
- metadata gerada

Governanca:

- safety com `ALLOW`, `DELAY`, `BLOCK`
- idempotencia por chave
- `publish_record` canonico
- metrics consumindo estado canonico
- analysis e consistency funcionando

Auditoria:

- gate final pre-D23 executado com `GO`
- batch local de 18 videos executado com `PASS`

## Como rodar os checks principais

### Gate final pre-D23

```powershell
./backend/scripts/run_pre_d23_final_release_audit_gate.ps1
```

Saida principal:

- `OUT/audit/pre_d23_final_gate/AUDIT_REPORT.md`

### Batch local validado

```powershell
python backend/scripts/run_local_d23_18_batch.py
```

Validacao posterior:

```powershell
python backend/scripts/run_local_d23_18_batch.py --validate-only --base-dir OUT/batches/<batch_dir>
```

## Testes

Executar a suite critica atual:

```powershell
python -m unittest -q ^
  tests.test_content_pipeline_d27_unittest ^
  tests.test_script_generation_unittest ^
  tests.test_screen_text_adapter_unittest
```

O gate final tambem cobre:

- build
- regressao
- smoke runtime
- consistency
- security checks
- video QC

## Regras Arquiteturais

- contrato antes de extensao
- nao quebrar contratos da Fase 1
- `publish_record` e `metrics` continuam canonicos
- safety nao pode ser contornado
- pipeline nao escreve `publish_record` diretamente
- Fase 2 nao substitui runtime nem pipeline; ela decide, a Fase 1 executa

## Fase 2

A Fase 2 esta especificada e congelada para implementacao.

Documentos-base:

- `docs/runtime/phase2_definition_report_v1_0.md`
- `docs/runtime/phase2_implementation_map_v1_0.md`

Escopo da Fase 2:

- `Creative Orchestrator Service`
- `Trend Analysis Agent`
- `Strategy Agent`
- `Script Agent`
- `Voice Agent`
- `Asset Selection Agent`
- `Video QC Agent`
- `Account Health Agent`
- `Learning and Optimization Agent`
- `Experiment Capability`

## Observacoes

- o modelo local do Piper `.onnx` nao fica versionado no Git por causa do limite de tamanho do GitHub
- artefatos operacionais em `OUT/` podem ser limpos entre batches
- este repositorio prioriza auditabilidade e integridade operacional antes de qualidade criativa premium

## Estado Atual

O projeto esta pronto para:

- preservar a baseline da Fase 1
- iniciar implementacao controlada da Fase 2

O proximo passo arquitetural correto e construir a camada `backend/app/creative/` seguindo os contratos congelados em `docs/runtime/phase2_implementation_map_v1_0.md`.
