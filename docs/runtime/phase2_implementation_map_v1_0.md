CortAI - Mapa de Implementacao da Fase 2

Creative Intelligence Layer

Versao: 1.0
Status: Congelado para Implementacao
Documento: `docs/runtime/phase2_implementation_map_v1_0.md`

---

## 1. Objetivo

Este documento congela a forma como a Fase 2 deve existir no repositorio.

Ele define:

- mapa de diretorios
- lista de modulos
- contratos canonicos em codigo
- fronteiras entre Fase 2 e Fase 1

O objetivo e evitar:

- acoplamento ruim
- nomes inconsistentes
- storage duplicado
- contratos divergentes

---

## 2. Regra de Ouro

A Fase 2 nao substitui a Fase 1.

A Fase 2:

- decide
- recomenda
- seleciona
- consolida contexto

A Fase 1:

- executa
- renderiza
- persiste artefatos operacionais
- publica internamente no runtime
- coleta metricas

Em codigo:

- agentes da Fase 2 nao chamam uns aos outros diretamente
- agentes da Fase 2 nao escrevem `publish_record`
- agentes da Fase 2 nao escrevem `metrics`
- agentes da Fase 2 nao chamam `Safety Layer` diretamente
- toda coordenacao passa pelo `Creative Orchestrator Service`

---

## 3. Mapa de Diretorios

Estrutura recomendada:

```text
backend/app/creative/
  orchestrator/
    __init__.py
    models.py
    service.py
    events.py

  agents/
    __init__.py

    trend_analysis/
      __init__.py
      models.py
      service.py

    strategy/
      __init__.py
      models.py
      service.py

    script/
      __init__.py
      models.py
      service.py

    voice/
      __init__.py
      models.py
      service.py

    asset_selection/
      __init__.py
      models.py
      service.py

    video_qc/
      __init__.py
      models.py
      service.py

    account_health/
      __init__.py
      models.py
      service.py

    learning/
      __init__.py
      models.py
      service.py

  capabilities/
    __init__.py
    experiment/
      __init__.py
      models.py
      service.py

  context/
    __init__.py
    models.py
    repository.py
    file_store.py
    pg_store.py

  contracts/
    __init__.py
    creative_pack.py
    orchestrator_io.py
    agent_common.py

backend/data/context/
  trends/
  strategy/
  learning/
  qc_history/

tests/
  test_creative_orchestrator_phase2_unittest.py
  test_trend_analysis_agent_phase2_unittest.py
  test_strategy_agent_phase2_unittest.py
  test_script_agent_phase2_unittest.py
  test_voice_agent_phase2_unittest.py
  test_asset_selection_agent_phase2_unittest.py
  test_video_qc_agent_phase2_unittest.py
  test_account_health_agent_phase2_unittest.py
  test_learning_agent_phase2_unittest.py
  test_experiment_capability_phase2_unittest.py
  test_phase2_context_repository_unittest.py
  test_phase2_smoke_integration_unittest.py
```

---

## 4. Lista de Modulos por Dominio

### 4.1 `backend/app/creative/orchestrator/`

Arquivos:

- `models.py`
- `service.py`
- `events.py`

Responsabilidade:

- receber entrada canonica da Fase 2
- carregar contexto
- coordenar agentes
- aplicar fallback
- consolidar o `creative_pack`
- emitir eventos da camada cognitiva

### 4.2 `backend/app/creative/agents/trend_analysis/`

Arquivos:

- `models.py`
- `service.py`

Responsabilidade:

- carregar e consolidar perfis de tendencia por nicho
- aplicar fallback para nicho-pai ou perfil generico

### 4.3 `backend/app/creative/agents/strategy/`

Arquivos:

- `models.py`
- `service.py`

Responsabilidade:

- gerar `account_strategy_profile`
- tratar `cold_start`
- consolidar estrategia recomendada por conta

### 4.4 `backend/app/creative/agents/script/`

Arquivos:

- `models.py`
- `service.py`

Responsabilidade:

- gerar `hook/setup/payoff`
- produzir `script_plan`
- respeitar contexto estrategico e experimental

