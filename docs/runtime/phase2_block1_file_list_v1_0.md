CortAI - Lista de Arquivos da Primeira Entrega da Fase 2

Bloco 1

Versao: 1.0
Status: Congelado para Implementacao
Documento: `docs/runtime/phase2_block1_file_list_v1_0.md`

---

## 1. Objetivo

Este documento congela a lista exata de arquivos que devem existir na primeira entrega da Fase 2.

O Bloco 1 cobre apenas:

- Creative Orchestrator Service minimo
- Script Agent
- Voice Agent
- Video QC Agent

Este bloco nao deve antecipar:

- Trend Analysis Agent
- Strategy Agent
- Account Health Agent
- Learning Agent
- Experiment Capability formal
- Asset Selection Agent complexo

---

## 2. Regra de Escopo

O Bloco 1 existe para provar que a Fase 2 consegue:

- montar um `creative_pack` minimo
- decidir `script_plan`
- decidir `voice_plan`
- validar qualidade minima via `Video QC Agent`
- entregar a decisao para o pipeline da Fase 1 sem quebrar contratos existentes

Tudo que nao for necessario para esse fluxo fica fora do Bloco 1.

---

## 3. Arquivos a Criar no Bloco 1

### 3.1 Contratos

Criar:

- `backend/app/creative/__init__.py`
- `backend/app/creative/contracts/__init__.py`
- `backend/app/creative/contracts/creative_pack.py`
- `backend/app/creative/contracts/orchestrator_io.py`
- `backend/app/creative/contracts/agent_common.py`

Responsabilidade:

- congelar os contratos canonicos da primeira entrega

### 3.2 Orchestrator

Criar:

- `backend/app/creative/orchestrator/__init__.py`
- `backend/app/creative/orchestrator/models.py`
- `backend/app/creative/orchestrator/service.py`
- `backend/app/creative/orchestrator/events.py`

Responsabilidade:

- coordenar `Script Agent`, `Voice Agent` e `Video QC Agent`
- montar `CreativePack`
- aplicar fallback minimo
- emitir eventos `CREATIVE/*`

### 3.3 Script Agent

Criar:

- `backend/app/creative/agents/__init__.py`
- `backend/app/creative/agents/script/__init__.py`
- `backend/app/creative/agents/script/models.py`
- `backend/app/creative/agents/script/service.py`

Responsabilidade:

- produzir `ScriptPlan`
- gerar `hook/setup/payoff`
- usar contexto minimo do input

### 3.4 Voice Agent

Criar:

- `backend/app/creative/agents/voice/__init__.py`
- `backend/app/creative/agents/voice/models.py`
- `backend/app/creative/agents/voice/service.py`

Responsabilidade:

- produzir `VoicePlan`
- preferir provider premium quando configurado
- aplicar fallback explicito para `Piper`

### 3.5 Video QC Agent

Criar:

- `backend/app/creative/agents/video_qc/__init__.py`
- `backend/app/creative/agents/video_qc/models.py`
- `backend/app/creative/agents/video_qc/service.py`

Responsabilidade:

- validar qualidade minima do video apos render
- emitir `APPROVE` ou `REJECT`

### 3.6 Testes

Criar:

- `tests/test_creative_orchestrator_phase2_unittest.py`
- `tests/test_script_agent_phase2_unittest.py`
- `tests/test_voice_agent_phase2_unittest.py`
- `tests/test_video_qc_agent_phase2_unittest.py`
- `tests/test_phase2_block1_smoke_unittest.py`

Responsabilidade:

- travar contratos
- validar fallback
- validar integracao minima com a Fase 1

---

## 4. Arquivos que Nao Devem Ser Criados Ainda

Nao criar no Bloco 1:

- `backend/app/creative/context/repository.py`
- `backend/app/creative/context/file_store.py`
- `backend/app/creative/context/pg_store.py`
- `backend/app/creative/agents/trend_analysis/*`
- `backend/app/creative/agents/strategy/*`
- `backend/app/creative/agents/account_health/*`
- `backend/app/creative/agents/learning/*`
- `backend/app/creative/agents/asset_selection/*`
- `backend/app/creative/capabilities/experiment/*`
- testes desses modulos

Motivo:

- tudo isso pertence a blocos posteriores
- criar agora aumenta risco de deriva e acoplamento prematuro

---

## 5. Contratos Minimos por Arquivo

### 5.1 `creative_pack.py`

Deve definir:

- `CreativePack`
- `ScriptPlan`
- `VoicePlan`

Campos minimos:

- `creative_pack_id`
- `account_id`
- `niche`
- `topic`
- `script_plan`
- `voice_plan`
- `generated_at`
- `orchestrator_version`

### 5.2 `orchestrator_io.py`

Deve definir:

- `CreativeOrchestratorInput`
- `CreativeOrchestratorResult`

Campos minimos de input:

- `account_id`
- `niche`
- `topic`
- `publish_slot`

Campos minimos de result:

- `creative_pack`
- `fallbacks_used`
- `events_emitted`

### 5.3 `agent_common.py`

Deve definir:

- `AgentFailure`
- `FallbackDecision`

Enums minimos:

- `DecisionStatus`
- `FailureSeverity`

### 5.4 `script/models.py`

Deve definir:

- `ScriptAgentInput`
- `ScriptAgentResult`

### 5.5 `voice/models.py`

Deve definir:

- `VoiceAgentInput`
- `VoiceAgentResult`

### 5.6 `video_qc/models.py`

Deve definir:

- `VideoQcInput`
- `VideoQcResult`

Campos minimos:

- `status`
- `reasons`
- `checked_at`

---

## 6. Integracao Minima com a Fase 1

O Bloco 1 deve integrar sem alterar contratos existentes.

Fluxo minimo permitido:

```text
Creative Orchestrator
-> Content Pipeline (Fase 1)
-> Video QC Agent
-> Safety Layer
```

Regras:

- `Creative Orchestrator` nao escreve `publish_record`
- `Video QC Agent` roda antes do `Safety Layer`
- se `Video QC Agent` retornar `REJECT`, o fluxo para
- `Safety Layer` continua sendo a autoridade de risco

---

## 7. Criterio de Conclusao do Bloco 1

O Bloco 1 so pode ser considerado concluido se:

1. todos os arquivos desta lista existirem
2. nenhum arquivo fora do escopo tiver sido introduzido
3. os testes do Bloco 1 estiverem verdes
4. um smoke minimo provar:
   - `Creative Orchestrator`
   - `Script Agent`
   - `Voice Agent`
   - `Content Pipeline`
   - `Video QC Agent`
   - `Safety Layer`
5. a baseline da Fase 1 continuar verde

---

## 8. Conclusao

Com esta lista, a primeira entrega da Fase 2 deixa de ser ambigua.

O Bloco 1 fica congelado como um slice pequeno, auditavel e implementavel sem invadir os blocos seguintes.
