CortAI - Lista de Arquivos do Bloco 3 da Fase 2

Trend Context and Visual Context

Versao: 1.0
Status: Congelado para Implementacao
Documento: `docs/runtime/phase2_block3_file_list_v1_0.md`

---

## 1. Objetivo do Documento

Este documento congela a lista exata de arquivos e modulos que podem nascer no Bloco 3 da Fase 2, evitando deriva de implementacao.

O Bloco 3 introduz apenas:

- `Trend Analysis Agent`
- `Asset Selection Agent`

Nenhum outro agente deve ser criado neste slice.

---

## 2. Diretorios Permitidos

Todos os arquivos novos devem nascer dentro de:

- `backend/app/creative/agents/`

Subdiretorios permitidos neste bloco:

- `backend/app/creative/agents/trend_analysis/`
- `backend/app/creative/agents/asset_selection/`

Nenhum outro diretorio novo deve ser criado neste bloco.

---

## 3. Arquivos Exatos a Criar

### 3.1 Trend Analysis Agent

Criar:

- `backend/app/creative/agents/trend_analysis/__init__.py`
- `backend/app/creative/agents/trend_analysis/models.py`
- `backend/app/creative/agents/trend_analysis/service.py`

#### `models.py`

Deve definir:

- `TrendAnalysisInput`
- `TrendProfile`
- `TrendAnalysisResult`

#### `service.py`

Deve implementar:

- `TrendAnalysisAgentService`

Responsabilidade:

- carregar `trend_profile` do nicho
- aplicar fallback para `DEFAULT`
- nao fazer scraping
- nao depender de API externa

### 3.2 Asset Selection Agent

Criar:

- `backend/app/creative/agents/asset_selection/__init__.py`
- `backend/app/creative/agents/asset_selection/models.py`
- `backend/app/creative/agents/asset_selection/service.py`

#### `models.py`

Deve definir:

- `AssetSelectionInput`
- `AssetSelection`
- `AssetSelectionResult`

#### `service.py`

Deve implementar:

- `AssetSelectionAgentService`

Responsabilidade:

- escolher `hook_background`
- escolher `setup_background`
- escolher `payoff_background`
- escolher `visual_style`
- escolher `motion_profile`
- aplicar fallback para selecao default

---

## 4. Arquivos de Teste Obrigatorios

Criar:

- `tests/test_trend_analysis_agent_phase2_unittest.py`
- `tests/test_asset_selection_agent_phase2_unittest.py`
- `tests/test_phase2_block3_smoke_unittest.py`

Responsabilidade:

- validar contratos minimos
- validar fallback
- validar integracao do `Creative Orchestrator` com ambos os agentes

---

## 5. Integracao Minima Permitida

Alteracoes minimas permitidas em:

- `backend/app/creative/orchestrator/service.py`
- `backend/app/creative/orchestrator/models.py`
- `backend/app/creative/contracts/creative_pack.py`

Objetivo da integracao:

- permitir que o `Creative Orchestrator` consuma `trend_profile`
- permitir que o `Creative Orchestrator` consuma `asset_selection`
- incluir ambos no `creative_pack`

Nenhuma outra alteracao estrutural e permitida.

---

## 6. Integracoes Proibidas

Nao e permitido criar neste bloco:

- `Learning Agent`
- `Experiment Agent` formal
- RAG
- scraping automatico
- storage novo fora do permitido
- qualquer mudanca estrutural na Fase 1
- qualquer alteracao estrutural dos Blocos 1 ou 2

Tambem nao e permitido:

- chamar runtime diretamente
- alterar `safety`
- alterar `publish_record`
- alterar `metrics`

---

## 7. Fallback Obrigatorio

### 7.1 Trend Analysis Agent

Se nao houver profile do nicho:

- `trend_profile = DEFAULT`

Regra:

- nunca interromper o fluxo por ausencia de trend profile

### 7.2 Asset Selection Agent

Se falhar a selecao contextual:

- `asset_selection = DEFAULT`

Regra:

- nunca interromper o fluxo criativo por ausencia de asset especializado
- o fallback deve continuar compatível com a baseline da Fase 1

---

## 8. Critério de Conclusao do Bloco 3

O Bloco 3 sera considerado concluido quando:

1. `trend_profile` for carregado ou cair em fallback controlado
2. `asset_selection` for gerado ou cair em fallback controlado
3. o `Creative Orchestrator` consumir ambos
4. o `creative_pack` incluir ambos
5. o pipeline continuar funcionando
6. smoke do Bloco 3 passar
7. regressao do Bloco 1 passar
8. regressao do Bloco 2 passar
9. regressao relevante da Fase 1 passar

---

## 9. Conclusao

Com esta lista, o Bloco 3 fica congelado como um slice pequeno, auditavel e controlado.

O objetivo e adicionar exatamente:

- contexto externo estruturado por nicho
- contexto visual coerente com a estrategia

Nada alem disso.