### 4.5 `backend/app/creative/agents/voice/`

Arquivos:

- `models.py`
- `service.py`

Responsabilidade:

- definir provider de voz
- selecionar voz, estilo e parametros narrativos
- materializar `voice_plan`

### 4.6 `backend/app/creative/agents/asset_selection/`

Arquivos:

- `models.py`
- `service.py`

Responsabilidade:

- selecionar assets por papel narrativo
- validar elegibilidade visual
- materializar `asset_plan`

### 4.7 `backend/app/creative/agents/video_qc/`

Arquivos:

- `models.py`
- `service.py`

Responsabilidade:

- validar qualidade do video antes de seguir para safety
- emitir `APPROVE` ou `REJECT`

### 4.8 `backend/app/creative/agents/account_health/`

Arquivos:

- `models.py`
- `service.py`

Responsabilidade:

- avaliar risco por conta
- emitir `SAFE`, `CAUTION` ou `HOLD`

### 4.9 `backend/app/creative/agents/learning/`

Arquivos:

- `models.py`
- `service.py`

Responsabilidade:

- consolidar recomendacoes baseadas em metricas reais
- produzir `learning_recommendations`

### 4.10 `backend/app/creative/capabilities/experiment/`

Arquivos:

- `models.py`
- `service.py`

Responsabilidade:

- encapsular assignment experimental
- expor variacoes permitidas
- integrar com D31 sem alterar seu contrato base

### 4.11 `backend/app/creative/context/`

Arquivos:

- `models.py`
- `repository.py`
- `file_store.py`
- `pg_store.py`

Responsabilidade:

- definir persistencia canonica da camada cognitiva
- abstrair PostgreSQL e backup em JSON/JSONL

### 4.12 `backend/app/creative/contracts/`

Arquivos:

- `creative_pack.py`
- `orchestrator_io.py`
- `agent_common.py`

Responsabilidade:

- congelar nomes de contratos em codigo
- impedir deriva de schemas entre agentes

---

## 5. Contratos Congelados em Codigo

Os nomes abaixo ficam congelados para a implementacao da Fase 2.

### 5.1 Contratos do Orchestrator

Definir em:

- `backend/app/creative/contracts/orchestrator_io.py`

Modelos canonicos:

- `CreativeOrchestratorInput`
- `CreativeOrchestratorResult`
- `CreativeOrchestratorFailure`

Campos minimos de `CreativeOrchestratorInput`:

- `account_id: str`
- `niche: str`
- `topic: str`
- `publish_slot: str`
- `creative_pack_id: str | None`
- `experiment_assignment_id: str | None`
- `account_context_ref: str | None`
- `trend_context_ref: str | None`

Campos minimos de `CreativeOrchestratorResult`:

- `creative_pack: CreativePack`
- `fallbacks_used: list[str]`
- `events_emitted: list[str]`
- `qc_required: bool`

### 5.2 Contrato Canonico do Creative Pack

Definir em:

- `backend/app/creative/contracts/creative_pack.py`

Modelos canonicos:

- `CreativePack`
- `StrategyProfile`
- `TrendProfile`
- `ScriptPlan`
- `VoicePlan`
- `AssetPlan`
- `ExperimentAssignment`

Campos minimos de `CreativePack`:

- `creative_pack_id: str`
- `account_id: str`
- `niche: str`
- `topic: str`
- `strategy_profile: StrategyProfile`
- `trend_profile: TrendProfile`
- `script_plan: ScriptPlan`
- `voice_plan: VoicePlan`
- `asset_plan: AssetPlan`
- `experiment_assignment: ExperimentAssignment | None`
- `generated_at: str`
- `orchestrator_version: str`

### 5.3 Contratos Comuns de Agente

Definir em:

- `backend/app/creative/contracts/agent_common.py`

Modelos canonicos:

- `AgentDecision`
- `AgentFailure`
- `FallbackDecision`

Enums congelados:

- `DecisionStatus`
- `FallbackMode`
- `FailureSeverity`

Valores minimos de `DecisionStatus`:

