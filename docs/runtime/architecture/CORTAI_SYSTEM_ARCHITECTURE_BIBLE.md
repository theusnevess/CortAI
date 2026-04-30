# CORTAI SYSTEM ARCHITECTURE BIBLE

Versao: 1.1
Status: Documento mestre de continuidade arquitetural com atualizacao canonica Phase 2.6
Escopo: consolidacao de arquitetura, fases, contratos, fluxos, gates, artefatos e estado atual do sistema
Ultima consolidacao: `2026-04-26`

---

## 1. Objetivo Deste Documento

Este documento existe para servir como fonte unica de continuidade para:

- novos chats de LLM
- novos engenheiros entrando no projeto
- auditorias tecnicas
- checkpoints de arquitetura
- continuidade de projeto sem perda de contexto

Ele consolida, em um unico artefato:

- o que o CortAI e
- como o sistema esta dividido
- o que ja foi implementado
- o que esta congelado
- como a Fase 1 e a Fase 2 se relacionam
- quais sao os contratos canonicos
- quais sao os gates de qualidade
- qual e o estado tecnico atual
- qual e o proximo gargalo prioritario

Regra de uso:

- se houver conflito entre este documento e a implementacao atual em codigo, a implementacao atual vence para comportamento runtime
- se houver conflito entre este documento e documentos congelados de especificacao, os documentos congelados vencem para escopo arquitetural
- quando houver drift entre documentacao e codigo, esse drift deve ser explicitado, nunca assumido

---

## 2. Resumo Executivo

O CortAI e um sistema de producao automatizada de videos curtos com camada operacional e camada cognitiva separadas.

Arquitetura em alto nivel:

```text
Operational Layer (Phase 1)
  runtime
  scheduler
  safety
  content pipeline
  publish manifest
  publish_record
  metrics
  analysis
  consistency

Cognitive Layer (Phase 2)
  account health
  trend analysis
  learning
  strategy
  experiment
  asset selection
  creative orchestrator
  script agent
  voice agent
  video qc
```

Estado atual real:

- Phase 1: concluida e validada
- Phase 2: concluida e congelada
- Phase 2.5A: concluida e validada
- Phase 2.5B: concluida e validada
- Core runtime: `FROZEN_AND_VALIDATED`
- Change policy: `FROZEN_UNLESS_GOVERNANCE_REOPEN`
- Script Agent: endurecido em Phase 2.6, aprovado em gate proprio e pronto para v3 com monitoramento
- Voice Agent: endurecido em Phase 2.6, aprovado em gate proprio e pronto para v3 com monitoramento
- Asset Selection Agent: endurecido em Phase 2.6, aprovado em gate proprio e pronto para v3 com monitoramento
- Video QC Agent: endurecido em Phase 2.6, aprovado em gate proprio e pronto para v3 com monitoramento
- Voice subsystem: corrigido, governado e aprovado em gate
- Hook visual alignment: promovido como baseline
- Phase 2.6 Wave 1: `Learning Agent`, `Account Health Agent` e `Trend Analysis Agent` endurecidos e aprovados com monitoramento
- Phase 2.6 Wave 1 Master Gate: `GO_WITH_MONITORING`
- Absolute Master Gate pre-Wave 2: `GO_WITH_MONITORING`
- Phase 2.6 Wave 2: `Script Agent`, `Voice Agent`, `Asset Selection Agent` e `Video QC Agent` concluidos e aprovados com `GO_WITH_MONITORING`
- Phase 2.6 Wave 2 Master Gate: `GO_WITH_MONITORING`
- provider local principal atual: `Kokoro`
- fallback duro local: `Piper`
- proximo trabalho autorizado: `PHASE_2_6_FINAL_MASTER_GATE`

Conclusao tecnica atual:

- o sistema deixou de ser apenas um pipeline de render automatizado
- o sistema ja opera como uma camada cognitiva modular sobre uma base operacional robusta
- o `Script Agent` agora e audit-grade para construcao narrativa, com `script_trace` reconstruivel
- o `Voice Agent` agora e audit-grade para planejamento de voz, com `voice_trace` reconstruivel e sem fabricar execucao TTS
- o `Asset Selection Agent` agora e audit-grade para selecao visual metadata-only, com `asset_trace` reconstruivel e fallback honesto
- o `Video QC Agent` agora e audit-grade para avaliacao final de artefato, com `qc_trace` reconstruivel sem alterar `APPROVE/HOLD/REJECT`
- o foco natural seguinte e o `PHASE_2_6_FINAL_MASTER_GATE`, mantendo a Phase 2.6 como hardening governado, nao como expansao livre

---

## 3. O Que e o CortAI

O CortAI e um estÃºdio automatizado para geracao de videos curtos orientados a retencao.

O sistema recebe contexto de conta e tema, produz decisao criativa, gera script, escolhe voz, monta assets, renderiza video, executa verificacao de qualidade e persiste os artefatos operacionais.

Formato narrativo base:

- `hook`
- `setup`
- `payoff`

Tipo de saida:

- video vertical
- audio narrado
- captions/screen text
- metadata
- manifest
- publish records e metricas operacionais

O sistema nao deve ser entendido como um simples renderer. O renderer e uma consequencia da cadeia cognitiva.

---

## 4. Filosofia Arquitetural

### 4.1 Separacao por camadas

O principio mais importante do projeto e:

- Fase 1 executa
- Fase 2 decide

Traduzido para codigo:

- a camada cognitiva nao escreve `publish_record`
- a camada cognitiva nao escreve `metrics`
- a camada cognitiva nao chama `safety` diretamente
- a camada cognitiva nao chama `runtime` diretamente
- a coordenacao da camada cognitiva passa pelo `Creative Orchestrator`
- a coordenacao operacional passa pelo runtime e pipeline da Fase 1

### 4.2 Slices pequenos e congelados

O projeto nao evoluiu por refactor amplo. Ele evoluiu por blocos pequenos, cada um com:

- definicao congelada
- file list congelada
- implementacao controlada
- testes
- smoke
- regressao
- checkpoint formal

### 4.3 Qualidade via gates, nao opiniao

Melhorias importantes devem fechar com evidencia materializada, nao com avaliacao subjetiva.

Isso resultou em:

- gates pesados de sistema
- gates de fase
- gate de excelencia do Script Agent

---

## 5. Estado Atual do Projeto

### 5.1 Phase 1

Status:

- `COMPLETED`

Escopo validado:

- runtime distribuido
- scheduler
- safety layer
- content pipeline
- publish manifest
- publish_record canonico
- metrics collector
- analysis
- simulation
- consistency checker

Documento de encerramento:

- `docs/reference/LEGACY_RUNTIME_ARCHIVE.md`

### 5.2 Phase 2

Status:

- `COMPLETED`

Escopo validado:

- Creative Orchestrator
- Script Agent
- Voice Agent
- Video QC Agent
- Strategy Agent
- Account Health Agent
- Trend Analysis Agent
- Asset Selection Agent
- Learning / Optimization Agent
- Experiment Capability

Documento de encerramento:

- `docs/reference/LEGACY_RUNTIME_ARCHIVE.md`

### 5.3 Phase 2.5

Status atual:

- subfase de excelencia concluida em dois marcos incrementais sem redesenhar o sistema

Trabalho concluido nesta subfase:

- upgrade profundo do `Script Agent`
- gate de excelencia do `Script Agent`
- troca de provider cloud primario de script para `Groq`
- `Phase 2.5A`: correcao arquitetural do subsistema de voz
- `VoicePlan` tornado operativo
- introducao de `Voice Interpreter`
- introducao de `TTS Router` canonico
- `tts_trace` com provider requisitado/executado e fallback explicito
- `Phase 2.5B`: integracao do `Kokoro` como provider local principal
- preservacao do `Piper` como fallback duro
- rerun do `Voice Agent Excellence Gate` com comparacao objetiva `Kokoro vs Piper`

Trabalho prioritario seguinte:

- consolidacao documental e checkpoint do baseline local com `Kokoro`
- expansao de provider somente sob hipotese clara e gate comparativo

---

## 6. Baselines e Checkpoints

Checkpoints formais ja estabelecidos:

- `cortai-phase2-block1`
- `cortai-phase2-block2`
- `cortai-phase2-block3`
- `cortai-phase2-block4`

Objetivo desses checkpoints:

- rollback claro
- auditoria
- reversibilidade
- baseline por bloco

Estado final da Fase 2:

- sistema versionado
- camada cognitiva auditavel
- worktree historicamente tratado com congelamento por bloco

---

## 7. Mapa de Diretorios Relevantes

### 7.1 Camada operacional

Diretorios centrais:

