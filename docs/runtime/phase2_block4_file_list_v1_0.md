CortAI - Fase 2

Bloco 4 - File List

Documento: docs/runtime/phase2_block4_file_list_v1_0.md
Versao: 1.0
Status: Escopo congelado

---

## 1. Objetivo

Este documento define exatamente quais arquivos podem nascer no Bloco 4 da Fase 2.

O objetivo e evitar deriva entre:

- especificacao
- implementacao
- arquitetura existente

Somente os arquivos listados aqui podem ser criados.

---

## 2. Diretorios Permitidos

Somente os seguintes diretorios podem receber novos arquivos:

- `backend/app/creative/agents/learning/`
- `backend/app/creative/experiments/`
- `backend/data/learning/`
- `backend/data/experiments/`
- `tests/`

Nenhum outro diretorio pode ser criado ou modificado fora das integracoes minimas permitidas.

---

## 3. Arquivos a Criar

### 3.1 Learning / Optimization Agent

Diretorio:

- `backend/app/creative/agents/learning/`

Arquivos obrigatorios:

- `backend/app/creative/agents/learning/__init__.py`
- `backend/app/creative/agents/learning/models.py`
- `backend/app/creative/agents/learning/service.py`

Responsabilidade

O agente deve:

- ler dados de performance existentes
- gerar `learning_insights`
- fornecer recomendacoes estruturadas

---

### 3.2 Experiment Capability

Diretorio:

- `backend/app/creative/experiments/`

Arquivos obrigatorios:

- `backend/app/creative/experiments/__init__.py`
- `backend/app/creative/experiments/models.py`
- `backend/app/creative/experiments/service.py`

Responsabilidade

A capability deve:

- gerar `experiment_plan`
- estruturar variantes experimentais
- integrar com o fluxo cognitivo existente

---

## 4. Persistencia Permitida

Diretorios:

- `backend/data/learning/`
- `backend/data/experiments/`

Esses diretorios podem conter:

- `*.json`
- `*.jsonl`

Exemplos:

- `backend/data/learning/learning_insights.json`
- `backend/data/experiments/experiment_plan.json`

Nenhum banco novo deve ser introduzido neste bloco.

---

## 5. Testes Obrigatorios

Os seguintes testes devem ser criados:

- `tests/test_learning_agent_phase2_unittest.py`
- `tests/test_experiment_capability_phase2_unittest.py`
- `tests/test_phase2_block4_smoke_unittest.py`

---

## 6. Integracao Permitida

Alteracoes minimas sao permitidas apenas em:

- `backend/app/creative/orchestrator/service.py`
- `backend/app/creative/orchestrator/models.py`
- `backend/app/creative/contracts/creative_pack.py`

Essas alteracoes devem servir exclusivamente para:

- incluir `learning_insights`
- incluir `experiment_plan`

no `creative_pack`.

---

## 7. Integracoes Proibidas

Nao podem ser criados ou modificados:

- runtime
- scheduler
- safety layer
- publish_record
- metrics collector
- analysis layer
- simulation
- consistency
- pipeline da Fase 1

Tambem e proibido implementar:

- RAG
- scraping
- treinamento de modelo
- fine-tuning
- LoRA
- RL
- experiment agent autonomo complexo

---

## 8. Fallback Obrigatorio

### Learning Agent

Se nao houver dados suficientes:

- `learning_insights = DEFAULT`

O fluxo nunca deve falhar por ausencia de historico.

---

### Experiment Capability

Se nenhum experimento estiver configurado:

- `experiment_plan = DEFAULT`

O fluxo deve continuar normalmente.

---

## 9. Criterio de Conclusao do Bloco 4

O Bloco 4 sera considerado concluido quando:

- `Learning Agent` funcionar
- `Experiment Capability` funcionar
- `Creative Orchestrator` consumir ambos
- `creative_pack` incluir:
  - `learning_insights`
  - `experiment_plan`
- pipeline continuar funcionando
- testes passarem
- smoke passar
- nenhuma regressao da Fase 1
- nenhuma regressao dos Blocos 1, 2 ou 3

---

## 10. Arquivos que NAO devem nascer neste bloco

Explicitamente proibido criar:

- `learning_rag_service.py`
- `experiment_agent_full.py`
- `model_training_service.py`
- `data_scraper_service.py`
- `adaptive_optimizer.py`

Essas capacidades pertencem a fases futuras.

---

## 11. Ordem Esperada de Implementacao

1. `Learning Agent`
2. `Experiment Capability`
3. integracao minima com `Orchestrator`
4. atualizacao minima do `creative_pack`
5. testes unitarios
6. smoke do Bloco 4
7. regressoes dos blocos anteriores

---

## 12. Conclusao

Este documento congela o escopo tecnico do Bloco 4, garantindo que:

- a implementacao permaneca pequena
- o sistema continue auditavel
- a arquitetura da Fase 1 permaneca intacta
- a Fase 2 evolua incrementalmente

---

## Proximo passo natural

Apos criar este arquivo:

1. gerar o prompt de implementacao do Bloco 4
2. executar a implementacao controlada
3. rodar testes e smoke
4. checkpoint formal do Bloco 4