- `APPROVE`
- `REJECT`
- `SAFE`
- `CAUTION`
- `HOLD`
- `ALLOW`
- `DELAY`
- `BLOCK`

Regra:

- agentes podem ter modelos especificos locais
- mas resultados externos devem derivar destes contratos base

---

## 6. Contratos Especificos por Agente

### 6.1 Trend Analysis Agent

Definir em:

- `backend/app/creative/agents/trend_analysis/models.py`

Modelos:

- `TrendAnalysisInput`
- `TrendAnalysisProfile`
- `TrendAnalysisResult`

### 6.2 Strategy Agent

Definir em:

- `backend/app/creative/agents/strategy/models.py`

Modelos:

- `StrategyAgentInput`
- `AccountStrategyProfile`
- `StrategyAgentResult`

### 6.3 Script Agent

Definir em:

- `backend/app/creative/agents/script/models.py`

Modelos:

- `ScriptAgentInput`
- `ScriptPlan`
- `ScriptAgentResult`

Regra:

- `ScriptPlan` deste modulo deve ser alias ou reexport do contrato canonico em `creative_pack.py`

### 6.4 Voice Agent

Definir em:

- `backend/app/creative/agents/voice/models.py`

Modelos:

- `VoiceAgentInput`
- `VoicePlan`
- `VoiceAgentResult`

### 6.5 Asset Selection Agent

Definir em:

- `backend/app/creative/agents/asset_selection/models.py`

Modelos:

- `AssetSelectionInput`
- `AssetPlan`
- `AssetSelectionResult`

### 6.6 Video QC Agent

Definir em:

- `backend/app/creative/agents/video_qc/models.py`

Modelos:

- `VideoQcInput`
- `VideoQcDecision`
- `VideoQcResult`

Campos minimos:

- `status: Literal["APPROVE", "REJECT"]`
- `reasons: list[str]`
- `checked_at: str`

### 6.7 Account Health Agent

Definir em:

- `backend/app/creative/agents/account_health/models.py`

Modelos:

- `AccountHealthInput`
- `AccountHealthDecision`
- `AccountHealthResult`

Campos minimos:

- `status: Literal["SAFE", "CAUTION", "HOLD"]`
- `signals: list[str]`
- `checked_at: str`

### 6.8 Learning Agent

Definir em:

- `backend/app/creative/agents/learning/models.py`

Modelos:

- `LearningAgentInput`
- `LearningRecommendation`
- `LearningAgentResult`

### 6.9 Experiment Capability

Definir em:

- `backend/app/creative/capabilities/experiment/models.py`

Modelos:

- `ExperimentCapabilityInput`
- `ExperimentAssignment`
- `ExperimentCapabilityResult`

Regra:

- `ExperimentAssignment` deste modulo deve ser alias ou reexport do contrato canonico em `creative_pack.py`

---

## 7. Persistencia Canonica

### 7.1 Repositorio unico da camada cognitiva

Toda persistencia da Fase 2 deve passar por:

- `backend/app/creative/context/repository.py`

Interface minima:

- `load_trend_profile(...)`
- `save_trend_profile(...)`
- `load_strategy_profile(...)`
- `save_strategy_profile(...)`
- `save_learning_recommendations(...)`
- `save_video_qc_decision(...)`
- `save_orchestrator_output(...)`
- `load_account_context(...)`

### 7.2 Implementacoes de store

Implementacoes:

- `pg_store.py`
- `file_store.py`

Regra:

- `pg_store.py` e a fonte principal
- `file_store.py` materializa backup auditavel
- agentes nao acessam `PostgreSQL` ou arquivos diretamente fora do repositorio

### 7.3 O que nao pode acontecer

- agent escrevendo JSON arbitrario fora de `backend/data/context/`
- agent escrevendo tabela propria sem passar pelo repositorio
- duplicacao do mesmo dominio em varios lugares

---

## 8. Regras de Integracao com a Fase 1

### 8.1 Ponto unico de entrada

A Fase 2 deve integrar com a Fase 1 por meio do `creative_pack` entregue ao pipeline.