- `backend/app/runtime/`
- `backend/app/content/`
- `backend/app/publish/`
- `backend/app/metrics/`
- `backend/app/analysis/`
- `backend/app/safety/`
- `backend/app/simulation/`
- `backend/app/consistency/`

### 7.2 Camada cognitiva

Diretorio central:

- `backend/app/creative/`

Subdominios implementados:

- `backend/app/creative/orchestrator/`
- `backend/app/creative/agents/script/`
- `backend/app/creative/agents/voice/`
- `backend/app/creative/agents/video_qc/`
- `backend/app/creative/agents/strategy/`
- `backend/app/creative/agents/account_health/`
- `backend/app/creative/agents/trend_analysis/`
- `backend/app/creative/agents/asset_selection/`
- `backend/app/creative/agents/learning/`
- `backend/app/creative/experiments/`
- `backend/app/creative/contracts/`

### 7.3 Dados locais e artefatos

Diretorios importantes:

- `backend/data/trends/`
- `backend/data/learning/`
- `backend/data/experiments/`
- `OUT/`
- `OUT/audit/`

### 7.4 Documentacao arquitetural

Diretorio principal:

- `docs/runtime/`

---

## 8. Fase 1 em Detalhe: Camada Operacional

Phase 1 validou a infraestrutura necessaria para que videos fossem produzidos, validados e persistidos.

### 8.1 Runtime distribuido

Arquivos centrais:

- `backend/app/runtime/executor.py`
- `backend/app/runtime/worker.py`
- `backend/app/runtime/scheduler/service.py`
- `backend/app/runtime/scheduler/planner.py`
- `backend/app/runtime/rollout/pilot_runner.py`

Responsabilidade:

- planejar execucao
- despachar tarefas
- garantir ciclo operacional

### 8.2 Content Pipeline

Arquivos centrais:

- `backend/app/content/pipeline/service.py`
- `backend/app/content/pipeline/orchestrator.py`
- `backend/app/content/pipeline/tts.py`
- `backend/app/content/pipeline/render.py`
- `backend/app/content/pipeline/publish.py`
- `backend/app/content/pipeline/models.py`

Responsabilidade:

- receber envelope canonico
- gerar audio
- renderizar video
- gerar metadata
- gerar `PublishManifest`

Restricao importante:

- o pipeline nao escreve `publish_record` diretamente

### 8.3 Safety Layer

Diretorio:

- `backend/app/safety/`

Decisoes possiveis:

- `ALLOW`
- `DELAY`
- `BLOCK`

Responsabilidade:

- autoridade de decisao antes da publicacao/runtime publish

### 8.4 Metrics, Analysis, Simulation, Consistency

Responsabilidades:

- metricas operacionais
- artefatos de analise
- simulacao offline
- consistencia de artefatos

Artefatos conhecidos:

- `OUT/analysis/consistency_check.json`
- `OUT/analysis/consistency_check.md`

### 8.5 O que a Phase 1 provou

Loop operacional validado:

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

---

## 9. Fase 2 em Detalhe: Camada Cognitiva

Phase 2 adicionou decisao criativa, contexto e controle de qualidade sem invadir a Fase 1.

### 9.1 Objetivo da Fase 2

Permitir que o sistema:

- decida com base em conta
- use tendencia
- use contexto visual
- gere estrategia
- aprenda levemente com dados
- formalize experimentos
- produza roteiro e voz orientados pela camada cognitiva

### 9.2 Regra de ouro

A Fase 2:

- decide
- recomenda
- seleciona
- consolida contexto

A Fase 1:

- executa
- renderiza
- persiste
- publica dentro do runtime
- coleta metricas

### 9.3 Fluxo cognitivo final validado

```text
Account Health Agent
-> Trend Analysis Agent
-> Learning / Optimization Agent
-> Strategy Agent
-> Experiment Capability
-> Asset Selection Agent
-> Creative Orchestrator
-> Script Agent
-> Voice Agent
-> Content Pipeline (Fase 1)
-> Video QC Agent
```

### 9.4 O que a Phase 2 provou

O sistema agora consegue:

- avaliar saude da conta
- gerar estrategia por conta
- usar tendencia por nicho
- usar contexto visual
- gerar roteiro contextual
- selecionar configuracao de voz
- validar qualidade do video antes do publish
- produzir learning insights
- formalizar variacoes experimentais

---

## 10. Blocos Implementados na Fase 2

### 10.1 Bloco 1 - Creative Core

Entregas:

- `Creative Orchestrator Service`
- `Script Agent`
- `Voice Agent`
- `Video QC Agent`

Resultado provado:

- montagem de `creative_pack`
- script
- voz
- pipeline
- `Video QC`

### 10.2 Bloco 2 - Account Decision Layer

Entregas:

- `Strategy Agent`
- `Account Health Agent`

Resultado provado:

- `SAFE`
- `CAUTION`
- `HOLD`
- interrupcao controlada antes do pipeline quando necessario

### 10.3 Bloco 3 - Trend and Visual Context

Entregas:

- `Trend Analysis Agent`
- `Asset Selection Agent`

Resultado provado:

- `trend_profile`
- `asset_selection`
- contexto visual e de tendencia no `creative_pack`

### 10.4 Bloco 4 - Learning and Experiment Control

Entregas:

- `Learning / Optimization Agent`
- `Experiment Capability`

Resultado provado:

- `learning_insights`
- `experiment_plan`
- contexto adaptativo leve e auditavel

---

## 11. Fase 2.5 em Detalhe: Upgrade do Script Agent

### 11.1 Problema original

O `Script Agent` original era o maior gargalo criativo porque:

- consumia pouco contexto real
- usava prompt generico
- dependia de modelo local limitado
- tinha fallback fraco
- sofria dano semantico no adapter

### 11.2 Estado apos upgrade

O agente passou a:

- consumir `strategy_profile`
- consumir `trend_profile`
- consumir `learning_insights`
- consumir `experiment_plan`
- usar provider cloud primario
- manter fallback local
- manter fallback deterministico de emergencia
- gerar saida estruturada
- reduzir dano semantico do adapter

### 11.3 Provider chain atual de script

Estado implementado em codigo:

- `Groq` como provider cloud primario
- `Ollama` como fallback local
- `fallback_contextual` como ultimo nivel

Arquivo central:

- `backend/app/content/script_gen/service.py`

### 11.4 Gate de excelencia do Script Agent

Documentacao:

- `docs/reference/LEGACY_RUNTIME_ARCHIVE.md`

Runner:

- `backend/scripts/run_script_agent_excellence_gate.ps1`

Evidencia:

- `OUT/audit/script_agent_excellence_gate/`

### 11.5 Resultado tecnico mais recente conhecido

Rerun forte validado:

- `GO`
- `Failures: 0`
- `Warnings: 0`

Bateria de 20 scripts:

- `provider_counts`:
  - `groq: 19`
  - `ollama: 1`
- `groq_to_ollama_count: 1`
- `avg_latency_s: 1.299`
- `distinct_hooks: 19`
- `distinct_modes: 7`
- `cliche_hits: 0`
- `weak_payoff_hits: 0`

Lote de 5 videos:

- `5/5 READY`
- `5/5 APPROVE`
- `5/5 groq_structured`

Arquivos de evidencia:

- `OUT/audit/script_agent_excellence_gate/AUDIT_REPORT.md`
- `OUT/audit/script_agent_excellence_gate/script_battery_20.json`
- `OUT/audit/script_agent_excellence_gate/video_batch_5.json`

### 11.6 Conclusao da Fase 2.5 ate agora

O `Script Agent` deixou de ser o gargalo principal.

Novo gargalo prioritario:

- `Voice Agent`

---

## 12. Contratos Canonicos

### 12.1 Creative Pack

Arquivo:

- `backend/app/creative/contracts/creative_pack.py`

Modelos canonicos relevantes:

- `StrategyProfile`
- `TrendProfile`
- `ScriptPlan`
- `VoicePlan`
- `AssetPlan`
- `LearningInsights`
- `ExperimentPlan`
- `ExperimentAssignment`
- `CreativePack`

Estado real implementado do `CreativePack`:

- `creative_pack_id`
- `account_id`
- `niche`
- `topic`
- `strategy_profile`
- `trend_profile`
- `script_plan`
- `voice_plan`
- `asset_plan`
- `learning_insights`
- `experiment_plan`
- `experiment_assignment`
- `generated_at`
- `orchestrator_version`
- `account_health_status`
- `recommended_constraints`

Observacao importante:

- `CreativePack.to_dict()` expoe tambem `asset_selection` como alias de `asset_plan` para compatibilidade

### 12.2 Orchestrator IO

Arquivo:

- `backend/app/creative/contracts/orchestrator_io.py`

