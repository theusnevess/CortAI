CortAI - Fase 2

Bloco 4 - Learning & Experiment Control

Documento: `docs/runtime/phase2_block4_definition_v1_0.md`
Versao: 1.0
Status: Aprovado para Implementacao (escopo congelado)

---

## 1. Objetivo do Bloco 4

O Bloco 4 introduz a primeira capacidade real de adaptacao orientada por dados dentro da camada cognitiva do CortAI.

Ate o Bloco 3, o sistema ja possui:

- controle de qualidade do video
- geracao de script
- selecao de voz
- estrategia por conta
- health por conta
- contexto de tendencias
- contexto visual

O Bloco 4 adiciona duas capacidades:

1. `Learning / Optimization Agent`
2. formalizacao da `Experiment Capability`

O objetivo nao e treinar modelos nem implementar aprendizado pesado.
O objetivo e permitir que o sistema:

- leia sinais relevantes de performance
- gere recomendacoes estruturadas
- formalize variantes de experimento de forma canonica
- alimente os agentes ja existentes com contexto de otimizacao

---

## 2. Escopo Estrito do Bloco 4

O Bloco 4 implementa apenas:

- `Learning / Optimization Agent`
- formalizacao da `Experiment Capability`

Nada alem disso.

---

## 3. Escopo Proibido

Nao fazem parte do Bloco 4:

- RAG
- scraping automatizado
- fine-tuning
- LoRA
- RL
- treinamento de modelo
- agent framework generico
- `Experiment Agent` separado/autonomo alem do necessario
- alteracao estrutural da Fase 1
- alteracao estrutural dos Blocos 1, 2 ou 3 fora da integracao minima permitida

O Bloco 4 nao implementa aprendizado de pesos de modelo.
Ele implementa aprendizado estrategico e operacional leve.

---

## 4. Arquitetura do Bloco 4

Apos o Bloco 4, o fluxo cognitivo passa a ser:

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

---

## 5. Learning / Optimization Agent

### Objetivo

Ler dados de performance ja existentes no sistema e produzir recomendacoes estruturadas para melhorar os proximos batches.

### Fontes permitidas

O agente pode ler apenas fontes ja existentes e aprovadas:

- `publish_records`
- `video_metrics`
- outputs de `analysis`
- outputs de `attribution`
- resultados de experimentos ja registrados
- `strategy profiles` recentes
- `qc history`

### O que ele produz

O agente gera um objeto como:

- `learning_insights`

Exemplos de conteudo:

- hooks que performaram melhor
- duracao mais eficiente
- tipos de visual mais fortes
- vozes que performaram melhor
- sinais de saturacao
- recomendacoes de variacao

### Exemplos de recomendacao

- preferir hook tipo `question`
- reduzir duracao para `35-45s`
- evitar `visual_style X` em conta `Y`
- aumentar agressividade do hook em conta `Z`
- diminuir repeticao de background

### Papel arquitetural

O agente nao altera diretamente outros agentes.
Ele apenas produz recomendacoes estruturadas e auditaveis.

Essas recomendacoes sao consumidas por:

- `Strategy Agent`
- `Script Agent`
- `Asset Selection Agent`
- `Voice Agent`

### Fallback obrigatorio

Se nao houver dados suficientes:

- `learning_insights = DEFAULT`

Nunca falhar o fluxo por ausencia de historico.

---

## 6. Experiment Capability

### Objetivo

Formalizar a variacao experimental ja prevista na arquitetura.

No Bloco 4, isso continua sendo uma capability, nao um agente autonomo completo.

### Papel

Permitir que o sistema produza variantes controladas, por exemplo:

- `hook A / hook B`
- duracao curta / media
- `visual_style A / visual_style B`
- `voice style A / voice style B`

### Base tecnica

A `Experiment Capability` deve usar o `D31 Experiment Framework` ja existente na Fase 1.

### Resultado esperado

A capability deve produzir um objeto como:

- `experiment_plan`