### 8.2 O que a Fase 2 nao pode fazer

- escrever `publish_record`
- chamar `metrics collector`
- disparar `Safety Layer` diretamente
- reescrever artefatos do pipeline apos render
- alterar contratos de `ExecutionEnvelope` e `PipelineResult` por conta propria

### 8.3 Ordem operacional congelada

Fluxo permitido:

```text
Creative Orchestrator
-> Content Pipeline
-> Video QC Agent
-> Safety Layer
-> Runtime Publish
-> Metrics Collector
-> Learning Agent
```

### 8.4 Regra de rejeicao do Video QC

Se `Video QC Agent` retornar `REJECT`:

- o fluxo para
- nao chama `Safety Layer`
- nao gera `publish_record`
- nao segue para runtime publish

---

## 9. Eventos Congelados da Camada Cognitiva

Os nomes abaixo ficam congelados para implementacao.

Definir emissores em:

- `backend/app/creative/orchestrator/events.py`

Eventos minimos:

- `CREATIVE/orchestrator_started`
- `CREATIVE/orchestrator_completed`
- `CREATIVE/orchestrator_failed`
- `CREATIVE/trend_profile_loaded`
- `CREATIVE/strategy_profile_generated`
- `CREATIVE/script_generated`
- `CREATIVE/voice_selected`
- `CREATIVE/assets_selected`
- `CREATIVE/video_qc_approved`
- `CREATIVE/video_qc_rejected`
- `CREATIVE/account_health_safe`
- `CREATIVE/account_health_caution`
- `CREATIVE/account_health_hold`
- `CREATIVE/learning_recommendations_generated`

Regra:

- nao criar eventos `CONTENT/*` na Fase 2
- nao criar eventos `SAFETY/*` na Fase 2

---

## 10. Ordem de Implementacao Recomendada

### Bloco 1

- `creative/contracts/*`
- `creative/orchestrator/*`
- `creative/context/*`

### Bloco 2

- `agents/script/*`
- `agents/voice/*`
- `agents/video_qc/*`

### Bloco 3

- `agents/strategy/*`
- `agents/account_health/*`

### Bloco 4

- `agents/trend_analysis/*`
- `agents/asset_selection/*`

### Bloco 5

- `capabilities/experiment/*`
- `agents/learning/*`
- smoke de integracao da Fase 2

---

## 11. Suite de Testes Obrigatoria

Arquivos obrigatorios:

- `tests/test_creative_orchestrator_phase2_unittest.py`
- `tests/test_trend_analysis_agent_phase2_unittest.py`
- `tests/test_strategy_agent_phase2_unittest.py`
- `tests/test_script_agent_phase2_unittest.py`
- `tests/test_voice_agent_phase2_unittest.py`
- `tests/test_asset_selection_agent_phase2_unittest.py`
- `tests/test_video_qc_agent_phase2_unittest.py`
- `tests/test_account_health_agent_phase2_unittest.py`
- `tests/test_learning_agent_phase2_unittest.py`
- `tests/test_experiment_capability_phase2_unittest.py`
- `tests/test_phase2_context_repository_unittest.py`
- `tests/test_phase2_smoke_integration_unittest.py`

Regra:

- nenhum modulo da Fase 2 entra sem teste correspondente

---

## 12. Criterio de Congelamento

O mapa da Fase 2 sera considerado congelado se:

- os diretorios acima forem mantidos
- os nomes dos contratos acima forem respeitados
- a persistencia passar pelo repositorio unico
- a Fase 2 nao invadir contratos da Fase 1

Mudancas nesses pontos depois do inicio da implementacao devem ser tratadas como alteracoes arquiteturais, nao como detalhe de codigo.

---

## 13. Conclusao

A especificacao da Fase 2 ja esta madura no nivel conceitual.

Este documento fecha o nivel que faltava para implementacao segura:

- onde cada coisa vive
- quais modulos existem
- quais contratos sao canonicos
- como a Fase 2 integra com a Fase 1

Com isso, a proxima etapa deixa de ser definicao e passa a ser execucao controlada.