Entrada canonica:

- `CreativeOrchestratorInput`

Campos:

- `account_id`
- `niche`
- `topic`
- `publish_slot`
- `creative_pack_id`
- `experiment_assignment_id`
- `account_context_ref`
- `trend_context_ref`

Saida canonica:

- `CreativeOrchestratorResult`

Campos:

- `creative_pack`
- `fallbacks_used`
- `events_emitted`
- `qc_required`

### 12.3 Contratos comuns de agente

Arquivo:

- `backend/app/creative/contracts/agent_common.py`

Conceitos importantes:

- `FallbackDecision`
- `FallbackMode`
- status de decisao
- falha padronizada

### 12.4 Narration contract

`ScriptPlan.narration_text()` e o ponto canonico que transforma:

- `hook`
- `setup`
- `payoff`

em texto entregue ao pipeline/TTS.

Regra atual:

- cada bloco recebe pontuacao terminal se necessario
- os blocos sao unidos por linhas em branco

---

## 13. Creative Orchestrator

Arquivo central:

- `backend/app/creative/orchestrator/service.py`

O `CreativeOrchestratorService` e o unico coordenador da camada cognitiva.

### 13.1 Responsabilidades

- resolver contexto por conta
- disparar agentes em ordem correta
- consolidar `creative_pack`
- emitir eventos cognitivos
- chamar o pipeline da Fase 1
- chamar `Video QC`

### 13.2 Fluxo interno atual

Passos:

1. `Account Health Agent`
2. `Trend Analysis Agent`
3. `Learning Agent`
4. `Strategy Agent`
5. `Experiment Capability`
6. `Asset Selection Agent`
7. `Script Agent`
8. `Voice Agent`
9. montagem de `CreativePack`
10. `ContentPipelineService.run_pipeline(...)`
11. `VideoQcAgentService.evaluate(...)`

### 13.3 Regra critica de `HOLD`

Se `Account Health` retornar `HOLD`:

- o fluxo para antes do pipeline
- nao renderiza
- nao chama `Video QC`

### 13.4 Integracao com pipeline

O pipeline recebe:

- `creative_pack_id`
- `account_id`
- `script_text` via `creative_pack.script_plan.narration_text()`
- `voice_profile`
- `publish_slot`
- `experiment_variant`

Isso preserva a regra:

- a camada cognitiva entrega decisao consolidada
- a camada operacional executa

---

## 14. Agentes Implementados

### 14.1 Account Health Agent

Diretorio:

- `backend/app/creative/agents/account_health/`

Funcao:

- avaliar risco da conta
- emitir `SAFE`, `CAUTION`, `HOLD`
- devolver `reasons` e `recommended_constraints`
- atuar como governador upstream de postura de conta/runtime
- expor telemetria enriquecida, componentes de risco, confidence da decisao, saude temporal, politica de input degradado, rationale de constraints e `health_trace`

Estado Phase 2.6:

- aprovado em gate proprio com `GO_WITH_MONITORING`
- validado pelo Gate Mestre Parcial Phase 2.6 Learning + Account Health
- `HOLD` continua autoridade de bloqueio upstream
- Strategy continua sendo a control layer
- residuos monitoraveis:
  - `ACCOUNT_HEALTH_RUNTIME_HISTORY_STILL_SHORT`
  - `ACCOUNT_HEALTH_TELEMETRY_PRODUCER_COVERAGE_STILL_EXPANDING`

Fallback:

- seguro
- explicito
- input ausente/degradado nao deve virar `SAFE` plenamente confiavel
- ausencia de dado isolada nao deve virar `HOLD` automatico

### 14.2 Trend Analysis Agent

Diretorio:

- `backend/app/creative/agents/trend_analysis/`

Funcao:

- carregar perfis de tendencia por nicho
- fonte local manual-curated

Storage:

- `backend/data/trends/*.json`

Fallback:

- `trend_profile = DEFAULT`

### 14.3 Learning Agent

Diretorio:

- `backend/app/creative/agents/learning/`

Funcao:

- ler sinais existentes do sistema
- produzir `learning_insights`
- interpretar evidencia real de QC/history
- calibrar confidence
- aplicar weighting temporal
- proteger contra contaminacao/ruido
- emitir pressao estrategica bounded e auditavel via `learning_policy.strategy_pressure`

Fontes tipicas:

- `publish_records`
- `video_metrics`
- `analysis`
- `execution_history`
- `video_qc`

Estado Phase 2.6:

- aprovado em gate proprio com `GO_WITH_MONITORING`
- validado pelo Gate Mestre Parcial Phase 2.6 Learning + Account Health
- nao decide Strategy
- nao decide publishability
- nao substitui QC
- residuos monitoraveis:
  - `LONGITUDINAL_PRODUCTION_HISTORY_STILL_SHORT`

Fallback:

- `learning_insights = DEFAULT`
- explicito em trace
- nao deve gerar confidence alta
- nao deve gerar strong policy pressure

### 14.4 Strategy Agent

Diretorio:

- `backend/app/creative/agents/strategy/`

Funcao:

- gerar `strategy_profile`

Usa:

- `health_status`
- sumario recente de metricas
- restricoes recomendadas

### 14.5 Experiment Capability

Diretorio:

- `backend/app/creative/experiments/`

Funcao:

- formalizar `experiment_plan`
- controlar variante canonica

Fallback:

- baseline segura

### 14.6 Asset Selection Agent

Diretorio:

- `backend/app/creative/agents/asset_selection/`

Funcao:

- selecionar assets por papel narrativo
- materializar `asset_plan`
- alinhar o `hook_asset` com o tipo de hook quando houver `visual_anchor` valido

### 14.7 Script Agent

Diretorio:

- `backend/app/creative/agents/script/`

Dependencias centrais:

- `backend/app/content/script_gen/service.py`
- `backend/app/content/screen_text/service.py`

Estado atual:

- contextualizado
- saida estruturada
- provider cloud primario
- fallback local
- fallback deterministico

### 14.8 Voice Agent

Diretorio:

- `backend/app/creative/agents/voice/`

Arquivos centrais:

- `backend/app/creative/agents/voice/service.py`
- `backend/app/creative/agents/voice/interpreter.py`

Estado atual implementado:

- resolve provider e voz sem sintetizar audio
- interpreta `hook -> setup -> payoff` de forma deterministica
- produz `VoicePlan` operativo
- delega roteamento concreto ao `TTS Router`
- preserva compatibilidade com provider premium por configuracao

Capacidades agora presentes:

- `Voice Interpreter` rule-based
- metadata de entrega por segmento
- pausas e contraste narrativo minimos
- `tts_trace` com provider requisitado e provider executado
- provider local principal: `Kokoro`
- fallback duro: `Piper`

### 14.9 Video QC Agent

Diretorio:

- `backend/app/creative/agents/video_qc/`

Funcao:

- validar video final antes de seguir
- `APPROVE` ou `REJECT`

Posicao arquitetural:

- depois do pipeline
- antes de qualquer passo de publicacao/safety subsequente

---

## 15. Script Agent: Detalhes Relevantes Para Continuidade

Arquivos centrais:

- `backend/app/creative/agents/script/service.py`
- `backend/app/creative/agents/script/models.py`
- `backend/app/content/script_gen/models.py`
- `backend/app/content/script_gen/service.py`
- `backend/app/content/screen_text/service.py`

### 15.1 Provider chain atual

Implementado hoje:

- `Groq`
- `Ollama`
- `fallback_contextual`

### 15.2 Observabilidade de provider

No estado atual, `ScriptGenerationResponse` materializa:

- `provider_used`
- `model_used`
- `prompt_used`
- `raw_output`
- `fallback`
- `provider_attempt_trace`

### 15.3 Instrumentacao de queda `groq -> ollama`

O gate agora grava, por item da bateria:

- `provider_attempt_trace`
- `groq_to_ollama_reason`

Isso permite ver exatamente quando o `Groq` caiu por:

- `429 Too Many Requests`
- erro de validacao
- outro erro operacional

### 15.4 Drift documental importante

O arquivo:

- `docs/reference/LEGACY_RUNTIME_ARCHIVE.md`

ainda menciona:

- `Gemini -> Ollama -> fallback deterministico`

Mas o comportamento implementado hoje e:

- `Groq -> Ollama -> fallback_contextual`

Para continuidade entre chats, o codigo e os artefatos de evidencia devem ser considerados a verdade operacional atual.

---

## 16. Voice Subsystem: Estado Atual

Arquivos centrais:

- `backend/app/creative/agents/voice/service.py`
- `backend/app/creative/agents/voice/interpreter.py`
- `backend/app/content/pipeline/tts_router.py`
- `backend/app/content/pipeline/kokoro_adapter.py`