Exemplo:

- `experiment_id`
- `variant_id`
- `variant_type`
- `variant_params`

### Integracao

O `experiment_plan` deve ser consumido por:

- `Strategy Agent`
- `Script Agent`
- `Asset Selection Agent`
- `Voice Agent`

### Limite do Bloco 4

O Bloco 4 nao cria um `Experiment Agent` superautonomo.

Ele apenas:

- formaliza o plano experimental
- padroniza a estrutura de variantes
- injeta esse contexto no fluxo cognitivo

---

## 7. Integracao com Creative Orchestrator

O `Creative Orchestrator` passa a consumir:

- `learning_insights`
- `experiment_plan`

E incluir ambos no `creative_pack`.

---

## 8. Persistencia

O Bloco 4 utiliza persistencia simples e auditavel.

### Learning insights

Exemplo de local:

- `backend/data/learning/`

### Experiment plans

Exemplo de local:

- `backend/data/experiments/`

A persistencia principal pode continuar apoiada em storage ja existente, com backup em JSON/JSONL.

---

## 9. Eventos Cognitivos

Eventos minimos introduzidos:

- `LEARNING_INSIGHTS_GENERATED`
- `LEARNING_INSIGHTS_FALLBACK`
- `EXPERIMENT_PLAN_GENERATED`
- `EXPERIMENT_PLAN_FALLBACK`

Esses eventos devem ser emitidos pelo `Creative Orchestrator`.

---

## 10. Testes Obrigatorios

Devem ser criados testes para:

- `Learning / Optimization Agent`
- `Experiment Capability`
- smoke do Bloco 4

Arquivos esperados:

- `tests/test_learning_agent_phase2_unittest.py`
- `tests/test_experiment_capability_phase2_unittest.py`
- `tests/test_phase2_block4_smoke_unittest.py`

---

## 11. Smoke do Bloco 4

Fluxo minimo esperado:

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
-> Content Pipeline
-> Video QC
```

Resultado esperado:

- `learning_insights_generated = true`
- `experiment_plan_generated = true`
- `pipeline_status = READY`
- `video_qc_status = APPROVE`

---

## 12. Criterio de Conclusao do Bloco 4

O Bloco 4 sera considerado concluido quando:

- `Learning / Optimization Agent` funcionar
- `Experiment Capability` funcionar
- `Creative Orchestrator` consumir ambos
- `creative_pack` incluir `learning_insights` e `experiment_plan`
- pipeline continuar funcionando
- testes passarem
- smoke passar
- nenhuma regressao da Fase 1
- nenhuma regressao dos Blocos 1, 2 ou 3

---

## 13. Resultado Esperado do Bloco 4

Apos a conclusao do Bloco 4, o CortAI passa a operar com:

- contexto de saude da conta
- contexto estrategico
- contexto de tendencia
- contexto visual
- contexto de aprendizado
- variacao experimental formalizada

Esse e o primeiro ponto em que o sistema comeca a se tornar adaptativo de forma explicita, ainda sem depender de treinamento pesado ou RAG.

---

## 14. Estado da Fase 2 apos Bloco 4

### Bloco 1

- `Creative Orchestrator`
- `Script Agent`
- `Voice Agent`
- `Video QC`

### Bloco 2

- `Strategy Agent`
- `Account Health Agent`

### Bloco 3

- `Trend Analysis Agent`
- `Asset Selection Agent`

### Bloco 4

- `Learning / Optimization Agent`
- `Experiment Capability` formalizada

---

## 15. Conclusao

O Bloco 4 encerra a primeira versao completa da camada cognitiva adaptativa leve do CortAI.

Ele nao transforma o sistema em um modelo treinado autonomamente, mas cria a base para:

- ajuste estrategico por dados
- controle formal de variantes
- evolucao incremental do conteudo

Esse e o limite correto para a Fase 2, mantendo o sistema modular, auditavel e compativel com a infraestrutura da Fase 1.
