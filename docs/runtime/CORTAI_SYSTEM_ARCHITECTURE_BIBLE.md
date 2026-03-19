# CORTAI SYSTEM ARCHITECTURE BIBLE

Versao: 1.0  
Status: Documento mestre de continuidade arquitetural  
Escopo: consolidacao de arquitetura, fases, contratos, fluxos, gates, artefatos e estado atual do sistema  
Ultima consolidacao: `2026-03-18`

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
- Script Agent: otimizado e aprovado em gate de excelencia
- Voice subsystem: corrigido, governado e aprovado em gate
- Hook visual alignment: promovido como baseline
- provider local principal atual: `Kokoro`
- fallback duro local: `Piper`

Conclusao tecnica atual:

- o sistema deixou de ser apenas um pipeline de render automatizado
- o sistema ja opera como uma camada cognitiva modular sobre uma base operacional robusta
- o elo fraco principal deixou de ser o `Script Agent`
- o subsistema de voz deixou de ser uma configuracao simbolica e passou a ser governado arquiteturalmente
- o foco natural seguinte deixa de ser correcao estrutural e passa a ser disciplina de baseline e expansao controlada de providers

---

## 3. O Que e o CortAI

O CortAI e um estúdio automatizado para geracao de videos curtos orientados a retencao.

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

- `docs/runtime/phase1_completion_report_v1_0.md`

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

- `docs/runtime/phase2_completion_report_v1_0.md`

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

- `docs/runtime/script_agent_excellence_gate_v1_0.md`

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

Fallback:

- seguro
- nunca deve bloquear o fluxo por acidente

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

Fontes tipicas:

- `publish_records`
- `video_metrics`
- `analysis`

Fallback:

- `learning_insights = DEFAULT`

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

- `docs/runtime/script_agent_excellence_gate_v1_0.md`

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

- `docs/runtime/pre_d23_final_release_audit_gate_v1_0.md`

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

- `docs/runtime/pre_phase3_system_final_gate_v1_0.md`

Objetivo:

- validar o sistema inteiro antes da proxima fase

### 20.3 Script Agent Excellence Gate

Script:

- `backend/scripts/run_script_agent_excellence_gate.ps1`

Documento:

- `docs/runtime/script_agent_excellence_gate_v1_0.md`

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

- `docs/runtime/voice_agent_excellence_gate_v1_0.md`

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

## 26. Como Um Novo Chat Deve Ler o Projeto

Ordem recomendada de leitura para continuidade:

1. `docs/runtime/CORTAI_SYSTEM_ARCHITECTURE_BIBLE.md`
2. `docs/runtime/phase1_completion_report_v1_0.md`
3. `docs/runtime/phase2_completion_report_v1_0.md`
4. `docs/runtime/phase2_implementation_map_v1_0.md`
5. `docs/runtime/script_agent_excellence_gate_v1_0.md`
6. `docs/runtime/phase2_5_voice_agent_definition_v1_0.md`
7. `docs/runtime/phase2_5_voice_agent_file_list_v1_0.md`
8. `docs/runtime/voice_agent_excellence_gate_v1_0.md`
9. `docs/runtime/phase2_5b_kokoro_integration_definition_v1_0.md`
10. `docs/runtime/phase2_5b_kokoro_file_list_v1_0.md`
11. `OUT/audit/script_agent_excellence_gate/AUDIT_REPORT.md`
12. `OUT/audit/phase2_5_voice_agent/AUDIT_REPORT.md`
13. `OUT/audit/phase2_5b_kokoro/AUDIT_REPORT.md`
14. `OUT/audit/voice_agent_excellence_gate/AUDIT_REPORT.md`

Se o chat for trabalhar em voz ou providers:

15. ler `backend/app/creative/agents/voice/service.py`
16. ler `backend/app/creative/agents/voice/interpreter.py`
17. ler `backend/app/content/pipeline/tts_router.py`
18. ler `backend/app/content/pipeline/kokoro_adapter.py`
19. ler como o `Creative Orchestrator` consome a voz e como o pipeline materializa `tts_trace`

---

## 27. Bootstrap Prompt Recomendado Para Novo Chat

Exemplo de bootstrap enxuto:

```text
Voce esta entrando no projeto CortAI.

Fonte principal de contexto:
- docs/runtime/CORTAI_SYSTEM_ARCHITECTURE_BIBLE.md

Estado atual:
- Phase 1: concluida
- Phase 2: concluida
- Phase 2.5A: Voice Architecture Repair concluida e validada
- Phase 2.5B: Kokoro Integration concluida e validada
- Script Agent nao e mais o gargalo principal
- Voice subsystem agora e governado por `VoicePlan`, `Voice Interpreter` e `TTS Router`
- baseline local principal atual: `Kokoro`
- fallback duro atual: `Piper`

Restri??es:
- nao quebrar Fase 1
- nao quebrar contratos canonicos
- nao redesenhar o sistema
- preservar Creative Orchestrator como coordenador unico
- manter fallback chains

Objetivo atual:
- consolidar o baseline local atual e so expandir providers sob hipotese clara, gate e comparacao objetiva
```

---

## 28. Veredito Arquitetural Atual

Leitura honesta do estado do projeto:

- o CortAI nao e mais um prototipo solto
- o projeto ja possui baseline operacional validada
- a camada cognitiva esta implementada e congelada no escopo da Fase 2
- o `Script Agent` ja passou por gate de excelencia com evidencia
- o subsistema de voz ja passou por correcao estrutural e por gate de excelencia
- o sistema e suficientemente maduro para consolidar baseline antes de nova expansao

Em termos de engenharia:

- infraestrutura: madura
- pipeline: funcional
- multiagente: funcional
- gates: maduros
- baseline local de voz: governado
- contexto para continuidade por LLM: centralizado

---

## 29. Conclusao Final

O CortAI hoje deve ser entendido como um sistema em duas grandes camadas:

1. uma camada operacional robusta validada na Fase 1
2. uma camada cognitiva modular validada na Fase 2

Sobre essas duas camadas, a Fase 2.5 introduziu melhorias de excelencia em gargalos perceptiveis, com o `Script Agent` ja elevado e o subsistema de voz ja corrigido e consolidado com `Kokoro` como baseline local principal.

Este documento existe para impedir perda de contexto, regressao conceitual e deriva arquitetural entre sessoes, pessoas e ciclos de implementacao.

Se um novo chat precisar de uma unica fonte para entender o sistema antes de agir, este e o documento certo para abrir primeiro.