Comportamento atual:

- `Voice Agent` produz `VoicePlan` operativo
- `Voice Interpreter` interpreta `hook/setup/payoff`
- `TTS Router` e a autoridade unica de roteamento
- `Kokoro` e o provider local principal
- `Piper` permanece como fallback duro
- `tts_trace` materializa provider requisitado, provider executado e fallback

Estado perceptivo atual:

- gargalo estrutural de voz resolvido
- contraste narrativo preservado
- monotonia reduzida em relacao ao baseline `Piper`
- latencia melhor que o baseline local anterior

Leitura tecnica:

- a voz do CortAI ja nao e simbolicamente decidida
- ela agora e arquiteturalmente governada e auditavel
- o proximo risco deixou de ser arquitetura e passou a ser disciplina de baseline e expansao de providers

---

## 17. Content Pipeline Atual

Diretorio:

- `backend/app/content/pipeline/`

### 17.1 Entradas principais vindas da camada cognitiva

- `script_text`
- `voice_profile`
- `creative_pack_id`
- `account_id`
- `publish_slot`
- `experiment_variant`

### 17.2 Responsabilidades

- TTS
- render
- metadata
- manifest

### 17.3 TTS atual

Arquivos centrais:

- `backend/app/content/pipeline/tts.py`
- `backend/app/content/pipeline/tts_router.py`
- `backend/app/content/pipeline/kokoro_adapter.py`

Baseline validada atual:

- `Kokoro` como provider local principal
- `Piper` como fallback duro

Observabilidade operacional:

- `tts_trace` em `PipelineResult`
- `provider_requested`
- `provider_executed`
- `voice_id_requested`
- `voice_id_executed`
- `fallback_used`
- `fallback_reason`
- `latency_s`
- `audio_duration_s`

### 17.4 Render atual

Arquivo:

- `backend/app/content/pipeline/render.py`

Saida:

- video vertical
- metadata
- audio

---

## 18. Persistencia e Fontes de Dados

### 18.1 Tendencias

Storage:

- `backend/data/trends/`

Formato:

- JSON manual-curated por nicho

### 18.2 Learning

Storage de apoio:

- `backend/data/learning/`

Fontes reais de leitura:

- `publish_records`
- `video_metrics`
- `analysis`

### 18.3 Experimentos

Storage:

- `backend/data/experiments/`

### 18.4 Artefatos de auditoria

Diretorio principal:

- `OUT/audit/`

Exemplos:

- `OUT/audit/script_agent_excellence_gate/`
- `OUT/audit/pre_phase3_final_gate/`

### 18.5 Artefatos operacionais

Diretorio principal:

- `OUT/`

Tipos de artefato:

- videos
- audios
- metadata
- relatorios de gate
- evidencias de auditoria

---

## 19. Eventos e Observabilidade

### 19.1 Eventos cognitivos

Emitidos pelo `Creative Orchestrator` em:

- `backend/app/creative/orchestrator/events.py`

Eventos relevantes observados/esperados:

- `CREATIVE/orchestrator_started`
- `CREATIVE/orchestrator_completed`
- `CREATIVE/trend_profile_loaded`
- `CREATIVE/trend_profile_fallback`
- `CREATIVE/strategy_profile_generated`
- `CREATIVE/script_generated`
- `CREATIVE/voice_selected`
- `CREATIVE/asset_selection_generated`
- `CREATIVE/asset_selection_fallback`
- `CREATIVE/learning_insights_generated`
- `CREATIVE/learning_insights_fallback`
- `CREATIVE/experiment_plan_generated`
- `CREATIVE/experiment_plan_fallback`
- `CREATIVE/video_qc_approved`
- `CREATIVE/video_qc_rejected`
- `CREATIVE/account_health_safe`
- `CREATIVE/account_health_caution`
- `CREATIVE/account_health_hold`

### 19.2 Observabilidade operacional

Coberturas existentes:

- logs de gate
- JSONs de auditoria
- metrics da Fase 1
- analysis outputs
- consistency outputs

---

## 20. Gates de Qualidade Existentes

### 20.1 Pre-D23 final release audit gate

Script:

- `backend/scripts/run_pre_d23_final_release_audit_gate.ps1`

Documento:

- `docs/reference/LEGACY_RUNTIME_ARCHIVE.md`

Objetivo:

- build
- testes
- regressao
- contratos
- infra
- seguranca
- smoke
- video QC
- consistency

### 20.2 Pre-Phase3 system final gate

Script:

- `backend/scripts/run_pre_phase3_system_final_gate.ps1`

Documento:

- `docs/reference/LEGACY_RUNTIME_ARCHIVE.md`

Objetivo:

- validar o sistema inteiro antes da proxima fase

### 20.3 Script Agent Excellence Gate

Script:

- `backend/scripts/run_script_agent_excellence_gate.ps1`

Documento:

- `docs/reference/LEGACY_RUNTIME_ARCHIVE.md`

Evidencia:

- `OUT/audit/script_agent_excellence_gate/`

### 20.4 Phase 2.5A Voice Architecture Audit

Evidencia:

- `OUT/audit/phase2_5_voice_agent/AUDIT_REPORT.md`
- `OUT/audit/phase2_5_voice_agent/smoke_results.json`
- `OUT/audit/phase2_5_voice_agent/voice_router_trace.json`

### 20.5 Voice Agent Excellence Gate

Script:

- `backend/scripts/run_voice_agent_excellence_gate.ps1`

Documento:

- `docs/reference/LEGACY_RUNTIME_ARCHIVE.md`

Evidencia:

- `OUT/audit/voice_agent_excellence_gate/`

### 20.6 Phase 2.5B Kokoro Audit

Evidencia:

- `OUT/audit/phase2_5b_kokoro/AUDIT_REPORT.md`
- `OUT/audit/phase2_5b_kokoro/smoke_results.json`
- `OUT/audit/phase2_5b_kokoro/gate_comparison.json`

---

## 21. Qualidade Atual do Sistema

### 21.1 O que ja esta forte

- runtime operacional
- pipeline de video
- safety
- metrics e analysis
- consistencia
- camada cognitiva modular
- `Script Agent` significativamente melhorado
- subsistema de voz corrigido arquiteturalmente
- `Kokoro` validado como baseline local principal
- fallback chains funcionais
- gates com evidencia materializada

### 21.2 O que ainda e gargalo

Principal risco atual:

- expansao prematura de providers sem hipotese forte

Gargalos secundarios possiveis:

- estabilidade de provider cloud do `Script Agent`
- refinamento fino de estilo e puntuacao de copy
- disciplina de produto para nao degradar o baseline de voz

---

## 22. Known Bottlenecks

### 22.1 Provider expansion discipline

O principal risco atual deixou de ser arquitetura e passou a ser governanca de baseline.

Riscos concretos:

- abrir muitos providers cedo demais
- degradar `TTS Router` por conveniencia
- perder comparabilidade contra o baseline `Kokoro`

### 22.2 Script provider variance

No `Script Agent`, o provider primario cloud pode sofrer:

- `429 Too Many Requests`

O sistema e resiliente, mas a estabilidade do primario nao e garantida em toda bateria.

### 22.3 Emotion / delivery ceiling

Mesmo com `Kokoro`, a entrega de voz ainda pode evoluir em:

- expressividade fina
- variacao emocional
- acabamento de prosodia em nichos mais dramaticos

### 22.4 Finishing quality

Ainda existem casos isolados de:

- phrasing seco
- pontuacao/quotes incompletos
- setups menos fortes do que hooks/payoffs

---

## 23. Upcoming Gates

### 23.1 Voice Agent Excellence Gate

Status atual:

- implementado
- aprovado com `Piper`
- rerodado e aprovado com `Kokoro`

### 23.2 Experiment System Validation

Objetivo:

- validar que variacoes experimentais continuam canonicamente auditaveis

### 23.3 Narrative Diversity Monitoring

Objetivo:

- monitorar regressao de diversidade narrativa ao longo do tempo

### 23.4 Phase 2.5C Provider Expansion Gate

So deve existir se houver hipotese clara para novo provider local ou premium experimental

---

## 24. Riscos Arquiteturais a Evitar

Um novo chat nao deve sugerir, sem necessidade forte:

- reescrever a Fase 1
- transformar o sistema em framework multiagente generico
- introduzir `RAG` pesado
- introduzir scraping automatizado agressivo
- quebrar o `creative_pack`
- desintermediar o `Creative Orchestrator`
- fazer agentes escreverem `publish_record`
- fazer agentes escreverem `metrics`
- chamar `safety` diretamente desde a camada cognitiva
- espalhar responsabilidades entre agentes

