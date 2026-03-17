CortAI - Lista de Arquivos do Bloco 2 da Fase 2

Strategy and Account Health Layer

Versao: 1.0
Status: Congelado para Implementacao
Documento: `docs/runtime/phase2_block2_file_list_v1_0.md`

---

## 1. Objetivo do Documento

Este documento congela a lista exata de arquivos e modulos que podem nascer no Bloco 2 da Fase 2, evitando deriva de implementacao.

O Bloco 2 introduz apenas:

- `Strategy Agent`
- `Account Health Agent`

Nenhum outro agente deve ser criado neste slice.

---

## 2. Diretorios Permitidos

Todos os arquivos novos devem nascer dentro de:

- `backend/app/creative/agents/`

Subdiretorios permitidos neste bloco:

- `backend/app/creative/agents/strategy/`
- `backend/app/creative/agents/account_health/`

Nenhum outro diretorio novo deve ser criado neste bloco.

---

## 3. Arquivos a Criar

### 3.1 Strategy Agent

Criar:

- `backend/app/creative/agents/strategy/__init__.py`
- `backend/app/creative/agents/strategy/models.py`
- `backend/app/creative/agents/strategy/service.py`

#### `models.py`

Deve definir:

- `StrategyInput`
- `StrategyProfile`
- `StrategyResult`

#### `service.py`

Deve implementar:

- `StrategyAgentService`

Responsabilidade:

- gerar `strategy_profile`
- aplicar fallback minimo
- nao executar pipeline
- nao chamar runtime

### 3.2 Account Health Agent

Criar:

- `backend/app/creative/agents/account_health/__init__.py`
- `backend/app/creative/agents/account_health/models.py`
- `backend/app/creative/agents/account_health/service.py`

#### `models.py`

Deve definir:

- `AccountHealthInput`
- `AccountHealthStatus`
- `AccountHealthDecision`
- `AccountHealthResult`

#### `service.py`

Deve implementar:

- `AccountHealthAgentService`

Responsabilidade:

- gerar `health_status`
- produzir `reasons`
- produzir `recommended_constraints`
- aplicar fallback minimo

---

## 4. Arquivos de Teste Obrigatorios

Criar:

- `tests/test_strategy_agent_phase2_unittest.py`
- `tests/test_account_health_agent_phase2_unittest.py`
- `tests/test_phase2_block2_smoke_unittest.py`

Responsabilidade:

- validar contratos minimos
- validar fallback
- validar integracao do `Creative Orchestrator` com ambos os agentes
- validar comportamento de `HOLD`

---

## 5. Arquivos que Nao Devem Nascer Agora

Proibido criar neste bloco:

- `backend/app/creative/agents/trend_analysis/*`
- `backend/app/creative/agents/learning/*`
- `backend/app/creative/agents/asset_selection/*`
- `backend/app/creative/capabilities/experiment/*`
- `backend/app/creative/context/*`
- `backend/app/creative/rag/*`

Tambem e proibido:

- alterar a lista de arquivos do Bloco 1
- criar novos contratos canonicos fora do que ja foi congelado
- criar storage paralelo para a Fase 2

Esses itens pertencem a blocos posteriores.

---

## 6. Contratos Minimos por Arquivo

### 6.1 `strategy/models.py`

Deve definir:

- `StrategyInput`
- `StrategyProfile`
- `StrategyResult`

Campos minimos de `StrategyInput`:

- `account_id`
- `account_goal`
- `recent_metrics_summary`
- `health_status`
- `recommended_constraints`

Campos minimos de `StrategyProfile`:

- `goal`
- `content_mode`
- `hook_aggressiveness`
- `target_duration_range`
- `variation_policy`

### 6.2 `account_health/models.py`

Deve definir:

- `AccountHealthInput`
- `AccountHealthStatus`
- `AccountHealthDecision`
- `AccountHealthResult`

Campos minimos de `AccountHealthInput`:

- `account_id`
- `recent_publish_count`
- `recent_format_repetition_ratio`
- `recent_views_drop_ratio`
- `recent_low_performance_streak`

Campos minimos de `AccountHealthDecision`:

- `status`
- `reasons`
- `recommended_constraints`

Valores validos de `AccountHealthStatus`:

- `SAFE`
- `CAUTION`
- `HOLD`

---

## 7. Integracao Permitida com Bloco 1

`Strategy Agent` e `Account Health Agent` podem ser utilizados apenas pelo:

- `Creative Orchestrator Service`

Fluxo permitido:

```text
Account Health Agent
-> Strategy Agent
-> Creative Orchestrator
-> Script Agent
-> Voice Agent
-> Content Pipeline
-> Video QC
```

Regra:

- `Creative Orchestrator` continua sendo o ponto central da camada cognitiva
- os agentes do Bloco 2 nao chamam agentes do Bloco 1 diretamente

---

## 8. Integracao Proibida

Nao e permitido neste bloco:

- chamar runtime diretamente
- alterar safety
- alterar `publish_record`
- alterar `metrics`
- alterar o pipeline da Fase 1 fora do ponto minimo de integracao no `Creative Orchestrator`
- escrever diretamente em storage operacional da Fase 1

---

## 9. Fallback Obrigatorio

### 9.1 Strategy Agent

Fallback minimo:

- `strategy_profile = DEFAULT`

Exemplo minimo:

- `goal = retention`
- `content_mode = standard`
- `hook_aggressiveness = medium`
- `target_duration_range = 8-12s`
- `variation_policy = low`

Regra:

- o `Strategy Agent` nunca pode retornar perfil vazio

### 9.2 Account Health Agent

Fallback minimo:

- `health_status = SAFE`
- `reasons = ["fallback_default"]`
- `recommended_constraints = {}`

Regra:

- fallback nunca deve bloquear publicacao
- `HOLD` nao pode ser emitido por fallback

---

## 10. Criterio de Conclusao do Bloco 2

O Bloco 2 e considerado concluido quando:

1. `Strategy Agent` gera `strategy_profile`
2. `Account Health Agent` gera `health_status`
3. `Creative Orchestrator` consome ambos
4. o fluxo completo continua funcionando
5. `HOLD` impede o fluxo criativo
6. testes passam
7. smoke passa
8. nenhuma regressao da Fase 1 e do Bloco 1 e detectada

---

## 11. Conclusao

Com esta lista, o Bloco 2 fica congelado como um slice pequeno, auditavel e controlado.

O objetivo nao e ampliar a Fase 2 inteira, mas adicionar exatamente a primeira camada de decisao por conta:

- saude da conta
- estrategia por conta

Nada alem disso.