---

## 25. Drift e Notas Importantes Para Continuidade

### 25.1 Drift de provider do Script Agent

Documentos antigos podem citar:

- `Gemini`

Estado real implementado atualmente:

- `Groq`

### 25.2 Mapas de implementacao vs codigo real

O `phase2_implementation_map_v1_0.md` usa uma estrutura idealizada mais ampla, incluindo:

- `backend/app/creative/context/`
- `capabilities/experiment/`

O estado implementado real hoje usa:

- `backend/app/creative/experiments/`

e parte da persistencia segue simples/local, como definido pelos blocos congelados.

### 25.3 Veredito sobre esse drift

Para continuidade por LLM:

- use os documentos congelados para entender a intencao arquitetural
- use o codigo atual para entender o comportamento real em runtime

### 15.5 Hook Visual Alignment (Baseline Behavior)

O baseline do CortAI agora inclui alinhamento do primeiro frame visual com o tipo de hook gerado.

Fluxo padrao:

```text
hook_text
-> hook_type detection (experiential | inferential)
-> visual_anchor selection
-> first_frame asset selection
```

Regra central:

- o primeiro frame deve materializar a anomalia do hook, nao apenas o ambiente

Separacao de dialetos:

- `experiential`
  - tipo: evento fisico ou diretamente imaginavel
  - regra: mostrar `entidade + estado anomalo`
  - exemplos:
    - camera com glitch
    - porta ou acesso selado
    - painel ou display com aviso
- `inferential`
  - tipo: inconsistencia documental ou logica
  - regra: mostrar `evidencia da contradicao`
  - exemplos:
    - log com data impossivel
    - transcript inconsistente
    - arquivo alterado

Prioridade de selecao:

```text
1. visual_anchor (se detectado)
2. fallback tematico (apenas se necessario)
```

Regra operacional:

- e proibido usar opening generico quando ha anchor valido

Escopo:

- atua apenas na selecao do `hook_asset`
- nao altera:
  - `Script Agent`
  - `hook_text`
  - `setup/payoff`
  - `TTS / voice`
  - providers

Residual conhecido:

- `map / blueprint literalness`
  - limitado pela asset library atual
  - nao bloqueia o baseline
  - permanece sob monitoramento

Seguranca operacional:

- `CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT`
  - baseline ativo por padrao
  - `0` desliga para rollback rapido

---

### 25.6 Candidate Universe Expansion (Baseline Behavior)

O CortAI passa a expandir o universo candidato antes da composicao e do sequencing, com o objetivo de reduzir skew estrutural no feed.

Fluxo logico:

```text
candidate universe
-> conservative inferential supply expansion
-> document/evidence visual subtyping
-> feed candidate composition
-> feed sequencing
```

#### 1. Inferential supply expansion

O sistema amplia conservadoramente a presenca de hooks inferenciais apenas quando o conteudo ja contem sinais semanticamente compativeis, como:

- `record`
- `log`
- `tape`
- `transcript`
- `archive`
- `date`
- `discrepancy`

Principio:

- expandir apenas quando a natureza do conteudo ja for inferencial

Regras:

- preferir falso negativo a falso positivo
- nunca converter caso claramente experiencial
- nunca abrir novo dialeto
- nunca alterar `setup/payoff`

#### 2. Document visual subtyping

O anchor visual `document` deixa de operar como monocategoria e passa a usar subtipos controlados dentro da mesma familia semantica, como:

- `document_printed`
- `document_redacted`
- `document_annotated`
- `terminal_log`
- `transcript_sheet`
- `evidence_board`
- `timestamp_closeup`

Principio:

- expandir dentro da semantica, nao fora dela

Objetivo:

- reduzir monocultura visual documental
- aumentar variedade valida no pool
- melhorar o feed downstream sem quebrar coerencia investigativa

#### 3. Safety / rollback

A expansao permanece protegida por flag operacional:

- `CORTAI_EXPERIMENT_CANDIDATE_UNIVERSE_EXPANSION`

Comportamento:

- `ON` -> baseline atual expandido
- `OFF` -> retorno imediato ao comportamento anterior

#### 4. Known monitoring points

Manter monitoramento leve para:

- `inferential overreach`
- `document subtype saturation`
- drift por nicho em:
  - `mystery_dark`
  - `investigative`

---

### 25.7 Editorial Mix Adjustment (Baseline Behavior)

#### Contexto

O `investigation_stream` apresenta skew estrutural para `inferential`, o que pode gerar fadiga dialetal mesmo com a pipeline tecnica estavel.

O ajuste correto ocorre antes da pipeline, na composicao do lote editorial.

#### Principio

- qualidade do feed investigativo depende da mistura de tipos de investigacao, nao apenas da qualidade individual dos itens

#### Classificacao editorial

Cada tema investigativo deve ser classificado como:

- `inferential`
- `experiential_eligible`

#### Criterios de `experiential_eligible`

Um tema so se qualifica se:

- possui entidade fisica clara
- possui anomalia observavel ou imaginavel diretamente
- nao depende exclusivamente de evidencia documental

#### Regras de composicao do lote

Para lote de `8-12`:

- alvo:
  - `>= 3` temas `experiential_eligible` quando houver universo real
- evitar:
  - `5/5 inferential` em qualquer janela simulada
- aplicar:
  - dispersao leve dos temas experienciais ao longo do lote

#### Fallback editorial

Se o universo tematico for predominantemente documental:

- aceitar skew
- registrar:

```json
{
  "editorial_mix_relaxed": true,
  "reason": "insufficient_experiential_topics_available"
}
```

Nunca:

- forcar tema artificial
- degradar plausibilidade narrativa

#### Integracao com pipeline

Este ajuste ocorre antes de:

- `Script Agent`
- visual alignment
- candidate universe
- sequencing

Nenhuma camada tecnica e modificada por esta regra editorial.

#### Impacto esperado

- reducao de:
  - `max_consecutive_same_hook_type`
  - `dialect_fatigue_rate`
- manutencao de:
  - coerencia investigativa
  - naturalidade do feed

---

## 26. Como Um Novo Chat Deve Ler o Projeto

Ordem recomendada de leitura para continuidade:

1. `docs/runtime/architecture/CORTAI_SYSTEM_ARCHITECTURE_BIBLE.md`
2. `docs/runtime/architecture/CORTAI_RUNTIME_MASTER_STATE_V2_5.md`
3. `docs/runtime/phase-2-6/master/PHASE_2_6_EXCELLENCE_HARDENING_MASTER_PLAN.md`
4. `docs/runtime/phase-2-6/master-gates/PHASE_2_6_PARTIAL_MASTER_GATE_LEARNING_ACCOUNT_HEALTH.md`
5. `OUT/audit/phase_2_6_partial_master_gate_learning_account_health/final_verdict.json`
6. `docs/runtime/baselines/learning/LEARNING_AGENT_SYSTEM_BIBLE_PHASE1.md`
7. `docs/runtime/phase-2-6/agents/learning/LEARNING_AGENT_V2_6_EXCELLENCE_PLAN.md`
8. `docs/runtime/phase-2-6/agents/learning/LEARNING_AGENT_V2_6_EXCELLENCE_GATE.md`
9. `OUT/audit/learning_agent_v2_6_excellence_gate/final_verdict.json`
10. `docs/runtime/baselines/account-health/ACCOUNT_HEALTH_AGENT_SYSTEM_BIBLE_PHASE1.md`
11. `docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_PLAN.md`
12. `docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_GATE.md`
13. `OUT/audit/account_health_agent_v2_6_excellence_gate/final_verdict.json`
14. `docs/reference/LEGACY_RUNTIME_ARCHIVE.md`
15. `docs/reference/LEGACY_RUNTIME_ARCHIVE.md`
16. `docs/reference/LEGACY_RUNTIME_ARCHIVE.md`
17. `docs/reference/LEGACY_RUNTIME_ARCHIVE.md`
18. `docs/reference/LEGACY_RUNTIME_ARCHIVE.md`
19. `docs/reference/LEGACY_RUNTIME_ARCHIVE.md`
20. `docs/reference/LEGACY_RUNTIME_ARCHIVE.md`
21. `docs/reference/LEGACY_RUNTIME_ARCHIVE.md`
22. `docs/reference/LEGACY_RUNTIME_ARCHIVE.md`
23. `OUT/audit/script_agent_excellence_gate/AUDIT_REPORT.md`
24. `OUT/audit/phase2_5_voice_agent/AUDIT_REPORT.md`
25. `OUT/audit/phase2_5b_kokoro/AUDIT_REPORT.md`
26. `OUT/audit/voice_agent_excellence_gate/AUDIT_REPORT.md`

Se o chat for trabalhar em voz ou providers:

27. ler `backend/app/creative/agents/voice/service.py`
28. ler `backend/app/creative/agents/voice/interpreter.py`
29. ler `backend/app/content/pipeline/tts_router.py`
30. ler `backend/app/content/pipeline/kokoro_adapter.py`
31. ler como o `Creative Orchestrator` consome a voz e como o pipeline materializa `tts_trace`

Se o chat for trabalhar em Phase 2.6:

32. ler primeiro o Absolute Master Gate pre-Wave 2
33. confirmar que Learning, Account Health e Trend permanecem `GO_WITH_MONITORING`
34. confirmar que Script Agent v2.6 permanece `GO_WITH_MONITORING`
35. nao iniciar Voice sem plano formal proprio

---

## 27. Bootstrap Prompt Recomendado Para Novo Chat

Exemplo de bootstrap enxuto:

```text
Voce esta entrando no projeto CortAI.

Fonte principal de contexto:
- docs/runtime/architecture/CORTAI_SYSTEM_ARCHITECTURE_BIBLE.md

Estado atual:
- Phase 1: concluida
- Phase 2: concluida
- Phase 2.5A: Voice Architecture Repair concluida e validada
- Phase 2.5B: Kokoro Integration concluida e validada
- Core runtime: FROZEN_AND_VALIDATED
- Change policy: FROZEN_UNLESS_GOVERNANCE_REOPEN
- Learning Agent v2.6: GO_WITH_MONITORING
- Account Health Agent v2.6: GO_WITH_MONITORING
- Trend Analysis Agent v2.6: GO_WITH_MONITORING
- Wave 1 Master Gate: GO_WITH_MONITORING
- Absolute Master Gate pre-Wave 2: GO_WITH_MONITORING
- Script Agent v2.6: GO_WITH_MONITORING
- Voice subsystem agora e governado por `VoicePlan`, `Voice Interpreter` e `TTS Router`
- baseline local principal atual: `Kokoro`
- fallback duro atual: `Piper`

Restri??es:
- nao quebrar Fase 1
- nao quebrar contratos canonicos
- nao redesenhar o sistema
- preservar Creative Orchestrator como coordenador unico
- manter fallback chains
- nao modificar core pipeline sem governance reopen
- nao alterar Strategy para satisfazer gates
- nao transformar Learning em Strategy
- nao transformar Account Health em Strategy, QC ou Learning
- nao transformar Trend em Strategy, Asset, QC ou Publisher
- nao transformar Script em Strategy, Voice, Asset ou QC

Objetivo atual:
- criar o plano formal do Voice Agent v2.6 antes de qualquer implementacao
```

---

## 28. Veredito Arquitetural Atual

Leitura honesta do estado do projeto:

- o CortAI nao e mais um prototipo solto
- o projeto ja possui baseline operacional validada
- a camada cognitiva esta implementada e congelada no escopo da Fase 2
- o `Script Agent` ja passou por gate de excelencia com evidencia
- o subsistema de voz ja passou por correcao estrutural e por gate de excelencia
- o core runtime esta `FROZEN_AND_VALIDATED`
- Learning Agent v2.6 foi endurecido e aprovado com monitoramento
- Account Health Agent v2.6 foi endurecido e aprovado com monitoramento
- Trend Analysis Agent v2.6 foi endurecido e aprovado com monitoramento
- o Wave 1 Master Gate retornou `GO_WITH_MONITORING`
- o Absolute Master Gate pre-Wave 2 retornou `GO_WITH_MONITORING`
- Script Agent v2.6 foi endurecido e aprovado com monitoramento
- Voice Agent v2.6 foi endurecido e aprovado com monitoramento
- Asset Selection Agent v2.6 foi endurecido e aprovado com monitoramento
- Video QC Agent v2.6 foi endurecido e aprovado com monitoramento
- o Wave 2 Master Gate retornou `GO_WITH_MONITORING`
- o sistema esta autorizado a prosseguir para o `PHASE_2_6_FINAL_MASTER_GATE`, nao para novo feature work direto

Em termos de engenharia:

- infraestrutura: madura
- pipeline: funcional
- multiagente: funcional
- gates: maduros
- baseline local de voz: governado
- Learning: audit-grade evidence interpretation com pressao estrategica bounded
- Account Health: posture governor com telemetria, risk components, confidence, temporal health, degraded input policy, constraints rationale e `health_trace`
- Trend: context provider com source governance, provenance, freshness, confidence calibration, shift analysis, downstream utility e `trend_trace`
- Script: narrative construction agent com context governance, quality rubric, hook/setup/payoff analysis, anti-cliche analysis, provider/fallback honesty, confidence calibration e `script_trace`
- Voice: voice planning agent com contract governance, delivery semantics, timing/pause analysis, monotony/contrast analysis, provider/fallback honesty, audio validation linkage, confidence calibration e `voice_trace`
- Asset Selection: visual selection agent metadata-only com context governance, catalog/source governance, visual intent, semantic alignment, truthfulness/mismatch risk, fallback honesty, diversity guard, confidence calibration e `asset_trace`
- Video QC: final artifact evaluator com input governance, evidence scoring, confidence, decision semantics/severity e `qc_trace`
- contexto para continuidade por LLM: centralizado

---

## 29. Conclusao Final

O CortAI hoje deve ser entendido como um sistema em duas grandes camadas:

1. uma camada operacional robusta validada na Fase 1
2. uma camada cognitiva modular validada na Fase 2

Sobre essas duas camadas, a Fase 2.5 introduziu melhorias de excelencia em gargalos perceptiveis, com o `Script Agent` ja elevado e o subsistema de voz ja corrigido e consolidado com `Kokoro` como baseline local principal.

Sobre esse baseline, a Phase 2.6 iniciou hardening governado em ondas. A Wave 1 (`Learning Agent`, `Account Health Agent`, `Trend Analysis Agent`) ja passou por gates proprios, Wave 1 Master Gate e Absolute Master Gate pre-Wave 2 com recomendacao de v3 readiness com monitoramento. A Wave 2 (`Script Agent`, `Voice Agent`, `Asset Selection Agent`, `Video QC Agent`) tambem ja passou por gates proprios e pelo Wave 2 Master Gate com `GO_WITH_MONITORING`.

Este documento existe para impedir perda de contexto, regressao conceitual e deriva arquitetural entre sessoes, pessoas e ciclos de implementacao.

Se um novo chat precisar de uma unica fonte para entender o sistema antes de agir, este e o documento certo para abrir primeiro.

---

## 30. Atualizacao Canonica Phase 2.6 - Learning + Account Health

Nota de continuidade: esta secao registra um estado intermediario historico da Phase 2.6. O estado operacional atual e supersedido pela Secao 31.

Esta secao atualiza o estado do sistema apos o Gate Mestre Parcial:

`OUT/audit/phase_2_6_partial_master_gate_learning_account_health/final_verdict.json`

Resultado:

```json
{
  "system": "CORTAI_RUNTIME_V2_5",
  "phase": "2.6",
  "audit_type": "PHASE_2_6_PARTIAL_MASTER_GATE_LEARNING_ACCOUNT_HEALTH",
  "verdict": "GO_WITH_MONITORING",
  "recommendation": "PROCEED_TO_TREND_ANALYSIS_AGENT_V2_6_PLAN",
  "critical_failures": 0,
  "blocking_failures": []
}
```

### 30.1 Learning Agent v2.6

Status:

- `GO_WITH_MONITORING`
- ready for v3 with monitoring
- evidence-backed
- confidence-calibrated
- temporally credible
- contamination-aware
- strategy-pressure bounded
- traceable end-to-end
- deterministic under controlled replay
- boundary preserved

Canonical artifacts:

- `docs/runtime/phase-2-6/agents/learning/LEARNING_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/learning/LEARNING_AGENT_V2_6_EXCELLENCE_GATE.md`
- `tests/gates/agents/learning/run_learning_agent_v2_6_excellence_gate.py`
- `OUT/audit/learning_agent_v2_6_excellence_gate/final_verdict.json`

Residual monitoring:

- `LONGITUDINAL_PRODUCTION_HISTORY_STILL_SHORT`

Boundary:

- Learning may produce bounded policy pressure.
- Learning must not decide Strategy.
- Learning must not decide publishability.
- Learning must not override Health, QC, Trend, Novelty or Experiment.

### 30.2 Account Health Agent v2.6

Status:

- `GO_WITH_MONITORING`
- ready for v3 with monitoring
- telemetry-enriched
- risk-component explicit
- confidence-calibrated
- temporally aware
- safe under degraded input
- constraints rationale complete
- traceable end-to-end through `health_trace`
- HOLD authority preserved
- boundary preserved

Canonical artifacts:

- `docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/account-health/ACCOUNT_HEALTH_AGENT_V2_6_EXCELLENCE_GATE.md`
- `tests/gates/agents/account_health/run_account_health_agent_v2_6_excellence_gate.py`
- `OUT/audit/account_health_agent_v2_6_excellence_gate/final_verdict.json`

Residual monitoring:

- `ACCOUNT_HEALTH_RUNTIME_HISTORY_STILL_SHORT`
- `ACCOUNT_HEALTH_TELEMETRY_PRODUCER_COVERAGE_STILL_EXPANDING`

Boundary:

- Account Health owns `SAFE`, `CAUTION`, `HOLD`.
- Account Health may constrain Strategy.
- Account Health must not become Strategy.
- Account Health must not become QC, Learning, Experiment or rollout optimization.

### 30.3 Integrated Gate Result

Gate executed:

- `tests/gates/phase_2_6/run_phase_2_6_partial_master_gate_learning_account_health.py`

Artifacts:

- `docs/runtime/phase-2-6/master-gates/PHASE_2_6_PARTIAL_MASTER_GATE_LEARNING_ACCOUNT_HEALTH.md`
- `OUT/audit/phase_2_6_partial_master_gate_learning_account_health/final_verdict.json`
- `OUT/audit/phase_2_6_partial_master_gate_learning_account_health/checklist_results.json`
- `OUT/audit/phase_2_6_partial_master_gate_learning_account_health/scenario_outputs.json`
- `OUT/audit/phase_2_6_partial_master_gate_learning_account_health/metrics.json`
- `OUT/audit/phase_2_6_partial_master_gate_learning_account_health/cross_agent_consistency.json`

Validation summary:

- unit/integration battery: `149 passed`
- Blocks A-P: `16/16 passed`
- Cross-agent scenarios: `6/6 passed`
- blocking failures: `[]`
- fake confidence detected: `false`
- silent failures detected: `false`
- boundary violations detected: `false`
- non-determinism detected: `false`

### 30.4 Current Operational Rule

The system may proceed to:

- `Trend Analysis Agent v2.6 Excellence Plan`

The system must not proceed directly to:

- Trend implementation without plan
- core pipeline modification
- Strategy redesign
- Publisher work
- external expansion
- hidden enforcement

The current correct next artifact is:

- `docs/runtime/phase-2-6/agents/trend-analysis/TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_PLAN.md`

Final Phase 2.6 posture after this update:

```json
{
  "phase_2_6_wave_1": {
    "learning_agent_v2_6": "GO_WITH_MONITORING",
    "account_health_agent_v2_6": "GO_WITH_MONITORING",
    "partial_master_gate_learning_account_health": "GO_WITH_MONITORING",
    "recommendation": "PROCEED_TO_TREND_ANALYSIS_AGENT_V2_6_PLAN"
  }
}
```

---

## 31. Atualizacao Canonica Phase 2.6 - Wave 1 + Script Agent v2.6

Nota de continuidade: esta secao registra um estado intermediario historico. O estado operacional atual e supersedido pela Secao 32.

Esta secao atualiza o estado do sistema apos:

- `OUT/audit/trend_analysis_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/phase_2_6_wave_1_master_gate/final_verdict.json`
- `OUT/audit/cortai_absolute_master_gate/final_verdict.json`
- `OUT/audit/script_agent_v2_6_excellence_gate/final_verdict.json`

Resultado consolidado:

```json
{
  "phase": "2.6",
  "wave_1": {
    "learning_agent_v2_6": "GO_WITH_MONITORING",
    "account_health_agent_v2_6": "GO_WITH_MONITORING",
    "trend_analysis_agent_v2_6": "GO_WITH_MONITORING",
    "wave_1_master_gate": "GO_WITH_MONITORING",
    "absolute_master_gate_pre_wave_2": "GO_WITH_MONITORING"
  },
  "wave_2": {
    "script_agent_v2_6": "GO_WITH_MONITORING",
    "next_authorized_plan": "VOICE_AGENT_V2_6_EXCELLENCE_PLAN"
  }
}
```

### 31.1 Trend Analysis Agent v2.6

Status:

- `GO_WITH_MONITORING`
- ready for v3 with monitoring
- source-governed
- provenance-aware
- freshness-disciplined
- confidence-calibrated as trust in trend context
- shift-aware without forecasting
- downstream utility clear and advisory only
- traceable end-to-end through `trend_trace`
- fallback-honest
- boundary preserved

Canonical artifacts:

- `docs/runtime/phase-2-6/agents/trend-analysis/TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/trend-analysis/TREND_ANALYSIS_AGENT_V2_6_EXCELLENCE_GATE.md`
- `tests/gates/agents/trend_analysis/run_trend_analysis_agent_v2_6_excellence_gate.py`
- `OUT/audit/trend_analysis_agent_v2_6_excellence_gate/final_verdict.json`

Residual monitoring:

- `TREND_RUNTIME_HISTORY_STILL_SHORT`
- `TREND_PRODUCER_COVERAGE_STILL_BOUNDED`
- `TREND_LONGITUDINAL_SOURCE_DIVERSITY_STILL_EXPANDING`

Boundary:

- Trend provides governed context.
- Trend must not become Strategy.
- Trend must not become Asset, QC, Publisher, Learning or an external intelligence platform.
- Trend confidence measures trust in emitted trend context, not trend strength or expected performance.

### 31.2 Wave 1 Master And Absolute Master Gates

Wave 1 Master Gate:

- `docs/runtime/phase-2-6/master-gates/PHASE_2_6_WAVE_1_MASTER_GATE.md`
- `tests/gates/phase_2_6/run_phase_2_6_wave_1_master_gate.py`
- `OUT/audit/phase_2_6_wave_1_master_gate/final_verdict.json`

Absolute Master Gate pre-Wave 2:

- `docs/runtime/phase-2-6/master-gates/CORTAI_ABSOLUTE_MASTER_GATE_PRE_WAVE_2.md`
- `tests/gates/phase_2_6/run_cortai_absolute_master_gate.py`
- `OUT/audit/cortai_absolute_master_gate/final_verdict.json`

Consolidated reading:

- Wave 1 agents are ready for v3 with monitoring.
- No critical failures.
- No blocking failures.
- No fake confidence.
- No silent failures detected.
- No boundary violations detected.
- No non-determinism detected under controlled replay.
- Residuals are monitoring-class, not structural blockers.

### 31.3 Script Agent v2.6

Status:

- `GO_WITH_MONITORING`
- ready for v3 with monitoring
- runtime-real
- context-governed
- quality-rubric explicit
- hook/setup/payoff aware
- diversity and anti-cliche aware
- provider/fallback honest
- confidence-calibrated as trust in script construction
- traceable end-to-end through `script_trace`
- deterministic under controlled replay
- boundary preserved

Canonical artifacts:

- `docs/runtime/phase-2-6/agents/script/SCRIPT_AGENT_V2_6_EXCELLENCE_PLAN.md`
- `docs/runtime/phase-2-6/agents/script/SCRIPT_AGENT_V2_6_EXCELLENCE_GATE.md`
- `tests/gates/agents/script/run_script_agent_v2_6_excellence_gate.py`
- `OUT/audit/script_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/script_agent_v2_6_excellence_gate/checklist_results.json`
- `OUT/audit/script_agent_v2_6_excellence_gate/scenario_outputs.json`
- `OUT/audit/script_agent_v2_6_excellence_gate/metrics.json`

Gate result:

```json
{
  "verdict": "GO_WITH_MONITORING",
  "scenario_pass_count": "8/8",
  "tests": "134 passed",
  "critical_failures": 0,
  "blocking_failures": [],
  "release_state": "READY_FOR_V3_WITH_MONITORING",
  "recommendation": "PROCEED_TO_VOICE_AGENT_V2_6_PLAN"
}
```

Residual monitoring:

- `SCRIPT_RUNTIME_PROVIDER_HISTORY_STILL_SHORT`
- `SCRIPT_LONGITUDINAL_QUALITY_HISTORY_STILL_SHORT`
- `SCRIPT_PROVIDER_REPAIR_METADATA_STILL_NOT_REPORTED`

Boundary:

- Script owns hook/setup/payoff and narrative construction trace.
- Script must not decide Strategy.
- Script must not decide Voice, Asset, QC, Experiment or Publisher behavior.
- Script confidence measures trust in script construction, not performance.
- Script trace explains why the `ScriptPlan` was emitted; it must not rewrite the script.

### 31.4 Historical Operational Rule

At the time of this historical checkpoint, the system could proceed to:

- `Voice Agent v2.6 Excellence Plan`

The system must not proceed directly to:

- Voice implementation without a formal plan
- provider expansion without a gated provider plan
- core pipeline modification
- Strategy redesign
- Publisher work
- hidden publish enforcement
- QC ownership drift

The current correct next artifact is:

- `docs/runtime/phase-2-6/agents/voice/VOICE_AGENT_V2_6_EXCELLENCE_PLAN.md`

Final Phase 2.6 posture after this update:

```json
{
  "phase_2_6": {
    "wave_1": "READY_FOR_V3_WITH_MONITORING",
    "script_agent_v2_6": "READY_FOR_V3_WITH_MONITORING",
    "next_authorized_work": "VOICE_AGENT_V2_6_EXCELLENCE_PLAN",
    "core_pipeline_unchanged": true,
    "strategy_unchanged": true,
    "publisher_out_of_scope": true
  }
}
```

---

## 32. Atualizacao Canonica Phase 2.6 - Wave 2 Master Gate

Esta secao supersede a leitura operacional da Secao 31 para o estado atual da Phase 2.6.

Estado consolidado apos:

- `OUT/audit/script_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/voice_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/asset_selection_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/video_qc_agent_v2_6_excellence_gate/final_verdict.json`
- `OUT/audit/phase_2_6_wave_2_master_gate/final_verdict.json`

Resultado consolidado:

```json
{
  "phase": "2.6",
  "wave_1": {
    "learning_agent_v2_6": "READY_FOR_V3_WITH_MONITORING",
    "account_health_agent_v2_6": "READY_FOR_V3_WITH_MONITORING",
    "trend_analysis_agent_v2_6": "READY_FOR_V3_WITH_MONITORING",
    "wave_1_master_gate": "GO_WITH_MONITORING"
  },
  "wave_2": {
    "script_agent_v2_6": "READY_FOR_V3_WITH_MONITORING",
    "voice_agent_v2_6": "READY_FOR_V3_WITH_MONITORING",
    "asset_selection_agent_v2_6": "READY_FOR_V3_WITH_MONITORING",
    "video_qc_agent_v2_6": "READY_FOR_V3_WITH_MONITORING",
    "wave_2_master_gate": "GO_WITH_MONITORING"
  },
  "next_authorized_gate": "PHASE_2_6_FINAL_MASTER_GATE"
}
```

### 32.1 Wave 2 Master Gate Result

Gate executed:

- `tests/gates/phase_2_6/run_phase_2_6_wave_2_master_gate.py`

Artifacts:

- `docs/runtime/phase-2-6/master-gates/PHASE_2_6_WAVE_2_MASTER_GATE.md`
- `OUT/audit/phase_2_6_wave_2_master_gate/final_verdict.json`
- `OUT/audit/phase_2_6_wave_2_master_gate/checklist_results.json`
- `OUT/audit/phase_2_6_wave_2_master_gate/scenario_outputs.json`
- `OUT/audit/phase_2_6_wave_2_master_gate/metrics.json`
- `OUT/audit/phase_2_6_wave_2_master_gate/cross_agent_consistency.json`

Validation summary:

- verdict: `GO_WITH_MONITORING`
- blocks: `16/16 passed`
- test battery: `343 passed`
- critical failures: `0`
- blocking failures: `[]`
- fake confidence detected: `false`
- silent failures detected: `false`
- boundary violations detected: `false`
- non-determinism detected: `false`
- trace incomplete: `false`
- recommendation: `PROCEED_TO_PHASE_2_6_FINAL_MASTER_GATE`

### 32.2 Script Agent v2.6

Status:

- `GO_WITH_MONITORING`
- ready for v3 with monitoring
- context-governed
- quality-rubric explicit
- hook/setup/payoff aware
- diversity and anti-cliche aware
- provider/fallback honest
- confidence-calibrated as trust in script construction
- traceable end-to-end through `script_trace`
- boundary preserved

Residual monitoring:

- `SCRIPT_RUNTIME_PROVIDER_HISTORY_STILL_SHORT`
- `SCRIPT_LONGITUDINAL_QUALITY_HISTORY_STILL_SHORT`
- `SCRIPT_PROVIDER_REPAIR_METADATA_STILL_NOT_REPORTED`

Boundary:

- Script constructs narrative.
- Script must not become Strategy, Voice, Asset, QC, Publisher or performance predictor.

### 32.3 Voice Agent v2.6

Status:

- `GO_WITH_MONITORING`
- ready for v3 with monitoring
- contract-governed
- delivery semantics explicit
- timing and pause semantics explicit
- monotony and contrast analysis explicit
- provider/fallback honest
- audio validation linkage honest
- confidence-calibrated as trust in voice plan execution readiness
- traceable end-to-end through `voice_trace`
- TTS Router boundary preserved

Residual monitoring:

- `VOICE_TTS_TRACE_NOT_AVAILABLE_AT_VOICE_AGENT_LAYER`
- `VOICE_RUNTIME_AUDIO_VALIDATION_HISTORY_STILL_SHORT`
- `VOICE_PROVIDER_EXECUTION_HISTORY_STILL_SHORT`

Boundary:

- Voice plans voice delivery.
- Voice must not fabricate TTS execution.
- Voice must not become Script, Strategy, QC, Publisher or TTS Router.

### 32.4 Asset Selection Agent v2.6

Status:

- `GO_WITH_MONITORING`
- ready for v3 with monitoring
- context-governed
- catalog/source-governed
- segment visual intent explicit
- visual semantic alignment metadata-only
- visual truthfulness and mismatch risk explicit
- fallback/safe-default honest
- diversity and repetition guarded
- confidence-calibrated as trust in asset selection
- traceable end-to-end through `asset_trace`
- selection, ranking and fallback behavior preserved

Residual monitoring:

- `ASSET_RUNTIME_VISUAL_HISTORY_STILL_SHORT`
- `ASSET_CATALOG_COVERAGE_STILL_EXPANDING`
- `ASSET_IMAGE_PIXEL_VALIDATION_NOT_AVAILABLE_AT_SELECTION_LAYER`

Boundary:

- Asset Selection selects visual assets from governed metadata/catalog surfaces.
- Asset Selection must not become Strategy, QC, Publisher or pixel-level visual truth authority.

### 32.5 Video QC Agent v2.6

Status:

- `GO_WITH_MONITORING`
- ready for v3 with monitoring
- input/artifact-governed
- evidence scoring explicit
- confidence-calibrated as trust in QC decision
- decision semantics and severity explicit
- traceable end-to-end through `qc_trace`
- `APPROVE/HOLD/REJECT` preserved
- `publishable` semantics preserved
- boundary preserved

Residual monitoring:

- `VIDEO_QC_RUNTIME_HISTORY_STILL_SHORT`
- `VIDEO_QC_PRODUCT_SIGNAL_CALIBRATION_STILL_MATURING`
- `VIDEO_QC_LAYER_ATTRIBUTION_EVIDENCE_STILL_LIMITED`
- `VIDEO_QC_MEDIA_PROBE_COVERAGE_ENVIRONMENT_DEPENDENT`

Boundary:

- Video QC evaluates final artifacts.
- Video QC must not repair, publish, rewrite, rerender, resynthesize voice, replace assets or predict performance.

### 32.6 Integrated Wave 2 Reading

The output-quality pipeline is now audit-grade under controlled validation:

- Script output feeds Voice without contract drift.
- Script output feeds Asset and QC surfaces where applicable.
- Voice plan remains traceable and does not become Script, Strategy or TTS Router.
- Asset plan remains traceable and does not become Strategy or QC.
- Video QC remains final artifact evaluator and does not become Publisher.
- No output-quality agent overrides Strategy.
- No output-quality agent creates new publishability authority beyond existing QC semantics.
- Fallbacks are explicit and not treated as success.
- All Wave 2 traces are reconstructible.

### 32.7 Current Operational Rule

The system may proceed to:

- `PHASE_2_6_FINAL_MASTER_GATE`

The system must not proceed directly to:

- Wave 3
- Publisher changes
- core pipeline modification
- Strategy redesign
- hidden publishability enforcement
- provider expansion
- asset ranking changes
- QC threshold changes
- performance prediction

Final Phase 2.6 posture after this update:

```json
{
  "phase_2_6": {
    "wave_1": "READY_FOR_V3_WITH_MONITORING",
    "wave_2": "READY_FOR_V3_WITH_MONITORING",
    "wave_2_master_gate": "GO_WITH_MONITORING",
    "next_authorized_work": "PHASE_2_6_FINAL_MASTER_GATE",
    "core_pipeline_unchanged": true,
    "strategy_unchanged": true,
    "publisher_out_of_scope": true
  }
}
```
