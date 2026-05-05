# Legacy Operations And Product Specs

Archived reference for old scattered operations, observability, product, analytics, integration and UI docs.

## Consolidation Notice

This file consolidates documentation that was previously split across multiple legacy files. The source contents are preserved below for auditability.

## Source Files

- `docs/analysis/analysis_research_layer_v1_0.md`
- `docs/analysis/data_consistency_checker_v1_0.md`
- `docs/analytics/content_performance_attribution_v1_0.md`
- `docs/arquitecture layers/ARCHITECTURE_FREEZE.md`
- `docs/arquitecture layers/CHECKLIST.md`
- `docs/arquitecture layers/CORE_LOCK.md`
- `docs/arquitecture layers/EXECUTOR_LAYER.md`
- `docs/arquitecture layers/EXTENSION_MAP.md`
- `docs/arquitecture layers/OBSERVER_LAYER.md`
- `docs/arquitecture layers/PLANNER_LAYER.md`
- `docs/arquitecture layers/TEST_CASES.md`
- `docs/arquitecture layers/TEST_STRATEGY.md`
- `docs/arquitecture layers/VALIDATION_CHECKLIST.md`
- `docs/audit/release_audit_gate_d27_d33_v1_0.md`
- `docs/cognitive/ACTION.md`
- `docs/cognitive/AGENT_REGISTRY.md`
- `docs/cognitive/COGNITIVE_LOOP.md`
- `docs/cognitive/DECISION.md`
- `docs/cognitive/EVENT_LOG.md`
- `docs/cognitive/EXECUTOR.md`
- `docs/cognitive/INDEX.md`
- `docs/cognitive/OBSERVATION.MD`
- `docs/cognitive/OUTCOME.md`
- `docs/cognitive/PIPELINE_PHASE.md`
- `docs/cognitive/STATE.md`
- `docs/cognitive/STATE_SNAPSHOT.md`
- `docs/concurrency/concurrency_failure_matrix_v1_0.md`
- `docs/concurrency/d12_concurrency_hardening_v1_0.md`
- `docs/concurrency/op_key_catalog_v1_0.md`
- `docs/content/content_template_library_v1_0.md`
- `docs/content/creative_pack_generator_v1_0.md`
- `docs/d3_go_nogo_checklist.md`
- `docs/data/publish_record_v1.md`
- `docs/experiments/experiment_framework_v1_0.md`
- `docs/integration/external_platform_integration_v1_0.md`
- `docs/intelligence/platform_intelligence_v1_0.md`
- `docs/metrics/metrics_collector_v1_0.md`
- `docs/observability.md`
- `docs/observability/event_append_v1_0.md`
- `docs/observability/event_index_v1_0.md`
- `docs/observability/event_query_forensics_v1_0.md`
- `docs/observability/hot_storage_v1_0.md`
- `docs/observability/seek_cursor_encoding_v1_0.md`
- `docs/ops/slo_alerting_v1_0.md`
- `docs/p2_results.md`
- `docs/perf/load_testing_v1_0.md`
- `docs/pipeline/window_post_pipeline_v1_0.md`
- `docs/pr_checklist_observability.md`
- `docs/pr_p1_closed_p2_start.md`
- `docs/product/content_attribution_v1_0.md`
- `docs/product/strategy_learning_v1_0.md`
- `docs/product/strategy_patch_application_v1_0.md`
- `docs/roadmap_v2.md`
- `docs/runbook_operacional_v1.8.1.md`
- `docs/runbook_operacional_v1.8.2.md`
- `docs/simulation/offline_simulation_engine_v1_0.md`
- `docs/ui/operator_actions_v1_0.md`
- `docs/ui/operator_console_v1_0.md`
- `docs/ui/strategy_observatory_v1_0.md`
- `docs/versioning.md`

## Consolidated Contents

---

## Source: `docs/analysis/analysis_research_layer_v1_0.md`

# CortAI - Analysis and Research Layer

Versao: `v1.0`
Aplica-se a: `CortAI >= D33`
Stage: `D34`

## Objetivo

Transformar artefatos ja produzidos pelo CortAI em sumarios uteis para decisao rapida apos o piloto, sem alterar o comportamento do sistema.

O D34 existe para reduzir o tempo entre:

- dado bruto
- insight consolidado
- decisao operacional ou estrategica

## Principios

- somente leitura
- somente agregacao deterministica
- inputs append-only
- outputs derivados
- nenhuma mutacao em `publish`, `safety`, `scheduler`, `metrics collector` ou `rollout`

## Fontes de dados

O D34 consome apenas artefatos ja existentes no sistema.

### Publish

- `publish_records`

### Metrics

- `video_metrics`

### Experiments

- `experiments`
- `experiment_assignments`
- `experiment_results`

### Attribution

- `hook_performance`
- `structure_performance`
- `duration_analysis`
- `pattern_performance`

### Intelligence

- `publish_windows`
- `pacing_profiles`
- `risk_profiles`
- `account_health`

### Safety

- `SAFETY/*` events
- cooldown history
- pacing delay history

## Saidas do D34

O D34 gera quatro sumarios principais.

### 1. Pilot Metrics Summary

Arquivo:

- `OUT/analysis/pilot_metrics_summary.json`

Responsabilidade:

- consolidar metricas gerais do piloto
- resumir desempenho por conta
- resumir desempenho por janela

Campos minimos esperados:

- `generated_at`
- `pilot_scope`
- `total_publish_records`
- `total_metrics_records`
- `accounts[]`
- `aggregate_views`
- `aggregate_watch_time`
- `aggregate_completion_rate`
- `aggregate_avg_watch_time`

### 2. Experiment Winners

Arquivo:

- `OUT/analysis/experiment_winners.json`

Responsabilidade:

- comparar variantes A/B
- apontar winner provisório por experimento
- registrar quando nao ha sinal suficiente

Campos minimos esperados:

- `generated_at`
- `experiments[]`
  - `experiment_id`
  - `scope`
  - `variant_a`
  - `variant_b`
  - `winner`
  - `winner_reason`
  - `confidence`
  - `evidence_count`

### 3. Hook Performance Summary

Arquivo:

- `OUT/analysis/hook_performance_summary.json`

Responsabilidade:

- consolidar performance por hook
- consolidar performance por estrutura
- consolidar performance por duracao

Campos minimos esperados:

- `generated_at`
- `hooks[]`
- `structures[]`
- `durations[]`
- `top_hook`
- `top_structure`
- `preferred_duration`

### 4. Account Health Summary

Arquivo:

- `OUT/analysis/account_health_summary.json`

Responsabilidade:

- consolidar saude operacional por conta
- resumir delays, cooldowns e risco
- indicar conta saudavel vs conta em observacao

Campos minimos esperados:

- `generated_at`
- `accounts[]`
  - `account_id`
  - `health_status`
  - `risk_level`
  - `cooldown_active`
  - `cooldown_count`
  - `pacing_delay_count`
  - `publish_block_count`
  - `notes[]`

## Regras de agregacao

### Determinismo

Mesma entrada logica deve produzir a mesma saida logica.

Isso implica:

- ordenacao estavel
- serializacao estavel
- ausencia de RNG
- ausencia de timestamp dinamico fora de `generated_at`

### Read-only

O D34 nunca deve:

- criar `publish_record`
- alterar estado de safety
- alterar scheduler
- alterar assignments de experimento
- alterar patch ou estrategia

### Tolerancia a dados incompletos

Se algum input estiver ausente:

- gerar sumario parcial ou vazio
- nao quebrar a execucao inteira
- explicitar ausencia de evidencia quando necessario

### Sem side effects no runtime

O D34 nao participa do caminho critico de execucao.

Ele opera fora de:

- `publish.py`
- `safety_gate.py`
- `scheduler`
- `worker execution`
- `metrics collector`

## Relacao com modulos existentes

### D30 - Platform Intelligence

O D34 le os outputs de inteligencia para:

- resumir janelas recomendadas
- resumir pacing recomendado
- resumir risco por conta

### D31 - Experiment Framework

O D34 usa assignments e resultados para:

- comparar A/B
- apontar winner provisório
- registrar experimentos sem sinal suficiente

### D32 - Advanced Attribution

O D34 usa attribution para:

- resumir hook vencedor
- resumir estrutura mais eficaz
- resumir duracao preferivel

### D26 - Strategy Observatory

O D34 gera outputs de analise que ajudam leitura operacional e estrategica, mas nao substitui o observatorio.

## Persistencia

A persistencia do D34 e em JSON derivado, sobrescrevivel por execucao do proprio sumario.

Diretorio:

- `OUT/analysis/`

Arquivos:

- `pilot_metrics_summary.json`
- `experiment_winners.json`
- `hook_performance_summary.json`
- `account_health_summary.json`

Observacao:

- os inputs seguem append-only
- os outputs do D34 sao snapshots derivados e reexecutaveis

## Casos de uso

Apos o piloto, o operador deve conseguir responder rapidamente:

- qual conta esta mais saudavel
- qual variante esta ganhando
- qual hook esta performando melhor
- qual estrutura segurou mais watch time
- qual faixa de duracao parece preferivel

## Fora de escopo

O D34 nao inclui:

- mutacao de pipeline
- winner selection automatica com rollout automatico
- engine estatistico avancado
- dashboard novo
- mudancas em `publish`, `safety`, `scheduler`, `rollout` ou `collector`

## Resultado esperado

Apos o D34, o CortAI ganha uma camada de analise e pesquisa que converte artefatos brutos em sumarios operacionais e estrategicos utilizaveis.


---

## Source: `docs/analysis/data_consistency_checker_v1_0.md`

# Data Consistency Checker v1.0

## Scope

`D38 â€” Data Consistency Checker v1.0` adiciona uma camada read-only para validar integridade entre os artefatos do piloto e do learning loop.

O checker existe para responder apenas:

- os artefatos estao consistentes?
- se nao estiverem, onde esta a quebra?

## Goals

- detectar inconsistencias silenciosas antes e durante o piloto
- gerar saida objetiva `OK / FAIL`
- expor contagens claras por check
- nao modificar nenhum artefato existente

## Out of Scope

- nenhum auto-fix
- nenhum fallback magico
- nenhuma mutacao de dados
- nenhuma alteracao em:
  - `publish`
  - `safety`
  - `scheduler`
  - `metrics collector`
  - `rollout`

## Inputs

Fontes de dados lidas:

- `publish_records`
- `video_metrics`
- `experiments`
- `experiment assignments`
- `experiment results`
- `creative_packs`
- artefatos de `analysis`

## Checks

Checks minimos do v1.0:

1. todo `publish_record` esperado tem `video_metrics`
2. todo `video_metrics` referencia `publish_record` existente
3. todo `experiment assignment` referencia experimento existente
4. todo resultado de experimento referencia assignment existente
5. todo `creative_pack_id` usado em `publish_record.metadata` existe
6. todo artefato de `analysis` e derivavel dos inputs presentes

## Output Files

Saidas derivadas:

- `OUT/analysis/consistency_check.json`
- `OUT/analysis/consistency_check.md`

## Output Contract

Modelo minimo:

- `status: OK | FAIL`
- `generated_at`
- `checks`
- `summary_counts`

Cada item em `checks` deve conter, no minimo:

- `check_id`
- `status`
- `expected`
- `found`
- `missing_count`
- `notes`

## Rules

- somente leitura
- mesma entrada produz a mesma saida funcional
- diferencas aceitas apenas em `generated_at`
- falhas devem ser explicitas e contaveis
- ausencia parcial de dados deve gerar `FAIL` ou resultado vazio coerente, nunca reparo silencioso

## OK / FAIL Semantics

`OK`:

- todos os checks executados passaram
- nenhuma referencia critica ausente

`FAIL`:

- pelo menos um check falhou
- a saida deve indicar claramente qual relacao esta inconsistente

## Operator Usage

O checker deve ser seguro para uso:

- antes do piloto
- durante as primeiras 12h
- ao final das 72h

## Invariants

- sem side effects
- sem escrita fora de `OUT/analysis/`
- sem alterar inputs append-only
- sem dependencia de servicos externos


---

## Source: `docs/analytics/content_performance_attribution_v1_0.md`

# D32 - Advanced Content Performance Attribution v1.0

## Objetivo

Atribuir performance granular aos elementos do conteudo para explicar por que um video performa melhor ou pior.

Entidades analisadas:
- hook
- estrutura narrativa
- duracao
- padrao de conteudo

## Inputs

- `OUT/data/publish_records/publish_records.jsonl`
- `OUT/data/video_metrics/video_metrics.jsonl`
- `OUT/content/creative_packs/creative_packs.jsonl`
- `OUT/experiments/assignments.jsonl`

## Outputs

Persistencia em `OUT/attribution/`:
- `hook_performance.jsonl`
- `structure_performance.jsonl`
- `duration_analysis.jsonl`
- `pattern_performance.jsonl`

## Entidades de saida

### HookPerformance

- `hook_performance_id`
- `account_id`
- `publish_id`
- `creative_pack_id`
- `hook_key`
- `hook_type`
- `views`
- `completion_rate`
- `watch_3s_rate`
- `experiment_variant`
- `generated_at`

### StructurePerformance

- `structure_performance_id`
- `account_id`
- `publish_id`
- `creative_pack_id`
- `structure_key`
- `views`
- `completion_rate`
- `experiment_variant`
- `generated_at`

### DurationAnalysis

- `duration_analysis_id`
- `account_id`
- `publish_id`
- `creative_pack_id`
- `duration_s`
- `duration_bucket`
- `completion_rate`
- `dropoff_point`
- `generated_at`

### PatternPerformance

- `pattern_performance_id`
- `account_id`
- `publish_id`
- `creative_pack_id`
- `pattern_key`
- `views`
- `completion_rate`
- `experiment_variant`
- `generated_at`

## Regras

- analise deterministica
- append-only
- recomputacao identica -> `NOOP`
- payload diferente para a mesma chave -> `CONFLICT`
- nenhuma mutacao do pipeline

## Heuristicas v1.0

### Hook type

- `QUESTION`: hook termina ou contem `?`
- `LISTICLE`: hook contem numero inicial
- `CURIOSITY`: hook contem `por que`, `o que`, `como`
- `STATEMENT`: fallback

### Structure key

Derivada dos blocos presentes no `script_skeleton`, por exemplo:

`HOOK>SETUP>ANGLE>PAYOFF>CTA`

### Duration

Fonte preferencial:
- `publish_record.metadata.duration_s`
- fallback: `publish_record.metadata.effective_duration_s`
- fallback: `0`

Buckets:
- `SHORT` <= 30s
- `MEDIUM` <= 60s
- `LONG` > 60s

### Pattern key

- `FACT_LIST`
- `CURIOSITY_ARC`
- `STORY_BREAKDOWN`
- `GENERAL`

## Integracao

Consome:
- D29 (`creative_packs`)
- D31 (`experiment_assignments`)

Alimenta:
- D26 (observability)
- D30 (intelligence)
- Strategy Learning / analise manual

## Criterio de aceite

O D32 fecha se:
- analise de hook funciona
- analise de estrutura funciona
- analise de duracao funciona
- persistencia append-only funciona
- recomputacao eh deterministica
- assignment de experimento eh refletido quando presente


---

## Source: `docs/arquitecture layers/ARCHITECTURE_FREEZE.md`

# ðŸ”’ ARCHITECTURE_FREEZE.md

**Congelamento CanÃ´nico da Arquitetura**

---

## 1. PropÃ³sito

Este documento declara o **congelamento formal** da arquitetura do sistema, estabelecendo um **baseline imutÃ¡vel** para desenvolvimento, auditoria e evoluÃ§Ã£o controlada.

A partir deste ponto, **nenhuma alteraÃ§Ã£o estrutural** Ã© permitida sem um processo explÃ­cito de descongelamento.

---

## 2. Escopo do Congelamento

O congelamento aplica-se a **contratos, limites e invariantes**, nÃ£o a implementaÃ§Ãµes internas que **nÃ£o violem** tais contratos.

### Camadas Congeladas

* `CORTAI_CORE.md`
* `OBSERVER_LAYER.md`
* `EXECUTOR_LAYER.md`
* `PLANNER_LAYER.md`

Todos os documentos acima passam a ser considerados **canÃ´nicos**.

---

## 3. Invariantes Globais Congelados

A partir deste freeze, tornam-se invariantes globais:

* Append-only como princÃ­pio de persistÃªncia
* SeparaÃ§Ã£o estrita entre:

  * ObservaÃ§Ã£o
  * CogniÃ§Ã£o
  * Planejamento
  * ExecuÃ§Ã£o
* AusÃªncia de aprendizado implÃ­cito
* Determinismo por contrato
* Auditoria total por histÃ³rico

Nenhuma camada pode violar o papel das demais.

---

## 4. Limites de Responsabilidade (Resumo)

### Observer Layer

* Observa o mundo externo
* NÃ£o decide
* NÃ£o executa

### Cognitive Core

* Registra State, Decision e Outcome
* NÃ£o observa diretamente
* NÃ£o executa

### Planner Layer

* Estrutura possibilidades
* NÃ£o decide
* NÃ£o executa

### Executor Layer

* Executa comandos explÃ­citos
* NÃ£o decide
* NÃ£o planeja

---

## 5. Artefatos Persistentes Reconhecidos

Os seguintes artefatos sÃ£o reconhecidos como vÃ¡lidos neste freeze:

* `storage/audit_log.jsonl`
* `storage/process_id.txt`

Nenhum novo artefato persistente Ã© permitido sem autorizaÃ§Ã£o explÃ­cita.

---

## 6. O que NÃƒO pode mudar sem Descongelamento

* Estrutura dos contratos
* PapÃ©is das camadas
* Invariantes descritos
* Fluxo entre camadas
* SemÃ¢ntica de State / Decision / Outcome

---

## 7. O que PODE evoluir sob o Freeze

* ImplementaÃ§Ãµes internas
* OtimizaÃ§Ãµes que nÃ£o alterem semÃ¢ntica
* Testes
* DocumentaÃ§Ã£o explicativa adicional

âš ï¸ Desde que **nenhum contrato seja violado**.

---

## 8. Processo de Descongelamento (Futuro)

Qualquer mudanÃ§a estrutural exigirÃ¡:

1. Documento explÃ­cito de descongelamento
2. Justificativa tÃ©cnica
3. Impacto sobre invariantes
4. Nova versÃ£o de contrato

Sem exceÃ§Ãµes.

---

## 9. Status

* âœ… Arquitetura congelada
* âœ… Contratos vÃ¡lidos
* âœ… Sistema auditÃ¡vel
* âœ… EvoluÃ§Ã£o apenas controlada

---

## 10. PrincÃ­pio Final

> **Arquitetura congelada nÃ£o Ã© arquitetura morta.**
> Ã‰ arquitetura **confiÃ¡vel**.

---

ðŸ“Œ **Fim do ARCHITECTURE_FREEZE.md**


---

## Source: `docs/arquitecture layers/CHECKLIST.md`

# Checklist de Progresso â€” CortAI

Este documento registra **tudo que jÃ¡ foi concluÃ­do** e **tudo que ainda falta**, em ordem lÃ³gica e arquitetural.

---

## âœ… ConcluÃ­do

### NÃºcleo Cognitivo

* [x] DefiniÃ§Ã£o completa do `CORTAI_CORE.md`
* [x] ImplementaÃ§Ã£o dos Loops 1â€“4
* [x] PersistÃªncia append-only (`audit_log.jsonl`)
* [x] Identidade persistente de processo (`process_id.txt`)
* [x] Congelamento formal do Core

### Contratos Arquiteturais

* [x] `OBSERVER_LAYER.md` (contrato mÃ­nimo)
* [x] `EXECUTOR_LAYER.md` (contrato mÃ­nimo)
* [x] `PLANNER_LAYER.md` (contrato mÃ­nimo)
* [x] `ARCHITECTURE_FREEZE.md`

### GovernanÃ§a e Qualidade

* [x] `TEST_STRATEGY.md`
* [x] `EXTENSION_MAP.md`
* [x] Checklist de validaÃ§Ã£o manual

### OrganizaÃ§Ã£o

* [x] Estrutura de pastas definida
* [x] SeparaÃ§Ã£o clara entre core e extensÃµes
* [x] README.md reescrito e alinhado Ã  arquitetura

---

## â³ Pendente (ordem recomendada)

### Ambiente

* [ ] Configurar chat no VS Code
* [ ] Validar fluxo de interaÃ§Ã£o local (sem observaÃ§Ã£o real)

### ObservaÃ§Ã£o

* [ ] Implementar Observer sintÃ©tico simples
* [ ] Validar emissÃ£o de eventos conforme contrato
* [ ] Garantir ausÃªncia de lÃ³gica no Observer

### ExecuÃ§Ã£o

* [ ] Implementar Executor mock
* [ ] Validar recebimento de `Decision`
* [ ] Garantir efeitos controlados e auditÃ¡veis

### Planejamento (opcional / futuro)

* [ ] Criar Planner noop
* [ ] Validar encadeamento sem alterar core

### IntegraÃ§Ã£o

* [ ] Rodar ciclos completos ponta a ponta
* [ ] Inspecionar audit_log manualmente
* [ ] Validar rastreabilidade total

---

## âŒ Explicitamente Fora de Escopo (por enquanto)

* InteligÃªncia adaptativa
* Aprendizado automÃ¡tico
* OtimizaÃ§Ã£o de decisÃµes
* AlteraÃ§Ãµes no Cognitive Core

---

## ðŸ§Š Regra de Ouro

Se algo **nÃ£o estÃ¡ no checklist**, nÃ£o deve ser feito.

Qualquer novo item exige revisÃ£o arquitetural antes de execuÃ§Ã£o.


---

## Source: `docs/arquitecture layers/CORE_LOCK.md`

# CORE LOCK â€” NÃºcleo Cognitivo Congelado

Este arquivo declara o **congelamento formal e definitivo** do nÃºcleo cognitivo do projeto **CortAI**.

---

## 1. Escopo do NÃºcleo Congelado

O nÃºcleo cognitivo Ã© composto **exclusivamente** pelos seguintes elementos, conforme definidos no `CORTAI_CORE.md` e seus apÃªndices tÃ©cnicos:

- Loop 1 â€” Ciclo Cognitivo BÃ¡sico
- Loop 2 â€” Continuidade Temporal
- Loop 3 â€” Continuidade Causal Referencial
- Loop 4 â€” Identidade de Processo Persistente

Implementados principalmente no arquivo:

backend/app/cognitive_core.py

E nos artefatos persistentes:

E nos artefatos persistentes:


---

## 2. Invariantes Absolutos (ImutÃ¡veis)

A partir deste ponto, **NENHUMA** modificaÃ§Ã£o futura pode:

- Alterar as estruturas `State`, `Decision` ou `Outcome`
- Alterar o fluxo `State â†’ Decision â†’ Outcome`
- Alterar os identificadores (`state_id`, `decision_id`, `outcome_id`, `process_id`)
- Alterar o mecanismo de persistÃªncia (append-only, JSONL)
- Alterar a identidade persistente de processo
- Introduzir inteligÃªncia, heurÃ­stica, aprendizado ou inferÃªncia no nÃºcleo
- Criar dependÃªncias externas dentro do nÃºcleo

---

## 3. Regra de EvoluÃ§Ã£o do Sistema

Toda evoluÃ§Ã£o futura do projeto **CortAI** deve ocorrer **fora do nÃºcleo cognitivo**, obedecendo Ã s seguintes regras:

- O nÃºcleo **somente emite eventos**
- Camadas superiores **somente leem** os artefatos do nÃºcleo
- Nenhuma camada externa pode:
  - Modificar o nÃºcleo
  - Interromper ciclos
  - Injetar decisÃµes
  - Reescrever estados

O nÃºcleo passa a ser tratado como **infraestrutura cognitiva imutÃ¡vel**.

---

## 4. ViolaÃ§Ã£o de Contrato

Qualquer tentativa de:

- Modificar o nÃºcleo congelado
- Reinterpretar seus invariantes
- Introduzir lÃ³gica adicional no core

Deve ser tratada como **violaÃ§Ã£o arquitetural grave** e **rejeitada**.

---

## 5. Status

**CORE LOCK ATIVO**

Data de congelamento: ____ / ____ / ______

Assinatura conceitual:
> O nÃºcleo estÃ¡ completo. EvoluÃ­mos acima dele.


---

## Source: `docs/arquitecture layers/EXECUTOR_LAYER.md`

---

# EXECUTOR_LAYER.md

## Contrato CanÃ´nico do Executor Layer â€” CortAI

---

## 1. PAPEL DO EXECUTOR LAYER

O **Executor Layer** Ã© responsÃ¡vel **exclusivamente** por **executar aÃ§Ãµes explÃ­citas** que lhe sÃ£o enviadas pelo NÃºcleo Cognitivo.

Ele **nÃ£o observa**, **nÃ£o decide**, **nÃ£o aprende** e **nÃ£o mantÃ©m estado cognitivo**.

O Executor **age**, e apenas isso.

---

## 2. PRINCÃPIO FUNDAMENTAL

> **O Executor executa exatamente o que foi ordenado, sem interpretaÃ§Ã£o.**

Qualquer forma de inferÃªncia, escolha, otimizaÃ§Ã£o ou encadeamento Ã© **estritamente proibida**.

---

## 3. ENTRADA AUTORIZADA (CONTRATO NÃšCLEO â†’ EXECUTOR)

O Executor **sÃ³ pode receber** aÃ§Ãµes no seguinte formato lÃ³gico:

### Campos obrigatÃ³rios

* `decision_id` â€” identificador Ãºnico da decisÃ£o
* `action_type` â€” string literal descrevendo a aÃ§Ã£o
* `action_payload` â€” dados necessÃ¡rios para a execuÃ§Ã£o

### Garantias

* Toda aÃ§Ã£o **vem de uma decisÃ£o existente**
* O Executor **nÃ£o recebe estado**
* O Executor **nÃ£o recebe histÃ³rico**
* O Executor **nÃ£o conhece o processo cognitivo**

---

## 4. COMPORTAMENTO OBRIGATÃ“RIO

Ao receber uma aÃ§Ã£o vÃ¡lida, o Executor deve:

1. Executar **exatamente uma aÃ§Ã£o**
2. NÃ£o disparar outras aÃ§Ãµes
3. NÃ£o registrar decisÃµes
4. NÃ£o criar novos eventos
5. NÃ£o alterar arquivos do Core
6. NÃ£o persistir estado cognitivo

---

## 5. SAÃDA AUTORIZADA (EXECUTOR â†’ NÃšCLEO)

ApÃ³s a execuÃ§Ã£o, o Executor **deve retornar** um feedback factual contendo:

### Campos obrigatÃ³rios

* `decision_id` â€” o mesmo recebido
* `execution_status` â€” valor literal (`SUCCESS` ou `FAILURE`)

### Campos opcionais

* `metrics` â€” dados factuais simples (ex: duraÃ§Ã£o, contagem, cÃ³digo)

### ProibiÃ§Ãµes

* Nenhuma interpretaÃ§Ã£o
* Nenhuma recomendaÃ§Ã£o
* Nenhuma decisÃ£o
* Nenhuma inferÃªncia

---

## 6. FALHAS

* Falha **Ã© um resultado vÃ¡lido**
* Falhas **nÃ£o abortam o sistema**
* Falhas **nÃ£o sÃ£o tratadas como exceÃ§Ã£o cognitiva**
* Falhas **devem ser reportadas como dado**

O Executor **nunca tenta corrigir a prÃ³pria falha**.

---

## 7. LIMITES ABSOLUTOS

O Executor **NÃƒO PODE**:

* Criar ou alterar `State`
* Criar ou alterar `Decision`
* Criar ou alterar `Outcome`
* Ler ou escrever `audit_log.jsonl`
* Persistir identidade de processo
* Encadear execuÃ§Ãµes
* Tomar decisÃµes condicionais

---

## 8. RELAÃ‡ÃƒO COM OUTRAS CAMADAS

### NÃºcleo Cognitivo

* Ãšnica autoridade decisÃ³ria
* Executor Ã© totalmente subordinado

### Observer Layer

* Nenhuma interaÃ§Ã£o direta
* O Executor **nÃ£o observa o mundo**

---

## 9. VALIDAÃ‡ÃƒO DE CONFORMIDADE

Uma implementaÃ§Ã£o do Executor estÃ¡ **correta** se:

* Executa aÃ§Ãµes somente quando invocado
* Retorna feedback factual
* NÃ£o altera estado cognitivo
* NÃ£o cria efeitos colaterais fora da aÃ§Ã£o solicitada
* Pode ser substituÃ­da sem impacto no Core

---

## 10. REGRA FINAL (INQUEBRÃVEL)

> **Se o Executor â€œparecer inteligenteâ€, ele estÃ¡ errado.**

InteligÃªncia vive no Core.
ExecuÃ§Ã£o vive no Executor.

---

**FIM DO CONTRATO DO EXECUTOR LAYER**

---


---

## Source: `docs/arquitecture layers/EXTENSION_MAP.md`

# EXTENSION_MAP.md

## Objetivo

Este documento define **como o sistema CortAI pode evoluir** apÃ³s o congelamento do Core, **sem violar invariantes**, **sem alterar loops existentes** e **sem comprometer auditabilidade**.

Ele **nÃ£o autoriza implementaÃ§Ã£o automÃ¡tica**. Serve como **mapa de extensÃ£o segura**.

---

## 1. O QUE ESTÃ CONGELADO (IMUTÃVEL)

Os seguintes artefatos **NUNCA** devem ser alterados apÃ³s o freeze:

* `backend/app/cognitive_core.py`
* `CORTAI_CORE.md`
* ApÃªndices tÃ©cnicos dos Loops 1â€“4
* `ARCHITECTURE_FREEZE.md`
* Estrutura e semÃ¢ntica de:

  * `State`
  * `Decision`
  * `Outcome`
* PersistÃªncia:

  * `storage/audit_log.jsonl`
  * `storage/process_id.txt`

Qualquer alteraÃ§Ã£o nesses itens **quebra compatibilidade histÃ³rica**.

---

## 2. ONDE EXTENSÃ•ES SÃƒO PERMITIDAS

### 2.1 Observer Layer

Local esperado:

```
backend/app/observers/
```

PermissÃµes:

* Criar novos observers
* Traduzir eventos externos em `observation_payload`

RestriÃ§Ãµes:

* NÃ£o criar decisÃµes
* NÃ£o acessar audit log
* NÃ£o manter estado interno persistente

---

### 2.2 Planner Layer

Local esperado:

```
backend/app/planners/
```

PermissÃµes:

* Analisar `State` jÃ¡ criado
* Sugerir `decision_type` e `rationale`

RestriÃ§Ãµes:

* NÃ£o executar aÃ§Ãµes
* NÃ£o persistir nada diretamente
* NÃ£o alterar estrutura do `Decision`

Obs: planners **nÃ£o substituem** o Core â€” apenas influenciam inputs futuros.

---

### 2.3 Executor Layer

Local esperado:

```
backend/app/executors/
```

PermissÃµes:

* Executar intenÃ§Ãµes recebidas
* Retornar feedback factual

RestriÃ§Ãµes:

* NÃ£o decidir
* NÃ£o criar estado
* NÃ£o acessar histÃ³rico

---

## 3. COMO ADICIONAR NOVOS LOOPS

### Regra absoluta

> Nenhum novo loop pode modificar ou reprocessar dados de loops anteriores.

### Procedimento obrigatÃ³rio

1. Criar **documento de Loop N**
2. Criar **ApÃªndice TÃ©cnico MÃ­nimo**
3. Validar:

   * nÃ£o altera invariantes
   * nÃ£o altera Core
4. Somente apÃ³s isso:

   * implementar

---

## 4. EVOLUÃ‡ÃƒO PERMITIDA (EXEMPLOS)

Permitido:

* Loop de avaliaÃ§Ã£o estatÃ­stica (somente leitura)
* Planner probabilÃ­stico
* Executor assÃ­ncrono
* Observers multimodais

Proibido:

* Reescrever decisÃµes passadas
* Mutar estados
* Inserir inferÃªncia implÃ­cita no Core

---

## 5. PRINCÃPIO DE OURO

> **O Core nÃ£o aprende.**
>
> O sistema aprende **ao redor** do Core.
>
> O Core apenas registra, encadeia e preserva causalidade.

---

## 6. CHECK FINAL ANTES DE QUALQUER EXTENSÃƒO

Antes de implementar qualquer coisa nova:

* [ ] NÃ£o toca no Core
* [ ] NÃ£o altera schemas
* [ ] NÃ£o reescreve histÃ³rico
* [ ] NÃ£o cria atalhos
* [ ] EstÃ¡ documentado antes

Se algum item falhar â†’ **extensÃ£o proibida**.

---

**FIM DO EXTENSION_MAP.md**


---

## Source: `docs/arquitecture layers/OBSERVER_LAYER.md`

---

# OBSERVER_LAYER.md

**Contrato MÃ­nimo da Camada de ObservaÃ§Ã£o**

---

## 1. DEFINIÃ‡ÃƒO FORMAL

O **Observer Layer** Ã© uma camada **estritamente passiva**, responsÃ¡vel por **ler, reconstruir e expor** o comportamento do NÃºcleo Cognitivo **sem interferir** em sua execuÃ§Ã£o.

Ele **nÃ£o participa** do loop cognitivo.
Ele **nÃ£o influencia decisÃµes**.
Ele **nÃ£o modifica dados persistidos**.

---

## 2. FONTE ÃšNICA DE VERDADE

O Observer **sÃ³ pode ler** os seguintes artefatos:

```
storage/audit_log.jsonl
storage/process_id.txt
```

### ProibiÃ§Ãµes absolutas

O Observer **NÃƒO PODE**:

* escrever nesses arquivos
* reordenar registros
* corrigir inconsistÃªncias
* preencher lacunas
* inferir causalidade ausente

Se algo **nÃ£o estÃ¡ registrado**, ele **nÃ£o existe** para o Observer.

---

## 3. ESCOPO FUNCIONAL AUTORIZADO

O Observer Layer pode **exclusivamente**:

1. **Ler** registros persistidos
2. **Reconstruir sequÃªncias** de execuÃ§Ã£o
3. **Agrupar ciclos** por `process_id`
4. **Encadear estados** via:

   * `previous_state_id`
   * `previous_outcome_id`
5. **Expor visÃ£o temporal e causal** do sistema

Nada alÃ©m disso.

---

## 4. UNIDADE DE OBSERVAÃ‡ÃƒO

A menor unidade vÃ¡lida de observaÃ§Ã£o Ã©:

```
(State â†’ Decision â†’ Outcome)
```

### Invariantes

* Um `State` **sempre precede** uma `Decision`
* Uma `Decision` **sempre precede** um `Outcome`
* Um `Outcome` **encerra** um ciclo observÃ¡vel
* Um ciclo **nunca Ã© parcial** no Observer
  (se faltar algo, o ciclo Ã© invÃ¡lido)

---

## 5. MODELO DE LEITURA (NÃƒO EXECUTÃVEL)

O Observer **opera conceitualmente** em trÃªs nÃ­veis:

### 5.1 NÃ­vel Linear

Leitura sequencial do `audit_log.jsonl`:

* ordem fÃ­sica do arquivo = ordem temporal
* nenhuma reordenaÃ§Ã£o permitida

---

### 5.2 NÃ­vel Temporal

ReconstruÃ§Ã£o da cadeia de estados:

```
State(n) â†’ State(n+1)
```

usando:

* `previous_state_id`

Se a referÃªncia nÃ£o existir, a cadeia **se rompe**.

---

### 5.3 NÃ­vel Causal

ReconstruÃ§Ã£o de causalidade mÃ­nima:

```
Outcome(n) â†’ State(n+1)
```

usando:

* `previous_outcome_id`

Se ausente ou invÃ¡lido, **nenhuma causalidade Ã© assumida**.

---

## 6. SAÃDAS PERMITIDAS

O Observer Layer pode produzir **apenas representaÃ§Ãµes derivadas**, tais como:

* timelines
* Ã¡rvores de execuÃ§Ã£o
* grÃ¡ficos de encadeamento
* relatÃ³rios post-mortem
* visualizaÃ§Ãµes

### RestriÃ§Ãµes

Essas saÃ­das:

* âŒ nÃ£o alimentam o Core
* âŒ nÃ£o alteram decisÃµes futuras
* âŒ nÃ£o geram novos estados
* âŒ nÃ£o criam feedback

SÃ£o **estritamente externas**.

---

## 7. RELAÃ‡ÃƒO COM OUTRAS CAMADAS

### RelaÃ§Ã£o com o Core

* O Observer **depende** do Core
* O Core **nÃ£o conhece** o Observer

DependÃªncia **unidirecional**.

---

### RelaÃ§Ã£o com Executors, Agents, UI

O Observer:

* pode ser usado por UI
* pode ser usado por ferramentas de auditoria
* pode ser usado por anÃ¡lise humana

Mas **nunca** por mecanismos decisÃ³rios.

---

## 8. CRITÃ‰RIO DE CORREÃ‡ÃƒO

O Observer Layer estÃ¡ correto se:

* conseguir reconstruir **exatamente** o que aconteceu
* sem adicionar informaÃ§Ã£o
* sem omitir registros
* sem interpretar intenÃ§Ã£o
* apenas refletindo fatos persistidos

Se dois Observers diferentes lerem o mesmo log,
**ambos devem produzir a mesma visÃ£o factual**.

---

## 9. PROIBIÃ‡Ã•ES EXPLÃCITAS

O Observer **NÃƒO Ã‰**:

* um agente
* um avaliador
* um juiz
* um otimizador
* um planejador
* um crÃ­tico
* um segundo cÃ©rebro

Ele Ã© **testemunha**, nÃ£o participante.

---

## 10. STATUS DO DOCUMENTO

* Este contrato **nÃ£o autoriza implementaÃ§Ã£o automÃ¡tica**
* Ele **define limites**, nÃ£o cÃ³digo
* Qualquer implementaÃ§Ã£o futura exige **apÃªndice tÃ©cnico prÃ³prio**

---

**FIM DO CONTRATO DO OBSERVER LAYER**

# APÃŠNDICE TÃ‰CNICO MÃNIMO â€” OBSERVER LAYER (READâ€‘ONLY)

Este apÃªndice tÃ©cnico **nÃ£o altera** o contrato do Observer Layer.
Ele existe **exclusivamente** para remover ambiguidade de implementaÃ§Ã£o futura **sem permitir aÃ§Ã£o, decisÃ£o ou escrita**.

Nada neste documento adiciona capacidade cognitiva ao sistema.

---

## 1. FINALIDADE DO OBSERVER (TÃ‰CNICA)

O Observer Layer Ã© uma **camada de leitura passiva**, responsÃ¡vel apenas por:

* Ler registros jÃ¡ persistidos
* Reconstruir cadeias temporais e causais
* Expor visÃµes derivadas **sem interpretaÃ§Ã£o**

O Observer **nÃ£o executa**, **nÃ£o decide**, **nÃ£o escreve**, **nÃ£o corrige**.

---

## 2. FONTE ÃšNICA DE DADOS

O Observer **pode ler somente** os seguintes artefatos:

```
storage/audit_log.jsonl
storage/process_id.txt
```

RestriÃ§Ãµes:

* Nenhum outro arquivo Ã© autorizado
* Logs de aplicaÃ§Ã£o sÃ£o proibidos como fonte
* MemÃ³ria em tempo de execuÃ§Ã£o Ã© proibida

---

## 3. MODELO DE LEITURA PERMITIDO

### 3.1 Unidade mÃ­nima de leitura

O Observer lÃª **apenas registros completos**, nunca linhas parciais.

Cada linha representa exatamente **um evento factual**:

* State
* Decision
* Outcome

---

### 3.2 Ordem de leitura

* A leitura Ã© **estritamente sequencial**
* A ordem do arquivo Ã© a ordem factual
* ReordenaÃ§Ã£o Ã© proibida

---

## 4. RECONSTRUÃ‡Ã•ES AUTORIZADAS

O Observer **pode reconstruir**:

* Linha temporal de States por `process_id`
* Cadeia `State â†’ Decision â†’ Outcome`
* RelaÃ§Ãµes via:

  * `previous_state_id`
  * `previous_outcome_id`

O Observer **nÃ£o pode inferir** relaÃ§Ãµes ausentes.

---

## 5. SAÃDAS PERMITIDAS

O Observer **pode produzir apenas**:

* Estruturas de leitura
* VisÃµes ordenadas
* Resumos factuais (contagens, listas, sequÃªncias)

Exemplos permitidos:

* "NÃºmero de decisÃµes por processo"
* "Estados Ã³rfÃ£os"
* "DecisÃµes sem outcome"

---

## 6. SAÃDAS PROIBIDAS

O Observer **nÃ£o pode produzir**:

* Julgamentos
* ClassificaÃ§Ãµes sem base explÃ­cita
* RecomendaÃ§Ãµes
* Alertas acionÃ¡veis
* IntenÃ§Ãµes de aÃ§Ã£o

---

## 7. PROIBIÃ‡Ã•ES ABSOLUTAS

O Observer **NUNCA** pode:

* Criar arquivos
* Modificar arquivos
* Corrigir dados
* Preencher lacunas
* Normalizar registros
* Executar cÃ³digo do Core

---

## 8. RELAÃ‡ÃƒO COM O CORE

* O Core **ignora completamente** o Observer
* O Observer **depende totalmente** do Core
* NÃ£o existe chamada Core â†’ Observer
* NÃ£o existe feedback Observer â†’ Core

ComunicaÃ§Ã£o Ã© **unidirecional e assÃ­ncrona**.

---

## 9. CRITÃ‰RIO DE IMPLEMENTAÃ‡ÃƒO CORRETA

Uma implementaÃ§Ã£o do Observer estÃ¡ correta se:

* Pode ser desligada sem afetar o Core
* NÃ£o altera nenhum byte persistido
* NÃ£o impede execuÃ§Ã£o do sistema
* Produz exatamente os mesmos resultados a partir dos mesmos dados

---

## 10. SINAL CLARO DE VIOLAÃ‡ÃƒO

Qualquer Observer que:

* "Explique" decisÃµes
* "Avalie" outcomes
* "Sugira" aÃ§Ãµes
* "Aprenda" padrÃµes

**nÃ£o Ã© um Observer**, Ã© um agente cognitivo ilegÃ­timo.

---

**FIM DO APÃŠNDICE TÃ‰CNICO**

Este documento **congela o Observer como camada passiva**.
Nenhuma expansÃ£o Ã© autorizada sem revisÃ£o explÃ­cita do Core.


---

## Source: `docs/arquitecture layers/PLANNER_LAYER.md`

---

# ðŸ“˜ PLANNER_LAYER.md

**Contrato CanÃ´nico do Planner Layer**

---

## 1. PropÃ³sito

O **Planner Layer** Ã© responsÃ¡vel por **estruturar opÃ§Ãµes de aÃ§Ã£o futuras** a partir de:

* Estados observados
* Outcomes registrados
* HistÃ³rico explÃ­cito do sistema

âš ï¸ O Planner **NÃƒO decide**, **NÃƒO executa** e **NÃƒO aprende**.

Ele apenas **organiza possibilidades** de forma determinÃ­stica e auditÃ¡vel.

---

## 2. PosiÃ§Ã£o na Arquitetura

```
Observer Layer
      â†“
Cognitive Core
      â†“
Planner Layer
      â†“
Executor Layer
```

O Planner atua **apÃ³s a observaÃ§Ã£o e o ciclo cognitivo**, mas **antes de qualquer execuÃ§Ã£o futura planejada**.

---

## 3. Entradas Permitidas

O Planner Layer **pode ler** exclusivamente:

* Estados (`State`)
* Outcomes (`Outcome`)
* HistÃ³rico append-only (ex: audit_log.jsonl)
* Identidade de processo (`process_id`)

âš ï¸ O Planner **NÃƒO pode receber comandos externos diretos**.

---

## 4. SaÃ­das Permitidas

O Planner Layer **pode produzir apenas**:

* Estruturas de **OpÃ§Ãµes Planejadas**
* Metadados descritivos (ex: rÃ³tulos, razÃµes, prÃ©-condiÃ§Ãµes)

Essas saÃ­das **NÃƒO disparam execuÃ§Ã£o**
e **NÃƒO alteram o Core**.

---

## 5. Estrutura Conceitual MÃ­nima

### 5.1 Planned Option (estrutura abstrata)

Uma opÃ§Ã£o planejada representa **uma possibilidade**, nÃ£o uma intenÃ§Ã£o.

Campos mÃ­nimos conceituais:

* `option_id`
* `origin_state_id`
* `description`
* `constraints`
* `created_at`

âš ï¸ Nenhuma opÃ§Ã£o contÃ©m decisÃ£o final.

---

## 6. RestriÃ§Ãµes Fundamentais (Invariantes)

O Planner Layer **NUNCA** pode:

* Criar ou modificar `Decision`
* Criar ou modificar `Outcome`
* Executar aÃ§Ãµes
* Invocar executor
* Alterar estados passados
* Alterar o fluxo do Core
* Persistir fora dos artefatos explicitamente autorizados

---

## 7. Determinismo

Dado o mesmo conjunto de:

* Estados
* Outcomes
* ConfiguraÃ§Ã£o estÃ¡tica

O Planner Layer deve produzir **as mesmas opÃ§Ãµes**, na mesma ordem.

âš ï¸ Aleatoriedade, heurÃ­stica adaptativa e aprendizado sÃ£o proibidos nesta camada.

---

## 8. PersistÃªncia

Neste estÃ¡gio:

* A persistÃªncia do Planner Ã© **opcional**
* Caso exista, deve ser:

  * Append-only
  * Separada do Core
  * Totalmente auditÃ¡vel

Nenhuma persistÃªncia Ã© obrigatÃ³ria no MVP.

---

## 9. Isolamento

O Planner Layer:

* NÃ£o conhece implementaÃ§Ãµes do Executor
* NÃ£o acessa sensores
* NÃ£o observa o mundo externo
* NÃ£o altera o estado global

Ele opera **exclusivamente sobre histÃ³rico interno**.

---

## 10. EvoluÃ§Ã£o Permitida (Futuro)

Somente apÃ³s validaÃ§Ã£o explÃ­cita do Core, o Planner poderÃ¡ futuramente:

* Introduzir heurÃ­sticas
* Introduzir pontuaÃ§Ã£o de opÃ§Ãµes
* Introduzir estratÃ©gias
* Integrar modelos externos

âš ï¸ Nenhuma dessas evoluÃ§Ãµes estÃ¡ ativa neste contrato.

---

## 11. Status do Contrato

* âœ… Congelado
* âœ… Minimalista
* âœ… Sem inteligÃªncia embutida
* âœ… CompatÃ­vel com auditoria total
* âœ… Preparado para expansÃ£o futura controlada

---

## 12. RelaÃ§Ã£o com Outros Contratos

Este contrato Ã© **complementar** a:

* `CORTAI_CORE.md`
* `OBSERVER_LAYER.md`
* `EXECUTOR_LAYER.md`

Nenhum contrato se sobrepÃµe a outro.

---

## 13. PrincÃ­pio Fundamental

> **O Planner propÃµe.
> O Core decide.
> O Executor executa.**

---

ðŸ“Œ **Fim do contrato do Planner Layer**

---


---

## Source: `docs/arquitecture layers/TEST_CASES.md`

---

# TEST_CASES.md

**Projeto:** CortAI 1.0
**Estado:** Core congelado
**Escopo:** ValidaÃ§Ã£o funcional e estrutural
**Proibido:** inferÃªncia, otimizaÃ§Ã£o, novos comportamentos

---

## 1. PrincÃ­pios de Teste

* Todos os testes sÃ£o **determinÃ­sticos**
* Nenhum teste avalia â€œqualidadeâ€ de decisÃ£o
* Apenas **existÃªncia, encadeamento e persistÃªncia**
* O **audit_log.jsonl** Ã© a fonte de verdade
* Ordem dos eventos Ã© obrigatÃ³ria

---

## 2. PrÃ©-condiÃ§Ãµes Globais

* DiretÃ³rio `storage/` existente ou criÃ¡vel
* PermissÃ£o de escrita em disco
* Sistema iniciado sem erros
* Nenhum arquivo corrompido

---

## 3. Casos de Teste â€” LOOP 1

### CriaÃ§Ã£o do Ciclo Cognitivo BÃ¡sico

---

### TC-01 â€” CriaÃ§Ã£o de State inicial

**PrÃ©-condiÃ§Ã£o**

* `storage/audit_log.jsonl` inexistente ou vazio

**AÃ§Ã£o**

* Enviar payload para endpoint `/observe`

**VerificaÃ§Ã£o esperada**

* Um registro `State` Ã© criado
* Campos obrigatÃ³rios presentes:

  * `state_id`
  * `timestamp`
  * `observation_payload`
* `previous_state_id == null`

---

### TC-02 â€” Registro de Decision

**PrÃ©-condiÃ§Ã£o**

* TC-01 executado

**AÃ§Ã£o**

* Mesma execuÃ§Ã£o do ciclo

**VerificaÃ§Ã£o esperada**

* Um registro `Decision` existe
* `decision.state_id` referencia o `state_id` criado
* `decision_type == "NOOP"`

---

### TC-03 â€” Registro de Outcome

**PrÃ©-condiÃ§Ã£o**

* Executor retorna resposta vÃ¡lida

**AÃ§Ã£o**

* ConclusÃ£o do ciclo

**VerificaÃ§Ã£o esperada**

* Um registro `Outcome` Ã© criado
* `outcome.decision_id` corresponde Ã  Decision
* Ordem no log:

  1. State
  2. Decision
  3. Outcome

---

## 4. Casos de Teste â€” LOOP 2

### Continuidade Temporal

---

### TC-04 â€” Encadeamento de State

**PrÃ©-condiÃ§Ã£o**

* Pelo menos um ciclo anterior executado

**AÃ§Ã£o**

* Executar novo `/observe`

**VerificaÃ§Ã£o esperada**

* Novo `State.previous_state_id` aponta para o Ãºltimo `state_id`
* Nenhuma quebra de ordem no log

---

## 5. Casos de Teste â€” LOOP 3

### Continuidade Causal Referencial

---

### TC-05 â€” ReferÃªncia ao Outcome anterior

**PrÃ©-condiÃ§Ã£o**

* Pelo menos um ciclo completo existente

**AÃ§Ã£o**

* Executar novo ciclo

**VerificaÃ§Ã£o esperada**

* `State.previous_outcome_id` existe
* Valor corresponde ao Ãºltimo `Outcome.outcome_id`

---

## 6. Casos de Teste â€” LOOP 4

### Identidade Persistente de Processo

---

### TC-06 â€” CriaÃ§Ã£o do process_id

**PrÃ©-condiÃ§Ã£o**

* `storage/process_id.txt` inexistente

**AÃ§Ã£o**

* Executar `/observe`

**VerificaÃ§Ã£o esperada**

* Arquivo `process_id.txt` criado
* ConteÃºdo Ã© um UUID vÃ¡lido

---

### TC-07 â€” ReutilizaÃ§Ã£o do process_id

**PrÃ©-condiÃ§Ã£o**

* `process_id.txt` existente

**AÃ§Ã£o**

* Executar mÃºltiplos ciclos

**VerificaÃ§Ã£o esperada**

* Todos os `State.process_id` sÃ£o idÃªnticos
* Nenhuma sobrescrita do arquivo

---

## 7. Casos de Teste â€” Observer Layer

---

### TC-08 â€” ObservaÃ§Ã£o nÃ£o altera estado

**PrÃ©-condiÃ§Ã£o**

* Core ativo

**AÃ§Ã£o**

* Enviar payload arbitrÃ¡rio

**VerificaÃ§Ã£o esperada**

* Observer apenas dispara ciclo
* Nenhuma lÃ³gica decisÃ³ria no Observer

---

## 8. Casos de Teste â€” Executor Layer

---

### TC-09 â€” Executor nÃ£o decide

**PrÃ©-condiÃ§Ã£o**

* Decision emitida

**AÃ§Ã£o**

* Executor recebe `decision_id`, `action_type`, `payload`

**VerificaÃ§Ã£o esperada**

* Executor apenas retorna feedback
* Nenhuma mutaÃ§Ã£o de State ou Decision

---

## 9. Casos de Teste â€” Invariantes Globais

---

### TC-10 â€” Append-only do audit_log

**AÃ§Ã£o**

* Executar mÃºltiplos ciclos

**VerificaÃ§Ã£o esperada**

* Nenhum registro Ã© removido
* Nenhum registro Ã© sobrescrito
* Apenas append no final do arquivo

---

## 10. CritÃ©rio de AprovaÃ§Ã£o

O sistema Ã© considerado **correto** se:

* Todos os testes acima forem satisfeitos
* Nenhuma exceÃ§Ã£o nÃ£o tratada ocorrer
* Nenhum contrato for violado
* O Core permanecer congelado

---

## 11. Encerramento

> Este arquivo **nÃ£o autoriza implementaÃ§Ã£o**.
> Ele apenas **define verificaÃ§Ãµes objetivas**.

---


---

## Source: `docs/arquitecture layers/TEST_STRATEGY.md`

# TEST_STRATEGY.md

## 1. PropÃ³sito

Este documento define a **estratÃ©gia mÃ­nima e obrigatÃ³ria de testes** do projeto **CortAI**, garantindo que:

- O comportamento do sistema seja **verificÃ¡vel**
- Os contratos definidos em:
  - `CORTAI_CORE.md`
  - `OBSERVER_LAYER.md`
  - `PLANNER_LAYER.md`
  - `EXECUTOR_LAYER.md`
- sejam **respeitados sem inferÃªncia**
- Nenhum teste introduza **lÃ³gica, inteligÃªncia ou decisÃµes novas**

O objetivo dos testes **nÃ£o Ã© validar qualidade cognitiva**, mas **validar integridade estrutural, causal e contratual**.

---

## 2. PrincÃ­pios Fundamentais

### 2.1 Testes nÃ£o decidem comportamento

- Testes **nÃ£o interpretam intenÃ§Ã£o**
- Testes **nÃ£o inferem estados**
- Testes **nÃ£o simulam inteligÃªncia**
- Testes **nÃ£o corrigem comportamento**

Eles apenas **verificam conformidade**.

---

### 2.2 Testes sÃ£o determinÃ­sticos

- Entradas conhecidas
- SaÃ­das verificÃ¡veis
- Ordem explÃ­cita
- PersistÃªncia observÃ¡vel

---

### 2.3 Testes sÃ£o observacionais

- O sistema Ã© tratado como **caixa preta estrutural**
- Apenas artefatos persistidos e contratos sÃ£o avaliados
- Nenhum teste acessa lÃ³gica interna alÃ©m do permitido pelo contrato pÃºblico

---

## 3. Escopo de Testes

### 3.1 O que DEVE ser testado

- CriaÃ§Ã£o de `State`
- Encadeamento correto de:
  - `previous_state_id`
  - `previous_outcome_id`
- PersistÃªncia do `process_id`
- Append-only do `audit_log.jsonl`
- EmissÃ£o obrigatÃ³ria e ordenada de:
  - State â†’ Decision â†’ Outcome
- Conformidade de campos obrigatÃ³rios
- NÃ£o violaÃ§Ã£o de contratos entre camadas

---

### 3.2 O que NÃƒO deve ser testado

- Qualidade da decisÃ£o
- MÃ©rito da aÃ§Ã£o
- OtimizaÃ§Ã£o
- EstratÃ©gia
- Planejamento
- EficiÃªncia
- InteligÃªncia emergente

Qualquer teste com esse objetivo Ã© **proibido**.

---

## 4. Tipos de Teste Permitidos

### 4.1 Testes de Estrutura (ObrigatÃ³rios)

Verificam se os artefatos persistidos:

- Existem
- EstÃ£o bem formados
- ContÃªm todos os campos exigidos
- NÃ£o contÃªm campos proibidos

Exemplo de verificaÃ§Ã£o permitida:

- Um registro `State` **contÃ©m** `state_id`
- Um `State` **nÃ£o contÃ©m** lÃ³gica ou resultado
- Um `Outcome` **refere-se** a um `decision_id` existente

---

### 4.2 Testes de SequÃªncia Temporal (ObrigatÃ³rios)

Verificam que:

1. Cada ciclo gera exatamente:
   - 1 State
   - 1 Decision
   - 1 Outcome
2. A ordem no `audit_log.jsonl` Ã© preservada
3. O encadeamento causal Ã© contÃ­nuo

---

### 4.3 Testes de PersistÃªncia (ObrigatÃ³rios)

Verificam que:

- `audit_log.jsonl` Ã© append-only
- Nenhuma linha Ã© sobrescrita
- `process_id.txt`:
  - Ã‰ criado apenas se inexistente
  - MantÃ©m o mesmo valor entre execuÃ§Ãµes

---

### 4.4 Testes de Contrato entre Camadas

Verificam que:

- Observer apenas observa
- Planner apenas produz intenÃ§Ã£o
- Executor apenas executa

Nenhuma camada:

- Acessa estado interno de outra
- Modifica artefatos fora do contrato
- Persiste dados nÃ£o autorizados

---

## 5. Artefatos de Teste

### 5.1 Arquivos observÃ¡veis

Os testes **podem ler**, mas **nÃ£o modificar**:

- `storage/audit_log.jsonl`
- `storage/process_id.txt`

---

### 5.2 Arquivos proibidos

Testes **nÃ£o podem criar**:

- Novos arquivos persistentes
- Novos formatos de log
- Backups
- Snapshots automÃ¡ticos

---

## 6. EstratÃ©gia de ExecuÃ§Ã£o

### 6.1 Ambiente

- Ambiente local isolado
- DiretÃ³rio `storage/` limpo antes do primeiro teste
- Nenhum mock que introduza comportamento novo

---

### 6.2 Ordem mÃ­nima recomendada

1. Teste de inicializaÃ§Ã£o limpa
2. Teste de primeiro ciclo cognitivo
3. Teste de mÃºltiplos ciclos sequenciais
4. Teste de reinicializaÃ§Ã£o com persistÃªncia
5. Teste de integridade do log

---

## 7. CritÃ©rios de Falha

Um teste **deve falhar** se:

- Qualquer campo obrigatÃ³rio estiver ausente
- A ordem State â†’ Decision â†’ Outcome for violada
- Um identificador nÃ£o referenciar corretamente o anterior
- Um arquivo persistente for recriado indevidamente
- Um contrato for violado, mesmo que o sistema â€œfuncioneâ€

---

## 8. CritÃ©rios de AprovaÃ§Ã£o

O sistema Ã© considerado **aprovado** quando:

- Todos os testes estruturais passam
- Nenhum contrato Ã© violado
- Nenhuma inferÃªncia Ã© necessÃ¡ria para interpretar os resultados
- A cadeia causal Ã© auditÃ¡vel apenas lendo os logs

---

## 9. Status Arquitetural

Este documento:

- EstÃ¡ subordinado ao `ARCHITECTURE_FREEZE.md`
- NÃ£o redefine arquitetura
- NÃ£o introduz novos loops
- NÃ£o cria novas responsabilidades

Ele **apenas descreve como verificar** o que jÃ¡ foi congelado.

---

## 10. ClÃ¡usula Final

Se um comportamento **nÃ£o puder ser testado sem inferÃªncia**, entÃ£o:

> Esse comportamento **nÃ£o Ã© testÃ¡vel**
> e **nÃ£o deve existir** no sistema.

---

**Fim do documento.**


---

## Source: `docs/arquitecture layers/VALIDATION_CHECKLIST.md`

---

# VALIDATION_CHECKLIST.md

**Projeto:** CortAI 1.0
**Estado:** Core congelado
**Tipo:** ValidaÃ§Ã£o manual operacional
**Proibido:** inferÃªncia, otimizaÃ§Ã£o, refatoraÃ§Ã£o

---

## 1. PreparaÃ§Ã£o do Ambiente

* [ ] RepositÃ³rio clonado sem modificaÃ§Ãµes manuais
* [ ] Branch correta selecionada
* [ ] Ambiente virtual ativo (se aplicÃ¡vel)
* [ ] AplicaÃ§Ã£o inicia sem erros
* [ ] DiretÃ³rio `storage/` existe ou Ã© criado automaticamente
* [ ] PermissÃ£o de escrita confirmada

---

## 2. VerificaÃ§Ã£o de Arquivos ObrigatÃ³rios

### Core

* [ ] `CORTAI_CORE.md` presente na raiz
* [ ] Core marcado como **congelado**
* [ ] Nenhuma ediÃ§Ã£o recente apÃ³s congelamento

---

### CÃ³digo

* [ ] `backend/app/cognitive_core.py` existe
* [ ] Arquivo contÃ©m:

  * [ ] CriaÃ§Ã£o de `State`
  * [ ] EmissÃ£o de `Decision`
  * [ ] Registro de `Outcome`
  * [ ] Encadeamento temporal (`previous_state_id`)
  * [ ] Encadeamento causal (`previous_outcome_id`)
  * [ ] `process_id` persistente

---

### PersistÃªncia

* [ ] `storage/audit_log.jsonl` existe apÃ³s primeira execuÃ§Ã£o
* [ ] Arquivo Ã© append-only
* [ ] `storage/process_id.txt` existe
* [ ] ConteÃºdo do `process_id.txt` nÃ£o muda entre execuÃ§Ãµes

---

## 3. ExecuÃ§Ã£o Manual â€” Loop Cognitivo

### LOOP 1 â€” CriaÃ§Ã£o BÃ¡sica

* [ ] Enviar requisiÃ§Ã£o `/observe`
* [ ] Um `State` Ã© registrado
* [ ] Um `Decision` Ã© registrado
* [ ] Um `Outcome` Ã© registrado
* [ ] Ordem correta no `audit_log.jsonl`

---

### LOOP 2 â€” Continuidade Temporal

* [ ] Executar `/observe` novamente
* [ ] Novo `State.previous_state_id` preenchido
* [ ] Valor referencia o `state_id` anterior

---

### LOOP 3 â€” Continuidade Causal

* [ ] Executar novo ciclo
* [ ] `State.previous_outcome_id` preenchido
* [ ] Valor referencia o Ãºltimo `Outcome`

---

### LOOP 4 â€” Identidade de Processo

* [ ] `process_id.txt` criado apenas uma vez
* [ ] Todos os `State.process_id` sÃ£o idÃªnticos
* [ ] Nenhuma sobrescrita do arquivo

---

## 4. Observer Layer

* [ ] Observer apenas recebe payload
* [ ] Observer nÃ£o transforma dados
* [ ] Observer nÃ£o decide
* [ ] Observer apenas dispara o ciclo

---

## 5. Executor Layer

* [ ] Executor recebe:

  * [ ] `decision_id`
  * [ ] `action_type`
  * [ ] `action_payload`
* [ ] Executor nÃ£o altera estado
* [ ] Executor nÃ£o gera decisÃµes
* [ ] Executor retorna feedback simples

---

## 6. Invariantes Estruturais

* [ ] Nenhuma funÃ§Ã£o escolhe comportamento
* [ ] Nenhum `if` com lÃ³gica cognitiva
* [ ] Nenhuma mutaÃ§Ã£o retroativa
* [ ] Nenhum dado Ã© reescrito
* [ ] Nenhuma inferÃªncia implÃ­cita

---

## 7. Auditoria Manual

* [ ] `audit_log.jsonl` pode ser lido linha a linha
* [ ] Cada ciclo forma uma trilha completa:

  ```
  State â†’ Decision â†’ Outcome
  ```
* [ ] Cadeia temporal contÃ­nua
* [ ] Cadeia causal contÃ­nua
* [ ] Cadeia de processo Ãºnica

---

## 8. CritÃ©rio de AprovaÃ§Ã£o Final

O sistema Ã© considerado **VALIDADO MANUALMENTE** se:

* [ ] Todos os itens acima estiverem marcados
* [ ] Nenhum comportamento inesperado ocorrer
* [ ] Nenhuma violaÃ§Ã£o de contrato for observada
* [ ] Core permanece congelado

---

## 9. Encerramento

> Este checklist **nÃ£o autoriza alteraÃ§Ãµes**.
> Ele apenas **confirma conformidade**.

---


---

## Source: `docs/audit/release_audit_gate_d27_d33_v1_0.md`

# CortAI - Release Audit Gate Completo

Versao: `v1.0`
Aplica-se a: `CortAI >= D33`
Uso: auditoria completa antes do piloto real D23

## Objetivo

Confirmar que o sistema esta:

- funcional
- consistente
- seguro
- observavel
- operavel
- pronto para o piloto real

## Regra de decisao

### GO

Somente se houver:

- 0 falhas em testes
- 0 regressões criticas
- 0 duplicacoes indevidas de estado
- 0 vazamentos de estado entre execucoes
- 0 vulnerabilidades conhecidas relevantes
- 0 erros operacionais sem explicacao
- 0 caminhos criticos fora do comportamento planejado

### NO-GO

Se aparecer qualquer um destes:

- `publish_record` duplicado sem justificativa
- publicacao falsa em `DELAY` ou `BLOCK`
- idempotencia quebrada
- inconsistencia entre log e indice
- scheduler duplicando tasks
- worker executando sem lease
- metricas nao persistindo
- alertas/SLO incoerentes
- endpoint critico indisponivel
- segredo exposto
- fallback quebrado
- evento obrigatorio nao emitido

## Escopo desta auditoria

### Nucleo funcional

- `D27` - Content Pipeline Automation
- `D28` - Platform Safety Layer
- `D29` - Creative Pack Generator
- `D30` - Platform Intelligence
- `D31` - Experiment Framework
- `D32` - Advanced Attribution
- `D33` - Metrics Collector

### Regressões obrigatorias

- `D3` - publish_records
- `D16 / D16.5 / D17` - event storage, index, hot store
- `D19` - SLO + alerting
- `D20` - distributed execution
- `D21` - distributed scheduler
- `D22` - external integration
- `D23` - rollout policy
- `D24 / D24.5` - operator console / actions
- `D26` - strategy observatory

## Parte 1 - Testes automatizados

### 1. Testes principais do bloco atual

```powershell
python -m unittest -q ^
  tests.test_content_pipeline_d27_unittest ^
  tests.test_platform_safety_d28_unittest ^
  tests.test_creative_pack_generator_d29_unittest ^
  tests.test_platform_intelligence_d30_unittest ^
  tests.test_experiment_framework_d31_unittest ^
  tests.test_content_attribution_d32_unittest ^
  tests.test_metrics_collector_d33_unittest
```

Criterio:

- tudo verde
- nenhum skip relevante

### 2. Regressões criticas

```powershell
python -m unittest -q ^
  tests.test_publish_records_d3_unittest ^
  tests.test_event_index_d16_unittest ^
  tests.test_event_append_write_through_d16_5_unittest ^
  tests.test_hot_storage_d17_unittest ^
  tests.test_slo_alerting_d19_unittest ^
  tests.test_distributed_execution_d20_unittest ^
  tests.test_distributed_scheduler_d21_unittest ^
  tests.test_external_platform_integration_d22_unittest ^
  tests.test_real_batch_rollout_d23_unittest ^
  tests.test_operator_console_d24_unittest ^
  tests.test_operator_actions_d24_5_unittest ^
  tests.test_strategy_observatory_d26_unittest
```

Criterio:

- 0 falhas
- 0 regressões de comportamento

### 3. Compilacao / sanidade de import

```powershell
Get-ChildItem backend/app/content/pipeline/*.py | ForEach-Object { python -m py_compile $_.FullName }
Get-ChildItem backend/app/safety/*.py | ForEach-Object { python -m py_compile $_.FullName }
Get-ChildItem backend/app/content/creative_pack/*.py | ForEach-Object { python -m py_compile $_.FullName }
Get-ChildItem backend/app/intelligence/*.py | ForEach-Object { python -m py_compile $_.FullName }
Get-ChildItem backend/app/experiments/*.py | ForEach-Object { python -m py_compile $_.FullName }
Get-ChildItem backend/app/attribution/*.py | ForEach-Object { python -m py_compile $_.FullName }
Get-ChildItem backend/app/metrics/*.py | ForEach-Object { python -m py_compile $_.FullName }
```

Criterio:

- 0 erros de sintaxe/import

## Parte 2 - Verificacoes funcionais manuais

### 4. Content Pipeline (D27)

Validar:

- creative_pack gera render_job
- TTS gera artefato
- render gera video e metadata
- publish gera publish_record
- retry funciona
- duplicidade vira `NOOP`

Checklist:

- [ ] `OUT/content/audio/` tem arquivo
- [ ] `OUT/content/video/` tem arquivo
- [ ] `OUT/content/metadata/` tem arquivo
- [ ] nomes coerentes com `render_job_id`

NO-GO se:

- TTS/render nao gerarem artefatos
- publish_record nao persistir
- duplicidade gerar duas publicacoes

### 5. Safety Layer (D28)

Validar:

- `ALLOW -> PUBLISH_DONE`
- `DELAY -> DELAYED`
- `BLOCK -> BLOCKED`
- `PUBLISH_RATE_LIMIT -> risco alto + cooldown`

Checklist:

- [ ] `DELAY` nao cria `publish_record`
- [ ] `BLOCK` nao cria `publish_record`
- [ ] cooldown persistido em `OUT/safety/`
- [ ] pacing persistido em `OUT/safety/`
- [ ] eventos `SAFETY/*` emitidos

NO-GO se:

- `DELAY` ou `BLOCK` gerarem publicacao
- state nao persistir
- risk detector nao alterar estado

### 6. Creative Pack Generator (D29)

Validar:

- `creative_pack_id` deterministico
- variacoes estaveis
- persistencia append-only
- `WRITTEN | NOOP | CONFLICT`

Checklist:

- [ ] `OUT/content/creative_packs/creative_packs.jsonl` existe
- [ ] mesma chave logica -> `NOOP`
- [ ] payload diferente -> `CONFLICT`

NO-GO se:

- ID nao for estavel
- store sobrescrever historico
- conflito passar silenciosamente

### 7. Platform Intelligence (D30)

Validar:

- recomendacoes geradas
- risco por conta gerado
- account health snapshot persistido
- nenhuma mutacao do caminho de execucao

Checklist:

- [ ] `OUT/intelligence/publish_windows.jsonl`
- [ ] `OUT/intelligence/pacing_profiles.jsonl`
- [ ] `OUT/intelligence/risk_profiles.jsonl`
- [ ] `OUT/intelligence/account_health.jsonl`

NO-GO se:

- nao persistir
- gerar resultado inconsistente para mesmo input
- tocar em `publish`/`scheduler`/`safety` diretamente

### 8. Experiment Framework (D31)

Validar:

- experimento criado
- assignment deterministico
- mesma entrada -> mesma variante
- append-only consistente

Checklist:

- [ ] `OUT/experiments/experiments.jsonl`
- [ ] `OUT/experiments/assignments.jsonl`
- [ ] `OUT/experiments/results.jsonl`

NO-GO se:

- assignment variar entre execucoes identicas
- duplicidade nao virar `NOOP`

### 9. Advanced Attribution (D32)

Validar:

- hook analysis
- structure analysis
- duration analysis
- integracao com experiment assignments

Checklist:

- [ ] `OUT/attribution/hook_performance.jsonl`
- [ ] `OUT/attribution/structure_performance.jsonl`
- [ ] `OUT/attribution/duration_analysis.jsonl`
- [ ] `OUT/attribution/pattern_performance.jsonl`

NO-GO se:

- recomputacao for instavel
- dados inconsistentes quebrarem API
- attribution ignorar experiment assignments

### 10. Metrics Collector (D33)

Validar:

- coleta real/stub bem-sucedida
- append-only
- idempotencia por bucket logico
- compatibilidade com publish_record

Checklist:

- [ ] `OUT/metrics/video_metrics.jsonl` existe
- [ ] primeira coleta persiste linha
- [ ] coleta duplicada da mesma janela vira `NOOP`
- [ ] `publish_id` e `video_id` coerentes

NO-GO se:

- coleta nao persistir
- duplicar a mesma coleta
- quebrar por publish inexistente sem erro explicito

## Parte 3 - Observabilidade e eventos

### 11. Event sanity

Verificar presenca de eventos minimos:

#### CONTENT

- [ ] `CONTENT/tts_started`
- [ ] `CONTENT/tts_completed`
- [ ] `CONTENT/render_started`
- [ ] `CONTENT/render_completed`
- [ ] `CONTENT/publish_started`
- [ ] `CONTENT/publish_completed`
- [ ] `CONTENT/pipeline_failed` quando aplicavel

#### SAFETY

- [ ] `SAFETY/pacing_delay`
- [ ] `SAFETY/publish_blocked`
- [ ] `SAFETY/risk_detected`
- [ ] `SAFETY/cooldown_started`

#### METRICS

- [ ] `METRICS/collection_started`
- [ ] `METRICS/collection_completed`
- [ ] `METRICS/collection_failed` quando aplicavel

NO-GO se:

- eventos criticos nao forem emitidos
- eventos divergirem do contrato congelado

### 12. Event query / trace

```powershell
python -m unittest -q ^
  tests.test_event_query_forensics_and_scanner_d13_unittest ^
  tests.test_event_query_trace_builder_d13_unittest ^
  tests.test_event_query_seek_pagination_d14_unittest ^
  tests.test_event_query_api_endpoint_d15_unittest
```

Criterio:

- paginacao estavel
- cursor integro
- trace funcional
- anti-scan preservado

NO-GO se:

- cursor duplicar/perder eventos
- forensics policy falhar
- `/events` quebrar

## Parte 4 - Runtime, workers, scheduler e rollout

### 13. Workers / leases / idempotencia

```powershell
python -m unittest -q ^
  tests.test_distributed_execution_d20_unittest ^
  tests.test_concurrency_failure_matrix_d12_unittest
```

Validar:

- [ ] dois workers nao executam a mesma task ao mesmo tempo
- [ ] retry nao duplica efeito
- [ ] lease expirada aborta corretamente
- [ ] `op_key` duplicado -> `NOOP` ou `CONFLICT` correto

NO-GO se:

- double execution
- task duplicada
- lease bypass

### 14. Scheduler

```powershell
python -m unittest -q tests.test_distributed_scheduler_d21_unittest
```

Validar:

- [ ] janelas planejadas corretamente
- [ ] scheduler restart nao duplica task
- [ ] multiplas contas geram filas independentes

NO-GO se:

- scheduler criar task duplicada
- `window_id` inconsistente
- enqueue nao for idempotente

### 15. Rollout / allowlist / kill switch

```powershell
python -m unittest -q tests.test_real_batch_rollout_d23_unittest
```

Validar:

- [ ] allowlist bloqueia conta nao elegivel
- [ ] kill switch impede novas tasks
- [ ] worker respeita rollout policy
- [ ] artifacts do piloto sao produzidos no fluxo de teste

NO-GO se:

- rollout ignorar allowlist
- kill switch nao tiver efeito real

## Parte 5 - Operator layer

### 16. Console / Operator Actions / Strategy Observatory

```powershell
python -m unittest -q ^
  tests.test_operator_console_d24_unittest ^
  tests.test_operator_actions_d24_5_unittest ^
  tests.test_strategy_observatory_d26_unittest
```

Validar:

- [ ] console e read-only onde deve ser
- [ ] actions exigem reason
- [ ] requeue idempotente
- [ ] ack de alerta auditavel
- [ ] observatory liga patch -> window -> scorecard

NO-GO se:

- console expuser mutation indevida
- operator action contornar policy
- observatory quebrar vinculacao de dados

## Parte 6 - Infra, endpoints e probes

### 17. Health / Ready

Validar live:

- [ ] `GET /health` em `:8000` -> `200`
- [ ] `GET /ready` em `:8000` -> `200`
- [ ] `GET /health` em `:8002` -> `200`
- [ ] `GET /ready` em `:8002` -> `200`

Payload minimo esperado em `/ready`:

- [ ] `ready: true`
- [ ] `scheduler: ok`
- [ ] `workers >= 1`
- [ ] `queue: ok`
- [ ] `event_index: ok`
- [ ] `hot_store: ok`

NO-GO se:

- `/ready` nao responder `200`
- payload indicar componente critico indisponivel

## Parte 7 - Seguranca

### 18. Dependencias

```powershell
pip-audit
pip check
```

Criterio:

- [ ] sem vulnerabilidades conhecidas relevantes
- [ ] sem conflitos de dependencia

NO-GO se:

- vulnerabilidade alta/critica conhecida
- conflito de dependencia que possa quebrar runtime

### 19. Secrets / gitleaks

```powershell
gitleaks detect --source . -v
```

Validar:

- [ ] 0 leaks novos
- [ ] fingerprints historicos aceitos documentados
- [ ] nenhum token atual exposto

NO-GO se:

- segredo novo em `HEAD`
- segredo real exposto sem rotacao/aceitacao formal

## Parte 8 - Evidencias e artefatos

### 20. Diretorios que devem existir

Confirmar:

- [ ] `OUT/content/`
- [ ] `OUT/safety/`
- [ ] `OUT/intelligence/`
- [ ] `OUT/experiments/`
- [ ] `OUT/attribution/`
- [ ] `OUT/metrics/`
- [ ] `OUT/ops/`
- [ ] `OUT/rollout/` se houver execucao piloto/operacional simulada

NO-GO se:

- modulo persiste em lugar errado
- artefatos criticos nao forem produzidos

## Parte 9 - Relatorio da auditoria

### 21. Gerar evidencias

Salvar em:

- `OUT/audit/D27_D33/`

Arquivos minimos:

- `AUDIT_REPORT.md`
- `pytest_d27_d33.txt`
- `content_artifacts_check.txt`
- `safety_artifacts_check.txt`
- `intelligence_artifacts_check.txt`
- `metrics_artifacts_check.txt`
- `event_sanity.txt`
- `infra_health.txt`
- `security_scan.txt`
- `py_compile.txt`

## Estrutura do veredito final

Se tudo passar:

- Gate de codigo: `PASS`
- Gate operacional: `PASS`
- Gate de seguranca: `PASS`
- Gate para prosseguir: `GO`

Se qualquer ponto critico falhar:

- Gate de codigo: `PASS/FAIL`
- Gate operacional: `PASS/FAIL`
- Gate de seguranca: `PASS/FAIL`
- Gate para prosseguir: `NO-GO`

## Leitura final correta

Se esse checklist ficar verde, voce podera dizer com confianca:

- o CortAI esta integralmente conforme o planejado
- a base tecnica esta consistente
- a operacao esta segura
- o sistema esta pronto para o piloto real
- o que resta e apenas a condicao externa das contas


---

## Source: `docs/cognitive/ACTION.md`

# Action

## Objetivo

A **Action** representa uma **instruÃ§Ã£o executÃ¡vel formal** derivada de uma `Decision`.

Ela descreve **o que deve ser feito no mundo interno ou externo**, mas **nÃ£o contÃ©m lÃ³gica decisÃ³ria**.

> Action Ã© execuÃ§Ã£o declarada, nÃ£o raciocÃ­nio.

---

## Papel no Modelo Cognitivo

Fluxo canÃ´nico:

```

State â†’ Decision â†’ Action â†’ Outcome

````

A `Action`:
- Ã© criada a partir de uma Decision
- Ã© executada por um Executor
- produz exatamente um Outcome

---

## DefiniÃ§Ã£o Conceitual

**Action Ã© uma unidade atÃ´mica de execuÃ§Ã£o, semanticamente tipada, que transforma o estado do sistema ou do ambiente externo.**

Ela Ã©:
- explÃ­cita
- rastreÃ¡vel
- validÃ¡vel
- reexecutÃ¡vel

---

## Estrutura CanÃ´nica

```python
Action {
    action_id: UUID
    decision_id: UUID
    timestamp: datetime

    type: ActionType
    parameters: dict

    execution_policy: ExecutionPolicy
    invariants: ActionInvariants
}
````

---

## Componentes da Action

### 1. Identidade & ReferÃªncia

```python
action_id: UUID
decision_id: UUID
timestamp: datetime
```

**Invariantes**

* Uma Action pertence a exatamente uma Decision
* Uma Action nÃ£o existe sem Decision
* Uma Action Ã© imutÃ¡vel apÃ³s criada

---

### 2. Tipo da Action

```python
ActionType = Enum(
    "TRANSCRIBE_AUDIO",
    "SEGMENT_AUDIO",
    "CUT_VIDEO_SEGMENT",
    "GENERATE_CAPTION",
    "WRITE_FILE",
    "PUBLISH_CONTENT",
    "DISCARD_SEGMENT"
)
```

Define **o domÃ­nio semÃ¢ntico da execuÃ§Ã£o**.

**Invariantes**

* O tipo determina o Executor elegÃ­vel
* Tipos sÃ£o estÃ¡veis e versionÃ¡veis

---

### 3. ParÃ¢metros

```python
parameters: dict
```

ContÃ©m **todos os dados necessÃ¡rios para execuÃ§Ã£o**, sem dependÃªncia implÃ­cita de contexto.

Exemplos:

```json
{
  "start_time": 120.5,
  "end_time": 145.2,
  "output_path": "/clips/highlight.mp4"
}
```

**Invariantes**

* Nenhum parÃ¢metro pode ser inferido
* Todos os parÃ¢metros devem ser serializÃ¡veis

---

### 4. Execution Policy

```python
ExecutionPolicy {
    retry_allowed: bool
    max_retries: int
    timeout_ms: int
    idempotent: bool
}
```

Define **como a Action pode ser executada**, nÃ£o *se* serÃ¡ executada.

**Invariantes**

* Retry nunca altera parÃ¢metros
* Actions idempotentes podem ser reexecutadas sem efeitos colaterais

---

### 5. Invariantes da Action

```python
ActionInvariants {
    requires_state_snapshot: bool
    produces_side_effects: bool
    reversible: bool
}
```

Define propriedades fundamentais da Action.

**Exemplos**

* `WRITE_FILE` â†’ `produces_side_effects = true`
* `DISCARD_SEGMENT` â†’ `reversible = false`

---

## Propriedades Fundamentais

### Atomicidade

* Action Ã© tudo ou nada
* Falha parcial Ã© proibida

### Isolamento

* Uma Action nÃ£o conhece outras Actions
* CoordenaÃ§Ã£o ocorre fora (Executor / Orquestrador)

### ReexecuÃ§Ã£o Controlada

* Permitida apenas se idempotente
* Sempre rastreÃ¡vel

---

## Anti-PadrÃµes (Proibidos)

* LÃ³gica de decisÃ£o dentro da Action
* Leitura direta do State
* ModificaÃ§Ã£o implÃ­cita de contexto
* Actions genÃ©ricas sem tipo claro

---

## RelaÃ§Ã£o com Outros Contratos

| Contrato | RelaÃ§Ã£o                    |
| -------- | -------------------------- |
| Decision | Origina a Action           |
| Executor | Executa a Action           |
| Outcome  | Resultado da execuÃ§Ã£o      |
| State    | Nunca acessado diretamente |

---

## Exemplo Completo

```json
{
  "action_id": "uuid-301",
  "decision_id": "uuid-900",
  "timestamp": "2026-01-22T22:45:10Z",
  "type": "CUT_VIDEO_SEGMENT",
  "parameters": {
    "start_time": 120.5,
    "end_time": 145.2,
    "output_path": "/clips/highlight.mp4"
  },
  "execution_policy": {
    "retry_allowed": true,
    "max_retries": 2,
    "timeout_ms": 5000,
    "idempotent": true
  },
  "invariants": {
    "requires_state_snapshot": true,
    "produces_side_effects": true,
    "reversible": false
  }
}
```

---


---

## Source: `docs/cognitive/AGENT_REGISTRY.md`

---

# Agent Registry â€” Contrato CanÃ´nico

## 1. Objetivo

O **Agent Registry** Ã© o componente arquitetural responsÃ¡vel por mapear **Actions** (definidas no domÃ­nio cognitivo) para **Agentes** executÃ¡veis concretos no sistema.

Ele atua como uma camada de resoluÃ§Ã£o estrita entre:

* O modelo cognitivo (`Decision` / `Action`)
* Os agentes estruturais do CortAI

> **Nota CrÃ­tica:** O Registry Ã© puramente um diretÃ³rio de resoluÃ§Ã£o. Ele **NÃƒO** toma decisÃµes e **NÃƒO** executa aÃ§Ãµes.

---

## 2. Responsabilidades

Abaixo estÃ£o definidos os limites de atuaÃ§Ã£o do componente:

### **O Agent Registry DEVE:**

* **Resolver** uma `Action` para um `Agent` vÃ¡lido.
* **Garantir** que apenas Actions conhecidas e registradas sejam processadas.
* **Ser DeterminÃ­stico:** Para uma mesma `Action`, deve retornar sempre o mesmo `Agent`.
* **Ser ExtensÃ­vel:** Permitir novos registros sem quebrar contratos existentes.

### **O Agent Registry NÃƒO DEVE:**

* Executar lÃ³gica de negÃ³cio.
* Alterar o estado do sistema (`State`).
* Criar novas decisÃµes (`Decisions`).
* Implementar estratÃ©gias de resiliÃªncia (*retries* ou *fallbacks*).
* Comunicar-se diretamente com a infraestrutura (bancos de dados, filas, APIs externas).

---

## 3. Interface Conceitual

A interaÃ§Ã£o com o Registry segue um padrÃ£o simples de entrada e saÃ­da.

### Entrada

Recebe uma `Action` formalmente vÃ¡lida contendo seu tipo e dados.

```json
{
  "action_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "segment_audio",
  "payload": {
    "source_uri": "s3://bucket/file.mp3",
    "strategy": "silence_detection"
  }
}

```

### SaÃ­da e Assinatura

Retorna uma referÃªncia Ã  classe ou instÃ¢ncia do Agente executÃ¡vel.

```typescript
// Assinatura Conceitual
function resolve(action: Action): Agent

```

---

## 4. Invariantes

Para manter a integridade do sistema, as seguintes regras sÃ£o absolutas:

1. **Unicidade:** Todo `Action.type` deve ter **exatamente UM** agente responsÃ¡vel.
2. **Registro ObrigatÃ³rio:** Se uma Action nÃ£o estiver registrada, a resoluÃ§Ã£o deve falhar imediatamente.
3. **Atomicidade de ResoluÃ§Ã£o:** O Registry jamais retorna mÃºltiplos agentes para uma Ãºnica Action.
4. **Passividade:** O Registry nÃ£o invoca o mÃ©todo `execute()` do Agente â€” ele apenas entrega a referÃªncia.

---

## 5. Actions CanÃ´nicas e Agentes Correspondentes

A tabela abaixo define o mapeamento oficial entre intenÃ§Ãµes cognitivas e executores estruturais.

| Action Type (`Action.type`) | Agent ResponsÃ¡vel |
| --- | --- |
| `collect_video` | **CollectorAgent** |
| `segment_audio` | **SegmenterAgent** |
| `transcribe_segments` | **TranscriberAgent** |
| `write_artifact` | **FileWriterAgent** |

> **Extensibilidade:** Novas Actions sÃ³ podem ser adicionadas atravÃ©s de uma extensÃ£o explÃ­cita no cÃ³digo ou configuraÃ§Ã£o do Registry.

---

## 6. Erros e Falhas

O tratamento de erros no Registry Ã© rÃ­gido, pois indica problemas na configuraÃ§Ã£o do sistema, nÃ£o no fluxo de negÃ³cio.

* **Action Desconhecida:** Dispara um **erro imediato de resoluÃ§Ã£o**.
* **Agent Ausente/InvÃ¡lido:** Dispara um **erro estrutural**.
* **Sem RecuperaÃ§Ã£o:** O Registry **NÃƒO** tenta *fallback* ou *retry*.

**ClassificaÃ§Ã£o:** Toda falha no Registry Ã© considerada uma **falha estrutural** (bug/configuraÃ§Ã£o), nunca uma falha cognitiva.

---

## 7. RelaÃ§Ã£o com o Executor

O Agent Registry funciona como um prÃ©-requisito obrigatÃ³rio para o **Executor Cognitivo**. O fluxo de interaÃ§Ã£o segue a ordem:

1. **Executor** recebe uma `Action`.
2. **Executor** consulta o **Agent Registry**.
3. **Executor** invoca o `Agent` retornado pelo Registry.
4. **Executor** captura o `Outcome` (resultado).

---


---

## Source: `docs/cognitive/COGNITIVE_LOOP.md`

# Executor Cognitivo MÃ­nimo

## 1. DefiniÃ§Ã£o

O **Executor Cognitivo MÃ­nimo** Ã© o componente responsÃ¡vel por **transformar uma Decision em execuÃ§Ã£o real**, conectando:

```
Decision â†’ Actions â†’ Agents â†’ Outcome
```

Ele **nÃ£o decide**, **nÃ£o aprende**, **nÃ£o reordena aÃ§Ãµes** e **nÃ£o cria novas Decisions**.
Sua funÃ§Ã£o Ã© puramente **determinÃ­stica e operacional**.

---

## 2. Responsabilidades

O Executor DEVE:

* Receber uma **Decision vÃ¡lida**
* Iterar sobre a lista ordenada de **Actions**
* Resolver cada Action via **Agent Registry**
* Executar o Agent correspondente
* Coletar resultados ou falhas
* Gerar exatamente **um Outcome** ao final

O Executor NÃƒO DEVE:

* Criar ou alterar Decisions
* Alterar a ordem das Actions
* Executar Actions fora da Decision
* Persistir State
* Tomar decisÃµes cognitivas

---

## 3. Contrato de Entrada

### Input: Decision

```json
{
  "decision_id": "uuid",
  "process_id": "uuid",
  "actions": ["COLLECT_VIDEO", "SEGMENT_AUDIO", "TRANSCRIBE_SEGMENTS"],
  "status": "pending"
}
```

PrÃ©-condiÃ§Ãµes:

* `actions` deve ser uma lista nÃ£o vazia
* Todas as Actions devem existir no Agent Registry

---

## 4. Contrato de SaÃ­da

### Output: Outcome

```json
{
  "outcome_id": "uuid",
  "process_id": "uuid",
  "source_decision_id": "uuid",
  "status": "success | partial_failure | failure",
  "action_results": [
    {
      "action": "COLLECT_VIDEO",
      "status": "success",
      "data": {}
    }
  ],
  "timestamp": "ISO-8601"
}
```

---

## 5. Fluxo de ExecuÃ§Ã£o CanÃ´nico

```
start
  â†“
load Decision
  â†“
for action in Decision.actions:
    resolve Agent via Registry
    execute Agent
    record result
    if fatal failure:
        break
  â†“
build Outcome
  â†“
end
```

---

## 6. PolÃ­tica de Falha (mÃ­nima)

* Falha em uma Action:

  * interrompe o loop
  * Outcome.status = `failure`

* Falha parcial (futuro):

  * algumas Actions executadas
  * Outcome.status = `partial_failure`

O Executor **nÃ£o faz retry**.
Retry Ã© responsabilidade do **loop cognitivo**.

---

## 7. PosiÃ§Ã£o na Arquitetura

```
Camada 6 â€” Pipelines DeterminÃ­sticos
â””â”€â”€ Executor Cognitivo
```

---

## 8. Invariantes

* Uma Decision gera no mÃ¡ximo **um Outcome**
* Actions sÃ£o executadas **em ordem**
* Executor Ã© stateless
* ExecuÃ§Ã£o Ã© reproduzÃ­vel

---

## 9. Exemplo Simplificado

Decision:

```
[COLLECT_VIDEO â†’ SEGMENT_AUDIO â†’ TRANSCRIBE_SEGMENTS]
```

Executor:

* chama CollectorAgent
* passa resultado para SegmenterAgent
* passa segmentos para TranscriberAgent
* gera Outcome final

---

Este Executor Ã© a ponte entre cogniÃ§Ã£o e realidade.


---

## Source: `docs/cognitive/DECISION.md`

# Decision

## Objetivo

A **Decision** representa o **resultado lÃ³gico do raciocÃ­nio** do CortAI a partir de um determinado `State`.

Ela define **o que deve ser feito**, mas **nÃ£o executa nada**.

> Decision Ã© intenÃ§Ã£o formalizada, nÃ£o aÃ§Ã£o.

---

## Papel no Modelo Cognitivo

Fluxo canÃ´nico:

```

State â†’ Decision â†’ Action â†’ Outcome

````

A `Decision`:
- interpreta o State
- seleciona um curso de aÃ§Ã£o
- mantÃ©m justificativa explÃ­cita
- permite auditoria e replay

---

## DefiniÃ§Ã£o Conceitual

**Decision Ã© a escolha determinÃ­stica (ou probabilÃ­stica controlada) de uma ou mais Actions, baseada exclusivamente no State atual.**

Ela atua como **ponte cognitiva** entre percepÃ§Ã£o e execuÃ§Ã£o.

---

## Estrutura CanÃ´nica

```python
Decision {
    decision_id: UUID
    state_id: UUID
    timestamp: datetime

    intent: DecisionIntent
    actions: List[ActionDescriptor]

    rationale: DecisionRationale
    confidence: float

    constraints: DecisionConstraints
}
````

---

## Componentes da Decision

### 1. Identidade & ReferÃªncia

```python
decision_id: UUID
state_id: UUID
timestamp: datetime
```

* `decision_id`: identifica unicamente a decisÃ£o
* `state_id`: State que originou a decisÃ£o
* `timestamp`: momento da decisÃ£o

**Invariantes**

* Uma Decision referencia exatamente **um State**
* Uma Decision nunca altera o State

---

### 2. Intent (IntenÃ§Ã£o)

```python
DecisionIntent {
    type: str
    description: str
}
```

Define **o objetivo cognitivo** da decisÃ£o.

Exemplos:

* `"segment_relevant_content"`
* `"generate_highlight"`
* `"discard_low_value_segment"`

**Invariantes**

* IntenÃ§Ã£o Ã© declarativa
* NÃ£o contÃ©m lÃ³gica de execuÃ§Ã£o

---

### 3. Actions Planejadas

```python
actions: List[ActionDescriptor]
```

Cada `ActionDescriptor` define:

* tipo de Action
* parÃ¢metros necessÃ¡rios
* ordem de execuÃ§Ã£o (se aplicÃ¡vel)

```python
ActionDescriptor {
    action_type: str
    parameters: dict
    priority: int
}
```

**Invariantes**

* Decision pode conter **zero ou mais Actions**
* Nenhuma Action Ã© executada neste estÃ¡gio

---

### 4. Rationale (Justificativa)

```python
DecisionRationale {
    summary: str
    signals: List[str]
    supporting_metrics: Dict[str, float]
}
```

Explica **por que** a decisÃ£o foi tomada.

**Exemplos de sinais**

* `"high_speech_density"`
* `"semantic_peak_detected"`
* `"low_confidence_transcription"`

**Invariantes**

* Rationale Ã© sempre legÃ­vel por humanos
* Baseada apenas em dados do State

---

### 5. ConfianÃ§a

```python
confidence: float  # intervalo [0.0, 1.0]
```

Indica o grau de seguranÃ§a da decisÃ£o.

**Invariantes**

* Nunca usada diretamente para executar
* Pode ser usada para:

  * auditoria
  * fallback
  * anÃ¡lise offline

---

### 6. Constraints (RestriÃ§Ãµes)

```python
DecisionConstraints {
    max_execution_time_ms: Optional[int]
    allow_parallel_execution: bool
    required_executor: Optional[str]
}
```

Define limites para execuÃ§Ã£o futura das Actions.

**Invariantes**

* Constraints limitam, nÃ£o obrigam
* Executor pode rejeitar execuÃ§Ã£o se violadas

---

## Propriedades Fundamentais

### Determinismo Controlado

* Mesmo State + mesmas regras â†’ mesma Decision
* Qualquer aleatoriedade deve ser explÃ­cita e rastreÃ¡vel

### SeparaÃ§Ã£o Total de ExecuÃ§Ã£o

* Decision **nunca executa**
* Decision **nÃ£o conhece infraestrutura**

### Auditabilidade

* Toda decisÃ£o Ã© explicÃ¡vel
* Toda decisÃ£o pode ser reavaliada offline

---

## Anti-PadrÃµes (Proibidos)

* Executar lÃ³gica de Action dentro da Decision
* Alterar State
* Tomar decisÃµes sem referÃªncia explÃ­cita ao State
* Ocultar rationale

---

## RelaÃ§Ã£o com Outros Contratos

| Contrato | RelaÃ§Ã£o com Decision    |
| -------- | ----------------------- |
| State    | Fonte Ãºnica             |
| Action   | Planejada pela Decision |
| Executor | Executa Actions         |
| Outcome  | Resultado da execuÃ§Ã£o   |

---

## Exemplo Simplificado

```json
{
  "decision_id": "uuid-900",
  "state_id": "uuid-123",
  "timestamp": "2026-01-22T22:43:10Z",
  "intent": {
    "type": "generate_highlight",
    "description": "Criar clipe a partir de pico semÃ¢ntico"
  },
  "actions": [
    {
      "action_type": "CUT_VIDEO_SEGMENT",
      "parameters": {
        "start": 120.5,
        "end": 145.2
      },
      "priority": 1
    }
  ],
  "rationale": {
    "summary": "Pico semÃ¢ntico detectado com alta densidade de fala",
    "signals": ["semantic_peak", "high_engagement_window"],
    "supporting_metrics": {
      "semantic_score": 0.91
    }
  },
  "confidence": 0.88,
  "constraints": {
    "max_execution_time_ms": 5000,
    "allow_parallel_execution": false
  }
}
```

---


---

## Source: `docs/cognitive/EVENT_LOG.md`

# Event Log

## Objetivo

O **Event Log** Ã© o **registro linear, imutÃ¡vel e ordenado de todos os eventos observÃ¡veis do CortAI**, internos e externos.

> O sistema **nÃ£o lembra estados passados** â€”
> ele **reconstrÃ³i tudo a partir de eventos**.

---

## Papel no Sistema

O Event Log Ã© a **espinha dorsal da auditabilidade, rastreabilidade e replay** do CortAI.

Ele permite:
- reconstruÃ§Ã£o completa do State
- anÃ¡lise pÃ³s-morte (post-mortem)
- debugging determinÃ­stico
- mÃ©tricas e monitoramento
- simulaÃ§Ãµes e replays cognitivos

---

## PrincÃ­pio Fundamental

> **Nada acontece no sistema sem gerar um evento.**

Se algo ocorreu e nÃ£o estÃ¡ no Event Log:
- Ã© invisÃ­vel
- Ã© irrelevante
- Ã© considerado inexistente

---

## DefiniÃ§Ã£o Conceitual

Um **Evento** Ã© o **registro atÃ´mico de algo que aconteceu**, em um instante especÃ­fico, com contexto suficiente para ser interpretado no futuro â€” sem ambiguidade.

Eventos:
- nÃ£o tÃªm intenÃ§Ã£o
- nÃ£o tomam decisÃµes
- nÃ£o causam efeitos diretos
- apenas registram fatos

---

## Estrutura CanÃ´nica do Evento

```python
Event {
    event_id: UUID
    event_type: EventType
    source: EventSource

    related_ids: dict
    payload: dict

    timestamp: datetime
    version: int
}
````

---

## Identificadores

### event_id

Identificador Ãºnico do evento.

**Invariantes**

* Nunca reutilizado
* Nunca modificado

---

## Tipo do Evento

```python
EventType = Enum(
    "OBSERVATION_RECORDED",
    "STATE_SNAPSHOT_CREATED",

    "DECISION_CREATED",

    "ACTION_CREATED",
    "ACTION_DISPATCHED",

    "ACTION_EXECUTED",
    "ACTION_FAILED",
    "ACTION_PARTIAL",

    "OUTCOME_RECORDED",

    "PIPELINE_PHASE_STARTED",
    "PIPELINE_PHASE_COMPLETED",

    "EXTERNAL_INPUT_RECEIVED",
    "ERROR_RAISED"
)
```

**Invariantes**

* Todo evento possui exatamente um tipo
* Tipos sÃ£o fechados (nÃ£o dinÃ¢micos)

---

## Fonte do Evento

```python
EventSource = Enum(
    "SYSTEM",
    "COGNITIVE_CORE",
    "PIPELINE",
    "AGENT",
    "EXECUTOR",
    "EXTERNAL"
)
```

Define **quem originou o evento**, nÃ£o quem serÃ¡ afetado.

---

## related_ids

```python
related_ids: {
    state_id?: UUID
    decision_id?: UUID
    action_id?: UUID
    outcome_id?: UUID
    agent_id?: UUID
}
```

Relaciona o evento a entidades do sistema.

**Invariantes**

* IDs ausentes significam â€œnÃ£o aplicÃ¡velâ€
* Nunca referencia entidades inexistentes

---

## Payload

```python
payload: dict
```

Dados especÃ­ficos do evento.

Exemplos:

* resumo da decisÃ£o
* erro ocorrido
* mÃ©tricas da fase
* metadados externos

**Invariantes**

* Payload nunca contÃ©m lÃ³gica
* Payload nunca altera comportamento
* Payload Ã© interpretÃ¡vel no futuro

---

## Timestamp

```python
timestamp: datetime
```

Momento exato da ocorrÃªncia.

**Invariantes**

* UTC obrigatÃ³rio
* Eventos sÃ£o totalmente ordenÃ¡veis no tempo

---

## Versionamento do Evento

```python
version: int
```

VersÃ£o do schema do evento.

**Invariantes**

* VersÃ£o nunca retrocede
* Permite evoluÃ§Ã£o sem quebrar replay

---

## Imutabilidade

Uma vez gravado:

* evento **nunca Ã© alterado**
* correÃ§Ãµes geram novos eventos
* histÃ³rico sempre preservado

---

## RelaÃ§Ã£o com State

* State **nÃ£o Ã© armazenado como verdade**
* State Ã© derivado do Event Log
* Snapshots apenas aceleram reconstruÃ§Ã£o

---

## RelaÃ§Ã£o com Outcome

* Todo Outcome gera pelo menos um evento
* Outcome **nÃ£o substitui evento**
* Evento Ã© a trilha; Outcome Ã© o artefato

---

## Eventos Internos vs Externos

### Eventos Internos

Gerados pelo prÃ³prio sistema:

* decisÃµes
* execuÃ§Ãµes
* erros
* transiÃ§Ãµes

### Eventos Externos

Entradas do mundo real:

* upload de mÃ­dia
* inputs do usuÃ¡rio
* sinais externos

Ambos sÃ£o tratados **de forma idÃªntica** no log.

---

## Exemplo de Evento (ExecuÃ§Ã£o de Action)

```json
{
  "event_id": "uuid",
  "event_type": "ACTION_EXECUTED",
  "source": "EXECUTOR",
  "related_ids": {
    "action_id": "uuid",
    "outcome_id": "uuid"
  },
  "payload": {
    "status": "SUCCESS"
  },
  "timestamp": "2026-01-22T19:34:12Z",
  "version": 1
}
```

---

## Replay Cognitivo

O sistema pode:

1. limpar o State atual
2. reler eventos em ordem
3. reconstruir decisÃµes, aÃ§Ãµes e outcomes
4. validar consistÃªncia

Sem heurÃ­sticas.
Sem inferÃªncias ocultas.

---

## Anti-PadrÃµes (Proibidos)

* alterar evento apÃ³s gravaÃ§Ã£o
* apagar eventos
* usar evento como decisÃ£o
* usar evento como estado

---

## Propriedades Fundamentais

### Determinismo

Mesmo log â†’ mesmo sistema reconstruÃ­do.

### Auditabilidade Total

Nada Ã© perdido.

### Observabilidade Completa

Tudo Ã© explicÃ¡vel.

---


---

## Source: `docs/cognitive/EXECUTOR.md`

# Executor

## Objetivo

O **Executor** Ã© o componente responsÃ¡vel por **executar uma Action** de forma controlada, observÃ¡vel e rastreÃ¡vel, produzindo exatamente um `Outcome`.

> Executor executa.
> Ele nÃ£o decide, nÃ£o interpreta, nÃ£o infere.

---

## Papel no Modelo Cognitivo

Fluxo canÃ´nico:

```

State â†’ Decision â†’ Action â†’ Executor â†’ Outcome

````

O Executor:
- recebe uma Action vÃ¡lida
- valida invariantes de execuÃ§Ã£o
- executa exatamente uma vez por tentativa
- registra o resultado como Outcome

---

## DefiniÃ§Ã£o Conceitual

**Executor Ã© um mecanismo operacional determinÃ­stico que transforma uma Action em um Outcome, respeitando polÃ­ticas de execuÃ§Ã£o e invariantes formais.**

Ele Ã©:
- substituÃ­vel
- isolado
- especializado por tipo de Action

---

## Estrutura Conceitual

```python
Executor {
    executor_id: UUID
    supported_action_types: List[ActionType]
    execution_mode: ExecutionMode
    capabilities: ExecutorCapabilities
}
````

---

## Componentes do Executor

### 1. Identidade

```python
executor_id: UUID
```

Identifica unicamente a instÃ¢ncia lÃ³gica do Executor.

**Invariantes**

* Executor Ã© versionÃ¡vel
* Executor pode ter mÃºltiplas instÃ¢ncias fÃ­sicas

---

### 2. Tipos de Action Suportados

```python
supported_action_types: List[ActionType]
```

Define **quais Actions este Executor pode executar**.

**Invariantes**

* Um Executor nunca executa Actions fora dessa lista
* Uma Action sÃ³ pode ser executada por Executor compatÃ­vel

---

### 3. Modo de ExecuÃ§Ã£o

```python
ExecutionMode = Enum(
    "SYNC",
    "ASYNC",
    "BATCH"
)
```

Define **como a execuÃ§Ã£o ocorre**, nÃ£o *quando*.

---

### 4. Capacidades do Executor

```python
ExecutorCapabilities {
    supports_retry: bool
    supports_idempotency: bool
    supports_timeouts: bool
    supports_side_effects: bool
}
```

**Invariantes**

* Capacidades devem ser compatÃ­veis com `ExecutionPolicy` da Action
* Incompatibilidade â†’ falha imediata

---

## Interface CanÃ´nica de ExecuÃ§Ã£o

```python
execute(action: Action) -> Outcome
```

### Regras da Interface

* Uma chamada â†’ um Outcome
* NÃ£o pode lanÃ§ar exceÃ§Ãµes nÃ£o capturadas
* Falha sempre retorna Outcome com status `FAILED`

---

## Ciclo de Vida da ExecuÃ§Ã£o

```text
1. Receber Action
2. Validar ActionType
3. Validar ExecutionPolicy
4. Executar aÃ§Ã£o concreta
5. Capturar efeitos e mÃ©tricas
6. Emitir Outcome
```

---

## ValidaÃ§Ãµes ObrigatÃ³rias

Antes da execuÃ§Ã£o:

* ActionType suportado
* ParÃ¢metros completos
* Policy compatÃ­vel
* Invariantes respeitados

ApÃ³s a execuÃ§Ã£o:

* Resultado materializado
* MÃ©tricas coletadas
* Status determinado

---

## Outcome Produzido

O Executor **Ã© o Ãºnico responsÃ¡vel** por produzir o `Outcome`.

Ele define:

* status (SUCCESS / FAILED / PARTIAL)
* outputs
* mÃ©tricas
* erros (se houver)

---

## Tipos de Executor (Exemplos)

### FileExecutor

* WRITE_FILE
* READ_FILE

### MediaExecutor

* CUT_VIDEO_SEGMENT
* MERGE_CLIPS

### AIExecutor

* TRANSCRIBE_AUDIO
* GENERATE_CAPTION

### NullExecutor

* DISCARD_SEGMENT

---

## Propriedades Fundamentais

### Determinismo

* Mesma Action + mesmo ambiente â†’ mesmo Outcome (quando idempotente)

### Isolamento

* Executor nÃ£o acessa State diretamente
* Executor nÃ£o cria Decisions

### Observabilidade

* Toda execuÃ§Ã£o Ã© logÃ¡vel
* Toda falha Ã© rastreÃ¡vel

---

## Anti-PadrÃµes (Proibidos)

* Executor decidir qual Action executar
* Executor modificar State
* Executor executar mÃºltiplas Actions
* LÃ³gica cognitiva dentro do Executor

---

## RelaÃ§Ã£o com Outros Contratos

| Contrato  | RelaÃ§Ã£o                      |
| --------- | ---------------------------- |
| Action    | Entrada obrigatÃ³ria          |
| Decision  | Origem indireta              |
| Outcome   | SaÃ­da obrigatÃ³ria            |
| Event Log | Fonte de eventos de execuÃ§Ã£o |

---

## Exemplo Conceitual

```python
class MediaExecutor(Executor):
    supported_action_types = ["CUT_VIDEO_SEGMENT"]

    def execute(self, action):
        clip = cut_video(
            action.parameters["start_time"],
            action.parameters["end_time"]
        )

        return Outcome.success(outputs={"clip_path": clip})
```

---


---

## Source: `docs/cognitive/INDEX.md`

# Contratos Estruturais â€” VisÃ£o Geral

Este documento apresenta a **visÃ£o geral** dos contratos estruturais do sistema **CortAI**. Os contratos definem, de forma formal e verificÃ¡vel, como informaÃ§Ã£o, decisÃ£o e execuÃ§Ã£o fluem pelo sistema.

> **Importante**: estes contratos **nÃ£o sÃ£o implementaÃ§Ãµes**. Eles estabelecem **invariantes, responsabilidades e limites**. Qualquer cÃ³digo futuro **deve obedecer estritamente** a estas definiÃ§Ãµes.

---

## Objetivo dos Contratos

Os contratos existem para:

* Eliminar ambiguidade arquitetural
* Separar **observaÃ§Ã£o**, **estado**, **decisÃ£o** e **execuÃ§Ã£o**
* Permitir versionamento, auditoria e replay
* Garantir previsibilidade e rastreabilidade
* Viabilizar testes determinÃ­sticos

---

## PrincÃ­pios Fundamentais

1. **Nada acontece sem ser observado**
2. **Nenhuma decisÃ£o ocorre fora de um estado conhecido**
3. **Nenhuma aÃ§Ã£o Ã© executada sem um executor explÃ­cito**
4. **Todo efeito gera um outcome verificÃ¡vel**
5. **Todo estado Ã© versionÃ¡vel e recuperÃ¡vel**
6. **Todo evento Ã© registrÃ¡vel**

---

## Fluxo CanÃ´nico do Sistema

```
Observation
   â†“
State (snapshot/version)
   â†“
Decision
   â†“
Action
   â†“
Executor
   â†“
Outcome
   â†“
Event Log
   â†“
State (nova versÃ£o)
```

Este fluxo Ã© **obrigatÃ³rio**. Nenhuma etapa pode ser pulada, fundida ou implÃ­cita.

---

## Contratos Definidos

### 1. Observation

Representa qualquer entrada percebida pelo sistema, interna ou externa.

* Pode ser externa (API, usuÃ¡rio, ambiente)
* Pode ser interna (telemetria, mÃ©tricas, timers)
* NÃ£o altera estado diretamente

ðŸ“„ Documento: `observation.md`

---

### 2. State

Representa o estado **imutÃ¡vel** do sistema em um ponto no tempo.

* Sempre versionado
* Derivado apenas de eventos vÃ¡lidos
* Nunca mutado diretamente

ðŸ“„ Documento: `state.md`

---

### 3. State Versioning & Snapshots

Define como estados sÃ£o armazenados, comparados e restaurados.

* Versionamento sequencial
* Snapshots opcionais
* Suporte a replay

ðŸ“„ Documento: `state_versioning.md`

---

### 4. Event Log

Registro cronolÃ³gico de tudo que ocorreu no sistema.

* Eventos internos e externos
* Fonte Ãºnica da verdade histÃ³rica
* Base para auditoria e replay

ðŸ“„ Documento: `event_log.md`

---

### 5. Decision

Resultado de um processo de inferÃªncia sobre um estado.

* NÃ£o executa aÃ§Ãµes
* NÃ£o altera estado
* Apenas **propÃµe** aÃ§Ãµes

ðŸ“„ Documento: `decision.md`

---

### 6. Action

Representa uma intenÃ§Ã£o de execuÃ§Ã£o concreta.

* Tipada
* ValidÃ¡vel
* ExecutÃ¡vel apenas por um Executor

ðŸ“„ Documento: `action.md`

---

### 7. Executor

Entidade responsÃ¡vel por executar aÃ§Ãµes.

* Humano, sistema ou agente
* Explicitamente identificado
* ResponsÃ¡vel pelo efeito gerado

ðŸ“„ Documento: `executor.md`

---

### 8. Outcome

Resultado observÃ¡vel da execuÃ§Ã£o de uma aÃ§Ã£o.

* Sucesso, falha ou efeito parcial
* Gera eventos
* Pode causar novo estado

ðŸ“„ Documento: `outcome.md`

---

## RelaÃ§Ã£o entre Contratos

| Contrato    | Depende de | Produz   |
| ----------- | ---------- | -------- |
| Observation | â€”          | Event    |
| State       | Event Log  | Snapshot |
| Decision    | State      | Action   |
| Action      | Decision   | Outcome  |
| Executor    | Action     | Outcome  |
| Outcome     | Action     | Event    |

---

## O Que Este Documento **NÃ£o** Ã‰

* âŒ NÃ£o Ã© documentaÃ§Ã£o de cÃ³digo
* âŒ NÃ£o Ã© guia de implementaÃ§Ã£o
* âŒ NÃ£o define agentes, ML ou heurÃ­sticas

Este README define **o contrato do sistema com ele mesmo**.

---

## PrÃ³ximos Documentos

A partir deste ponto, cada contrato serÃ¡ detalhado em **um arquivo prÃ³prio**, contendo:

* DefiniÃ§Ã£o formal
* Estrutura conceitual
* Invariantes
* Exemplos abstratos
* Erros proibidos

---

**Qualquer implementaÃ§Ã£o que viole estes contratos estÃ¡, por definiÃ§Ã£o, incorreta.**


---

## Source: `docs/cognitive/OBSERVATION.MD`

# Observation Contract

## 1. DefiniÃ§Ã£o

`Observation` Ã© a **Ãºnica porta de entrada canÃ´nica** de informaÃ§Ãµes no CortAI.

Ela representa qualquer evento, sinal ou dado detectÃ¡vel que **ocorre fora do nÃºcleo cognitivo** e que pode influenciar o estado do sistema.

Nada no sistema pode alterar o `State` diretamente sem antes se manifestar como uma `Observation`.

---

## 2. Papel no Fluxo Cognitivo

Fluxo obrigatÃ³rio:

```
Observation â†’ State â†’ Decision â†’ Action â†’ Outcome
```

A `Observation`:

* NÃ£o decide
* NÃ£o executa
* NÃ£o interpreta semanticamente
* Apenas **declara que algo ocorreu**

---

## 3. PrincÃ­pios InviolÃ¡veis

1. **Imutabilidade**
   Uma `Observation` nunca pode ser alterada apÃ³s criada.

2. **Atomicidade**
   Cada `Observation` representa **um Ãºnico fato observÃ¡vel**.

3. **Origem explÃ­cita**
   Toda observaÃ§Ã£o deve declarar quem a produziu.

4. **Timestamp obrigatÃ³rio**
   O tempo do evento deve estar presente e ser confiÃ¡vel.

5. **IndependÃªncia semÃ¢ntica**
   NÃ£o contÃ©m decisÃµes, inferÃªncias ou julgamentos.

---

## 4. Estrutura Formal

```json
{
  "id": "uuid",
  "type": "string",
  "source": "string",
  "timestamp": "ISO-8601",
  "payload": { "...": "dados brutos" },
  "metadata": {
    "confidence": "float?",
    "correlation_id": "uuid?",
    "tags": ["string"]
  }
}
```

---

## 5. Campos ObrigatÃ³rios

| Campo       | DescriÃ§Ã£o                             |
| ----------- | ------------------------------------- |
| `id`        | Identificador Ãºnico da observaÃ§Ã£o     |
| `type`      | Tipo canÃ´nico do evento observado     |
| `source`    | Origem (agente, sistema, API, sensor) |
| `timestamp` | Momento exato da ocorrÃªncia           |
| `payload`   | Dados brutos observados               |

---

## 6. Campos Opcionais

| Campo                     | Uso                              |
| ------------------------- | -------------------------------- |
| `metadata.confidence`     | Grau de confianÃ§a do evento      |
| `metadata.correlation_id` | Vincula observaÃ§Ãµes relacionadas |
| `metadata.tags`           | ClassificaÃ§Ã£o auxiliar           |

---

## 7. Tipos CanÃ´nicos de Observation

### 7.1 Externas

* `media_collected`
* `segment_detected`
* `transcription_generated`
* `highlight_requested`
* `publication_feedback`

### 7.2 Internas

* `state_snapshot_created`
* `decision_emitted`
* `action_executed`
* `outcome_registered`

---

## 8. Exemplos

### Exemplo: SegmentaÃ§Ã£o Detectada

```json
{
  "id": "obs-123",
  "type": "segment_detected",
  "source": "segmenter_agent",
  "timestamp": "2026-01-23T18:32:00Z",
  "payload": {
    "segment_id": "seg-88",
    "start": 120.5,
    "end": 148.2
  }
}
```

---

## 9. AntipadrÃµes (Proibido)

âŒ `Observation` que contÃ©m decisÃ£o

âŒ `Observation` que altera estado diretamente

âŒ `Observation` sem origem clara

âŒ `Observation` mutÃ¡vel

---

## 10. RelaÃ§Ãµes com Outros Contratos

* Alimenta: `State`
* Ã‰ registrada em: `Event Log`
* Nunca depende de: `Decision` ou `Action`

---

## 11. Garantias Arquiteturais

Se uma informaÃ§Ã£o **nÃ£o estÃ¡ representada como Observation**, entÃ£o:

* Ela **nÃ£o existe** para o CortAI
* Ela **nÃ£o pode** influenciar decisÃµes
* Ela **nÃ£o pode** alterar o estado

Essa regra Ã© absoluta.


---

## Source: `docs/cognitive/OUTCOME.md`

# Outcome

## Objetivo

O **Outcome** representa o **resultado observÃ¡vel, imutÃ¡vel e auditÃ¡vel da execuÃ§Ã£o de uma Action**.

> Outcome nÃ£o Ã© intenÃ§Ã£o.
> Outcome nÃ£o Ã© decisÃ£o.
> Outcome Ã© fato registrado.

---

## Papel no Modelo Cognitivo

Fluxo canÃ´nico:

```

State â†’ Decision â†’ Action â†’ Executor â†’ Outcome

````

O Outcome:
- encerra o ciclo de execuÃ§Ã£o de uma Action
- materializa sucesso ou falha
- alimenta observaÃ§Ãµes futuras
- nunca Ã© reinterpretado

---

## DefiniÃ§Ã£o Conceitual

**Outcome Ã© um artefato de resultado que captura o efeito real da execuÃ§Ã£o de uma Action, incluindo status, outputs, mÃ©tricas e erros.**

Ele Ã©:
- produzido exclusivamente por um Executor
- imutÃ¡vel apÃ³s criaÃ§Ã£o
- versionÃ¡vel
- persistÃ­vel

---

## Estrutura CanÃ´nica

```python
Outcome {
    outcome_id: UUID
    action_id: UUID
    executor_id: UUID

    status: OutcomeStatus
    outputs: dict
    metrics: dict
    error: Optional[ErrorInfo]

    started_at: datetime
    finished_at: datetime
    duration_ms: int
}
````

---

## Identificadores

### outcome_id

Identifica unicamente o Outcome.

**Invariantes**

* Nunca reutilizado
* Gerado no momento da execuÃ§Ã£o

---

### action_id

```python
action_id: UUID
```

Vincula o Outcome Ã  Action executada.

**Invariantes**

* Um Outcome corresponde a exatamente uma Action
* Uma Action pode gerar apenas um Outcome por execuÃ§Ã£o

---

### executor_id

```python
executor_id: UUID
```

Identifica quem executou a Action.

---

## Status do Outcome

```python
OutcomeStatus = Enum(
    "SUCCESS",
    "FAILED",
    "PARTIAL"
)
```

### DefiniÃ§Ãµes

* **SUCCESS**
  ExecuÃ§Ã£o completa, sem erros.

* **FAILED**
  ExecuÃ§Ã£o nÃ£o concluÃ­da ou invÃ¡lida.

* **PARTIAL**
  ExecuÃ§Ã£o incompleta, porÃ©m com efeitos vÃ¡lidos.

**Invariantes**

* Status Ã© obrigatÃ³rio
* Status nÃ£o pode ser alterado apÃ³s criaÃ§Ã£o

---

## Outputs

```python
outputs: dict
```

ContÃ©m os **artefatos produzidos pela execuÃ§Ã£o**.

Exemplos:

* caminho de arquivo
* identificador de clip
* texto transcrito
* payload estruturado

**Invariantes**

* Outputs sÃ³ existem se algo foi produzido
* Nunca contÃ©m inferÃªncias ou decisÃµes

---

## MÃ©tricas

```python
metrics: dict
```

Dados quantitativos da execuÃ§Ã£o.

Exemplos:

* tempo de execuÃ§Ã£o
* uso de memÃ³ria
* tamanho de arquivos
* custo estimado

**Invariantes**

* MÃ©tricas sÃ£o opcionais
* MÃ©tricas nunca influenciam decisÃµes diretamente

---

## Erro

```python
ErrorInfo {
    code: str
    message: str
    details: Optional[dict]
}
```

Presente apenas quando `status != SUCCESS`.

**Invariantes**

* FAILED â†’ error obrigatÃ³rio
* SUCCESS â†’ error proibido

---

## Temporalidade

```python
started_at: datetime
finished_at: datetime
duration_ms: int
```

**Invariantes**

* finished_at â‰¥ started_at
* duration_ms = finished_at - started_at
* Todos os Outcomes sÃ£o temporalmente ordenÃ¡veis

---

## Imutabilidade

ApÃ³s criado:

* nenhum campo pode ser alterado
* correÃ§Ãµes exigem novo Outcome
* auditoria sempre preservada

---

## RelaÃ§Ã£o com State

* Outcome **nÃ£o modifica State diretamente**
* Outcomes sÃ£o consumidos como Observation
* State evolui apenas via reduÃ§Ã£o de Observations

---

## RelaÃ§Ã£o com Event Log

Cada Outcome gera eventos observÃ¡veis:

```text
ACTION_EXECUTED
ACTION_FAILED
ACTION_PARTIAL
```

Esses eventos:

* alimentam monitoramento
* suportam replay
* permitem auditoria completa

---

## Exemplo de Outcome (Sucesso)

```json
{
  "outcome_id": "uuid",
  "action_id": "uuid",
  "executor_id": "uuid",
  "status": "SUCCESS",
  "outputs": {
    "transcript": "texto gerado"
  },
  "metrics": {
    "duration_ms": 3120
  },
  "error": null
}
```

---

## Exemplo de Outcome (Falha)

```json
{
  "outcome_id": "uuid",
  "action_id": "uuid",
  "executor_id": "uuid",
  "status": "FAILED",
  "outputs": {},
  "metrics": {},
  "error": {
    "code": "TIMEOUT",
    "message": "Tempo limite excedido"
  }
}
```

---

## Propriedades Fundamentais

### Observabilidade

Tudo que aconteceu estÃ¡ no Outcome.

### Auditabilidade

Nada Ã© apagado ou sobrescrito.

### Neutralidade Cognitiva

Outcome nÃ£o interpreta o que ocorreu.

---

## Anti-PadrÃµes (Proibidos)

* Outcome conter decisÃ£o
* Outcome modificar State
* Outcome ser reescrito
* Outcome conter lÃ³gica de retry

---


---

## Source: `docs/cognitive/PIPELINE_PHASE.md`

# Pipeline Phase

## Objetivo

A **Pipeline Phase** representa uma **etapa determinÃ­stica, finita e explicitamente definida** do fluxo de execuÃ§Ã£o do CortAI.

Ela existe para:
- organizar o processamento em passos claros
- garantir previsibilidade
- permitir auditoria e replay
- separar cogniÃ§Ã£o de execuÃ§Ã£o operacional

> Uma pipeline **nÃ£o pensa**.
> Ela **executa**.

---

## PrincÃ­pio Fundamental

> **Pipeline Ã© determinÃ­stica. CogniÃ§Ã£o Ã© probabilÃ­stica.**

Dado:
- a mesma entrada
- o mesmo estado
- a mesma fase

O resultado **deve ser o mesmo**.

---

## DefiniÃ§Ã£o Conceitual

Uma Pipeline Phase Ã©:

> â€œUm estÃ¡gio do sistema onde um conjunto especÃ­fico de Actions Ã© executado
> de forma controlada, ordenada e sem ambiguidade.â€

Ela atua como **ponte entre decisÃµes cognitivas e execuÃ§Ã£o concreta**.

---

## RelaÃ§Ã£o com o Modelo Cognitivo

Fluxo canÃ´nico:

```text
Observation
   â†“
State
   â†“
Decision
   â†“
Pipeline Phase
   â†“
Action(s)
   â†“
Outcome
   â†“
Event Log
````

A Pipeline Phase:

* **nÃ£o observa**
* **nÃ£o decide**
* **nÃ£o interpreta**
* **nÃ£o aprende**

Ela apenas executa o que foi decidido.

---

## Estrutura CanÃ´nica

```python
PipelinePhase {
    phase_id: UUID
    name: str
    order: int

    allowed_actions: List[ActionType]
    executor: ExecutorType

    is_terminal: bool
}
```

---

## phase_id

Identificador Ãºnico da fase.

**Invariantes**

* Ãšnico
* ImutÃ¡vel
* Referenciado por State e Event Log

---

## name

Nome semÃ¢ntico da fase.

### Exemplos

* `COLLECTION`
* `SEGMENTATION`
* `TRANSCRIPTION`
* `ANALYSIS`
* `HIGHLIGHT_SELECTION`

---

## order

```python
order: int
```

Define a **ordem linear** da pipeline.

**Invariantes**

* Ordem crescente
* NÃ£o hÃ¡ saltos implÃ­citos
* MudanÃ§a de ordem exige nova definiÃ§Ã£o de pipeline

---

## allowed_actions

```python
allowed_actions: List[ActionType]
```

Define **quais Actions sÃ£o vÃ¡lidas** nesta fase.

**Invariantes**

* Actions fora da lista sÃ£o proibidas
* Executor deve rejeitar aÃ§Ãµes invÃ¡lidas
* Garante seguranÃ§a operacional

---

## executor

```python
executor: ExecutorType
```

Define **quem executa as Actions** da fase.

### Exemplos

* `SYNC_EXECUTOR`
* `ASYNC_EXECUTOR`
* `MEDIA_EXECUTOR`

**Invariantes**

* Executor Ã© determinÃ­stico
* Executor nÃ£o decide
* Executor nÃ£o altera State diretamente

---

## is_terminal

```python
is_terminal: bool
```

Indica se a fase encerra o pipeline.

**Invariantes**

* Apenas uma fase pode ser terminal
* Fase terminal nÃ£o gera novas decisÃµes
* Finaliza o ciclo cognitivo

---

## Pipeline CanÃ´nica do CortAI

### FASE 1 â€” COLLECTION

* coleta vÃ­deo bruto
* armazena no MinIO
* registra metadata no PostgreSQL

### FASE 2 â€” SEGMENTATION

* segmentaÃ§Ã£o de Ã¡udio/vÃ­deo
* geraÃ§Ã£o de timestamps
* persistÃªncia de segmentos

### FASE 3 â€” TRANSCRIPTION

* transcriÃ§Ã£o por segmento
* associaÃ§Ã£o texto â†” tempo
* persistÃªncia de transcriÃ§Ãµes

### FASE 4 â€” ANALYSIS

* anÃ¡lise semÃ¢ntica
* scoring
* inferÃªncia de relevÃ¢ncia

### FASE 5 â€” HIGHLIGHT_SELECTION (Terminal)

* seleÃ§Ã£o de clipes
* decisÃ£o final
* emissÃ£o de outcomes finais

---

## TransiÃ§Ãµes de Fase

Uma fase sÃ³ pode transicionar se:

* todas as Actions foram executadas com sucesso
* Outcomes esperados foram emitidos
* Event Log foi persistido

Caso contrÃ¡rio:

* a fase Ã© interrompida
* erro Ã© logado
* sistema aguarda intervenÃ§Ã£o

---

## RelaÃ§Ã£o com State

O State contÃ©m:

```python
current_phase: PipelinePhase
```

A mudanÃ§a de fase:

* gera evento
* pode gerar snapshot
* nunca ocorre implicitamente

---

## Eventos Associados

Exemplos:

* `PIPELINE_PHASE_STARTED`
* `PIPELINE_PHASE_COMPLETED`
* `PIPELINE_PHASE_FAILED`

Todos registrados no Event Log.

---

## Exemplo PrÃ¡tico

```text
State.current_phase = SEGMENTATION

Decision â†’ EXECUTE_SEGMENTATION

Pipeline Phase SEGMENTATION:
  allowed_actions = [SEGMENT_AUDIO]
  executor = ASYNC_EXECUTOR

Outcome â†’ SEGMENTS_CREATED
```

---

## Anti-PadrÃµes (Proibidos)

* pular fases
* executar aÃ§Ã£o fora da fase correta
* tomar decisÃ£o dentro da pipeline
* alterar state sem evento

---

## Propriedades Garantidas

### Determinismo

Mesma fase + mesmas entradas â†’ mesmo resultado.

### Auditabilidade

Cada fase Ã© observÃ¡vel no Event Log.

### Isolamento Cognitivo

Pipeline nÃ£o interfere na lÃ³gica decisÃ³ria.

---


---

## Source: `docs/cognitive/STATE.md`

# State

## Objetivo

O **State** representa a **memÃ³ria cognitiva consolidada** do CortAI em um instante lÃ³gico do tempo.
Ele Ã© derivado **exclusivamente** de Observations processadas e serve como **base Ãºnica** para:

- tomada de decisÃ£o (`Decision`)
- execuÃ§Ã£o de aÃ§Ãµes (`Action`)
- auditoria e replay
- versionamento e snapshots

> O sistema **nÃ£o pensa fora do State**.

---

## Papel no Modelo Cognitivo

Fluxo canÃ´nico:

```

Observation â†’ State â†’ Decision â†’ Action â†’ Outcome

````

O `State`:
- agrega mÃºltiplas Observations
- normaliza informaÃ§Ãµes heterogÃªneas
- mantÃ©m continuidade temporal
- preserva rastreabilidade causal

---

## DefiniÃ§Ã£o Conceitual

**State Ã© a representaÃ§Ã£o factual, versionada e consistente do que o sistema acredita ser verdade naquele momento.**

O State:
- **nÃ£o interpreta**
- **nÃ£o decide**
- **nÃ£o executa**
- apenas **descreve**

---

## Estrutura CanÃ´nica

```python
State {
    state_id: UUID
    version: int
    timestamp: datetime

    observations: List[Observation]

    context: StateContext
    memory: StateMemory
    metrics: StateMetrics

    lineage: StateLineage
}
````

---

## Componentes do State

### 1. Identidade & Versionamento

```python
state_id: UUID
version: int
timestamp: datetime
```

* `state_id`: identifica a linha temporal do sistema
* `version`: incremento monotÃ´nico
* `timestamp`: momento lÃ³gico de consolidaÃ§Ã£o

**Invariantes**

* `version(n+1) > version(n)`
* States nunca sÃ£o sobrescritos

---

### 2. Observations Consolidadas

```python
observations: List[Observation]
```

* lista imutÃ¡vel das Observations usadas para gerar o State
* preserva causalidade e explicabilidade

**Invariantes**

* Observations nÃ£o sÃ£o alteradas apÃ³s consolidaÃ§Ã£o
* State referencia apenas Observations vÃ¡lidas

---

### 3. Contexto Derivado

```python
StateContext {
    media_id: str
    timeline_position: float
    active_pipeline_stage: int
}
```

* visÃ£o situacional do sistema
* reduz custo cognitivo para decisÃµes

**Invariantes**

* derivado apenas de Observations
* nÃ£o contÃ©m inferÃªncias subjetivas

---

### 4. MemÃ³ria Estruturada

```python
StateMemory {
    segments: List[Segment]
    transcriptions: List[Transcription]
    embeddings: Optional[List[Vector]]
}
```

* dados organizados e normalizados
* prontos para consumo pelo nÃºcleo cognitivo

**Invariantes**

* nenhuma mutaÃ§Ã£o in-place
* toda alteraÃ§Ã£o gera novo State

---

### 5. MÃ©tricas Objetivas

```python
StateMetrics {
    confidence_scores: Dict[str, float]
    coverage_ratio: float
    processing_latency_ms: int
}
```

* indicadores mensurÃ¡veis
* usados para validaÃ§Ã£o e auditoria

**Invariantes**

* mÃ©tricas informam, nÃ£o decidem
* nÃ£o carregam intenÃ§Ã£o ou valor

---

### 6. Lineage & Auditoria

```python
StateLineage {
    parent_state_id: Optional[UUID]
    originating_events: List[EventID]
}
```

* permite replay completo
* garante rastreabilidade causal

**Invariantes**

* todo State (exceto o inicial) possui `parent_state_id`

---

## Propriedades Fundamentais

### Imutabilidade

* State Ã© **append-only**
* alteraÃ§Ãµes geram nova versÃ£o

### Determinismo

* mesmo conjunto de Observations â†’ mesmo State

### Auditabilidade

* toda a histÃ³ria do sistema pode ser reconstruÃ­da

---

## Anti-PadrÃµes (Proibidos)

* Alterar State existente
* Misturar decisÃ£o dentro do State
* Persistir dados transitÃ³rios
* Inferir intenÃ§Ã£o ou valor subjetivo

---

## RelaÃ§Ã£o com Outros Contratos

| Contrato    | RelaÃ§Ã£o com State              |
| ----------- | ------------------------------ |
| Observation | Fonte primÃ¡ria                 |
| Decision    | Consome State                  |
| Action      | Executada a partir da Decision |
| Outcome     | Resultado da Action            |

---

## Exemplo Simplificado

```json
{
  "state_id": "uuid-123",
  "version": 4,
  "timestamp": "2026-01-22T22:41:00Z",
  "observations": [...],
  "context": {
    "media_id": "video_abc",
    "timeline_position": 132.4,
    "active_pipeline_stage": 3
  },
  "memory": {
    "segments": [...],
    "transcriptions": [...]
  },
  "metrics": {
    "coverage_ratio": 0.87,
    "processing_latency_ms": 420
  },
  "lineage": {
    "parent_state_id": "uuid-122",
    "originating_events": ["event_778"]
  }
}
```

---


---

## Source: `docs/cognitive/STATE_SNAPSHOT.md`

# State Snapshot

## Objetivo

O **State Snapshot** Ã© uma **captura materializada, versionada e imutÃ¡vel do State em um ponto especÃ­fico do tempo**, criada exclusivamente para **otimizar reconstruÃ§Ã£o**, **auditoria** e **replay cognitivo**.

> Snapshots **nÃ£o sÃ£o a verdade do sistema**.
> A verdade continua sendo o **Event Log**.

---

## PrincÃ­pio Fundamental

> **State pode ser descartado. Eventos nunca.**

Snapshots existem apenas para:
- acelerar reconstruÃ§Ã£o
- permitir checkpoints seguros
- reduzir custo de replay

---

## DefiniÃ§Ã£o Conceitual

Um **State Snapshot** representa:

> â€œO que o sistema acreditava ser verdade naquele instante,
> derivado de uma sequÃªncia especÃ­fica de eventos.â€

---

## RelaÃ§Ã£o com State

- State Ã© **volÃ¡til**
- Snapshot Ã© **persistente**
- Ambos sÃ£o derivados **do Event Log**

Snapshots **nÃ£o geram decisÃµes** e **nÃ£o alteram comportamento**.

---

## Estrutura CanÃ´nica

```python
StateSnapshot {
    snapshot_id: UUID
    state_id: UUID

    version: int
    derived_from_event_id: UUID

    state_payload: dict

    created_at: datetime
}
````

---

## Identificadores

### snapshot_id

Identificador Ãºnico do snapshot.

**Invariantes**

* Nunca reutilizado
* Nunca modificado

---

### state_id

Identificador do State que foi materializado.

**Invariantes**

* Refere-se a um State vÃ¡lido
* Nunca aponta para mÃºltiplos States

---

## Versionamento

```python
version: int
```

VersÃ£o do schema do snapshot.

**Invariantes**

* VersÃ£o monotÃ´nica crescente
* Permite evoluÃ§Ã£o do formato
* NÃ£o afeta replay lÃ³gico

---

## derived_from_event_id

```python
derived_from_event_id: UUID
```

Indica **o Ãºltimo evento aplicado** para gerar o snapshot.

**Invariantes**

* Snapshot representa exatamente:

  ```
  State = apply(events[0..derived_from_event_id])
  ```
* Nenhum evento posterior estÃ¡ incluÃ­do

---

## ConteÃºdo do Snapshot

```python
state_payload: dict
```

RepresentaÃ§Ã£o serializada do State.

Pode conter:

* mÃ©tricas agregadas
* status interno
* flags de controle
* referÃªncias temporÃ¡rias

**Invariantes**

* NÃ£o contÃ©m lÃ³gica
* NÃ£o contÃ©m decisÃµes futuras
* NÃ£o contÃ©m efeitos colaterais

---

## created_at

```python
created_at: datetime
```

Momento exato da criaÃ§Ã£o.

**Invariantes**

* UTC obrigatÃ³rio
* NÃ£o altera ordem causal

---

## GeraÃ§Ã£o de Snapshots

Snapshots **sÃ³ podem ser gerados**:

* em pontos seguros do pipeline
* apÃ³s eventos completamente aplicados
* sem concorrÃªncia de escrita

### Exemplos de Gatilhos

* final de fase do pipeline
* N eventos aplicados
* estado consistente atingido
* checkpoint manual

---

## RelaÃ§Ã£o com Replay

Replay padrÃ£o:

1. carregar snapshot mais recente â‰¤ alvo
2. aplicar eventos subsequentes
3. reconstruir State final

Replay completo:

* ignora snapshots
* usa apenas eventos

---

## Falhas e RecuperaÃ§Ã£o

Se um snapshot:

* estiver corrompido â†’ descartar
* estiver ausente â†’ reconstruir via eventos
* estiver desatualizado â†’ reaplicar eventos

Snapshots **nunca bloqueiam o sistema**.

---

## Imutabilidade

Uma vez persistido:

* snapshot nÃ£o Ã© alterado
* correÃ§Ãµes geram novo snapshot
* histÃ³rico preservado

---

## RelaÃ§Ã£o com Event Log

Cada snapshot deve gerar um evento:

```text
STATE_SNAPSHOT_CREATED
```

Esse evento referencia:

* snapshot_id
* state_id
* derived_from_event_id

---

## Exemplo de Snapshot

```json
{
  "snapshot_id": "uuid",
  "state_id": "uuid",
  "version": 1,
  "derived_from_event_id": "uuid",
  "state_payload": {
    "pipeline_phase": 3,
    "segments_processed": 42,
    "last_decision": "HIGHLIGHT_CANDIDATE"
  },
  "created_at": "2026-01-22T20:01:00Z"
}
```

---

## Anti-PadrÃµes (Proibidos)

* usar snapshot como fonte de verdade
* modificar snapshot apÃ³s criaÃ§Ã£o
* gerar snapshot no meio de transiÃ§Ã£o
* tomar decisÃµes baseadas no snapshot

---

## Propriedades Garantidas

### Determinismo

Mesmo snapshot + mesmos eventos â†’ mesmo State.

### Auditabilidade

ReconstruÃ§Ã£o total sempre possÃ­vel.

### Isolamento Cognitivo

Snapshots nÃ£o influenciam decisÃµes futuras.

---


---

## Source: `docs/concurrency/concurrency_failure_matrix_v1_0.md`

# Concurrency Failure Matrix v1.0

## Objetivo
Definir respostas canonicas para falhas de concorrencia em D12.

## Matriz

| Caso | Deteccao | Acao | Severidade | reason_code |
|---|---|---|---|---|
| Double-apply com mesmo op_key e hash diferente | `idempotency_check_or_reserve` | BLOCK | HIGH | `IDEMPOTENCY_CONFLICT` |
| Lease negada (owner ativo) | `acquire_lease` | BLOCK | MEDIUM | `LEASE_DENIED` |
| Lease expirada antes de write | validacao de lease handle | BLOCK | HIGH | `LEASE_EXPIRED` |
| Snapshot ausente para executar D10 | precondicao no pipeline | BLOCK | HIGH | `SNAPSHOT_MISSING` |
| Snapshot parcial/invalido | validacao de schema/hash | BLOCK | HIGH | `SNAPSHOT_INVALID` |
| Reexecucao com mesmo op_key e hash igual | idempotency store | NOOP | LOW | `IDEMPOTENCY_NOOP` |
| Release apos expiracao | release defensivo | DEGRADE | LOW | `LEASE_RELEASE_AFTER_EXPIRY` |

## Regras de decisao
- BLOCK: risco de drift ou verdade parcial.
- DEGRADE: erro sem impacto na verdade final.
- NOOP: repeticao segura detectada por hash igual.


---

## Source: `docs/concurrency/d12_concurrency_hardening_v1_0.md`

# D12 Concurrency Hardening v1.0

## Objetivo
Garantir exclusividade de escrita, idempotencia e snapshot atomico por janela para evitar double-apply, escrita fora de ordem e estado parcial.

## Escopo v1.0
- Leases por conta e por janela.
- Catalogo de op_key para operacoes criticas.
- Reserva idempotente por op_key + payload hash.
- Snapshot atomico da janela antes do fluxo D10.

## Invariantes
1. Um writer por chave (`account_id` ou `account_id+window_id`).
2. Operacoes criticas protegidas por `op_key`.
3. Pipeline de janela executa sob `LEASE_WINDOW`.
4. Toda violacao gera evento com `reason_code`.
5. `BLOCK` quando ha risco de drift.

## Leases
- `LEASE_ACCOUNT:{account_id}`
- `LEASE_WINDOW:{account_id}:{window_id}`

## Regras de lease
- Lease expirada bloqueia escrita.
- Renovacao falha se owner mudou.
- Release de lease inexistente nao quebra execucao.

## Integracao com D10
1. `window_pipeline` adquire `LEASE_WINDOW`.
2. Reserva `AGG:{account_id}:{window_id}`.
3. Gera snapshot atomico e persiste.
4. Executa D10 usando snapshot imutavel.

## Resultado esperado
Execucao deterministica, sem aplicacao duplicada e com trilha auditavel por `account_id`, `window_id` e `op_key`.


---

## Source: `docs/concurrency/op_key_catalog_v1_0.md`

# OP Key Catalog v1.0

## Objetivo
Congelar formato de chaves idempotentes para operacoes criticas.

## Formato
`{OP}:{account_id}:{window_id}`

Operacoes que exigem stage:
`SPA:{account_id}:{window_id}:{stage}`

## Catalogo
- `AGG:{account_id}:{window_id}`
- `SC:{account_id}:{window_id}`
- `ATTR:{account_id}:{window_id}`
- `SL:{account_id}:{window_id}`
- `SPA:{account_id}:{window_id}:{stage}`
- `UPD:{account_id}:{window_id}`

## Regras
1. Mesmo `op_key` + mesmo `payload_hash` => `NOOP`.
2. Mesmo `op_key` + hash diferente => `CONFLICT`.
3. Operacao so finaliza apos `finalize_op`.
4. Toda reserva/finalizacao emite evento de auditoria.


---

## Source: `docs/content/content_template_library_v1_0.md`

# Content Template Library v1.0

## Scope

`D36 â€” Content Template Library v1.0` adiciona uma biblioteca estruturada de templates para alimentar o `CreativePackGenerator`.

Esta camada padroniza texto-base de:

- hooks
- estrutura narrativa
- pacing de roteiro
- CTA

## Goals

- aumentar consistencia dos `creative_packs`
- reduzir variacao ruim entre geracoes
- permitir selecao deterministica por tipo
- preparar variacoes controladas antes do piloto real

## Out of Scope

- nenhuma alteracao em `publish`
- nenhuma alteracao em `safety`
- nenhuma alteracao em `scheduler`
- nenhuma alteracao em `metrics`
- nenhuma chamada de API externa
- nenhuma mutacao do pipeline de conteudo

## Template Types

Tipos canonicos suportados no v1.0:

- `HOOK_QUESTION`
- `HOOK_CURIOUS_STATEMENT`
- `HOOK_REVEAL`
- `HOOK_CONTRAST`
- `HOOK_COUNTDOWN`

## Template Structure

Cada template representa um texto-base reutilizavel com esta estrutura logica:

1. `hook`
2. `setup`
3. `tension`
4. `reveal`
5. `cta`

Os campos textuais ficam organizados como:

- `hook_pattern`
- `body_pattern`
- `cta_pattern`

## Invariants

- templates sao deterministicos
- templates nao chamam servicos externos
- templates apenas geram texto-base
- templates sao usados apenas pelo `CreativePackGenerator`
- mesma entrada de selecao deve produzir a mesma ordem de templates
- variacoes simples devem ser estaveis por indice

## Persistence

Persistencia append-only em:

- `OUT/content/templates/templates.jsonl`

## Data Model

Modelo minimo:

- `template_id`
- `template_type`
- `structure`
- `hook_pattern`
- `body_pattern`
- `cta_pattern`
- `tags`
- `created_at`

## Service Responsibilities

A biblioteca deve expor:

- `list_templates()`
- `get_template(template_id)`
- `select_templates_by_type(template_type)`
- `generate_template_variations(template_id, count)`

## Deterministic Selection

Regras:

- a selecao por tipo deve preservar ordenacao estavel
- a geracao de variacoes nao usa RNG global
- o indice da variacao controla a saida

## Future Integration

Integracao prevista com:

- `D29 â€” Creative Pack Generator`

A integracao futura deve:

- escolher templates por tipo e contexto
- montar hooks e estruturas mais consistentes
- continuar sem tocar no runtime critico


---

## Source: `docs/content/creative_pack_generator_v1_0.md`

# D29 - Creative Pack Generator v1.0

## Objetivo

Gerar `creative_pack` de forma deterministica e auditavel a partir de um tema/oportunidade, sem alterar o caminho de `publish`.

Fluxo alvo:

`theme/opportunity -> creative_pack -> content pipeline -> publish`

## Escopo

Entra:
- geracao automatica de `creative_pack`
- hook candidates
- script skeleton
- angle
- title
- hashtags
- CTA
- variacoes por conta e `policy_stage`
- respeito a `account_policy` e `strategy_patch`
- persistencia append-only

Nao entra:
- alteracao do `publish.py`
- alteracao do `safety_gate`
- alteracao do scheduler/workers/rollout

## Contratos

### CreativePack

- `creative_pack_id`
- `account_id`
- `policy_stage`
- `theme`
- `variation_index`
- `angle`
- `title`
- `hook_candidates`
- `script_skeleton`
- `hashtags`
- `cta`
- `strategy_patch_id | null`
- `generated_at`

### Regras

- `creative_pack_id` eh deterministico
- mesma entrada logica gera `NOOP`
- payload diferente com mesma chave gera `CONFLICT`
- variacoes sao estaveis por `variation_index`
- `strategy_patch` so influencia quando `active=true`

## Persistencia

Path canonico:

`OUT/content/creative_packs/creative_packs.jsonl`

Semantica:
- append-only
- `WRITTEN | NOOP | CONFLICT`

## Integracao com strategy/policy

Inputs relevantes:
- `account_policy.stage`
- `account_policy.config`
- `strategy_patch.overrides`

Whitelisted:
- `a1_prefs_override`
- `a4_defaults_override`
- `a5_rewrite_defaults_override`

Exemplos de impacto:
- `a1_prefs_override.prefer_angles` influencia `angle`
- `a1_prefs_override.niches_boost` influencia hashtags
- `a4_defaults_override.force_number` influencia `title`
- `a4_defaults_override.increase_tension` influencia `hook_candidates`
- `a4_defaults_override.hook_style` influencia o tipo de hook
- `a5_rewrite_defaults_override.cta_style` influencia `cta`

## Eventos

Nao obrigatorios no v1.0.

Auditoria minima eh garantida pela persistencia append-only.

## Criterio de aceite

O D29 fecha se:
- gera `creative_pack` consistente
- variacoes sao estaveis
- `account_policy` e `strategy_patch` influenciam a saida sem quebrar determinismo
- persistencia idempotente funciona


---

## Source: `docs/d3_go_nogo_checklist.md`

# D+3 Webhook GO/NO-GO Checklist

Objetivo:
- avaliar a janela D+3 com criterio binario e sem reinterpretacao ad hoc;
- decidir se o runtime congelado segue para nova superficie ou se entra em correcao minima.

Artefatos obrigatorios:
- `OUT/D3/D0_summary.txt`
- `OUT/D3/D1_summary.txt`
- `OUT/D3/D2_summary.txt`
- `OUT/D3/D3_summary.txt`

## Criterio binario

`GO` somente se todos os pontos abaixo passarem:
- `status_public_5xx_rate == 0` em `D0..D3`
- `webhook_error_rate == 0` em `D0..D3`
- `webhook_p95_latency_ms` sem degradacao progressiva entre `D0` e `D3`
- `last_error_status` vazio ou compatÃ­vel com erro isolado nao recorrente
- ausencia de loop aparente:
  - crescimento de `webhook_sent` coerente com transicoes reais
  - sem aumento anormal de `sent` com `error_rate == 0` e sem causa operacional

`NO-GO` se qualquer um ocorrer:
- qualquer `5xx` recorrente em `/status/public`
- `webhook_error_rate > 0` recorrente
- `webhook_p95_latency_ms` degradando dia a dia
- `last_error_status` persistente ou repetitivo
- evidÃªncia de duplicacao/loop de disparo

## Leitura rapida por arquivo

Campos relevantes:
- `status_public_5xx_count`
- `status_public_5xx_rate`
- `status_public_p95_ms`
- `webhook_sent`
- `webhook_success`
- `webhook_error`
- `webhook_error_rate`
- `webhook_p95_latency_ms`
- `webhook_last_error_status`
- `webhook_last_error_ts`

Perguntas objetivas:
1. houve `5xx`?
2. houve erro de webhook?
3. a latencia do webhook ficou estavel?
4. o volume de `sent` cresceu de forma coerente?
5. houve sinal de erro persistente?

## Acao minima por falha

Se `status_public_5xx_rate > 0`:
- congelar rollout externo;
- reproduzir localmente com a mesma rota;
- corrigir somente o request path de `/status/public`.

Se `webhook_error_rate > 0`:
- validar endpoint consumidor e assinatura HMAC;
- verificar `last_error_status`;
- nao abrir novo consumidor ate zerar o erro.

Se `webhook_p95_latency_ms` degradar:
- confirmar se a degradacao vem do consumidor ou do envio local;
- manter 1 consumidor;
- nao adicionar retry/backoff antes da causa raiz.

Se houver loop:
- validar regra de transicao para `action_required`;
- comparar `sent` com mudancas reais de estado;
- corrigir apenas a regra de disparo.

## Proximo passo apos a decisao

Se `GO`:
- encerrar freeze;
- abrir o proximo slice com base no backlog priorizado;
- manter os artefatos D+3 como evidencia de rollout controlado.

Se `NO-GO`:
- abrir um slice minimo de correcao;
- reexecutar a observacao apos a correcao;
- nao abrir nova superficie antes de estabilizar.

## Backlog pos-D+3 (ordem recomendada)

1. `Decision Audit Log v0.1`
2. `Policy -> Status/Public v1.2` apenas se a janela confirmar estabilidade
3. segundo consumidor do webhook


---

## Source: `docs/data/publish_record_v1.md`

# Publish Record Spec v1.0

## Objetivo
Definir o artefato canonico que liga publicacao real ao motor de geracao:
`job_id -> video_id`.

## Shape canonico
```json
{
  "publish_id": "pub_20260304_0001",
  "account_id": "acc_ca_001",
  "job_id": "job_123",
  "video_id": "vid_abc",
  "platform": "tiktok",
  "publish_mode": "auto",
  "status": "posted",
  "published_at": "2026-03-04T18:00:00Z",
  "created_at": "2026-03-04T18:00:00Z",
  "metadata": {}
}
```

## Enums fechados
- `platform`: `tiktok | youtube_shorts | instagram_reels`
- `publish_mode`: `auto | manual | replay`
- `status`: `posted | failed | blocked`

## Invariantes
- `publish_id` e obrigatorio e unico.
- `video_id` valido nao pode existir sem `job_id`.
- Para `(job_id, account_id, platform)`, no maximo 1 registro `status=posted`.
- Escrita e append-only no log JSONL.

## API minima (v1.0)
- `write_publish_record(record)` grava registro validado.
- `get_by_job(job_id, account_id, platform)` consulta por job.
- `get_by_video(video_id, account_id, platform)` consulta por video.


---

## Source: `docs/experiments/experiment_framework_v1_0.md`

# D31 - Experiment Framework v1.0

## Objetivo

Permitir experimentacao controlada e auditavel de:

- creative packs
- hook styles
- pacing profiles
- publish windows

Sem alterar diretamente o pipeline de execucao.

## Escopo

Entra:
- entidade `Experiment`
- assignment deterministico A/B
- persistencia append-only de experimentos, assignments e resultados
- resolucao de variante para D29/D30/D26

Nao entra:
- engine estatistico avancado
- selecao automatica de vencedor
- rollout automatico do vencedor
- mutacao de policy
- mais de 2 variantes

## Entidades

### Experiment

- `experiment_id`
- `name`
- `scope`
- `variant_a`
- `variant_b`
- `status`
- `created_at`

Scopes permitidos no v1.0:
- `CREATIVE_PACK`
- `HOOK_STYLE`
- `PACING_PROFILE`
- `PUBLISH_WINDOW`

Status permitidos no v1.0:
- `DRAFT`
- `ACTIVE`
- `PAUSED`
- `ARCHIVED`

### ExperimentAssignment

- `assignment_id`
- `experiment_id`
- `subject_key`
- `variant`
- `assigned_at`

### ExperimentResult

- `result_id`
- `experiment_id`
- `subject_key`
- `variant`
- `window_id`
- `metrics`
- `recorded_at`

## Assignment

Assignment eh deterministico:

`hash(subject_key + experiment_id) % 2`

Saida:
- `A`
- `B`

Sem RNG global.

## Persistencia

Base:

`OUT/experiments/`

Arquivos:
- `experiments.jsonl`
- `assignments.jsonl`
- `results.jsonl`

Semantica:
- append-only
- mesmo payload -> `NOOP`
- payload diferente na mesma chave logica -> `CONFLICT`

## Integracao

Pode ser consumido por:
- D29 (`creative_pack` variation)
- D30 (`pacing` e `publish_window` recommendation)
- D26 (comparacao por janela)

No v1.0 o framework nao altera execucao sozinho.

## Invariantes

- experimentos nao mutam pipeline
- assignment eh estavel para o mesmo input
- comparabilidade por janela e preservada
- toda decisao de variante eh auditavel

## Criterio de aceite

O D31 fecha se:
- experimento pode ser criado
- assignment eh deterministico
- mesma entrada gera mesma variante
- persistencia append-only funciona
- duplicidade vira `NOOP`
- conflito vira `CONFLICT`


---

## Source: `docs/integration/external_platform_integration_v1_0.md`

# External Platform Integration v1.0

## Objetivo

Conectar o CortAI com uma plataforma externa real sem contaminar o nÃºcleo do sistema.

O provider inicial do D22 Ã©:

- `tiktok`

## Provider boundary

Toda integraÃ§Ã£o passa por:

`PlatformClient -> Normalized Adapter -> CortAI contracts`

O payload externo nunca entra direto no pipeline.

## Contratos internos produzidos

- `publish_record`
- `video_metrics`
- `integration_status` por resultado do serviÃ§o
- evento de observabilidade `INTEGRATION/provider_call`

## Retry policy

- `max_attempts = 3`
- backoff exponencial simples

Retry apenas para:

- timeout
- `429`
- `5xx` transitÃ³rio

Sem retry para:

- `400`
- auth invÃ¡lida
- payload invÃ¡lido

## IdempotÃªncia externa

Para mÃ©tricas:

`(provider, external_video_id, captured_window_id)`

Respostas duplicadas com mesmo payload -> `NOOP`

Payload diferente para a mesma chave -> `CONFLICT`

## Taxonomia mÃ­nima de erro

- `PROVIDER_TIMEOUT`
- `PROVIDER_RATE_LIMIT`
- `PROVIDER_AUTH_FAILED`
- `PROVIDER_INVALID_PAYLOAD`
- `PROVIDER_UNAVAILABLE`

## Observabilidade mÃ­nima

Toda chamada externa registra:

- `provider`
- `endpoint`
- `request_id`
- `external_id`
- `latency_ms`
- `retry_count`
- `result`

## Fora de escopo

- upload automÃ¡tico completo de vÃ­deo
- mÃºltiplas plataformas ao mesmo tempo
- login automatizado
- dashboard de provider


---

## Source: `docs/intelligence/platform_intelligence_v1_0.md`

# D30 - Platform Intelligence Layer v1.0

## Objetivo

Transformar sinais operacionais da plataforma em recomendacoes acionaveis, sem interferir diretamente na execucao.

Fluxo alvo:

`publish_records + video_metrics + safety_events -> platform intelligence outputs`

## Escopo

Entra:
- analise deterministica de janelas de publicacao
- recomendacao de pacing
- perfil de risco por conta
- snapshot de saude da conta
- persistencia append-only em `OUT/intelligence/`

Nao entra:
- alterar `publish.py`
- alterar `safety_gate`
- alterar scheduler
- alterar `publish_record`
- chamadas externas

## Inputs

- `OUT/data/publish_records/publish_records.jsonl`
- `OUT/data/video_metrics/video_metrics.jsonl`
- `OUT/events/events.jsonl` com familia `SAFETY/*`

## Outputs

### PublishWindowRecommendation

- `recommendation_id`
- `account_id`
- `generated_at`
- `best_publish_windows`
- `source_publish_count`
- `source_metric_count`

### PacingRecommendation

- `recommendation_id`
- `account_id`
- `generated_at`
- `recommended_min_interval_minutes`
- `recommended_max_posts_per_day`
- `recommended_max_posts_per_hour`
- `reason_codes`

### RiskProfile

- `profile_id`
- `account_id`
- `generated_at`
- `risk_level`
- `signal_counts`
- `latest_risk_ts`
- `reason_codes`

### AccountHealthSnapshot

- `snapshot_id`
- `account_id`
- `generated_at`
- `account_health`
- `avg_views`
- `avg_completion_rate`
- `publish_count`
- `risk_level`
- `reason_codes`

## Persistencia

Path base:

`OUT/intelligence/`

Arquivos:
- `publish_windows.jsonl`
- `pacing_profiles.jsonl`
- `risk_profiles.jsonl`
- `account_health.jsonl`

Semantica:
- append-only
- recomputacao identica -> `NOOP`
- payload diferente para mesma chave -> `CONFLICT`

## Regras de analise

### Publish windows

- agrupa publicacoes por hora UTC
- prioriza horas com melhor media de views e completion rate
- fallback sem metricas: usa frequencia de publicacao

### Pacing

- parte de baseline conservador
- degrada quando existem sinais `SAFETY/pacing_delay`, `SAFETY/risk_detected`, `SAFETY/cooldown_started`

### Risk profile

- considera apenas `SAFETY/*`
- deterministico por contagem e severidade

### Account health

- combina media de views, completion rate e risco
- classifica em `HEALTHY | WATCH | AT_RISK`

## Integracao

Conversa com:
- D28 (`SAFETY/*`)
- D26 (observabilidade estrategica)
- D21 (scheduler pode consumir as recomendacoes depois)

No v1.0 nao existe feedback automatico para scheduler ou publish.

## Criterio de aceite

O D30 fecha se:
- gera recomendacao de janela
- gera recomendacao de pacing
- detecta risco por conta
- produz snapshot de saude
- persiste append-only sem duplicacao em recomputacao identica


---

## Source: `docs/metrics/metrics_collector_v1_0.md`

# D33 - Metrics Collector v1.0

## Objetivo

Coletar metricas reais de performance dos videos para alimentar:

- D30 - Platform Intelligence
- D31 - Experiment Framework
- D32 - Advanced Attribution
- D26 - Strategy Observatory

Sem alterar o caminho de publish.

## Fluxo

`Platform API -> Metrics Collector Worker -> Normalized Metrics Model -> OUT/metrics/video_metrics.jsonl`

## Persistencia

Arquivo:

`OUT/metrics/video_metrics.jsonl`

Semantica:
- append-only
- idempotencia por `(publish_id, collected_at_bucket)`
- mesma coleta -> `NOOP`
- payload diferente na mesma chave -> `CONFLICT`

## Modelo canÃ´nico

### VideoMetricsRecord

- `metrics_id`
- `publish_id`
- `account_id`
- `video_id`
- `views`
- `likes`
- `comments`
- `shares`
- `watch_time_total`
- `avg_watch_time`
- `completion_rate`
- `view_3s_rate`
- `view_5s_rate`
- `collected_at`
- `collected_at_bucket`
- `age_hours`
- `provider`

## Frequencia recomendada

- primeiras 24h: a cada 30 min
- 24h-72h: a cada 2h
- acima de 72h: diario

## Eventos

- `METRICS/collection_started`
- `METRICS/collection_completed`
- `METRICS/collection_failed`
- `METRICS/api_rate_limited`

## Retry policy

- `max_attempts = 3`
- retry apenas para:
  - timeout
  - rate limit
  - erro 5xx transitÃ³rio

## Integracao

Input obrigatorio:
- `publish_record`

O collector nao inventa video fora de `publish_record`.

## Criterio de aceite

O D33 fecha se:
- coleta normal funciona
- idempotencia funciona
- erro de API e retry funcionam
- persistencia append-only funciona
- integracao com `publish_record` esta confirmada


---

## Source: `docs/observability.md`

# Contrato de Observabilidade (CortAI)

Este documento define o contrato minimo de observabilidade append-only do pipeline cognitivo.
O consumo e read-only a partir de JSONL/Observations; o destino e aggregate-only no Postgres.
Nao ha heuristica nem logica de decisao neste contrato.

## Eventos

### cognitive_loop_finished
Fonte: Observations (JSONL + Postgres `observations`).

Fatos obrigatorios:
- `event_type`
- `execution_status`
- `pipeline_status` (`completed` | `failed` | `blocked` | `truncated` | `published`)
- `termination_reason` (quando existir)
- `actions_executed`
- `last_action_type`
- `terminated`

Proibido em `facts`:
- Campos de caminho/path (ex.: `raw_video_minio_path`, `audio_local_path`, `manifest_path`)

### cognitive_metrics_alert
Fonte: agregacao de telemetria.

Fatos obrigatorios:
- `event_type`
- `metric_date` (YYYY-MM-DD)
- `reasons` (lista de strings)
- `total_runs`, `failed_runs`, `blocked_runs`
- `failed_ratio`, `threshold`

Fatos opcionais:
- `action_type`
- `p95_ms`, `threshold_ms`, `n`
- `ces_version`, `window_days`, `required_bad_days`, `bad_days_in_window`, `days_with_runs_in_window`, `ces_samples`

Reasons canonicamente suportados:
- `blocked_runs`
- `failed_ratio`
- `ces_regression:CES_v1`

### collector_run
Fonte: adaptador do coletor (`CollectorAdapter`) com persistencia best-effort em `observations`.

Objetivo:
- registrar sucesso ou falha classificada do coletor sem abrir query nova no request path;
- reduzir debug manual de problemas como URL invalida, `HTTP 4xx/5xx`, `timeout`, `DNS` e `TLS/CA`.

Fatos obrigatorios:
- `event_type` (`collector_run`)
- `status` (`success` | `failed`)
- `duration_ms`
- `source_ref` (sanitizado)
- `job_id` (quando existir)
- `source_type` (`audio` | `video` | `null`)
- `error_type` (`invalid_input` | `http_4xx` | `http_5xx` | `ssl_cert_verify_failed` | `dns_failed` | `timeout` | `upstream_blocked` | `unknown` | `null`)
- `retryable`

Fatos opcionais:
- `http_status`
- `minio_bucket`
- `minio_key_prefix`

Regras de sanitizacao:
- remover query params sensiveis de `source_ref` (`token`, `sig`, `signature`, `key`, `auth`, `access_token`);
- nunca persistir a chave completa do MinIO;
- `minio_key_prefix` deve ser apenas o prefixo truncado da key (maximo 32 chars).

Exemplo de sucesso:
```json
{
  "event_type": "collector_run",
  "status": "success",
  "source_type": "audio",
  "duration_ms": 842,
  "error_type": null,
  "http_status": null,
  "retryable": false,
  "job_id": "job-123",
  "source_ref": "http://localhost:8001/smoke-assets/audio_1s.wav",
  "minio_bucket": "videos-raw",
  "minio_key_prefix": "smoke/audio_1s.wav"
}
```

Exemplo de falha:
```json
{
  "event_type": "collector_run",
  "status": "failed",
  "source_type": null,
  "duration_ms": 119,
  "error_type": "http_4xx",
  "http_status": 404,
  "retryable": false,
  "job_id": "job-404",
  "source_ref": "https://example.com/video.mp4",
  "minio_bucket": null,
  "minio_key_prefix": null
}
```

## Recheck Maestro

Objetivo:
- validar o slice de orquestracao do Maestro com stop-the-line;
- gerar evidencia auditavel em `OUT/`;
- terminar em `GO` ou `NO-GO` com exit code coerente.

Pre-requisitos:
- Docker daemon ativo;
- Compose com `cortai_api`, `cortai_edge`, `cortai_db` e `cortai_minio` em execucao;
- endpoints internos expostos no `api`;
- gate interno habilitado para o header `X-Internal-Status: 1`.

Comando unico:
```powershell
.\scripts\recheck_maestro.ps1
```

Wrapper curto:
```cmd
scripts\recheck_maestro.cmd
```

Artefatos gerados:
- `OUT/00_maestro_precheck.txt`
- `OUT/01_maestro_gates_http.txt`
- `OUT/02_maestro_migration.txt`
- `OUT/03_maestro_pytest_focal.txt`
- `OUT/04_maestro_demo_smoke.txt`
- `OUT/05_maestro_real_failed_smoke.txt`
- `OUT/06_maestro_contract_v03.txt`
- `OUT/07_maestro_invariants.txt`
- `OUT/08_maestro_no_leak.txt`
- `OUT/09_maestro_logs.txt`
- `OUT/RECHECK_MAESTRO_TOTAL.md`
- `OUT/RECHECK_MAESTRO_SUMMARY.md`

Interpretacao:
- qualquer falha em uma secao stop-the-line encerra o script com `NO-GO`;
- migration e validada dentro do container `cortai_api`, que e o ambiente correto para o runtime do Maestro;
- `GO` exige gates, migration, testes focais, smoke demo, smoke real failed-controlado, persistencia, no-leak e logs.

## CI Strategy

### maestro_focal (GitHub Actions)

Objetivo:
- regressao rapida do nucleo Maestro (v0.3)

Escopo:
- `compileall` (stop-the-line)
- pytest focal:
  - `tests/test_maestro_orchestrator.py`
  - `tests/test_internal_maestro_api.py`
  - `tests/test_audio_extractor_adapter.py`
- sem Docker
- sem Compose
- sem DB

Tempo esperado:
- menor que 1 minuto

### recheck_maestro.ps1 (Local / Operacional)

Objetivo:
- auditoria completa do runtime Maestro

Inclui:
- gates HTTP
- migration no container correto
- smoke demo
- smoke real failed-controlado
- contrato v0.3
- invariantes
- no-leak
- logs
- evidencia em `OUT/`

CritÃ©rio:
- `GO` / `NO-GO` explicito

## Saida do pipeline

`write_artifact` gera um manifest deterministico em `storage/agent_output/<decision_id>.json` com:
- `process_id`, `decision_id`
- `pipeline_status`, `termination_reason`
- `segments_count`, `transcriptions_count`
- `artifact_paths.manifest_path`
- `artifacts.raw_video_minio_path`, `artifacts.audio_local_path`
- `created_at`

`publish_manifest` consome apenas o manifest (manifest-only) via `decision_id`.

## Receipt de publicacao

A auditoria de publish e persistida em `publish_receipts` com idempotencia por
`publish_decision_id`.

Campos principais:
- `publish_decision_id` (chave unica)
- `process_id`
- `manifest_decision_id`
- `pipeline_status` (`published` | `blocked` | `failed`)
- `execution_status` (`success` | `blocked` | `failed`)
- `target`
- `external_post_id` (quando existir)
- `error_type`, `error_message` (sem paths)
- `published_at`, `created_at`, `updated_at`

## Regras de dedupe

Agregacao de telemetria:
- Uma linha por `metric_date` em `cognitive_metrics_daily` (upsert).

Emissao de alertas:
- Dedupe por (`metric_date`, `reason`).
- Pode haver mais de um alerta por dia quando os motivos forem diferentes.

Emissao de loop finalizado:
- Um `cognitive_loop_finished` por `(process_id, source_outcome_id)`.
- Se `run_loop` receber um processo ja terminado, usa `stop_reason=already_terminated` e tenta emitir uma vez.
- Se o par ja existir, a emissao e ignorada (dedupe).

## Cognitive Efficiency Score (CES)

### CES Versions

Regra de versionamento:
- `CES_v1` e congelado e imutavel.
- `CES_v2` e congelado e imutavel.
- `CES_v3` e experimental.
- Novas formulas entram como novas versoes (`CES_v3`, `CES_v4`, ...).
- `ces_default_version` inicial: `CES_v1`.
- Campos top-level (`ces`, `ces_version`, `ces_reason`, `ces_components`, `budgets_used`) sempre refletem a versao default.
- `CES_v2` e `CES_v3` ficam disponiveis apenas em `ces_versions`, sem alterar o default.

Shape canonicamente exposto por item:
- `ces_default_version`
- `ces`
- `ces_version`
- `ces_reason`
- `ces_components`
- `budgets_used`
- `ces_versions` (`CES_v1`, `CES_v2`, `CES_v3`)

### CES_v1

Acoes canonicamente consideradas no `S_latency` e em `budgets_used`:
- `collect_video`
- `extract_audio`
- `segment_audio`
- `transcribe_segments`
- `write_artifact`
- `publish_manifest`

Elegibilidade:
- A acao entra no latency score apenas quando `n >= 10`.

Regra:
- `unknown` e excluido por design do latency score e de `budgets_used`.
- `unknown` pode aparecer em `latency_by_action` (telemetria bruta), mas nao participa de `S_latency`, pesos `n_a`, budgets `B_a` ou do CES.

Regra de dia sem execucao:
- Se `total_runs = 0`, retorna `ces = null` e `ces_reason = "no_runs"`.

### CES_v2

CES_v2 usa os mesmos sinais de entrada do CES_v1 (`status`, `actions`, `latency`, `trunc`) e
mantem as mesmas restricoes de whitelist/elegibilidade:
- whitelist de acoes identica ao CES_v1
- `n >= 10` para acao participar de `S_latency`
- `unknown` excluido por design
- `total_runs = 0` => `ces = null` e `ces_reason = "no_runs"`

Diferenca principal:
- `S_latency` usa penalizacao suave por excesso relativo ao budget da acao.
- Para cada acao elegivel:
  - `budget_ms = ceil(p95_ms * 1.10)`
  - `ratio = p95_ms / budget_ms`
  - `score_a = 1` quando `ratio <= 1`
  - `score_a = clamp(1 - k * (ratio - 1), 0, 1)` quando `ratio > 1` (com `k = 0.7`)
  - `S_latency` e a media ponderada por `n` das acoes elegiveis.

Politica:
- CES_v2 nao altera CES_v1; apenas expande a leitura em `ces_versions`.

### CES_v3 (experimental)

CES_v3 usa os mesmos sinais de entrada do CES_v1/CES_v2 (`status`, `actions`, `latency`, `trunc`) e
mantem as mesmas restricoes de whitelist/elegibilidade:
- whitelist de acoes identica ao CES_v1
- `n >= 10` para acao participar de `S_latency`
- `unknown` excluido por design
- `total_runs = 0` => `ces = null` e `ces_reason = "no_runs"`

Diferenca principal:
- `S_latency` usa budget por acao com fonte `dynamic_baseline_14d`.
- Regra de budget no v3:
  - primeiro tenta `latency_dynamic_baseline[action].budget_ms` (source `dynamic_14d`);
  - sem baseline elegivel, faz fallback para budget fixo v1 (`fixed_v1`).

Politica:
- CES_v3 e experimental e fica disponivel somente em `ces_versions`.
- CES_v3 nao altera `ces_default_version` nem os campos top-level.

### Baseline dinamico de latencia (read-only)

Objetivo:
- Expor baseline dinamico por acao como telemetria auxiliar, sem alterar o score default.

Regra canonica:
- `B_a_dynamic = ceil(median(p95_ms_ultimos_14_dias) * 1.10)`.
- Considera somente acoes da whitelist CES.
- Considera somente dias com `total_runs > 0`.
- Considera somente amostras por acao com `n >= 10`.
- Exclui `unknown` por design.

Fallback:
- Sem historico elegivel para a acao, usa budget fixo v1 (`fallback_fixed_v1`).

Exposicao no endpoint:
- `latency_dynamic_baseline_window_days`
- `latency_dynamic_baseline` (por acao: `budget_ms`, `source`, `samples_used`)

Invariante:
- Baseline dinamico e read-only e nao altera `ces`, `ces_version` nem `ces_default_version`.

### Cognitive Efficiency Score - Run-level

Versao:
- `CES_run_v1` (congelado e imutavel).
- Mudancas futuras geram novas versoes (`CES_run_v2`, `CES_run_v3`, ...).

Fonte de verdade:
- Para cada `process_id`, usar o `cognitive_loop_finished` mais recente por `timestamp`.
- Evento de fechamento: `facts.event_type = "cognitive_loop_finished"`.
- Dedupe de emissao continua por `(process_id, source_outcome_id)`.

Componentes do `CES_run_v1`:
- `S_status` por tabela fixa:
  - `published=1.00`
  - `completed=0.98`
  - `truncated=0.70`
  - `failed=0.35`
  - `blocked=0.10`
  - `unknown=0.00`
- `S_actions = clamp((6 - A) / (6 - 1), 0, 1)`, com `A = actions_executed`.
  - Se `actions_executed` ausente: `A=0` e `S_actions=0` (fallback deterministico).
- `S_trunc = 0` quando `pipeline_status = truncated`, senao `1`.
- Latencia real por run:
  - Duracao por acao: `duration_ms = outcome.timestamp - decision.timestamp`.
  - Pareamento por `process_id` + `source_decision_id == decision_id`.
  - Em caso de multiplos outcomes para a mesma decision, usar o mais recente por timestamp.
  - Whitelist: `collect_video`, `extract_audio`, `segment_audio`, `transcribe_segments`, `write_artifact`, `publish_manifest`.
  - `unknown` e excluido por design.
  - Elegibilidade run-level: a acao entra no score quando `n >= 3` dentro do run.
  - Budgets fixos iniciais (ms):
    - `collect_video`: 20000
    - `extract_audio`: 5000
    - `segment_audio`: 8000
    - `transcribe_segments`: 30000
    - `write_artifact`: 3000
    - `publish_manifest`: 3000
  - Score por acao:
    - `ratio = p95_ms / budget_ms`
    - se `ratio <= 1`: `score_a = 1`
    - se `ratio > 1`: `score_a = clamp(1 - 0.7 * (ratio - 1), 0, 1)`
  - `S_latency` e media ponderada por `n` das acoes elegiveis.
  - Se nao houver acao elegivel:
    - `S_latency = 1.0`
    - `latency_measured = false`
    - `budgets_used = {}`
  - Auditoria read-only do calculo:
    - `latency_pairs_used`: pares `decision -> outcome` usados.
    - `latency_pairs_ignored`: pares ignorados (sem match, fora da whitelist, timestamp invalido).
    - `latency_pairs_inverted`: pares com `decision_ts > outcome_ts`.
  - `latency_pairs_*` nao alteram o score; sao apenas telemetria de auditoria.
  - Invariante esperado: `latency_pairs_inverted = 0`; se maior que zero, tratar como investigacao de clock drift/ordem de eventos.

Contrato operacional v1.2 (lean list / heavy debug):
- `GET /api/v1/metrics/runs` e endpoint de lista lean:
  - retorna apenas `process_id`, `timestamp_finished`, `pipeline_status`, `ces_run`,
    `ces_run_version`, `ces_run_reason`, `ces_run_components`, `latency_measured`,
    `latency_pairs_inverted`.
  - nao retorna campos pesados (`budgets_used`, `latency_pairs_used`, `latency_pairs_ignored`).
  - nao executa calculo de latencia real por acao (run-level pesado).
- `GET /api/v1/metrics/runs/{process_id}` permanece endpoint de debug heavy:
  - inclui `latency_breakdown` (budgets por acao), `latency_pairs_used/ignored/inverted`,
    `links`, `artifact_refs`, `last_error` sanitizado.

### Run debug view

Endpoint read-only:
- `GET /api/v1/metrics/runs/{process_id}`

Contrato minimo:
- `run_summary` com status final, CES_run, componentes e auditoria de latencia (`latency_pairs_*`).
- `links` com `observation_id`, `source_outcome_id`, `source_decision_id`, `manifest_decision_id`, `publish_decision_id`.
- `artifact_refs` com `manifest_path` e `publish_receipt_id`.
- `last_error` sanitizado (`error_type`, `error_message` sem paths sensiveis).
- `latency_breakdown` somente para acoes whitelist.
- `missing_fields` quando algum dado opcional nao estiver disponivel.

Fonte de verdade:
- ultimo `cognitive_loop_finished` no Postgres para o `process_id`.

Pesos do `CES_run_v1`:
- `alpha=0.60` (status)
- `beta=0.15` (actions)
- `gamma=0.20` (latency)
- `delta=0.05` (trunc)

Formula:
- `CES_run_v1 = 100 * (alpha*S_status + beta*S_actions + gamma*S_latency + delta*S_trunc)`
- Clamp final em `[0, 100]`.

Casos ausentes:
- Se nao existir `cognitive_loop_finished` para o `process_id`: `ces_run = null`, `ces_run_reason = "missing_finished_observation"`.
- Se `pipeline_status` ausente no evento: `pipeline_status = "unknown"`, `ces_run = null`, `ces_run_reason = "missing_pipeline_status"`.

### CES Window Counter

`summary.ces_bad_days_in_window`:
- Numero de dias ruins dentro da janela `COGNITIVE_ALERT_CES_WINDOW_DAYS`.
- Dia ruim: `ces` (versao default) `< COGNITIVE_ALERT_CES_THRESHOLD`.
- `ces_window_effective_days` conta apenas dias validos (`ces != null` e `ces_reason != "no_runs"`).
- Exclui dias com `ces = null` (`ces_reason = "no_runs"`).
- Nao e persistido; e calculado dinamicamente no endpoint.
- Usa a mesma regra base do alerta `ces_regression:CES_v1`.

Campos de janela expostos no `summary`:
- `ces_window_days`
- `ces_window_effective_days`
- `ces_threshold`
- `ces_bad_days_required`
- `ces_bad_days_in_window`
- `ces_bad_days_ratio`

Regra de ratio:
- `ces_bad_days_ratio = ces_bad_days_in_window / ces_window_effective_days` quando `effective_days > 0`.
- `ces_bad_days_ratio = null` quando `effective_days = 0`.

## Variaveis de ambiente

Telemetria:
- `COGNITIVE_LOOP_MAX_STEPS` (padrao: 10)

Alertas:
- `COGNITIVE_ALERT_MAX_PER_DAY` (padrao: 5)
- `COGNITIVE_ALERT_P95_TRANSCRIBE_MS` (padrao: 60000)
- `COGNITIVE_ALERT_P95_COLLECT_MS` (padrao: 90000)
- `COGNITIVE_ALERT_P95_EXTRACT_MS` (padrao: 30000)
- `COGNITIVE_ALERT_P95_SEGMENT_MS` (padrao: 30000)
- `COGNITIVE_ALERT_CES_ENABLED` (padrao: 1)
- `COGNITIVE_ALERT_CES_THRESHOLD` (padrao: 85)
- `COGNITIVE_ALERT_CES_BAD_DAYS` (padrao: 3)
- `COGNITIVE_ALERT_CES_WINDOW_DAYS` (padrao: 7)

## Endpoints da API

### GET /api/v1/metrics/daily
Query params:
- `start_date` (YYYY-MM-DD)
- `end_date` (YYYY-MM-DD)
- `days` (1..365)

### GET /api/v1/metrics/overview
Query params:
- `start_date` (YYYY-MM-DD)
- `end_date` (YYYY-MM-DD)
- `days` (1..365)
- `include_reasons` (bool, default `false`)
- `include_baseline` (bool, default `false`)

Contrato de alertas no overview:
- `alerted` e `alert_count` sempre presentes.
- `alert_reasons` sempre presente no shape:
  - default (`include_reasons=false`): `[]`
  - `include_reasons=true`: reasons deduplicadas/ordenadas.
- `latency_dynamic_baseline` sempre presente no shape:
  - default (`include_baseline=false`): `{}`
  - `include_baseline=true`: baseline por acao (`budget_ms`, `source`, `samples_used`).
- Fonte DB-first:
  - overview le `cognitive_metrics_daily` (incluindo `alert_count`/`alert_reasons` materializados no agregado diario)
  - nao executa lookup de alertas em `observations` durante a request
  - resposta usa cache read-only curto (TTL 10s) por query para reduzir p95 sob concorrencia

### GET /api/v1/metrics/alerts
Query params:
- `start_date` (YYYY-MM-DD)
- `end_date` (YYYY-MM-DD)
- `limit` (1..500)
- `offset` (>= 0)

### GET /api/v1/observability/report
Query params:
- `window_days` (default 7, max 30)
- `timing_minutes` (default 15, max 60)
- `limit_alerts` (default 200, max 500)
- `limit_receipts` (default 50, max 200)
- `include_worst_runs` (default `false`)
- `include_receipts` (default `false`)
- `include_alert_items` (default `false`)
- `limit_worst_runs` (default 20, max 200; usado quando `include_worst_runs=true`)

Contrato minimo:
- endpoint read-only que consolida o runbook operacional em JSON deterministico
- inclui blocos de versao, timing, slo_daily, slo_alerts, runs, publish_receipts, checks e status
- modo default e lean (blocos pesados ficam opt-in por query params `include_*`)
- `status`:
  - `FAIL` se check hard falhar (`timing_events_15m`, `daily_has_requests_7d`, `receipts_path_leaks_30d`)
  - `WARN` quando `include_worst_runs=true` e `runs.worst` estiver vazio
  - `PASS` caso contrario

Comparativo de modo de resposta:

| Bloco | Default (lean) | Heavy (opt-in) |
|---|---|---|
| `version`, `timing`, `slo_daily`, `checks`, `status` | sempre presente | sempre presente |
| `runs.worst` | `[]` (desativado por default) | preenchido com `include_worst_runs=true` |
| `slo_alerts.items` | `[]` (somente `count`) | preenchido com `include_alert_items=true` |
| `publish_receipts.errors_7d` e `publish_receipts.latest_7d` | `[]` | preenchidos com `include_receipts=true` |

Guardrails do endpoint:
- `window_days > 30` => `400` (`error_type=RangeTooLarge`, `window_days_requested`, `window_days_max`)
- `timing_minutes > 60` => `400` (`error_type=RangeTooLarge`, `timing_minutes_requested`, `timing_minutes_max`)
- `limit_alerts > 500` => `400` (`error_type=LimitTooHigh`, `limit_alerts_requested`, `limit_alerts_max`)
- `limit_receipts > 200` => `400` (`error_type=LimitTooHigh`, `limit_receipts_requested`, `limit_receipts_max`)
- `limit_worst_runs > 200` => `400` (`error_type=LimitTooHigh`, `limit_worst_runs_requested`, `limit_worst_runs_max`)
- `include_worst_runs=true` com `window_days > 7` => `400` (`error_type=RangeTooLarge`, `window_days_max_for_worst_runs`)

Otimizacoes v1.3.2 (sem mudanca de contrato):
- `version.alembic_head` usa cache in-memory curto (TTL 60s) para remover query fixa do request path.
- `publish_receipts.path_leaks_30d` usa cache in-memory curto (TTL 30s) para reduzir custo recorrente.
- `slo_daily.summary` passa a ser derivado de `slo_daily.items` em memoria (sem query adicional).
- Em ambiente de testes (`pytest`), caches locais sao desativados para manter casos deterministas.
- Meta medida em regime (cache aquecido): `p95_db_queries ~= 2` e `p95_db_us ~= 3-4ms` no caminho default lean.
- Comportamento de cold-start (apos restart): o `p95_db_us` pode subir temporariamente para a faixa de `~20-25ms`.

## Metrics SLO

Escopo operacional:
- Valido para ambiente normal, com banco saudavel.
- Exclui cenarios de debug pesado e consultas de range grande.

Endpoints cobertos:
- `GET /api/v1/metrics/runs`
- `GET /api/v1/metrics/runs/{process_id}`
- `GET /api/v1/metrics/overview`
- `GET /api/v1/observability/report`

SLO real (contrato):
- `/metrics/runs`: `p95 <= 150ms`, `p99 <= 300ms`, `error_rate <= 1%`
- `/metrics/runs/{process_id}`: `p95 <= 200ms`, `p99 <= 400ms`, `error_rate <= 1%`
- `/metrics/overview`: `p95 <= 120ms`, `p99 <= 250ms`, `error_rate <= 1%`
- `/observability/report`: `p95 <= 300ms`, `p99 <= 600ms`, `error_rate <= 1%`

Error budget diario:
- `error_budget = 1%` por endpoint/dia.
- `allowed_errors = count_requests * 0.01`.
- `estimated_errors = count_requests * error_rate`.
- `remaining_errors = allowed_errors - estimated_errors`.

Guardrails de entrada:
- `limit_max = 200` para endpoint run-level paginado.
- `range_max_days = 31` para endpoint run-level com janela de datas.

### Event Types de SLO

`metrics_endpoint_timing`:
- Telemetria append-only por request dos endpoints de metricas alvo.
- Shape minimo em `facts`:
  - `endpoint`
  - `method`
  - `status_code`
  - `duration_ms`
  - `duration_us` (alta resolucao para diagnostico sub-ms)
  - `queue_us` (tempo entre entrada ASGI e inicio do handler)
  - `handler_ms`
  - `server_total_ms`
  - `server_total_us`
  - `query_fingerprint`
  - `cache_hit` (quando aplicavel, ex.: `/metrics/overview`)
  - `cache_key_hash` (hash curto da chave canonica, quando aplicavel)
  - `process_id` (quando existir no path)
  - `metric_date` (YYYY-MM-DD)

Diagnostico de fila (v1.2.6):
- Para `/api/v1/metrics/overview`, comparar p95 client-side vs p95 server-side (`duration_ms`) com `cache_hit=true`.
- Priorizar `queue_us`/`server_total_us` para separar fila de execucao interna do handler.

`metrics_slo_alert`:
- Alerta diario de regressao de SLO por endpoint.
- Condicoes canonicas:
  - `p95_ms > slo_p95` ou
  - `p99_ms > slo_p99` ou
  - `error_rate > 0.01`
- Dedupe por `(metric_date, endpoint, reason)`.

### GET /api/v1/status

Query params:
- `window_days` (default 7, max 30)

Contrato minimo:
- endpoint read-only para status executivo de SLO.
- retorna `overall_status` (`PASS|WARN|FAIL`), `slo_status`, `error_budget_remaining`, `ces_trend_status`.
- `FAIL` quando algum endpoint com dados viola SLO.
- `WARN` quando faltam dados para endpoint coberto no periodo.

Guardrail:
- `window_days > 30` => `400` (`error_type=RangeTooLarge`, `window_days_requested`, `window_days_max`)

### CI performance gate (minimo)

Pipeline CI deve validar regressao basica de performance para `/api/v1/metrics/runs`:
- 5 warmups + 50 chamadas medidas
- gate minimo: `p95 <= 300ms`
- gate minimo: `error_rate <= 1%`

## Exemplos

```bash
curl -s "http://localhost:8000/api/v1/metrics/daily?start_date=2026-02-10&end_date=2026-02-10"
curl -s "http://localhost:8000/api/v1/metrics/overview?days=7"
curl -s "http://localhost:8000/api/v1/metrics/alerts?start_date=2026-02-10&end_date=2026-02-10"
```

## Evidencia operacional (smoke runtime)

Data UTC: `2026-02-16T21:55:01Z`
Commit: `3622bf2`

```json
{"process_id":"P_PUBLISH_FLOW2","pipeline_status":"completed","execution_status":"success","ces_run":98.8,"latency_measured":false,"latency_pairs":{"used":2,"ignored":0,"inverted":0},"source_outcome_id":"a45a3872-1a7d-496b-b160-296ec033121e","last_error":{"error_type":null,"error_message":null}}
{"process_id":"P_VIDEO_6c2ff2f2-f28a-4c9f-9d5d-b4640b31d427","pipeline_status":"published","execution_status":"success","ces_run":100.0,"latency_measured":false,"latency_pairs":{"used":6,"ignored":1,"inverted":0},"source_outcome_id":"dfc94ca4-a948-4387-8fe5-4016f2182138","last_error":{"error_type":null,"error_message":null}}
{"process_id":"P_BLOCKED_EVIDENCE_4b29ae9a","pipeline_status":"blocked","execution_status":"blocked","ces_run":31.0,"latency_measured":false,"latency_pairs":{"used":0,"ignored":1,"inverted":0},"source_outcome_id":"61d985e7-65aa-4795-a0f4-2c2a054b84ea","last_error":{"error_type":"ArtifactNotFound","error_message":"manifest nao encontrado: <path>/agent_output/MISSING_MANIFEST_6f586b602f8e4b3aa6bf662b145fde03.json"}}
```

## Evidencia operacional - /observability/report (v1.8.2)

Data UTC: `2026-02-17`

- `/health`: `status=ok`, `api_version=1.8.2`, `ces_default_version=CES_v1`
- Shape minimo do report: validado
- Guardrails validados:
  - `window_days=31` -> `400 RangeTooLarge` (`window_days_max=30`)
  - `timing_minutes=61` -> `400 RangeTooLarge` (`timing_minutes_max=60`)
  - `limit_alerts=501` -> `400 LimitTooHigh` (`limit_alerts_max=500`)
  - `limit_receipts=201` -> `400 LimitTooHigh` (`limit_receipts_max=200`)
- `checks`: 6 itens, todos com `id` e `pass`
- Timing sanity: `events=29`, `bad_duration=0`
- `slo_daily`: `has_requests=true`, `items_len=2`
- `publish_receipts.path_leaks_30d=0`
- `status=WARN` (contrato: `PASS|WARN|FAIL`)
- Self-observing: `events_before=34` -> `events_after=38` apos 3 chamadas

### Links

- PR `feat/observability-report`: `https://github.com/theusnevess/CortAI/pull/new/feat/observability-report`
- Runbook operacional v1.8.2: `https://github.com/theusnevess/CortAI/blob/v1.8.2/docs/runbook_operacional_v1.8.2.md`

## Load Envelope v1.1 (baseline oficial)

Data UTC: `2026-02-18`

### Nota de ambiente: Docker Desktop + WSL2 (edge nao e fonte de verdade)

Quando o stack roda em Docker Desktop + WSL2 (`docker-desktop`), o proxy edge (Nginx) pode introduzir
latencia artificial de TTFB/queue que nao reflete o handler da API.

Regra canonica (importante):
- NAO calibrar SLO/envelope usando o caminho edge nesse ambiente.
- Para validacao local, use direct (`cortai_worker -> http://cortai_api:8000`) como referencia.
- Para envelope final e SLO "real", rode o benchmark em Linux nativo (VM/VPS/host), comparando direct vs edge.

Evidencia tipica do vies (sintoma):
- `upstream_connect_time ~ 0` e `upstream_header_time ~= request_time` altos no edge,
  enquanto `server_total_us` da API permanece baixo (cache-hit), indicando contensao/bridge fora do handler.

Perfil de carga:
- mix fixo: `/api/v1/metrics/runs` (60%), `/api/v1/observability/report` (25%), `/api/v1/metrics/overview` (15%)
- duracao por degrau: `60s`
- parametros fixos:
  - `/api/v1/metrics/runs?start_date=2026-02-11&end_date=2026-02-18&limit=200&offset=0`
  - `/api/v1/metrics/overview?days=7`
  - `/api/v1/observability/report?window_days=7&timing_minutes=15`

Snapshot de thresholds SLO usados no teste:
- `/api/v1/metrics/runs`: `p95 <= 150ms`, `p99 <= 300ms`, `error_rate <= 1%`
- `/api/v1/metrics/runs/{process_id}`: `p95 <= 200ms`, `p99 <= 400ms`, `error_rate <= 1%`
- `/api/v1/metrics/overview`: `p95 <= 120ms`, `p99 <= 250ms`, `error_rate <= 1%`
- `/api/v1/observability/report`: `p95 <= 300ms`, `p99 <= 600ms`, `error_rate <= 1%`

Resultado resumido:
- baseline p95:
  - runs `254.98ms`
  - report `113.67ms`
  - overview `91.16ms`
  - error_rate `0`
- degrau `C=1` p95:
  - runs `264.15ms` (`p99=306.06ms`)
  - report `121.5ms`
  - overview `102.37ms`
  - error_rate `0`
- degrau `C=5` p95:
  - runs `1053.9ms`
  - report `693.07ms`
  - overview `502.63ms`
  - error_rate `0`

Evidencia de observabilidade:
- `metrics_endpoint_daily` inclui os 3 endpoints do mix com `count_requests > 0`
- `metrics_slo_alert` emitido para `runs`, `report` e `overview`
- `timing.bad_duration = 0`

Conclusao operacional:
- safe envelope: `C=1`
- first violation: `C=5`
- violacao por latencia (SLO), nao por disponibilidade (sem 5xx)

## Envelope oficial v1.3 (Linux nativo)

Ambiente:
- Runner Linux nativo (fora Docker Desktop / WSL2)
- `wrk -t2 -c{1,2,5} -d60s --timeout 10s`
- Mix executado por endpoint isolado

Matriz consolidada:

| endpoint | C | p90 | p99 | req/s | timeouts |
|---|---:|---:|---:|---:|---:|
| overview | 1 | 218ms | 244ms | 4.73 | 0 |
| overview | 2 | 411ms | 451ms | 4.99 | 0 |
| overview | 5 | 823ms | 1.24s | 4.94 | 0 |
| runs | 1 | 231ms | 260ms | 4.49 | 0 |
| runs | 2 | 425ms | 451ms | 4.81 | 0 |
| runs | 5 | 1.26s | 1.68s | 4.79 | 0 |
| report | 1 | 241ms | 273ms | 4.26 | 0 |
| report | 2 | 433ms | 460ms | 4.69 | 0 |
| report | 5 | 866ms | 885ms | 4.73 | 0 |

Decisao:
- `safe_envelope_v1.3 = C1`

Justificativa:
- p90/p99 de `/metrics/overview` excede SLO ja em C1.
- Nenhum timeout ocorreu.
- Gargalo nao e handler (server-side sub-ms confirmado anteriormente).
- Limitacao atual e throughput do ambiente sob concorrencia >1.

Endpoint limitante:
- `/api/v1/metrics/overview`

## Stable Baseline Declaration - v1.9.x

A linha `v1.9.x` e considerada baseline estavel, auditavel e governada, com:
- Governanca de versao consistente (`/health` refletindo a versao operacional da release).
- Observabilidade completa em runtime (`timing`, `queue_us`, `db_us`, `server_total_us`).
- Endpoint `/api/v1/observability/report` em modo lean por default.
- Envelope oficial documentado e validado em Linux nativo.
- Sanitizacao validada (`path_leaks_30d = 0`).
- Sanidade de timing validada (`bad_duration = 0`).
- Telemetria append-only preservada.

A partir desta baseline:
- Mudancas estruturais devem abrir linha evolutiva explicita (ex.: v2.0).
- Ajustes de SLO/envelope devem ser deliberados, medidos e documentados.
- Evolucoes de performance devem manter rastreabilidade por evidencias runtime + pivot DB.

## Matriz P1 (workers x DB pool) - resultado e decisao (Linux nativo)

Objetivo:
- Validar se ajuste de process model (`API_WORKERS`) e DB pool (`DB_POOL_SIZE`) e suficiente para elevar o `safe_envelope v2.0` para `C=2` (mix 60/25/15), sem alterar logica dos endpoints.

Execucao:
- Artefato: `.tmp_matrix_p1/matrix_p1_summary.csv`
- Ambiente: Linux nativo
- Mix: `60/25/15`, duracao `60s` por degrau, timeout `10s`
- Concurrency avaliada: `C=2`
- Endpoints: `/api/v1/metrics/overview`, `/api/v1/metrics/runs`, `/api/v1/observability/report`

Checklist operacional P1 (PASS/FAIL):
- PASS: `timeouts=0` em todos os combos.
- PASS: `db_pool_wait_us=0` em todos os combos (sem contention de pool).
- FAIL: `safe_envelope_v2.0 = C2` nao atingido (latencia acima do SLO).
- PASS: endpoint limitante identificado de forma consistente: `/api/v1/metrics/overview`.

Winner P1 (melhor equilibrio geral):
- Config vencedora: `API_WORKERS=2`, `DB_POOL_SIZE=10`.
- Motivo: melhor equilibrio de `p90/p99` entre `overview/runs/report`, mantendo DB estavel e sem timeouts.

Resultados (C=2, winner):
- `/api/v1/metrics/overview`: `p90 587.3ms`, `p99 640.73ms`
- `/api/v1/metrics/runs`: `p90 600.26ms`, `p99 668.0ms`
- `/api/v1/observability/report`: `p90 572.5ms`, `p99 635.95ms`

Telemetria (p95):
- `queue_us` (`overview/runs`): `~1289us / ~1268us`
- `db_us` (`overview/runs/report`): `~8096us / ~6784us / ~6739us`
- `db_queries`: `2` (`overview/runs`), `3` (`report`)

Decisao P1:
- Conclusao: P1 confirma que `workers/pool` nao sao o gargalo dominante para viabilizar `C=2` com os SLOs atuais.
- `queue_us` baixo (ordem de `~1-2ms p95`) e `db_pool_wait_us=0` indicam ausencia de contencao de pool/fila interna.
- Mesmo assim, a latencia cliente (`p90/p99`) permanece alta e viola SLO em todos os combos.
- Endpoint limitante principal: `/api/v1/metrics/overview`, com `/metrics/runs` tambem acima do SLO no mesmo patamar.

Proximo passo canonico (P2):
- Seguir para P2 (throughput/process model/infra path) sem mexer em logica de endpoint.
- Alternativamente, revisao deliberada dos SLOs alvo para `C=2` (decisao de produto/operacao).

## P2-B1 sintetico (Windows/Docker Desktop)

Escopo:
- Validar pipeline de observabilidade (timing -> agregacao -> alerta -> report/status).
- Gerar artefatos equivalentes ao P2-B1 sem depender de runner externo.

Limite metodologico (obrigatorio):
- Este metodo **nao e validacao estrutural de infra path**.
- Este metodo **valida pipeline de observabilidade + SLO/alerts + envelope logico**.
- Decisao estrutural de capacidade (`safe_envelope_v2.0` definitivo) continua dependente de runner externo.

Comando de execucao:

```bash
python scripts/run_p2b1_synthetic.py --metric-date 2026-02-09 --base-url http://localhost:8000 --timing-minutes 60
```

Artefatos gerados em `.tmp_p2/`:
- `p2_a_summary_direct.csv`
- `p2_a_summary_edge.csv`
- `report_after_synth.json`
- `status_after_synth.json`

Checks esperados do script:
- `report.timing.events > 0`
- `report.slo_daily.has_requests == true`
- `report.slo_alerts.count > 0` quando ha breach
- `bad_duration == 0`
- `path_leaks_30d == 0`

## P2-B2.3a - Edge/Keepalive/Backlog (C=2, 3 reps, 60s)

Escopo:
- Ambiente local atual.
- Paths: direct (`:8000`) e edge (`:8001`).
- Objetivo: verificar se tuning de edge aproxima `C=2` dos SLOs sem alterar logica de endpoint.

Artefatos:
- `.tmp_p2/p2_b2_3a_baseline_direct.csv`
- `.tmp_p2/p2_b2_3a_baseline_edge.csv`
- `.tmp_p2/p2_b2_3a_keepalive_off_edge.csv`
- `.tmp_p2/p2_b2_3a_keepalive_on_edge.csv`
- `.tmp_p2/p2_b2_3a_buffering_on_edge.csv`
- `.tmp_p2/p2_b2_3a_buffering_off_edge.csv`
- `.tmp_p2/p2_b2_3a_workerconn4096_edge.csv`
- `.tmp_p2/edge_logs_15m_tail400.txt`
- `.tmp_p2/edge_p95_on.json`
- `.tmp_p2/p2_b2_3a_server_pivot.json`

Preflight:
- `/health`: `status=ok`, `api_version=1.9.6`.
- `/api/v1/observability/report`: `bad_duration=0`, `path_leaks_30d=0`.

Diagnostico de edge (logs):
- `p95_uct=0.0s`
- `p95_uht~=0.815s`
- `p95_rt~=0.812s`
- Interpretacao: TTFB domina; connect nginx->api nao e o gargalo.

A/B keepalive OFF vs ON (p99, edge):
- `overview`: `829.59ms -> 800.37ms` (`-3.52%`)
- `runs`: `787.70ms -> 805.60ms` (`+2.27%`)
- `report`: `799.69ms -> 834.41ms` (`+4.34%`)
- Resultado: **FAIL** (criterio de ganho `>=20%` nao atingido).

A/B buffering ON vs OFF:
- Resultado: **FAIL** (ganho inconsistente e regressao em `report`).

Capacidade edge (`worker_connections 4096`):
- Resultado: **FAIL** (sem melhora consistente; regressao em parte dos cenarios).
- Mantido `worker_connections=8192` no estado final local.

Decisao P2-B2.3a:
- **FAIL** para objetivo de aproximar `C=2` do SLO via tuning de edge.
- Melhor equilibrio local entre testadas: `keepalive OFF + proxy_buffering OFF + worker_connections=8192` (sem ganho suficiente para promocao de envelope).
- Endpoint limitante: `/api/v1/metrics/overview` (principal), com `/api/v1/metrics/runs` como co-limitante.

Proxima etapa canonica:
- Avancar para **P2-B2.3b** (infra/OS/backlog/limits): backlog/accept queue, `ulimit`/sockets, portas efemeras/TIME_WAIT, tuning de accept loop, e validacao final com runner separado para decisao estrutural.

## P2-B2.3b - Infra/OS Path (Backlog, Sockets, Accept Loop)

Escopo:
- Ambiente Linux (preferencialmente runner separado).
- Objetivo: validar se gargalo `C=2` esta na camada OS/socket/accept e nao no app/DB/edge tuning.

Criterio de sucesso:
- ganho `>=15-20%` em `p99` no `C=2` sem alterar logica de endpoint
- `timeouts=0`
- `bad_duration=0`
- `db_pool_wait_us=0`

1) Backlog efetivo (listen / accept queue)
- Checklist:
  - `ss -ltnp | grep 8000`
  - verificar `Recv-Q` vs `Send-Q`
  - verificar `net.core.somaxconn`
  - verificar `net.ipv4.tcp_max_syn_backlog`
- Teste:
  - aumentar `somaxconn=4096`
  - aumentar `tcp_max_syn_backlog=4096`
  - reiniciar edge + api
  - rodar `C=2` (3 reps, 60s)
- PASS se:
  - `p99` reduzir `>=15%`
  - `Recv-Q` nao saturar sob carga

2) File descriptors (`ulimit`)
- Checklist:
  - `ulimit -n`
  - `cat /proc/<nginx_pid>/limits`
  - `cat /proc/<uvicorn_pid>/limits`
- Teste:
  - ajustar para `>=65535`
  - reexecutar `C=2`
- PASS se:
  - `p99` reduzir `>=15%`
  - nenhum erro de socket

3) TIME_WAIT / portas efemeras
- Checklist:
  - `ss -s`
  - `net.ipv4.ip_local_port_range`
  - `net.ipv4.tcp_tw_reuse`
- Teste:
  - expandir port range (ex.: `10000-65000`)
  - habilitar `tcp_tw_reuse=1`
  - reexecutar `C=2`
- PASS se:
  - `p99` reduzir `>=15%`
  - `TIME_WAIT` nao crescer descontroladamente

4) Accept loop tuning (nginx / uvicorn)
- Edge:
  - `multi_accept on;`
  - `reuseport on;`
- API:
  - testar com:
    - `workers=2` (baseline)
    - `workers=2 + --loop uvloop` (se aplicavel)
    - `workers=2 + --http httptools`
- PASS se:
  - `p99` reduzir `>=15%`
  - latencia mais estavel (menor variancia)

Artefatos obrigatorios:
- `.tmp_p2/p2_b2_3b_summary.csv`
- `.tmp_p2/p2_b2_3b_sysctl.txt`
- `.tmp_p2/p2_b2_3b_ss.txt`
- (se edge) logs com `rt/uct/uht`

Decisao P2-B2.3b:
- se nenhum ajuste infra produzir ganho `>=15-20%` em `C=2`:
  - concluir que `C=2` esta acima do envelope estrutural do ambiente atual
  - `safe_envelope_v2.0` permanece `C1`
  - proximo passo real passa a ser:
    - revisao deliberada de SLO, ou
    - mudanca de arquitetura (P2-C)

## P2-C - Architecture Path (caso P2-B2.3b nao atinja meta)

Escopo:
- Aplicavel somente se `P2-B2.3b` (infra/OS) nao produzir ganho `>=15-20%` em `p99` (`C=2`).
- Objetivo: revisar arquitetura para tornar `C=2` estruturalmente viavel sem degradar governanca/observabilidade.

Estado de entrada:
- `timeouts=0`
- `db_pool_wait_us=0`
- edge tuning nao resolve
- infra/OS tuning nao resolve
- limitantes: `/api/v1/metrics/overview` (principal), `/api/v1/metrics/runs` (co)

1) Opcao A - Revisao deliberada de SLO (envelope realista)
- Acao:
  - formalizar que `C2` excede envelope estrutural do ambiente atual
  - ajustar SLO para:
    - `C1` como envelope oficial
    - `C2` como best-effort nao contratual
- Criterio:
  - evidencia consolidada `P2-A + P2-B2.3a + P2-B2.3b`
- Impacto:
  - nenhuma alteracao arquitetural
  - mantem simplicidade operacional

2) Opcao B - Materializacao/cache estrutural (read path)
- Objetivo:
  - reduzir TTFB no `/metrics/overview` e `/metrics/runs`
- Possiveis intervencoes:
  - snapshot diario materializado (job assincrono)
  - cache Redis para overview (TTL curto)
  - pre-agregacao de metricas (write-time, nao read-time)
  - separar read-model (CQRS leve)
- Criterio de sucesso:
  - `p99 C=2 < 400ms` (ou meta definida)
  - `db_queries` estaveis
  - `bad_duration=0`

3) Opcao C - Separacao de servico (read API isolada)
- Acao:
  - separar endpoints de leitura pesada em servico dedicado
  - API principal mantem status/health/observability leve
- Objetivo:
  - isolar throughput read path
  - permitir tuning dedicado (workers, cache, autoscale)
- Criterio:
  - `C2` passa SLO com arquitetura segmentada

4) Opcao D - Ajuste de modelo de execucao
- Intervencoes possiveis:
  - async full-stack real (sem bloqueios sincronos residuais)
  - `uvloop` obrigatorio
  - HTTP server diferente (ex.: hypercorn/uvicorn config otimizada)
  - HTTP/2 (se edge suportar)

Decisao P2-C:
- Escolher exatamente uma:
  - revisao de SLO (operacional)
  - cache/materializacao (arquitetura leve)
  - servico dedicado read-path
  - mudanca de modelo de execucao

Observacao canonica:
- Se `P2-B2.3b` falhar:
  - concluir que gargalo e estrutural do ambiente/process model atual
  - `safe_envelope_v2.0` permanece `C1`
  - `C2` so passa com intervencao arquitetural deliberada

## P2-C - Kickoff (com gate explicito)

Premissas (gate):
- `safe_envelope_v2.0` (operacional) = `C1`
- `safe_envelope_v2.0` (estrutural) = `pending` (P2-B1 runner externo)
- Qualquer melhoria em P2-C deve:
  - manter `timeouts = 0`
  - manter `bad_duration = 0`
  - manter `path_leaks_30d = 0`
  - manter `db_pool_wait_us = 0` (ou evidenciar por que subiu)
- Sem mudanca de logica/contrato dos endpoints (apenas read-path/materializacao/cache/infra do read).

Objetivo P2-C (mensuravel):
- Tornar `C2` viavel sob SLO atual em Linux nativo (rodada estrutural posterior), reduzindo latencia do read-path para:
  - `p99 C2 <= SLO` por endpoint (`overview/runs/report`)
  - com `db_us` e `queue_us` previsiveis e baixos

### Metricas-alvo e hard checks

Hard checks (nao pode piorar):
- `timeouts = 0` (direct e edge)
- `error_rate = 0` (ou `<= SLO`, se aplicavel)
- `bad_duration = 0`
- `path_leaks_30d = 0`
- `db_pool_wait_us p95 = 0` (ou justificativa + fix)

Alvos de performance:
- `/metrics/overview` em `C2`: `p99` dentro do SLO
- `/metrics/runs` em `C2`: `p99` dentro do SLO
- `/observability/report` (default lean) em `C2`: `p99` dentro do SLO

Instrumentacao obrigatoria para P2-C:
- Pivot por endpoint no timing: `queue_us`, `handler_us`, `db_us`, `db_queries`, `db_pool_wait_us`, `server_total_us`
- Pivot por caminho (direct vs edge): `rt/uct/uht` (edge logs)
- Evidencia do read-path por request (fonte DB/materializado/cache em facts)

### Escolha de trilha (sem mudar logica de endpoint)

Trilha C1 - Materializacao/Cache (recomendado primeiro):
- Definir read models minimos por endpoint:
  - `overview_read_model` (agregado pronto)
  - `runs_read_model` (lista latest per process_id ja otimizada)
  - `report_read_model` (default lean mantendo `db_queries <= 4`)
- Estrategia de atualizacao:
  - job periodico (ex.: 1-5 min) ou trigger/append-only (se aplicavel)
- Contrato de consistencia:
  - `freshness_seconds` exposto em `/status` (somente leitura)
- Guardrails:
  - fallback para DB on-demand desligado por default
- Migracoes + indices:
  - indices alinhados com top queries do read model

Criterio de saida da Trilha C1:
- `db_queries` por endpoint em `C2` previsivel e baixo (ex.: 0-2)
- `db_us` reduzido e estavel
- `queue_us` sem explosao por saturacao do read-path

Trilha C2 - Servico read-path (se C1 nao bastar):
- Novo servico `metrics-read` (mesmo repo/compose)
- API principal consome read-service (HTTP interno) ou mesmo DB/read model
- Rate limits e timeouts internos definidos
- Observabilidade por hop (timing no chamador e no servico)

Criterio de saida da Trilha C2:
- Latencia C2 dentro do SLO com isolamento de recursos
- Evidencia de contensao de processo/loop (nao DB)

### DoD P2-C

Para fechar PR de P2-C:
- Sem mudanca de contrato publico
- Testes verdes (suite completa)
- Documentacao atualizada em `docs/observability.md`
- Tabela de evidencia (`C=1/2/5`) + pivots (`queue_us/db_us/db_queries`)
- Execucao local (operacional) demonstra melhoria vs baseline
- Sem regressao em `/observability/report` (`db_queries <= 4` e `p95_db_us` baixo em steady-state)

Gate estrutural (fora do DoD do PR, obrigatorio para promover envelope):
- Rodar P2-B1 com runner externo e atualizar decisao estrutural

### P2-C2.2 (async snapshot-first)

Objetivo:
- remover agregacao live do request path de `/api/v1/metrics/overview` e `/api/v1/metrics/runs`.

Contrato C2.2:
- `force_live=true` nao calcula no request.
- `force_live=true` retorna HTTP `202 Accepted` e enfileira refresh idempotente.
- request normal (sem `force_live`) le somente snapshot do read model.
- sem snapshot, retorna HTTP `503` com erro deterministico `SnapshotMissing`.

Fila de refresh:
- tabela `metrics_read_refresh_jobs` com `job_key` unico por (`endpoint`, `query_key`).
- enqueue com `INSERT ... ON CONFLICT DO NOTHING` e TTL (`expires_at`).
- `job_key = sha256(endpoint + query_key_canonica)`.
- runner minimo: `python scripts/run_read_refresh_jobs.py --limit 100`.

Payload esperado para `force_live=true`:
```json
{
  "snapshot_status": "queued",
  "correlation_id": "<job_key_hash>",
  "scope": "overview",
  "retry_after_seconds": 5
}
```

Notas:
- `correlation_id` = hash seguro do job (`job_key_hash`), sem expor `query_key`.
- `scope` canonico: `overview` ou `runs`.

Headers canonicos de envelope/degradacao:
- `X-Envelope: C1`
- `X-Reason: throughput_path` (quando degradado)
- `Retry-After: <segundos>` para respostas `202 Accepted` e `503 SnapshotMissing`

Cache de edge (P2-D2, SLO-aware delivery):
- aplicado apenas em `GET /api/v1/metrics/overview` e `GET /api/v1/metrics/runs`
- bypass canonico: `force_live=true` (`proxy_cache_bypass`/`proxy_no_cache`)
- TTLs no edge:
  - `200`: `10s`
  - `503 SnapshotMissing`: `1s` (amortecer thundering herd)
  - `202` e `429`: `0s` (nao cachear)
- stale policy: `stale-while-revalidate` com `proxy_cache_background_update on`
- header diagnostico no edge: `X-Edge-Cache: HIT|MISS|BYPASS|EXPIRED`

Revalidacao HTTP (P2-D3):
- backend (`overview`/`runs`) expÃµe `ETag` deterministico por versao de snapshot.
- requests com `If-None-Match` retornam `304 Not Modified` quando o snapshot nao mudou.
- edge ativa `proxy_cache_revalidate on` para aproveitar revalidacao condicional no upstream.
- `ETag` nao e emitido em `202 Accepted` nem em `503 SnapshotMissing`.

Erro deterministico sem snapshot:
```json
{
  "detail": {
    "snapshot_status": "missing",
    "scope": "overview",
    "next_action": "force_live",
    "estimated_ready_seconds": 5
  }
}
```

Notas:
- `scope` canonico: `overview` ou `runs`.
- `Retry-After` usa a mesma fonte de `estimated_ready_seconds`.

### Happy path (snapshot-first) - 503 -> 202 -> runner -> 200

```bash
# 1) GET normal (snapshot ausente -> 503)
curl -sS "http://localhost:8000/api/v1/metrics/overview?days=7"
curl -sS "http://localhost:8000/api/v1/metrics/runs?start_date=2026-02-13&end_date=2026-02-20&limit=50&offset=0"

# 2) Enfileira refresh (202 queued + correlation_id)
curl -sS "http://localhost:8000/api/v1/metrics/overview?days=7&force_live=true"
curl -sS "http://localhost:8000/api/v1/metrics/runs?start_date=2026-02-13&end_date=2026-02-20&limit=50&offset=0&force_live=true"

# 3) Processa fila de refresh (runner)
python scripts/run_read_refresh_jobs.py --limit 100

# 4) GET normal (200 com snapshot)
curl -sS "http://localhost:8000/api/v1/metrics/overview?days=7"
curl -sS "http://localhost:8000/api/v1/metrics/runs?start_date=2026-02-13&end_date=2026-02-20&limit=50&offset=0"
```

Exemplo `503 SnapshotMissing` (overview/runs):
```json
{"detail":{"snapshot_status":"missing","scope":"overview","next_action":"force_live","estimated_ready_seconds":5}}
```

Exemplo `202 Accepted` (overview/runs):
```json
{"snapshot_status":"queued","correlation_id":"a1b2c3d4","scope":"overview","retry_after_seconds":5}
```

Exemplo `429 RateLimited` (cooldown anti-abuso de `force_live`):
```json
{"error_type":"RateLimited","scope":"overview_force_live","retry_after_seconds":5,"cooldown_seconds":10}
```

Headers:
- `X-Envelope: C1`
- `Retry-After: <mesmo valor de retry_after_seconds>`

Nota operacional:
- repita o `GET` (ou consulte `/api/v1/status`) ate `freshness_seconds ~ 0` ou ate a resposta virar `200`.

### Warm-up opcional no deploy (read-path)

Quando usar:
- apos deploy/restart para reduzir `503 SnapshotMissing` nas primeiras chamadas.

Host (usa edge + runner no container `cortai_api`):
```bash
bash scripts/warmup_read_path.sh
```

Dentro do container da API (sem depender de `curl`):
```bash
docker exec -i cortai_api sh -lc "cd /app && bash scripts/warmup_read_path.sh"
```

Saida esperada (resumo):
- `overview_get_http=200`
- `runs_get_http=200`
- `overview_snapshot_status` / `runs_snapshot_status`
- `*_freshness_seconds`
- `jobs_queued_count=0`

Status/read-path:
- `GET /api/v1/status` expoe:
  - `read_path.overview_snapshot_status`
  - `read_path.overview_last_refreshed_at`
  - `read_path.overview_freshness_seconds`
  - `read_path.runs_snapshot_status`
  - `read_path.runs_last_refreshed_at`
  - `read_path.runs_freshness_seconds`
  - `read_path.runs_key_count`
  - `read_path.jobs_queued_count`

Telemetria:
- `metrics_endpoint_timing` mantem `db_us`, `db_queries`, `db_pool_wait_us`, `queue_us`, `server_total_us`.
- adiciona `snapshot_status`.
- para `202`, adiciona `job_enqueued` e `job_key_hash`.
- `overview_source` e `runs_source` continuam para auditoria do read-path.

Invariantes preservados:
- `bad_duration=0`
- `path_leaks_30d=0`
- `db_pool_wait_us=0` no steady-state observado

### Refresh jobs hardening (1 job/key + atomic claim)

Garantias operacionais:
- no maximo `1` job ativo por `job_key` (`queued` ou `running`);
- burst de `force_live` para a mesma key nao duplica job ativo (dedupe por `job_key`);
- runner faz claim atomico (`queued -> running`) antes de processar, evitando processamento duplicado quando dois runners executam em paralelo.

Escopo:
- hardening de confiabilidade do pipeline `metrics_read_refresh_jobs`;
- sem mudanca de contrato publico dos endpoints.

Evidencia:
- testes de concorrencia cobrem dedupe de enqueue e claim atomico entre dois runners.

### P2-C2.3 (split leve do read-path)

Objetivo:
- isolar throughput de leitura em processo dedicado (`read_api`) sem alterar logica de endpoint.

Wiring:
- novo app: `app.read_main:app` com routers read-only:
  - `/api/v1/metrics/*`
  - `/api/v1/observability/report`
  - `/api/v1/status`
  - `/health`
- novo servico compose: `read_api` (porta host `8002`).
- edge roteia:
  - `/api/v1/metrics/*` -> `cortai_read_api`
  - `/api/v1/observability/report` -> `cortai_read_api`
  - `/api/v1/status` e `/health` -> `cortai_read_api`
  - restante -> `cortai_api`

Status operacional:
- `/api/v1/status` inclui bloco `read_api`:
  - `enabled`
  - `up`
  - `base_url`

### Nota de anomalia (db_us)

Em janelas longas, pode aparecer `db_us` alto em `metrics_endpoint_timing` sem reproduzir em SQL:
- amostras pontuais mostraram `db_us` alto em `/metrics/runs` e `/observability/report`;
- `EXPLAIN (ANALYZE, BUFFERS)` das queries equivalentes permaneceu sub-ms;
- pivots curtos voltaram para `p95_db_us` em poucos ms, com `db_pool_wait_us=0`.

Regra operacional:
- nao tratar `db_us` alto isolado como `SQL slow` sem repetibilidade em rodada curta + `EXPLAIN`.
- priorizar correlacao com `rt/uct/uht` no edge para diagnostico de TTFB/infra-path.

### P2-D Branch B (fail-fast/backpressure)

Objetivo:
- eliminar request pendurado ate timeout de cliente sob saturacao de fila/worker.

Flags de controle:
- `METRICS_READ_REFRESH_MAX_QUEUE_DEPTH` (default `20`)
- `METRICS_READ_REFRESH_MAX_RUNNING_JOBS` (default `4`)
- `METRICS_READ_REFRESH_MAX_QUEUE_WAIT_MS` (default `1500`)
- `METRICS_READ_REFRESH_MAX_EXEC_MS` (default `5000`)

Comportamento:
- `force_live=true` em `overview/runs`:
  - `429 Backpressure` quando fila/worker passam do limite.
  - `503 QueueTimeout` quando enfileiramento excede `max_queue_wait_ms`.
- worker de refresh:
  - marca `failed` com `queue_wait_timeout` quando job envelhece na fila.
  - marca `failed` com `exec_timeout` quando execucao excede `max_exec_ms`.

Telemetria:
- `metrics_endpoint_timing` inclui `queue_wait_ms` e `exec_ms` no caminho de `force_live`.

Seguranca:
- resposta de erro continua minima/deterministica.
- sem vazamento de paths internos.

### Envelope v2.0 (declaracao estrutural final)

Fonte de verdade:
- `P2-B1` com runner externo (GitHub Actions), fora do host do SUT.

Decisao:
- `safe_envelope_v2.0` (estrutural) = `C1`.
- `C2` falha no SLO atual e fica classificado como `infra-bound` no ambiente atual.

Leitura consolidada:
- nao ha evidencia de gargalo dominante em `DB`, `pool`, `SQL` ou `handler`;
- o limitante observado esta no infra-path/latencia externa (runner/rede/tunel/camada de entrega).

### Regra de validade de benchmark (stop-the-line)

Uma rodada externa nao pode ser usada para promover envelope quando qualquer endpoint apresentar:
- `timeouts > 0`; ou
- `req/s < 1`.

Nesses casos:
- tratar a rodada como invalida para promocao;
- nao continuar tuning de app/edge com base nela;
- corrigir primeiro o ambiente de execucao (runner/rede/tunel/infra-path).

### SLO C1 (operacional)

Escopo:
- usado para classificacao operacional de rodadas validas em `C1` (runner externo/workflow).

Nivel A (confiabilidade / stop-the-line):
- `timeouts == 0`
- `req/s >= 1`
- `pct_5xx < 1%`

Nivel B (latencia operacional C1):
- `p99_overview <= 1500ms`
- `p99_runs <= 1500ms`
- `p99_report <= 1500ms`

Aplicacao no workflow:
- `p2_b1_runner_external.yml` avalia `C1` por endpoint (direct e edge, quando habilitado);
- escreve tabela `endpoint | p99 | rps | timeouts | pct_5xx | PASS/FAIL` no Step Summary;
- falha o job (`exit != 0`) quando qualquer limite de Nivel A ou Nivel B e violado.

### C1 Health Score (PASS/WARN/FAIL)

Objetivo:
- transformar a leitura de `C1` em classificacao automatica, sem interpretacao manual de CSV.

Fonte de verdade:
- `scripts/evaluate_c1_health.sh` (engine) + `p2_b1_runner_external.yml` (orquestracao).

Entradas:
- CSV(s) do `run_p2_matrix.sh` (`direct` e opcionalmente `edge`);
- apenas linhas `C=1` sao consideradas para o score.

Regras por endpoint:
- `FAIL` se qualquer condicao ocorrer:
  - `timeouts > 0`
  - `req/s < 1`
  - `pct_5xx >= 1%`
  - `p99 > fail_limit` do endpoint
- `WARN` (se nao houver `FAIL`) quando:
  - `p99 > warn_limit` do endpoint
  - `pct_429 > 0`
  - `pct_503 > 0`
- `PASS` caso contrario.

Thresholds atuais (`WARN` / `FAIL`):
- `overview`: `1500ms / 2500ms`
- `runs`: `1500ms / 2500ms`
- `report`: `1500ms / 2500ms`

Score final:
- se qualquer endpoint = `FAIL` -> `C1_HEALTH=FAIL`
- senao, se qualquer endpoint = `WARN` -> `C1_HEALTH=WARN`
- senao -> `C1_HEALTH=PASS`

Comportamento no workflow:
- o Step Summary mostra `C1_HEALTH` + tabela por endpoint (`p99`, `rps`, `timeouts`, `%429/%503/%5xx`, `decision`, `reason`);
- o job falha apenas quando `C1_HEALTH=FAIL`;
- `c1_health.json` e preservado como artefato para auditoria.

Exemplo (trecho de `c1_health.json`):
```json
{
  "c1_health": "WARN",
  "rows": [
    {
      "path": "direct",
      "endpoint": "overview",
      "decision": "WARN",
      "reason": "pct_503>0"
    }
  ]
}
```

Runbook curto:
- `FAIL`: parar benchmark formal / promocao e corrigir ambiente (`rede`, `runner`, `tunel`, `infra-path`).
- `WARN`: pode seguir, mas registrar `reason` no resultado e tratar como degradacao controlada.
- `PASS`: rodada valida para leitura operacional de `C1`.

### Runtime C1 Health Score (restricted)

Objetivo:
- expor uma leitura operacional de `C1` em `/api/v1/status` sem depender do workflow, com gate restrito.

Gate de exposicao (MVP):
- `EXPOSE_C1_HEALTH_STATUS=1` (env; default `0`)
- header `X-Internal-Status: 1`
- sem gate autorizado, `/status` continua igual (sem campo `c1_health`).

Cache (v1.1):
- cache em memoria por processo com TTL curto (`C1_HEALTH_CACHE_TTL_SECONDS`, default `10s`);
- chave fixa (janela fixa de `15m`);
- best effort (nao compartilha estado entre workers/processos).

Fonte / janela:
- `metrics_endpoint_timing` (runtime local)
- janela fixa de `15` minutos (`inputs.window_minutes=15`)
- `path` reportado como `direct` no MVP (sem inferencia de edge no request path)

Regras:
- mesmas regras/thresholds do `C1 Health Score` (workflow), com `timeouts=0` no runtime por limitacao da fonte (`metrics_endpoint_timing` nao observa timeout do cliente).
- `reasons` consolidados no topo (`endpoint:reason`) para leitura rapida de operador.
- `meta` informa se a resposta veio de cache e o custo do ultimo calculo (`compute_ms`).

Exemplo (trecho):
```json
{
  "c1_health": {
    "enabled": true,
    "score": "WARN",
    "inputs": {
      "window_minutes": 15,
      "source": "metrics_endpoint_timing"
    },
    "rows": [
      {
        "endpoint": "overview",
        "path": "direct",
        "decision": "WARN",
        "reasons": ["pct_503>0"]
      }
    ],
    "reasons": ["overview:pct_503>0"],
    "meta": {
      "cached": true,
      "cache_age_seconds": 3,
      "compute_ms": 8,
      "stale": false
    }
  }
}
```

### Operational Insights Panel (MVP)

Endpoint:
- `GET /api/v1/observability/overview`

Gate (restrito):
- requer `EXPOSE_C1_HEALTH_STATUS=1` no processo;
- requer header `X-Internal-Status: 1`;
- sem gate autorizado: `404`.

Entrega (MVP):
- `overall` (`score`, `decision`, `reasons`);
- `c1_health` (mesma logica do runtime C1 Health Score);
- `read_path` (freshness/status + `jobs_queued_count`);
- `guardrails` (counts `202/429/503` + ultimos `5` eventos).

Nao e:
- historico de health;
- exporter/Prometheus;
- substituto do `/api/v1/observability/report`;
- UI.

Exemplos:
```bash
# Sem gate (esperado: 404)
curl -i http://localhost:8000/api/v1/observability/overview

# Com gate (esperado: 200)
curl -sS -H "X-Internal-Status: 1" http://localhost:8000/api/v1/observability/overview
```

Exemplo (trecho):
```json
{
  "panel_version": "v1",
  "overall": { "score": "WARN", "decision": "degraded", "reasons": ["overview:pct_503>0"] },
  "guardrails": {
    "window_minutes": 15,
    "events": { "accepted_202": 1, "rate_limited_429": 1, "snapshot_missing_503": 0 },
    "last_events": [{ "endpoint": "/api/v1/metrics/overview", "status_code": 429 }]
  }
}
```

### Collector no Operational Insights (v0.1)

Objetivo:
- expor um resumo operacional do coletor na mesma janela curta do painel (`15m`);
- facilitar leitura rapida de sucesso/falha do coletor sem abrir dashboard novo;
- nao altera `trust` nem `recommendation` nesta versao.

Fonte:
- `observations`
- filtro: `facts.event_type = "collector_run"`

Shape:
```json
{
  "collector": {
    "window_minutes": 15,
    "events": {
      "success": 3,
      "failed": 1
    },
    "by_error_type": {
      "http_4xx": 1
    },
    "last_events": [
      {
        "ts": "2026-02-28T18:00:00Z",
        "status": "failed",
        "error_type": "http_4xx",
        "http_status": 404,
        "retryable": false,
        "job_id": "job-404"
      }
    ]
  }
}
```

Regras:
- `events` agrega apenas `success` e `failed`;
- `by_error_type` agrupa falhas por `error_type`;
- `last_events` e limitado aos `5` eventos mais recentes;
- `source_ref`, `minio_path` e qualquer campo sensivel nao entram no payload do overview;
- em caso de falha na agregacao, o painel retorna `"collector": null` (best-effort).

Notas de performance:
- janela fixa de `15m`;
- `last_events` limitado a `5`;
- objetivo: endpoint leve e previsivel (nao virar mini-report).

### Trust Banner (Product Signal)

Objetivo:
- expor um sinal de primeira linha ("posso confiar agora?") para UI/automacao, derivado do payload ja calculado do Insights Panel.

Regras (MVP):
- `red` / `action_required`: `c1_health=FAIL` ou `read_path.overview_snapshot_status=missing` ou `guardrails.snapshot_missing_503>0`;
- `yellow` / `degraded`: `c1_health=WARN` ou `read_path.overview_snapshot_status=stale` ou `guardrails.rate_limited_429>=3`;
- `green` / `healthy`: demais casos.

Precedencia:
- `red > yellow > green` (ex.: `WARN` + `snapshot missing` => `red`).

Exemplo (trecho):
```json
{
  "trust": {
    "state": "yellow",
    "decision": "degraded",
    "message": "Read-path stale but system responsive",
    "derived_from": ["read_path"]
  }
}
```

Notas:
- nao substitui monitoramento / historico;
- derivado de `c1_health` + `read_path` + `guardrails`;
- custo `O(1)` no request path (sem queries adicionais).

### Action Recommendation (MVP)

Objetivo:
- transformar sinal operacional (`trust`) em acao recomendada, de forma deterministica e sem query adicional.

Contrato (campo `recommendation` no painel):
```json
{
  "recommendation": {
    "action": "run_warmup | monitor | investigate_read_path | reduce_force_live_burst | inspect_upstream_path | open_report | none",
    "priority": "low | medium | high",
    "message": "string curta e deterministica",
    "derived_from": ["trust" | "read_path" | "guardrails" | "c1_health"]
  }
}
```

Regras + precedencia (MVP):
1. `overview_snapshot_status=missing` -> `run_warmup` (`high`)
2. `jobs_queued_count>0` -> `monitor` (`medium`)
3. `guardrails.snapshot_missing_503>0` -> `run_warmup` (`high`)
4. `guardrails.rate_limited_429>0` -> `reduce_force_live_burst` (`medium`)
5. `trust=red` -> `inspect_upstream_path` (`high`)
6. `trust=yellow` -> `open_report` (`medium`)
7. caso saudavel -> `none` (`low`)

Exemplo (snapshot missing -> warm-up):
```json
{
  "recommendation": {
    "action": "run_warmup",
    "priority": "high",
    "message": "Snapshots ausentes - execute warm-up do read-path.",
    "derived_from": ["read_path"]
  }
}
```

Exemplo (healthy -> none):
```json
{
  "recommendation": {
    "action": "none",
    "priority": "low",
    "message": "Nenhuma acao necessaria.",
    "derived_from": ["trust"]
  }
}
```

Notas:
- derivado de `trust` + `read_path` + `guardrails` + `c1_health`;
- precedencia e deterministica (early-return) e coberta por testes;
- custo `O(1)` no request path (sem queries adicionais).

### Internal Observability UI (MVP)

Objetivo:
- visualizar o `Operational Insights Panel` em `3-5s` para uso interno (operador/founder/dev), sem adicionar logica nova no backend.

Acesso:
- rota: `GET /internal/observability`
- gate: `EXPOSE_C1_HEALTH_STATUS=1`
- header obrigatorio: `X-Internal-Status: 1`
- sem gate autorizado: `404` (reduz descoberta)

O que a pagina mostra:
- `TRUST` (banner grande com `trust.message`)
- `Recommendation` (`action`, `priority`, `message`)
- `C1 Health` (linhas por endpoint com `decision`, `p99`, `rps`)
- `Read Path` (`overview/runs snapshot_status`, `freshness`, `jobs_queued_count`)
- `Guardrails` (counts `202/429/503` + `last_events`)

Notas de seguranca:
- `Cache-Control: no-store`
- endpoint interno; nao substitui monitoramento externo
- usa o mesmo gate restrito do painel JSON (sem auth publica adicional no MVP)

Notas tecnicas:
- render server-side (template HTML simples)
- reusa o mesmo builder do painel JSON (`/api/v1/observability/overview`)
- sem query nova e sem fetch HTTP interno

Teste rapido:
```bash
# sem header -> 404
curl -i http://localhost:8000/internal/observability

# com gate+header -> 200 HTML
curl -i -H "X-Internal-Status: 1" http://localhost:8000/internal/observability

# suite focada
pytest -q tests/test_internal_observability_ui.py
```

### Webhook action_required (v1)

Objetivo:
- permitir integracao externa reativa quando o estado publico transiciona para:
  - `state == "action_required"`
- sem alterar o contrato publico de `GET /api/v1/status/public`.

Escopo (v1):
- disparo apenas em transicao para `action_required`;
- fire-and-forget (nao bloqueia request publico);
- timeout fixo de `2s`;
- sem retry automatico;
- sem fila ou worker dedicado;
- ativacao opcional por ENV.

Ativacao (ENV):
- `STATUS_WEBHOOK_URL=<https://seu-endpoint>`
- `STATUS_WEBHOOK_SECRET=<opcional>`

Regras:
- sem `STATUS_WEBHOOK_URL`: webhook desativado (no-op);
- com `STATUS_WEBHOOK_SECRET`: envia assinatura HMAC SHA256 no header.

Payload enviado (POST JSON):
```json
{
  "state": "action_required",
  "action": "inspect",
  "as_of": "2025-01-01T12:00:00Z",
  "version": "v1"
}
```

Assinatura opcional:
- header: `X-Status-Signature: sha256=<hex_digest>`
- calculo: `HMAC_SHA256(secret, raw_body)`

Responsabilidades do consumidor:
- validar assinatura;
- validar idempotencia;
- aplicar rate limiting proprio.

Regra de disparo (anti-spam):
- somente em transicao real:
  - `previous_state != "action_required"`
  - `current_state == "action_required"`

Nao-objetivos (v1):
- retry automatico;
- backoff exponencial;
- persistencia de eventos;
- garantia de entrega;
- multi-webhook;
- webhook para outros estados.

Garantias:
- nao altera latencia de `/api/v1/status/public`;
- nao altera contrato publico;
- nao introduz query nova;
- nao introduz infra nova.

Observabilidade:
- falhas de envio nao impactam o endpoint publico;
- envio registra sucesso/falha e latencia no log da aplicacao.

### D+3 Webhook GO/NO-GO

Objetivo:
- rodar um freeze operacional de 72h com 1 consumidor e medir estabilidade real do webhook;
- produzir evidencia auditavel sem depender de coleta manual em logs.

Script:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/d3_webhook_run.ps1 -DayLabel D0
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/d3_webhook_run.ps1 -DayLabel D1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/d3_webhook_run.ps1 -DayLabel D2
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/d3_webhook_run.ps1 -DayLabel D3
```

Artefatos:
- `OUT/D3/00_env_presence.txt` (somente no `D0`)
- `OUT/D3/01_status_public_100.csv` e `OUT/D3/02_overview.json` no baseline
- `OUT/D3/D1_status_public_100.csv`, `OUT/D3/D2_status_public_100.csv`, `OUT/D3/D3_status_public_100.csv`
- `OUT/D3/D1_overview.json`, `OUT/D3/D2_overview.json`, `OUT/D3/D3_overview.json`
- `OUT/D3/D0_summary.txt`, `OUT/D3/D1_summary.txt`, `OUT/D3/D2_summary.txt`, `OUT/D3/D3_summary.txt`

O que o summary consolida:
- `status_public_5xx_count`
- `status_public_5xx_rate`
- `status_public_p95_ms`
- `webhook_sent`
- `webhook_success`
- `webhook_error`
- `webhook_error_rate`
- `webhook_p95_latency_ms`
- `webhook_last_error_status`
- `webhook_last_error_ts`

Criterio binario:
- `GO` quando:
  - `status_public_5xx_rate <= 0.001`
  - `status_public_p95_ms <= 300`
  - `webhook_error_rate < 0.01`
  - nao houver indicio de loop (envios sem transicao real) ou falso positivo recorrente
- `NO-GO` quando qualquer um desses limites falhar em janela recorrente de D+3.


---

## Source: `docs/observability/event_append_v1_0.md`

# Event Append v1.0

## Objetivo

Definir `append_event(event)` como ponto unico oficial de append de eventos observaveis.

Fluxo obrigatorio:

```text
append_event(event)
  -> JSONL append
  -> index write
```

## Regras congeladas

- A verdade canonica continua sendo o JSONL append-only.
- A ordem obrigatoria e `JSONL primeiro`, `indice depois`.
- Se o JSONL falhar, a operacao falha de forma dura.
- Se o indice falhar, o pipeline continua vivo e a falha fica registrada no retorno.
- O write-through nao pode criar evento no indice sem que ele exista no log.

## Shape minimo de evento

Campos esperados:

- `event_type`
- `ts`

Campos opcionais:

- `event_id`
- `writer_id`
- `severity`
- `action_taken`
- `account_id`
- `window_id`
- `job_id`
- `publish_id`
- `op_key`
- `details`

## Resultado

`append_event(...) -> AppendResult`

Campos:

- `jsonl_written`
- `index_written`
- `index_error`
- `source_file`
- `source_line`

## Integracao

- Emissores centrais devem migrar para `append_event()`.
- Emissores legados podem continuar fora do ponto central temporariamente.
- O rebuild do D16 permanece o mecanismo de reconciliacao oficial.


---

## Source: `docs/observability/event_index_v1_0.md`

# Event Index v1.0

## Objetivo

Adicionar um indice leve para acelerar consultas de eventos sem alterar o contrato append-only dos arquivos JSONL em `OUT/`.

Fluxo:

```text
events.jsonl / audit.jsonl / data/*.jsonl
  -> event_index.sqlite3
  -> EventQueryService
```

## Fonte da verdade

- Os arquivos JSONL continuam sendo a fonte canonica.
- O indice e um read model derivado.
- Se o indice estiver indisponivel, a consulta volta automaticamente para o scanner JSONL.

## Armazenamento

- Caminho padrao: `OUT/index/event_index.sqlite3`
- Tabela principal: `events_index`

Campos indexados:

- `source_file`
- `source_line`
- `event_id`
- `ts`
- `event_type`
- `writer_id`
- `severity`
- `action_taken`
- `account_id`
- `window_id`
- `job_id`
- `publish_id`
- `op_key`
- `details_json`

## Invariantes

- O indice nunca sobrescreve o JSONL.
- A chave de idempotencia do indice e `(source_file, source_line)`.
- Rebuild repetido sobre a mesma base nao duplica linhas.
- Ordenacao de consulta permanece canonica: `ts DESC, event_id DESC`.
- Fallback para scanner e obrigatorio se o indice nao existir ou falhar.

## Writer

- O writer e tolerante a falha.
- Falha no indice nao pode bloquear o pipeline principal.
- O writer usa `INSERT OR IGNORE` para preservar idempotencia.

## Repo

- `search(filters, limit, cursor_last)` retorna o mesmo shape logico de `EventQueryResult`.
- Filtros seguem o mesmo contrato do scanner.
- `time_range` continua obrigatorio.

## Rebuild

- O rebuild percorre os JSONL configurados e popula o indice.
- Linhas invalidas continuam sendo ignoradas, como no scanner.
- O rebuild pode ser executado multiplas vezes sem duplicacao.


---

## Source: `docs/observability/event_query_forensics_v1_0.md`

# Event Query & Forensics v1.0

## Problema
O sistema emite eventos em multiplas trilhas JSONL, mas ainda nao possui uma camada de consulta estruturada para investigacao operacional e forense.

## Objetivos
Permitir consultas deterministicas e somente leitura por:
- `account_id`
- `window_id`
- `job_id`
- `publish_id`
- `op_key`
- `event_type`
- `timestamp_range`

## Fontes de eventos
A camada D13 consulta dados existentes, sem alterar storage:
- `OUT/events/*.jsonl`
- `OUT/data/*.jsonl`
- `OUT/audit/*.jsonl`

## Tipos de eventos relevantes
- `PIPE/*`
- `LOCK/*`
- `IDEMPOTENCY/*`
- `SC/*`
- `ATTR/*`
- `SL/*`
- `REG/*`

## Queries minimas
| Query | Descricao |
|---|---|
| `get_events_by_account` | Lista eventos por conta |
| `get_events_by_window` | Reconstrui execucao da janela |
| `get_events_by_op_key` | Rastreia operacao idempotente |
| `get_pipeline_trace` | Monta trilha canonica do pipeline |

## Exemplo de trace
`window_pipeline -> AGG -> SC -> ATTR -> SL -> SPA`

## Invariantes
1. Somente leitura.
2. Sem modificacao de eventos de origem.
3. Sem alteracao de pipeline de negocio.
4. Consultas deterministicas com filtros explicitos.

## Estrutura inicial de modulos
```text
backend/app/observability/event_query/
  __init__.py
  models.py
  query_service.py
  indexer.py
  errors.py
```

## Fora de escopo (D13.1)
- Wiring no runtime.
- Index persistente.
- API publica.
- Replay automatico.

## Proximos passos
- D13.2: scanner JSONL + filtros.
- D13.3: builder de pipeline trace.
- D13.4: testes e casos forenses.


---

## Source: `docs/observability/hot_storage_v1_0.md`

# Hot Storage v1.0

## Objetivo

Adicionar uma camada de hot storage consultavel para eventos, separada do log canonico append-only.

Arquitetura:

```text
append_event()
  -> JSONL (verdade canonica)
  -> SQLite index (aceleracao local)
  -> Hot Store (query operacional)
```

## Papeis

- `JSONL`: fonte de verdade.
- `event_index.sqlite3`: aceleracao local para consultas simples.
- `events_hot.sqlite3`: camada operacional para consultas mais pesadas.

## Invariantes

- O hot store nunca substitui o JSONL como verdade.
- Se houver divergencia, o rebuild parte sempre do JSONL.
- O fallback de consulta e obrigatorio:
  1. hot store
  2. indice SQLite
  3. scanner JSONL

## Armazenamento

- Caminho padrao: `OUT/hot_store/events_hot.sqlite3`
- Chave de idempotencia: `event_id`

## Writer

- Writer idempotente por `event_id`.
- Falha do hot store nao bloqueia o pipeline.
- Rebuild/replay a partir do log canonico continua disponivel.

## Out of scope

- dashboards
- auth/rbac
- analytics avancado
- distributed query
- materialized views complexas


---

## Source: `docs/observability/seek_cursor_encoding_v1_0.md`

# Seek Cursor Encoding v1.0

## Objetivo
Definir cursor opaco e deterministico para paginacao keyset da camada Event Query.

## Formato
Cursor e um JSON canonico serializado em UTF-8 e codificado em base64url sem padding.

## Shape v1.0
```json
{
  "v": "1",
  "filters_hash": "sha256:...",
  "last": {
    "ts": "2026-03-05T10:00:00Z",
    "event_id": "evt_0001"
  },
  "issued_at": "2026-03-05T10:00:01Z",
  "sig": "optional-profile-b"
}
```

## Campos obrigatorios
- `v`
- `filters_hash`
- `last.ts`
- `last.event_id`
- `issued_at`

## Regras
1. `v` deve ser `"1"`.
2. `last.ts` e `issued_at` devem ser ISO8601 UTC validos.
3. `filters_hash` vincula cursor aos filtros da query.
4. `sig` e opcional no Profile A e obrigatoria no Profile B.

## Erros congelados (D14.1)
- `CURSOR_INVALID_ENCODING`
- `CURSOR_INVALID_JSON`
- `CURSOR_UNSUPPORTED_VERSION`
- `CURSOR_MISSING_FIELDS`
- `CURSOR_FILTERS_MISMATCH`
- `CURSOR_SIGNATURE_INVALID`

## Fora de escopo (D14.1)
- Cursor signing enforcement (Profile B) em runtime.
- Seek clause no SQL/API.
- Limit+1 e next_cursor em endpoints.


---

## Source: `docs/ops/slo_alerting_v1_0.md`

# SLO + Alerting v1.0

## Objetivo

Transformar as metricas do D18 em limites operacionais claros:

- SLOs
- SLIs
- error budget
- thresholds de alerta
- acoes operacionais minimas

## SLOs congelados

### Event Query

- `event_query_p95_ms`
- `event_query_error_rate`
- `event_query_fallback_rate`

### Pipeline

- `window_pipeline_success_rate`
- `window_post_pipeline_success_rate`

### Concorrencia

- `lease_denied_rate`
- `double_apply_count`
- `snapshot_partial_count`

### Learning / Patch

- `strategy_patch_conflict_rate`

## Thresholds v1.0

### CRITICAL imediato

- `double_apply_count > 0`
- `snapshot_partial_count > 0`
- `event_query_error_rate >= 0.05`

### WARN

- `event_query_p95_ms >= 250`
- `event_query_fallback_rate >= 0.10`
- `strategy_patch_conflict_rate >= 0.02`
- `lease_denied_rate >= 0.05`

### Error budget

`event_query_error_rate`

- alvo: `99.5%` de disponibilidade
- budget: `0.5%`
- budget consumido `>= 100%` gera alerta persistente

## Severidades e acoes

- `INFO` -> `OBSERVE`
- `WARN` -> `DEGRADE`
- `CRITICAL` -> `BLOCK`

## Artefatos

O D19 persiste:

- `OUT/ops/alerts.jsonl`
- `OUT/ops/slo_status.json`

## Regra arquitetural

O D19 nao altera contrato do pipeline.

Ele apenas:

1. avalia metricas
2. classifica severidade
3. gera alertas acionaveis
4. persiste estado operacional


---

## Source: `docs/p2_results.md`

# P2 Results

## P2-B1 sintetico (Windows/Docker Desktop)

Objetivo:
- Executar uma validacao sintetica do fluxo de observabilidade e SLO quando nao ha runner externo disponivel.

Nao objetivo:
- Este fluxo nao substitui P2-B1 estrutural (runner separado do SUT).

Execucao:

```bash
python scripts/run_p2b1_synthetic.py --metric-date 2026-02-09 --base-url http://localhost:8000 --timing-minutes 60
```

Artefatos esperados (`.tmp_p2/`):
- `p2_a_summary_direct.csv` (3 endpoints x 3 Cs = 9 linhas de dados)
- `p2_a_summary_edge.csv` (3 endpoints x 3 Cs = 9 linhas de dados)
- `report_after_synth.json`
- `status_after_synth.json`

ValidaÃ§Ãµes obrigatorias:
- Agregacao diaria executada duas vezes sem duplicar `metrics_slo_alert`.
- Monotonicidade de latencia no CSV sintetico (`C1 < C2 < C5`) por endpoint.
- `report_after_synth.json` com:
  - `timing.events > 0`
  - `slo_daily.has_requests == true`
  - `bad_duration == 0`
  - `publish_receipts.path_leaks_30d == 0`

Observacao:
- Resultado sintetico e util para validar pipeline e contratos.
- Decisao estrutural de capacidade segue dependente de medicao com runner externo.

## P2-C2.1 pos-merge (runs read-path, C=2)

Objetivo:
- Validar impacto do read-path materializado de `/api/v1/metrics/runs` em C=2 apos merge.

Escopo da rodada:
- Endpoint: `/api/v1/metrics/runs?start_date=2026-02-11&end_date=2026-02-18&limit=200&offset=0`
- Cenario: C=2, 3 repeticoes, 60s por repeticao
- Caminhos: direct (`:8000`) e edge (`:8001`)
- Artefatos:
  - `.tmp_p2/p2_c21_runs_c2_postmerge.csv`
  - `.tmp_p2/p2_c21_runs_c2_postmerge_summary.json`

Resultado consolidado:

| path   | avg p90 | avg p99 | avg req/s | timeouts |
|--------|---------|---------|-----------|----------|
| direct | 853.07ms | 894.33ms | 2.42 | 0 |
| edge   | 855.64ms | 889.17ms | 2.40 | 0 |

Pivot server-side (`metrics_endpoint_timing`, janela curta):
- `runs_source=read_model`: `n=875`, `avg_db_queries=1.00`, `p95_db_us=1181.50`
- `runs_source=live`: `n=4`, `avg_db_queries=3.25`, `p95_db_us=9410.50`
- `db_pool_wait_us=0` (sem contencao de pool)

Interpretacao:
- O read-path de runs ficou efetivo e previsivel no servidor (predominio `read_model`).
- Houve reducao objetiva de cauda em relacao ao baseline anterior (~1108.82ms p99 direct para ~894.33ms, cerca de -19%).
- Mesmo com melhora de runs, C=2 permanece fora do SLO de latencia no ambiente atual.

Decisao:
- `safe_envelope_v2.0` permanece `C1`.
- P2-C2.1 foi eficaz para isolamento de leitura e custo DB de runs, mas nao alterou o limite estrutural de envelope.

## P2-C2.2 (async snapshot-first) - validacao funcional

Objetivo:
- remover agregacao live do request path de `overview` e `runs`, migrando `force_live` para enqueue assÃ­ncrono.

Implementado:
- `force_live=true` retorna `202 Accepted` (sem calcular no request).
- fila idempotente `metrics_read_refresh_jobs` (TTL + `job_key` unico).
- runner de refresh: `python scripts/run_read_refresh_jobs.py --limit 100`.
- request normal le somente snapshot; sem snapshot retorna `503 SnapshotMissing`.
- `status` expoe snapshot status/freshness e jobs enfileirados.

Validacao:
- `python -m pytest -q` -> `62 passed`.
- `tests/test_metrics_api.py` e `tests/test_status_api.py` cobrem:
  - `202 Accepted` com payload deterministico;
  - dedupe de enqueue por `job_key`;
  - `503 SnapshotMissing` sem snapshot;
  - leitura `200` apos processamento do runner;
  - telemetria com `snapshot_status`, `job_enqueued`, `job_key_hash`.
- Happy path operacional (`503 -> 202 -> runner -> 200`): ver `docs/observability.md`, secao `Happy path (snapshot-first) - 503 -> 202 -> runner -> 200`.

Decisao:
- C2.2 conclui a mudanca arquitetural de request path (snapshot-first).
- `safe_envelope_v2.0` permanece `C1` ate rodada estrutural P2-B1 com runner externo.

## P2-C2.3 (read-path split) - kickoff

Objetivo:
- isolar read-path em processo dedicado para reduzir contencao de throughput sob C=2.

Escopo:
- novo servico `read_api` com `metrics + observability/report + status`.
- edge roteia endpoints de leitura para `read_api`.
- API principal permanece como origem das rotas nao-read.

Gate de validacao:
- benchmark C=2 (3x60s) comparando p99 com baseline C2.2.
- criterio de impacto: queda >=20% em p99 (`overview` e `runs`) com `timeouts=0`.

## P2-C2.4 (diagnostico curto de anomalia db_us)

Objetivo:
- verificar se `db_us` alto observado em janela longa era gargalo SQL real.

Resultado:
- logs do edge com formato `rt/uct/uht` ativos.
- p95: `uct=0.0s`, `uht~1.118s`, `rt~1.104s` (TTFB domina; connect nao domina).
- top amostras com `db_us` alto em janela longa apareceram para:
  - `/api/v1/metrics/runs` (`query_fingerprint=limit=200&offset=0&range=8d`)
  - `/api/v1/observability/report` (modo lean default)
- `EXPLAIN (ANALYZE, BUFFERS)` das queries representativas permaneceu sub-ms.
- rodada curta C=2 (20s) confirmou `p99` ~1s+ com:
  - `timeouts=0`
  - `p95_db_us` novamente em poucos ms
  - `db_pool_wait_us=0`

Decisao:
- anomalia `db_us` classificada como ruido/contensao de runtime, nao `SQL slow` repetivel.
- `safe_envelope_v2.0` permanece `C1`.
- gate estrutural continua em `P2-B1` com runner externo.

## P2-B1 estrutural (runner externo GitHub Actions)

Objetivo:
- fechar o gate estrutural de capacidade com runner externo (fora do host do SUT).

Fonte de execucao:
- GitHub Actions (`ubuntu-latest`) com workflow manual `p2_b1_runner_external`.
- Artefatos:
  - `.tmp_p2/p2_a_summary_direct.csv`
  - `.tmp_p2/p2_a_summary_edge.csv`

Escopo da comparacao:
- Cenario: `C=2`, `3` repeticoes, `60s` por repeticao.
- Endpoints: `overview`, `runs`, `report`.
- Caminhos:
  - `direct` (API direta)
  - `edge` (proxy/read path)

Resultado consolidado (media das 3 repeticoes, C=2):

| path   | endpoint | avg p90 | avg p99 | avg req/s | timeouts |
|--------|----------|---------|---------|-----------|----------|
| direct | overview | 1123.33ms | 2503.33ms | 1.92 | 0 |
| direct | runs     | 1106.67ms | 1866.67ms | 1.98 | 0 |
| direct | report   | 1170.00ms | 1830.00ms | 1.89 | 0 |
| edge   | overview | 1273.33ms | 1660.00ms | 1.75 | 0 |
| edge   | runs     | 1146.67ms | 1496.67ms | 1.90 | 0 |
| edge   | report   | 1226.67ms | 1706.67ms | 1.83 | 0 |

Decisao:
- `P2-B1`: `PASS` (metodologia estrutural concluida).
- `safe_envelope_v2.0` (estrutural): `C1`.
- `C2`: `FAIL` por latencia de cauda (p99 acima do SLO), mesmo com `timeouts=0`.

Endpoint limitante:
- principal: `/api/v1/metrics/overview`
- co-limitante: `/api/v1/metrics/runs`

Observacao:
- o caminho `edge` reduziu parte da cauda vs `direct` em alguns cenarios, mas nao o suficiente para promover `C2`.

## P2-D Branch B (fail-fast/backpressure)

Ramo seguido:
- **B (local/externo com saturacao)**, pois a causa predominante permaneceu em contensao de runtime/path com penduramento ate timeout.

O que mudou:
- fail-fast em `force_live` (`429 Backpressure` / `503 QueueTimeout`).
- timeout interno por etapa:
  - `max_queue_wait_ms` no enfileiramento.
  - `max_exec_ms` no worker de refresh.
- status de job padronizado em timeout:
  - `queue_wait_timeout`
  - `exec_timeout`

Antes (exemplo de rodada estrutural sob saturacao, C=2):
- `direct` com timeouts > 0 e cauda em segundos.

Depois (comportamento esperado/validado em testes):
- saturacao retorna `429/503` rapidamente (sem hang silencioso).
- contratos deterministas mantidos (`error_type`, `scope`, `snapshot_status`, `retry_after_seconds`).
- telemetria com amostra de `queue_wait_ms` vs `exec_ms`.

Flags/configs adicionadas:
- `METRICS_READ_REFRESH_MAX_QUEUE_DEPTH`
- `METRICS_READ_REFRESH_MAX_RUNNING_JOBS`
- `METRICS_READ_REFRESH_MAX_QUEUE_WAIT_MS`
- `METRICS_READ_REFRESH_MAX_EXEC_MS`

## Declaracao final de envelope v2.0 (estrutural)

Fonte de verdade:
- `P2-B1` com runner externo (GitHub Actions) e artefatos de benchmark.

Decisao oficial:
- `safe_envelope_v2.0` (estrutural) = `C1`.
- `C2` = `FAIL` no SLO atual e classificado como `infra-bound` no ambiente avaliado.

Interpretacao consolidada:
- gargalo nao e `DB`, `pool`, `SQL`, `handler` ou `read-model`;
- a degradacao dominante aparece no infra-path/latencia externa (runner -> edge/direct -> SUT).

Politica operacional:
- nao promover `C2` neste ambiente.
- `C2` so pode ser reavaliado com infraestrutura dedicada (ex.: VPS/host sem tunel) ou revisao explicita de SLO.
- SLO operacional de `C1`: ver `docs/observability.md` na secao `SLO C1 (operacional)`.
- C1 Health Score (`PASS|WARN|FAIL`) e regras de leitura do summary: ver `docs/observability.md` na secao `C1 Health Score (PASS/WARN/FAIL)`.
- Warm-up pos-deploy do read-path: ver `docs/observability.md` na secao `Warm-up opcional no deploy (read-path)`.

## Fechamento pos-auditoria (RECHECK TOTAL)

Status:
- **RECHECK TOTAL: GO**

Evidencias de correcao:
- `e16c04e` - `fix(observability): corrige telemetria e agregacao de metricas (post-auditoria)`
- `f167e4a` - `fix(ops): ajusta nginx/edge para consistencia operacional (post-auditoria)`

WARNs remanescentes (governados):
- bandit com achados Low/Medium (sem High)
- excecao ecdsa (`GHSA-wj6h-64fc-37mp`) formalizada em `SECURITY_ACCEPTED_RISKS.md`

## Regra de validade do benchmark externo (stop-the-line)

Uma rodada externa e invalida para promocao de envelope quando qualquer endpoint apresentar:
- `timeouts > 0`; ou
- `req/s < 1`.

Quando isso ocorrer:
- nao promover envelope;
- nao continuar tuning de app/edge com base nessa rodada;
- corrigir primeiro o ambiente/caminho de execucao (infra-path, tunel, rede, runner).

## Fase: C1 Health Score + Reliability Hardening - Status Final

Objetivo da fase:
- consolidar `C1` como estado operacional continuo (classificacao automatica + hardening de confiabilidade), sem perseguir throughput adicional.

Escopo entregue:
- stop-the-line no runner externo (`diag gate`);
- C1 Health Score engine + integracao no workflow;
- docs + runbook do C1 Health Score;
- hardening de refresh jobs (dedupe + atomic claim);
- warm-up opcional no deploy (read-path).

Garantias operacionais vigentes:
- benchmark invalido nao avanca para `formal`;
- classificacao automatica `PASS|WARN|FAIL` via `C1_HEALTH`;
- no maximo `1` refresh job ativo por `job_key` sob burst;
- runner seguro sob concorrencia (claim atomico, sem double-processing);
- warm-up reduz `SnapshotMissing` pos-deploy.

Pendencias conscientes:
- evidencia final do step `Evaluate C1 SLO` em host estavel (sem tunel) permanece pendente por limitacao de ambiente;
- `C2` permanece fora do escopo desta fase (continua `infra-bound` no ambiente atual).

Status final:
- `safe_envelope_v2.0` (estrutural): `C1`
- Fase `C1 Premium`: `CLOSED`

Proxima evolucao:
- deliberada e separada desta fase (infra dedicada para reavaliar `C2`, ou metricas runtime embutidas).

## Validacao humana completa do sinal operacional (v2.1.0)

Escopo:
- 5 participantes x 4 cenarios (`missing`, `stale`, `429`, `green`).
- UI interna em modo demo deterministico (`/internal/observability?demo_scenario=...`).
- Objetivo: validar compreensao de estado + acao sob pressao cognitiva leve.

KPIs finais:
- `taxa_acerto_30s = 0.95` (meta >= `0.85`) -> `PASS`
- `confianca_media = 4.10` (meta >= `4.0`) -> `PASS`
- `clareza_media = 8.15` (meta >= `8.0`) -> `PASS`
- confusao sistemica em `429`/`stale`: `nao observada`

Decisao:
- `APROVADO` para validacao humana do core cognitivo.
- Tag de checkpoint: `v2.1.0-human-validated-core`.

Observacao:
- ajuste final de microcopy para `429` (curto e humano) aplicado antes da rodada final:
  - "Chamadas demais em pouco tempo. Bloqueio temporario ativo. Aguarde alguns segundos e tente de novo."

## Rollout Public Status Endpoint - Day 0 (v2.1.x)

Contexto:
- Exposicao publica controlada do endpoint read-only:
  - `GET /api/v1/status/public`
- Contrato minimo congelado por 1 ciclo:
  - `{ "state": "...", "action": "...", "as_of": "...", "version": "v1" }`
- Sem novos campos, sem parametros e sem exposicao de metricas internas.

Evidencia tecnica - Day 0:
1. Validacao direta (read_api, sem edge)
   - endpoint: `http://127.0.0.1:8000/api/v1/status/public`
   - resultado:
     - `HTTP 200`
     - `Cache-Control: public, max-age=30`
     - payload minimo conforme contrato

2. Validacao via edge (nginx)
   - endpoint: `http://localhost:8001/api/v1/status/public`
   - resultado:
     - `HTTP 200`
     - `Cache-Control` preservado
     - payload minimo correto

3. Rate limit validado (edge)
   - configuracao:
     - `limit_req_zone`: `30 req/min` por IP
     - `burst=10`
     - `limit_req_status 429`
   - burst test (`40` requests):
     - `200: 15`
     - `429: 25`
     - `404: 0`
     - `5xx: 0`
   - confirmacao:
     - rate limit ativo
     - upstream funcional
     - path isolado corretamente

Commit de infraestrutura:
- `21b5be9`
- `feat(ops): aplica rate limit e logging dedicado para /api/v1/status/public no nginx`

Decisao operacional:
- status: `GO` para rollout publico controlado
- condicoes:
  - monitorar `2xx/4xx/5xx` e latencia `p95` por 7 dias
  - manter contrato congelado no periodo
  - sem expansao de escopo

Observacao:
- esta etapa marca a primeira exposicao publica de sinal operacional derivado do sistema interno validado (`v2.1.0-human-validated-core`), mantendo governanca de seguranca, sanitizacao e limitacao de trafego.

## Recheck Final - GO

Referencia de fix do bloqueante:
- `832100d` (`docs/perf` na trilha do fix de guardrail `429 RateLimited` deterministico; runtime validado apos rebuild local)

Resumo (10 linhas):
1. Recheck final executado localmente com evidencias em `OUT/RECHECK_REPORT.md`.
2. Suite completa no container: `75 passed`.
3. `force_live` retorna `202` padronizado em `overview` e `runs`.
4. Segunda chamada `force_live` no cooldown retorna `429 RateLimited` deterministico (`overview` e `runs`).
5. Runner de refresh processa fila e `GET` sem `force_live` retorna `200` para `overview` e `runs`.
6. `ETag` + `304 Not Modified` validados em `overview` e `runs`.
7. `nginx -t` OK e logs do edge com `rt/uct/uht` confirmados.
8. Hardening de refresh jobs validado por testes de concorrencia (`dedupe` + `atomic claim`).
9. Workflow/tooling/scripts/docs sanity: PASS (`diag gate`, `best-effort artifacts`, `C1 Health Score`, stop-the-line, happy path).
10. GO/NO-GO final: `GO`.

Decisao final:
- `GO`
- `safe_envelope_v2.0` (estrutural) = `C1`
- fase `C1 Premium + Health Score + Hardening`: encerrada

Nota (nao bloqueante):
- working tree local permaneceu suja por artefatos/experimentos (`.tmp_*`, `OUT/`, `docker-compose.netem.yml`, `infra/nginx/default.conf`);
- classificado como higiene local, sem evidencia de bug/regressao do sistema, e nao deve ser mergeado sem ticket explicito.

## Recheck rapido pos-fix - GO (Runtime Visibility validada)

Data:
- `2026-02-24`

Contexto:
- pos-fix de governanca de versao (`DEFAULT_APP_VERSION`), rebootstrap sequencial e validacao controlada de `c1_health` no `/status` (gate restrito).

Resultado:
- `GO`

Checks executados (stop-the-line):
1. Edge / nginx config
   - `nginx -t` (`cortai_edge`): `PASS`
2. Read-path warm-up
   - `scripts/warmup_read_path.sh` (`cortai_api`): `PASS`
   - `overview_get_http=200`
   - `runs_get_http=200`
   - `jobs_queued_count=0`
3. Guardrail anti-burst (`force_live`)
   - `PASS` (key nova no edge)
   - `overview?days=6`: `202 -> 429 RateLimited`
   - `runs?...end_date=2026-02-19...`: `202 -> 429 RateLimited`
4. ETag / `304`
   - `PASS` (edge)
   - `200` com `ETag`
   - `304 Not Modified` com `If-None-Match`
5. Runtime C1 Health Score (`/status`, gate ON)
   - `PASS`
   - `enabled=true`, `version=v1.1`
   - `score`, `rows[]`, `reasons[]`, `meta` presentes

Nota (cache TTL):
- com `api_workers=2`, o cache e por processo; `2` chamadas seguidas podem nao mostrar `cached=true`;
- loop curto confirmou cache hit (`cached=false -> cached=true`).

Governanca / versao (pos-fix):
- drift encerrado: `/health` em `:8000` e `:8001` retorna `api_version=1.9.9`
- commit aplicado: `1bb5beb` (`chore(version): bump DEFAULT_APP_VERSION to 1.9.9`)

Observacao operacional (runbook):
- ordem sequencial de rebootstrap evita `502` no edge:
  1. `api/read_api` primeiro
  2. `edge` por ultimo

Nota de ambiente (nao versionada):
- `EXPOSE_C1_HEALTH_STATUS=1` foi habilitado localmente no `docker-compose.yml` apenas para validacao;
- nao commitado (config de ambiente).

## Feature entregue: Operational Insights Panel (MVP)

Resumo:
- novo endpoint interno `GET /api/v1/observability/overview` (MVP) para leitura operacional consolidada;
- gate restrito (`EXPOSE_C1_HEALTH_STATUS=1` + `X-Internal-Status: 1`), retornando `404` sem autorizacao;
- payload inclui `overall`, `c1_health`, `read_path` e `guardrails` (counts `202/429/503` + ultimos `5` eventos).

Motivacao:
- oferecer visibilidade operacional rapida e vendavel sem acoplar com CI/workflow;
- manter custo previsivel e escopo congelado (nao substitui `/observability/report`).

Commits (MVP slice):
- `e25f65d` feat base (`/api/v1/observability/overview`)
- `8ebbd01` refactor (runtime health compartilhado)
- `fdbd45c` guardrails summary + `last_events`
- `4a605d0` testes (gate/shape/guardrails)
- `4906f56` Trust Banner (sinal `red|yellow|green` no payload)
- `1fbd92b` testes de derivacao do Trust Banner (inclui precedencia `red > yellow`)
- `c9f8fb3` Action Recommendation (acao/priority/message/derived_from no payload)
- `085b6dd` testes de mapeamento + precedencia da recommendation
- `3315c45` docs do Trust Banner (contrato + regras)

Extensao de produto (sobre o painel MVP):
- `Trust Banner` (`red|yellow|green`) integrado ao payload, com derivacao deterministica e precedencia testada;
- `Action Recommendation` (MVP) integrada ao payload, com acao recomendada deterministica (`run_warmup`, `monitor`, `reduce_force_live_burst`, `inspect_upstream_path`, `open_report`, `none`) e precedencia testada via endpoint real.
- `Internal Observability UI` (MVP) em `GET /internal/observability`, SSR simples com gate restrito, sem query nova e sem logica duplicada do painel.

## Maestro Runtime v0.2

Status:
- implementado e validado operacionalmente.

Inclui:
- persistencia leve de jobs do Maestro;
- migration `a7f9e1d2c3b4_add_maestro_jobs`;
- endpoint interno `GET /internal/maestro/jobs/{job_id}`;
- integracao do `POST /internal/maestro/run` com criacao e atualizacao do job (`running -> done|failed`), preservando `demo=1`.

Validacao focal:
- `tests/test_maestro_repository.py` âœ…
- `tests/test_internal_maestro_api.py` âœ…
- `tests/test_maestro_orchestrator.py` âœ…

Validacao operacional:
- `python -m alembic upgrade head` executado com sucesso no `cortai_api`;
- `alembic current` em `a7f9e1d2c3b4 (head)`;
- `POST /internal/maestro/run?demo=1` -> `done` persistido e recuperado via `GET /internal/maestro/jobs/{job_id}`;
- `POST /internal/maestro/run` -> `failed` controlado em `collector`, persistido e recuperado via `GET /internal/maestro/jobs/{job_id}`.

Observacao:
- o caminho real falhou por ambiente externo de coleta (`SSL/CERTIFICATE_VERIFY_FAILED` no coletor), nao por erro do runtime do Maestro.

## Collector TLS Fix

Status:
- corrigido no runtime do container e validado operacionalmente.

Inclui:
- `ca-certificates` + `openssl` no `backend/Dockerfile` e `backend/Dockerfile.gpu`;
- `update-ca-certificates` no build das imagens;
- `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE` e `CURL_CA_BUNDLE` fixados para `/etc/ssl/certs/ca-certificates.crt`;
- `compat_opts=['no-certifi']` no coletor para alinhar o `yt-dlp` ao CA store do sistema.

Validacao operacional:
- `requests.get("https://example.com")` dentro do `cortai_api` -> `200`;
- `POST /internal/maestro/run` com `source_ref=https://example.com/video.mp4` deixou de falhar por `SSL/CERTIFICATE_VERIFY_FAILED`;
- o erro real passou a ser `HTTP 404`, consistente com a URL de teste e com TLS funcional.


---

## Source: `docs/perf/load_testing_v1_0.md`

# Load Testing v1.0

## Objetivo

Medir, sob carga controlada:

- throughput
- latencia
- contencao por lease
- conflitos de idempotencia
- custo de fallback
- comportamento do pipeline em saturacao

Sem alterar contratos funcionais do sistema.

## Escopo

Entra:

- harness de carga para `window_pipeline`, `window_post_pipeline` e `/events`
- captura de metricas de latencia e throughput
- relatorio de saturacao em JSON e Markdown
- cenarios padrao de 10, 50 e 100 contas

Nao entra:

- tuning de banco
- autoscaling
- mudancas de arquitetura
- dashboards

## Metricas

Pipeline:

- `window_pipeline_latency_ms`
- `window_post_pipeline_latency_ms`

Query:

- `event_query_latency_ms`

Infra operacional:

- `lease_contention_rate`
- `idempotency_conflict_rate`
- `fallback_hit_rate`
- `error_rate`
- `throughput_ops_s`

## Cenarios

### load_10_accounts

- 10 contas
- 10 videos por conta
- 1 janela por conta
- burst leve de query

### load_50_accounts

- 50 contas
- 10 videos por conta
- 1 janela por conta
- burst medio de query

### load_100_accounts

- 100 contas
- 10 videos por conta
- 1 janela por conta
- burst mais alto de query
- rebuild opcional no final

### query_burst_fallback

- forca queda do hot store
- mede degradacao para indice/scanner

## Criterios GO/NO-GO

GO se:

- 0 corrupcao de dados
- 0 double-apply
- 0 snapshot inconsistente aceito
- query `/events` continua funcional sob burst
- fallback funciona sem quebra

NO-GO se:

- pipeline trava
- lease nao protege escrita
- patch duplica
- fallback perde consistencia
- query perde ordenacao ou paginacao

## Artefatos

O harness gera:

- `OUT/perf/load_test_report.json`
- `OUT/perf/load_test_report.md`

## Observacao arquitetural

`JSONL` continua sendo a verdade canonica.

O D18 mede comportamento sobre:

1. `JSONL`
2. indice SQLite
3. hot store

sem promover nenhuma dessas camadas derivadas a fonte de verdade.


---

## Source: `docs/pipeline/window_post_pipeline_v1_0.md`

# Window Post Pipeline v1.0 (D10)

## Objetivo
Orquestrar o caminho minimo pos-janela:

`window_metrics -> scorecard -> attribution -> strategy_learning`

com guard obrigatorio na entrada.

## Boundary de attribution
- O root canonico do subsystem de Content Performance Attribution e `backend/app/product/attribution/`.
- O trilho `backend/app/attribution/` permanece apenas como legado analitico / suporte nao canonico.
- O `D10` deve consumir o path canonico quando houver wiring concreto do servico de attribution.

## Ordem rigida
1. Guard
2. Scorecard
3. Attribution
4. Strategy Learning

## Entradas
- `account_id`
- `window_id`
- `deps` (servicos injetaveis)

## Saidas
Resultado unico com:
- status final
- status por etapa
- reason codes
- `op_key` de execucao

## Invariantes
- Se `guard.blocked == true`, nao executa scorecard/attribution/learning.
- Se scorecard nao for gerado, nao executa attribution/learning.
- Se attribution falhar por falta de metricas, nao executa learning.
- Nao aplica patch no registry (fora de escopo D10).

## Motivos de skip (minimo v1.0)
- `CONSISTENCY_VIOLATION_BLOCKED`
- `SCORECARD_NOT_GENERATED`
- `ATTRIBUTION_METRICS_MISSING`

## Idempotencia de execucao
- `op_key` canonico: `D10:{account_id}:{window_id}`.
- Se a execucao ja existe para o mesmo `op_key`, retorna `NOOP_EXECUTION`.

## Fora de escopo
- Application do patch no registry.
- Updater/account mutation.
- Estrategias de concorrencia avancadas (leases globais).


---

## Source: `docs/pr_checklist_observability.md`

# Checklist de PR - Observability / Publish

## 0) Contexto
- Objetivo do PR:
- Escopo (arquivos/areas tocadas):
- Invariantes respeitados: append-only, sem heuristica, facts sem paths.

## A) Migracoes / Banco
- [ ] `alembic upgrade head` executado sem erro
- [ ] `alembic current` aponta para `head`
- [ ] Sanity de tabela/indice novo (quando aplicavel)

Evidencias:
- `alembic upgrade head`:
- `alembic current`:

## B) Testes (Contrato API)
- [ ] `python -m pytest -q` passou
- [ ] Cobertura dos contratos:
  - [ ] `/metrics/daily`
  - [ ] `/metrics/overview`
  - [ ] `/metrics/alerts`
  - [ ] guardrails/dedupe

Comando:
`docker exec -i cortai_api sh -lc "cd /app && python -m pytest -q"`

Resultado:

## C) Smoke Telemetria (dia vazio)
- [ ] `aggregate_daily_metrics('2099-01-01')` com `status=done`
- [ ] Totais zerados
- [ ] Sem `cognitive_metrics_alert` no dia

Comando:
`docker exec -i cortai_worker python -c "from app.tasks.collector_tasks import aggregate_daily_metrics; r=aggregate_daily_metrics('2099-01-01'); assert r['status']=='done'; assert r['total_runs']==0; print('SMOKE_OK')"`

Query:
```sql
SELECT COUNT(*)
FROM observations
WHERE facts->>'event_type'='cognitive_metrics_alert'
  AND facts->>'metric_date'='2099-01-01';
```

## D) Contrato cognitive_loop_finished
- [ ] Termina e emite em cenarios observaveis
- [ ] `pipeline_status` valido
- [ ] Dedupe por `(process_id, source_outcome_id)`
- [ ] Sem paths em `facts`

## E) Manifest (write_artifact)
- [ ] `<decision_id>.json` existe
- [ ] Schema objetivo valido
- [ ] Observation sem paths

## F) Manifest-only Consumer (publish_manifest)
- [ ] Consumidor le apenas manifest
- [ ] `ArtifactNotFound` -> blocked
- [ ] `ArtifactInvalid` -> failed
- [ ] Sucesso com `last_action_type=publish_manifest`

## G) Publish Receipts (A-F)
- [ ] A) publish observado
- [ ] B/C) sem duplicata por `publish_decision_id`
- [ ] D) sem vazamento de path em `error_message`
- [ ] E) blocked/failed com `error_type` e `error_message`
- [ ] F) vinculo com manifest valido

Queries:
```sql
SELECT publish_decision_id, COUNT(*)
FROM publish_receipts
GROUP BY publish_decision_id
HAVING COUNT(*) > 1;
```

```sql
SELECT *
FROM publish_receipts
WHERE error_message ~ '(/tmp|storage|videos-raw|\\.mp4|\\.wav)'
LIMIT 20;
```

## H) Runtime / Operacao
- [ ] `git status` limpo
- [ ] `docker compose ps` com API/worker/beat up
- [ ] Sem `OutcomeMismatch` em logs do worker

## I) Notas de risco
- Backward-compatible:
- Requer restart:
- Downtime de migracao:
- Variaveis novas:


---

## Source: `docs/pr_p1_closed_p2_start.md`

# PR - Governance Formalization (P1 Closed + P2 Start)

## Title
`docs(observability): encerra P1 e formaliza inicio de P2 (throughput/infra path)`

## O que
- Registra resultado oficial da Matriz P1 (Linux nativo) em `docs/observability.md`.
- Formaliza entrada do ciclo P2 em `docs/roadmap_v2.md` com Definition of Done.

## Decisao
- `safe_envelope_v2.0 != C2` com SLO atual.
- Winner P1: `API_WORKERS=2`, `DB_POOL_SIZE=10`.
- Endpoint limitante principal: `/api/v1/metrics/overview`.
- Proximo passo canonico: P2 (throughput/infra path), sem mexer em logica de endpoint.

## Escopo
- Docs-only.
- Sem mudanca funcional de API/DB/core.

## Risco
- Nenhum risco de runtime (documentacao apenas).

## Evidencia
- Artefato da matriz: `.tmp_matrix_p1/matrix_p1_summary.csv`.
- Secao adicionada em `docs/observability.md` com resultados e decisao.
- Secao adicionada em `docs/roadmap_v2.md` com checklist e criterios de encerramento de P2.


---

## Source: `docs/product/content_attribution_v1_0.md`

# Content Attribution v1.0

## Objetivo
Conectar de forma determinÃ­stica os artefatos canÃ´nicos para formar o dataset de attribution:

`job_id -> publish_id/video_id -> video_metrics -> window_id -> scorecard`.

Esta camada nÃ£o faz aprendizado. Apenas constrÃ³i e persiste o registro estruturado.

## DecisÃµes congeladas (v1.0)

### 1) MÃ©tricas ausentes
- Se nÃ£o existir mÃ©trica real para o vÃ­deo: attribution nÃ£o Ã© gerado.
- Erro canÃ´nico: `ATTRIBUTION_METRICS_MISSING`.

### 2) IdempotÃªncia
- Chave canÃ´nica: `publish_id`.
- Motivo: representa a entidade real de publicaÃ§Ã£o e evita ambiguidade em reupload.

## Fluxo canÃ´nico
```text
job_id
  -> publish_record (D3)
  -> publish_id / video_id
  -> video_metrics (D4)
  -> window_metrics (D5)
  -> scorecard (D7)
  -> content_attribution (D8)
```

## Shape canÃ´nico mÃ­nimo
```json
{
  "attribution_id": "attr_pub_20260305_001",
  "account_id": "acc_ca_001",
  "publish_id": "pub_20260305_001",
  "video_id": "vid_abc123",
  "job_id": "job_789",
  "window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
  "policy_stage": "GROWTH",
  "hook_strategy": "open_loop_shock",
  "dominant_failure_reason": null,
  "effective_duration_s": 33,
  "rare_fact_placement_s": 18,
  "human_patch_detected": false,
  "views": 1200,
  "retention_3s": 0.46,
  "completion_rate": 0.31,
  "likes": 150,
  "follows": 18,
  "rpm": 0.84,
  "captured_at": "2026-03-05T00:02:00Z",
  "generated_at": "2026-03-05T00:05:00Z"
}
```

## Campos obrigatÃ³rios
- `attribution_id`
- `account_id`
- `publish_id`
- `video_id`
- `job_id`
- `window_id`
- `policy_stage`
- `hook_strategy`
- `human_patch_detected`
- `views`
- `retention_3s`
- `completion_rate`
- `captured_at`
- `generated_at`

## Campos opcionais
- `dominant_failure_reason`
- `effective_duration_s`
- `rare_fact_placement_s`
- `likes`
- `follows`
- `rpm`

## Invariantes
- `retention_3s` em `[0, 1]`.
- `completion_rate` em `[0, 1]`.
- `views >= 0`.
- `effective_duration_s > 0`.
- `rare_fact_placement_s >= 0`.
- `rare_fact_placement_s <= effective_duration_s`.
- `publish_id` obrigatÃ³rio para idempotÃªncia.

## Fora de escopo (v1.0)
- Ranking de estratÃ©gias.
- Aprendizado adaptativo.
- MutaÃ§Ã£o de policy/account registry.


---

## Source: `docs/product/strategy_learning_v1_0.md`

# Strategy Learning v1.0

## Objetivo
Gerar patch conservador e reversÃ­vel de estratÃ©gia por `(account_id, policy_stage, window_id)` usando apenas evidÃªncia real.

Sem LLM. Sem alteraÃ§Ã£o de `policy_stage`. Sem relaxar gates constitucionais.

## Inputs canÃ´nicos
- `window_metrics` (D5)
- `real_batch_scorecard` (D7)
- `content_attribution[]` (D8)

## Output canÃ´nico
- `strategy_patch` append-only
- `proposal_summary`

## Escopo permitido (whitelist rÃ­gida)
Apenas overrides nas camadas:
1. `A1` preferences
2. `A4` defaults
3. `A5` rewrite defaults

Qualquer override fora de `A1/A4/A5` Ã© ignorado com `SL_OVERRIDE_NOT_ALLOWED`.

## HeurÃ­stica conservadora (determinÃ­stica)
Patch ativo (`active=true`) apenas se:
- scorecard estÃ¡ verde (`status=STABLE`) E
- `videos_with_metrics >= min_videos_required` (v1.0: 5) E
- existe sinal consistente por feature (v1.0: >=60%)

Caso contrÃ¡rio:
- gera patch `NOOP` (`active=false`) com `reason_codes` explÃ­citos.

## PersistÃªncia
- Path: `OUT/data/strategy_patches.jsonl`
- Chave lÃ³gica: `(account_id, window_id, policy_stage, patch_kind=STRATEGY_V1)`
- IdempotÃªncia:
  - payload igual => `NOOP`
  - payload diferente => `STRATEGY_PATCH_CONFLICT`

## Erros canÃ´nicos
- `SL_SCORECARD_MISSING`
- `SL_WINDOW_METRICS_MISSING`
- `SL_ATTRIBUTION_EMPTY`
- `SL_POLICY_STAGE_INVALID`

## Shape mÃ­nimo do patch
```json
{
  "patch_id": "sp_acc_ca_001_w_2026-03-02..._GROWTH",
  "account_id": "acc_ca_001",
  "window_id": "w_2026-03-02T00:00:00Z_2026-03-05T00:00:00Z",
  "policy_stage": "GROWTH",
  "inputs": {
    "window_metrics_id": "wm_001",
    "scorecard_id": "sc_001",
    "attribution_count": 8
  },
  "overrides": {
    "a1_prefs_override": {},
    "a4_defaults_override": {},
    "a5_rewrite_defaults_override": {}
  },
  "active": false,
  "layers_applied": [],
  "reason_codes": ["INSUFFICIENT_VIDEOS"],
  "patch_kind": "STRATEGY_V1",
  "generated_at": "2026-03-05T03:00:00Z"
}
```


---

## Source: `docs/product/strategy_patch_application_v1_0.md`

# Strategy Patch Application v1.0

## Objetivo
Aplicar `strategy_patch` (D9) ao Account Registry de forma determinÃ­stica, auditÃ¡vel, idempotente e reversÃ­vel.

## Pipeline lÃ³gico
```text
strategy_patch
  -> whitelist_validation
  -> stage_match_check
  -> merge_registry_config
  -> persist_patch_application
  -> emit_audit_event
```

## Regras congeladas

### Whitelist rÃ­gida
Somente camadas permitidas:
- `A1`
- `A4`
- `A5`

Exemplos permitidos:
- `A1.topic_bias`
- `A4.hook_style`
- `A5.rewrite_flags`

Proibido:
- `policy_stage`
- `allocation`
- `retention_floor`
- `max_retry`

### IdempotÃªncia
Chave lÃ³gica:
- `(account_id, window_id, policy_stage)`

Resultado:
- inexistente -> `APPLY`
- payload igual -> `NOOP`
- payload diferente -> `CONFLICT`

### Stage mismatch
Se `patch.policy_stage != account_policy.stage`:
- `NOOP`
- sem aplicaÃ§Ã£o de override

### Rollback
Rollback automÃ¡tico quando:
- patch ativo
- `next_window_scorecard.performance_color == RED`

AÃ§Ã£o:
- remove `strategy_overrides.active`
- emite `SL/strategy_patch_rolled_back`

## Merge determinÃ­stico de configuraÃ§Ã£o
Ordem fixa:
1. `defaults_by_stage`
2. `account_policy`
3. `strategy_overrides.active`

## PersistÃªncia
- `OUT/data/strategy_patch_applications.jsonl`
- append-only

## Eventos
- `SL/strategy_patch_applied`
- `SL/strategy_patch_noop`
- `SL/strategy_patch_conflict`
- `SL/strategy_patch_rolled_back`

Payload mÃ­nimo:
- `account_id`
- `window_id`
- `policy_stage`
- `patch_id`
- `timestamp`


---

## Source: `docs/roadmap_v2.md`

# Roadmap v2.0 (Draft)

Objetivo:
- Definir direcao da linha v2.0 sem implementar mudancas estruturais no ciclo atual.
- Preservar a baseline estavel v1.9.x enquanto novas trilhas sao planejadas com criterio.

## 1) Performance Track

Meta:
- Elevar `safe_envelope` de `C1` para `C2` com evidencias reproduziveis.

Escopo:
- Tuning de pool/conexoes DB (sem alterar contrato publico).
- Tuning de workers/process model da API.
- Revisao de limites operacionais do report em carga concorrente.
- Investigacao de camada async DB (apenas se tuning nao for suficiente).

CritÃ©rios de saida:
- `timeouts = 0` em C2 para endpoints alvo.
- `bad_duration = 0` e `path_leaks_30d = 0` mantidos.
- Sem regressao de shape/guardrails.

## 2) Productization Track

Meta:
- Transformar observabilidade consolidada em superficies operacionais de consumo simples.

Escopo:
- Dashboard leve consumindo `/api/v1/observability/report` (read-only).
- Endpoint/status executivo para leitura de estado geral.
- Pagina HTML de status operacional (sem acoplamento ao core).

CritÃ©rios de saida:
- Contratos publicos documentados.
- Fluxo de diagnostico em ate 1 tela para operacao.
- Sem introduzir logica de decisao no frontend.

## 3) Architecture Track

Meta:
- Reduzir custo de request-path para blocos pesados via materializacao e processamento assÃ­ncrono.

Escopo:
- Materializacao de `worst_runs`.
- Materializacao de agregados de `publish_receipts`.
- Separacao opcional de relatorio pesado para job assÃ­ncrono read-only.

CritÃ©rios de saida:
- Custo DB previsivel em janela de carga.
- Dedupe e idempotencia preservados.
- Contrato do report mantido (lean default + opt-in heavy).

## Entry Criteria v2.0

Antes de iniciar implementacoes v2.0:
- Baseline v1.9.x formalmente declarada em docs.
- Governanca de versao alinhada (`tag` <-> `/health.api_version`).
- Smoke operacional verde (`/health`, `/status`, `/observability/report`).
- Evidencias de envelope e pivot DB anexadas para comparacao.

## Guardrails de Execucao

- Evitar mudancas simultaneas de contrato + arquitetura no mesmo PR.
- Priorizar sequencia: medir -> alterar -> validar -> documentar.
- Cada trilha deve gerar evidencia objetiva de PASS/FAIL.

## P2 - Definition of Done (Performance Track)

Objetivo de P2:
- Identificar onde a latencia nasce no caminho de throughput/infra sem mexer em logica de endpoint.

Escopo canonicamente aceito:
- Process model (`workers`, `backlog`, limites de concorrencia do servidor HTTP).
- I/O model (`keep-alive`, configuracao de conexoes do gerador de carga, path HTTP).
- Infra path (separacao runner x system under test, rede e roteamento do ambiente de benchmark).

Checklist de encerramento P2:
- Load generator executado fora do mesmo host/container do sistema alvo.
- Minimo de 3 rodadas por cenario com desvio registrado.
- Tabela consolidada: `endpoint x C(1/2/5) x p90/p99 x req/s x timeouts x config`.
- Evidencia de que `db_pool_wait_us` permanece controlado (ou justificativa quando subir).
- Identificacao objetiva do knob dominante (workers, keep-alive, backlog, client pool, infra path).
- Decisao formal: `C2 possivel com SLO atual? (sim/nao)` com justificativa.

Entrega obrigatoria:
- CSV consolidado do ciclo P2.
- Bloco de decisao adicionado em `docs/observability.md`.
- Atualizacao do runbook com criterio de repetibilidade do benchmark.


---

## Source: `docs/runbook_operacional_v1.8.1.md`

Runbook Operacional - CortAI v1.8.1 (Metrics SLO + Guardrails + Timing)

Versao: v1.8.1
Timezone padrao: UTC
Escopo: validar que a observabilidade de metricas esta viva, consistente e auditavel apos release.

0) Preflight (HTTP)

0.1 Healthcheck (versao e CES default)

PASS se:

status=ok

api_version=1.8.1

ces_default_version=CES_v1

Exemplo:

GET /health

0.2 Guardrails do endpoint de runs

PASS se:

/metrics/runs?limit=201 retorna 400 com LimitTooHigh

/metrics/runs com range > 31 dias retorna 400 com RangeTooLarge

Criterios:

detail.error_type == "LimitTooHigh"

detail.limit_requested e int

detail.limit_max == 200

E:

detail.error_type == "RangeTooLarge"

detail.range_days e int

detail.range_max == 31

1) Smoke HTTP (gera telemetria de timing)

Execute pelo menos uma vez cada endpoint:

1. GET /api/v1/metrics/overview?days=7

2. GET /api/v1/metrics/runs?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&limit=50&offset=0

3. GET /api/v1/metrics/runs/{process_id} (use um process_id real do /runs)

Objetivo: garantir que metrics_endpoint_timing esta sendo emitido em Observations e persistido (JSONL + Postgres).

2) SQL Bundle - Observability Report (v1.8.1)

Rode em Postgres (UTC).
Obs: publish_receipts.pipeline_status e o campo canonico.

2.0 Header / Contexto

SELECT
  NOW() AT TIME ZONE 'UTC' AS generated_at_utc,
  CURRENT_DATE AS current_date_utc;

2.1 Telemetria viva (ultimos 15 min): metrics_endpoint_timing

SELECT
  COUNT(*) AS timing_events_15m,
  MIN(timestamp) AS min_ts,
  MAX(timestamp) AS max_ts
FROM observations
WHERE facts->>'event_type' = 'metrics_endpoint_timing'
  AND timestamp >= NOW() - INTERVAL '15 minutes';

2.2 Timing por endpoint + sanity de duration (ultimos 15 min)

SELECT
  facts->>'endpoint' AS endpoint,
  facts->>'method' AS method,
  facts->>'status_code' AS status_code,
  COUNT(*) AS n_events,
  MIN((facts->>'duration_ms')::numeric) AS min_ms,
  MAX((facts->>'duration_ms')::numeric) AS max_ms
FROM observations
WHERE facts->>'event_type' = 'metrics_endpoint_timing'
  AND timestamp >= NOW() - INTERVAL '15 minutes'
GROUP BY 1,2,3
ORDER BY endpoint, status_code;

2.3 Dedupe de timing (nao pode haver 2 eventos "iguais" por request)

SELECT
  COUNT(*) AS duplicated_events
FROM (
  SELECT
    facts->>'endpoint' AS endpoint,
    facts->>'method' AS method,
    facts->>'timestamp' AS req_ts,
    COUNT(*) AS n
  FROM observations
  WHERE facts->>'event_type' = 'metrics_endpoint_timing'
    AND timestamp >= NOW() - INTERVAL '15 minutes'
  GROUP BY 1,2,3
  HAVING COUNT(*) > 1
) t;

2.4 Ultimos 7 dias: SLO diario por endpoint

SELECT
  metric_date,
  endpoint,
  count_requests,
  p50_ms,
  p95_ms,
  p99_ms,
  error_rate
FROM metrics_endpoint_daily
WHERE metric_date >= (CURRENT_DATE - INTERVAL '7 days')::date
ORDER BY metric_date ASC, endpoint ASC;

2.5 Pior dia por endpoint (ultimos 14 dias)

SELECT DISTINCT ON (endpoint)
  endpoint,
  metric_date,
  count_requests,
  p95_ms,
  p99_ms,
  error_rate
FROM metrics_endpoint_daily
WHERE metric_date >= (CURRENT_DATE - INTERVAL '14 days')::date
ORDER BY endpoint, p95_ms DESC, error_rate DESC, metric_date DESC;

2.6 SLO Alerts (ultimos 14 dias)

SELECT
  timestamp,
  process_id,
  facts->>'metric_date' AS metric_date,
  facts->>'endpoint' AS endpoint,
  facts->'reasons' AS reasons,
  facts
FROM observations
WHERE facts->>'event_type' = 'metrics_slo_alert'
  AND timestamp >= NOW() - INTERVAL '14 days'
ORDER BY timestamp DESC
LIMIT 200;

2.7 Top 20 piores runs (CES_run) - ultimos 2 dias (cast seguro)

Obs: so funciona se o cognitive_loop_finished estiver projetando ces_run em facts.
WITH finished AS (
  SELECT
    process_id,
    timestamp,
    facts,
    ROW_NUMBER() OVER (PARTITION BY process_id ORDER BY timestamp DESC) AS rn
  FROM observations
  WHERE facts->>'event_type' = 'cognitive_loop_finished'
    AND timestamp >= NOW() - INTERVAL '2 days'
)
SELECT
  process_id,
  timestamp AS finished_ts,
  COALESCE(facts->>'pipeline_status', 'unknown') AS pipeline_status,
  facts->>'execution_status' AS execution_status,
  facts->>'ces_run_version' AS ces_run_version,
  NULLIF(facts->>'ces_run','')::numeric AS ces_run,
  NULLIF(facts->'ces_run_components'->>'status','')::numeric AS s_status,
  NULLIF(facts->'ces_run_components'->>'actions','')::numeric AS s_actions,
  NULLIF(facts->'ces_run_components'->>'latency','')::numeric AS s_latency,
  NULLIF(facts->'ces_run_components'->>'trunc','')::numeric AS s_trunc,
  facts->>'ces_run_reason' AS ces_run_reason
FROM finished
WHERE rn = 1
  AND NULLIF(facts->>'ces_run','') IS NOT NULL
ORDER BY ces_run ASC
LIMIT 20;

2.8 publish_receipts: distribuicao de erros (ultimos 7 dias) com NULL visivel

SELECT
  COALESCE(error_type, 'unknown') AS error_type,
  COUNT(*) AS n
FROM publish_receipts
WHERE created_at >= NOW() - INTERVAL '7 days'
  AND pipeline_status IN ('blocked','failed')
GROUP BY 1
ORDER BY n DESC;

2.9 publish_receipts: ultimos 50 blocked/failed (ultimos 7 dias)

SELECT
  process_id,
  publish_decision_id,
  manifest_decision_id,
  pipeline_status,
  error_type,
  error_message,
  created_at
FROM publish_receipts
WHERE created_at >= NOW() - INTERVAL '7 days'
  AND pipeline_status IN ('blocked','failed')
ORDER BY created_at DESC
LIMIT 50;

2.10 Auditoria de sanitizacao (30 dias): vazamento de paths/artefatos em error_message

SELECT
  COUNT(*) AS error_message_path_leaks_30d
FROM publish_receipts
WHERE created_at >= NOW() - INTERVAL '30 days'
  AND (
    error_message ILIKE '%/tmp%' OR
    error_message ILIKE '%storage/%' OR
    error_message ILIKE '%videos-raw%' OR
    error_message ILIKE '%.mp4%' OR
    error_message ILIKE '%.wav%' OR
    error_message ILIKE '%.json%' OR
    error_message ILIKE '%agent_output%'
  );

2.11 Resumo final (ultimos 7 dias): volume e qualidade por endpoint

SELECT
  endpoint,
  SUM(count_requests) AS total_requests_7d,
  AVG(p95_ms) AS avg_p95_ms_7d,
  AVG(error_rate) AS avg_error_rate_7d
FROM metrics_endpoint_daily
WHERE metric_date >= (CURRENT_DATE - INTERVAL '7 days')::date
GROUP BY endpoint
ORDER BY total_requests_7d DESC;

3) Checklist PASS/FAIL (com base no bundle)

3.1 Timing / Telemetria

PASS se timing_events_15m > 0

PASS se o query 2.2 mostra os 3 endpoints:

/api/v1/metrics/runs

/api/v1/metrics/runs/{process_id}

/api/v1/metrics/overview

PASS se min_ms > 0 e max_ms > 0

PASS se duplicated_events = 0

3.2 Agregacao diaria SLO

PASS se 2.4 retorna linhas nos ultimos 7 dias

PASS se existe pelo menos 1 endpoint com count_requests > 0 nos ultimos 7 dias

PASS se nao ha duplicacao por (metric_date, endpoint) (implicito pela tabela + idempotencia do job)

3.3 Sanitizacao publish_receipts

PASS se error_message_path_leaks_30d = 0

3.4 Alertas SLO

PASS se, quando existirem alertas (2.6), reasons forem coerentes com:

p95_ms, p99_ms e/ou error_rate

PASS se nao existir duplicacao logica por (metric_date, endpoint, reason) (dedupe)

3.5 CES_run report

PASS se 2.7 retorna ces_run numerico

OK se vazio quando cognitive_loop_finished ainda nao projeta ces_run em facts (nao e falha do SLO)

4) Template de evidencia operacional (para anexar em PR/Issue)

Preencha:

generated_at_utc: <resultado do 2.0>

timing_events_15m: <resultado do 2.1>

duplicated_events: <resultado do 2.3>

endpoints vistos (2.2): <lista>

metrics_endpoint_daily linhas 7d: <quantidade>

pelo menos 1 endpoint count_requests>0: <sim/nao>

error_message_path_leaks_30d: <resultado do 2.10>

SLO alerts ultimos 14d: <0 / N + resumo reasons>

Top worst runs: <0 / N + motivo>


---

## Source: `docs/runbook_operacional_v1.8.2.md`

# CortAI - Runbook Operacional

Escopo: SLO + Guardrails + Timing + Runs + Receipts
Versao alvo: >= v1.8.1
Timezone padrao: UTC

## 0) Preflight (Contexto da Execucao)

Registrar manualmente antes de iniciar:

| Campo | Valor |
|---|---|
| `api_version` (`/health`) | |
| `ces_default_version` | |
| `git_tag` (se disponivel) | |
| `git_commit` (se disponivel) | |
| `alembic current` | |
| `generated_at_utc` | |

Comandos:

```bash
curl http://localhost:8000/health
docker exec -i cortai_api sh -lc "cd /app && alembic current"
```

### Opcional: modo automatizado via API

Endpoint read-only consolidado:

```bash
curl "http://localhost:8000/api/v1/observability/report?window_days=7&timing_minutes=15&limit_alerts=200&limit_receipts=50"
```

Leitura rapida:
- `status=PASS|WARN|FAIL`
- `checks[]` contem os mesmos criterios hard do runbook SQL
- `runs.worst` vazio gera `WARN` (nao `FAIL`) quando nao houver projecao de `ces_run`

### Importante: ambiente de benchmark (SLO/envelope)

Se estiver rodando em Docker Desktop + WSL2, nao use o caminho edge (Nginx) para calibrar SLO/envelope.
Esse ambiente pode distorcer TTFB/queue no proxy.

- Fonte de verdade local: direct (`cortai_worker -> cortai_api:8000`)
- Fonte de verdade final: Linux nativo (VM/VPS/host) com comparacao direct vs edge
- Evitar: definir envelope/SLO "real" com edge no Docker Desktop

## 1) Smoke HTTP (Contratos Publicos)

### 1.1 Health

Esperado:
- `status = ok`
- `api_version = 1.8.x`
- `ces_default_version = CES_v1`

### 1.2 Guardrails

Limit > 200:

```bash
curl ".../metrics/runs?start_date=2026-02-10&end_date=2026-02-11&limit=201"
```

Esperado:

```json
{
  "detail": {
    "error_type": "LimitTooHigh",
    "limit_requested": 201,
    "limit_max": 200
  }
}
```

Range > 31 dias:

```bash
curl ".../metrics/runs?start_date=2026-01-01&end_date=2026-04-01&limit=50"
```

Esperado:

```json
{
  "detail": {
    "error_type": "RangeTooLarge",
    "range_days": 91,
    "range_max": 31
  }
}
```

## 2) Telemetria Viva (ultimos 15 minutos)

```sql
SELECT
  COUNT(*) AS timing_events_15m,
  MIN(timestamp) AS min_ts,
  MAX(timestamp) AS max_ts
FROM observations
WHERE facts->>'event_type' = 'metrics_endpoint_timing'
  AND timestamp >= NOW() - INTERVAL '15 minutes';
```

PASS: `timing_events_15m > 0`

## 3) Sanity de duration_ms

```sql
SELECT COUNT(*) AS bad_duration
FROM observations
WHERE facts->>'event_type'='metrics_endpoint_timing'
  AND timestamp >= NOW() - INTERVAL '15 minutes'
  AND (
    (facts->>'duration_ms') IS NULL OR
    (facts->>'duration_ms') = '' OR
    (facts->>'duration_ms')::numeric < 0
  );
```

PASS: `bad_duration = 0`

## 4) SLO Diario por Endpoint (7 dias)

```sql
SELECT
  metric_date,
  endpoint,
  count_requests,
  p50_ms,
  p95_ms,
  p99_ms,
  error_rate
FROM metrics_endpoint_daily
WHERE metric_date >= (CURRENT_DATE - INTERVAL '7 days')::date
ORDER BY metric_date ASC, endpoint ASC;
```

Criterios:
- pelo menos 1 endpoint com `count_requests > 0`
- `p95_ms` e `p99_ms` preenchidos

## 5) Dedupe explicito (metrics_endpoint_daily)

```sql
SELECT metric_date, endpoint, COUNT(*) AS n
FROM metrics_endpoint_daily
WHERE metric_date >= (CURRENT_DATE - INTERVAL '14 days')::date
GROUP BY 1,2
HAVING COUNT(*) > 1;
```

PASS: `0 linhas`

## 6) SLO Alerts (14 dias)

```sql
SELECT
  timestamp,
  process_id,
  facts->>'metric_date' AS metric_date,
  facts->>'endpoint' AS endpoint,
  facts->'reasons' AS reasons
FROM observations
WHERE facts->>'event_type' = 'metrics_slo_alert'
  AND timestamp >= NOW() - INTERVAL '14 days'
ORDER BY timestamp DESC;
```

Criterios:
- `reasons` coerente com `p95/p99/error_rate`
- sem duplicacao por `(metric_date, endpoint, reason)`

## 7) Top 20 Piores Runs (2 dias)

```sql
WITH finished AS (
  SELECT
    process_id,
    timestamp,
    facts,
    ROW_NUMBER() OVER (PARTITION BY process_id ORDER BY timestamp DESC) AS rn
  FROM observations
  WHERE facts->>'event_type' = 'cognitive_loop_finished'
    AND timestamp >= NOW() - INTERVAL '2 days'
)
SELECT
  process_id,
  timestamp AS finished_ts,
  COALESCE(facts->>'pipeline_status', 'unknown') AS pipeline_status,
  NULLIF(facts->>'ces_run','')::numeric AS ces_run
FROM finished
WHERE rn = 1
  AND NULLIF(facts->>'ces_run','') IS NOT NULL
ORDER BY ces_run ASC
LIMIT 20;
```

PASS:
- `ces_run` numerico
- ordenacao ascendente coerente

## 8) Distribuicao de erros publish_receipts (7 dias)

```sql
SELECT
  COALESCE(error_type,'unknown') AS error_type,
  COUNT(*) AS n
FROM publish_receipts
WHERE created_at >= NOW() - INTERVAL '7 days'
  AND pipeline_status IN ('blocked','failed')
GROUP BY 1
ORDER BY n DESC;
```

## 9) Auditoria de Sanitizacao (30 dias)

```sql
SELECT COUNT(*) AS error_message_path_leaks_30d
FROM publish_receipts
WHERE created_at >= NOW() - INTERVAL '30 days'
  AND (
    error_message ILIKE '%/tmp%' OR
    error_message ILIKE '%storage/%' OR
    error_message ILIKE '%videos-raw%' OR
    error_message ILIKE '%.mp4%' OR
    error_message ILIKE '%.wav%' OR
    error_message ILIKE '%.json%' OR
    error_message ILIKE '%agent_output%'
  );
```

PASS: `error_message_path_leaks_30d = 0`

## 10) Resumo 7 dias por endpoint

```sql
SELECT
  endpoint,
  SUM(count_requests) AS total_requests_7d,
  AVG(p95_ms) AS avg_p95_ms_7d,
  AVG(error_rate) AS avg_error_rate_7d
FROM metrics_endpoint_daily
WHERE metric_date >= (CURRENT_DATE - INTERVAL '7 days')::date
GROUP BY endpoint
ORDER BY total_requests_7d DESC;
```

## Template de Evidencia Operacional

```text
CortAI Observability Report - vX.Y.Z
Generated at: <UTC>

Health:
- api_version:
- ces_default_version:

Timing (15m):
- timing_events_15m:
- bad_duration:

SLO Daily:
- endpoints ativos:

Alerts:
- count_last_14d:

Receipts:
- blocked/failed_last_7d:
- path_leaks_30d:

Status Final: PASS | WARN | FAIL
Observacoes:
```

## Criterios Globais de PASS

- telemetria viva
- `duration_ms` valido
- `metrics_endpoint_daily` populado
- sem duplicacao por endpoint/dia
- alertas idempotentes
- sanitizacao integra
- `ces_run` numerico quando presente

## Evidencia Runtime - /api/v1/observability/report (v1.8.2)

Data UTC: `2026-02-17`

- `/health`: `status=ok`, `api_version=1.8.2`, `ces_default_version=CES_v1`
- Happy path: shape minimo completo (`generated_at_utc`, `version`, `timing`, `slo_daily`, `slo_alerts`, `runs`, `publish_receipts`, `checks`, `status`)
- Guardrails:
  - `window_days=31` -> `400 RangeTooLarge` com `window_days_max=30`
  - `timing_minutes=61` -> `400 RangeTooLarge` com `timing_minutes_max=60`
  - `limit_alerts=501` -> `400 LimitTooHigh` com `limit_alerts_max=500`
  - `limit_receipts=201` -> `400 LimitTooHigh` com `limit_receipts_max=200`
- Checks: `checks_len=6`, todos com `id` e `pass`
- Timing sanity: `events=29`, `bad_duration=0`
- SLO daily: `has_requests=true`, `items_len=2`
- Sanitizacao: `path_leaks_30d=0`
- Status: `WARN` (valido por contrato)
- Self-observing confirmado: `events_before=34` -> `events_after=38` apos 3 chamadas

## Envelope v1.3 (Linux nativo)

Criterio:
- `0` timeouts
- p99 dentro do SLO definido por endpoint

Resultado:
- `C1`: estavel (sem timeouts)
- `C2`: degradacao significativa de latencia
- `C5`: latencia >800ms para overview e >1s para runs

Decisao operacional:
- safe concurrency = `1`
- escala horizontal recomendada antes de permitir `C>=2`
- proxima meta tecnica: reduzir p90 de `/metrics/overview` para `<=120ms`

Observacao:
- Docker Desktop + WSL2 nao foi usado como fonte de verdade para esta decisao.


---

## Source: `docs/simulation/offline_simulation_engine_v1_0.md`

# Offline Simulation Engine v1.0

## Scope

`D37 â€” Offline Simulation Engine v1.0` adiciona uma camada offline para simular o ciclo de aprendizagem do CortAI sem usar contas reais e sem publicar nada.

Fluxo simulado:

- `publish_records`
- `video_metrics`
- `experiment_results`
- inputs derivados para `analysis`

## Goals

- validar `D31`, `D32`, `D34` e `D38` com dados sintÃ©ticos
- exercitar cenarios de aprendizado antes do piloto real
- aumentar confianca nos fluxos de analise e consistencia
- evitar gasto de videos reais para debug funcional

## Out of Scope

- nenhuma publicacao real
- nenhuma chamada externa
- nenhuma alteracao em:
  - `publish`
  - `scheduler`
  - `workers`
  - `safety`
  - `metrics collector`
  - `rollout`

## Outputs

Outputs append-only previstos em `OUT/simulation/`:

- `simulated_publish_records.jsonl`
- `simulated_video_metrics.jsonl`
- `simulated_experiment_results.jsonl`
- `simulation_run_summary.json`

## Input Shape

O engine aceita apenas configuracao offline, por exemplo:

- `simulation_run_id`
- `account_ids`
- `videos_per_account`
- `experiment_variants`
- `seed`

## Data Model

Modelos minimos:

- `SimulatedPublishRecord`
- `SimulatedVideoMetrics`
- `SimulatedExperimentResult`
- `SimulationRunSummary`

## Invariants

- mesma entrada e mesmo seed produzem a mesma saida funcional
- ids sao determinÃ­sticos por `simulation_run_id + index`
- referencias internas precisam ser coerentes
- nenhum side effect fora de `OUT/simulation/`
- nenhum artefato real de runtime pode ser alterado

## Publish Simulation

O simulador de publish deve gerar registros equivalentes a `publish_records`, contendo pelo menos:

- `publish_id`
- `account_id`
- `video_id`
- `creative_pack_id`
- `platform`
- `status`

## Metrics Simulation

O simulador de mÃ©tricas deve gerar registros equivalentes a `video_metrics`, contendo pelo menos:

- `publish_id`
- `account_id`
- `video_id`
- `views`
- `avg_watch_time`
- `completion_rate`
- `view_3s_rate`
- `view_5s_rate`
- `collected_at_bucket`

## Experiment Simulation

O simulador de experimentos deve gerar resultados coerentes com variantes atribuidas, contendo pelo menos:

- `experiment_id`
- `assignment_id`
- `variant`
- `supporting_metric`
- `winner_hint`

## Runner Responsibilities

O runner deve:

1. gerar publishes simulados
2. gerar mÃ©tricas simuladas coerentes
3. gerar resultados de experimento coerentes
4. persistir os outputs
5. produzir um `simulation_run_summary`

## Integration Expectations

Os dados simulados devem ser consumiveis por:

- `D34 â€” Analysis & Research Layer`
- `D38 â€” Data Consistency Checker`

Sem adapters especiais ou mutacoes no runtime critico.


---

## Source: `docs/ui/operator_actions_v1_0.md`

# Operator Actions v1.0

## Objetivo

Adicionar um conjunto mÃ­nimo, seguro e auditÃ¡vel de aÃ§Ãµes operacionais ao console.

## AÃ§Ãµes permitidas

1. `pause-rollout`
2. `resume-rollout`
3. `requeue-task`
4. `rebuild-event-index`
5. `ack-alert`

## AÃ§Ãµes proibidas

- aplicar patch manualmente
- editar policy/account stage
- alterar scorecard
- alterar attribution
- apagar eventos/logs
- reprocessar janela inteira sem guard

## Regras

- toda aÃ§Ã£o exige `reason`
- toda aÃ§Ã£o exige `operator_id`
- toda aÃ§Ã£o gera trilha de auditoria
- nenhuma aÃ§Ã£o contorna lease, op_key ou rollout policy
- `ack-alert` nÃ£o apaga alerta

## PolÃ­tica por aÃ§Ã£o

### Pause / Resume Rollout

- atua no control plane do rollout
- nÃ£o derruba workers jÃ¡ em execuÃ§Ã£o
- afeta novas execuÃ§Ãµes via override operacional

### Requeue Task

- permitido apenas para `FAILED`, `BLOCKED` e `NOOP`
- proibido para `RUNNING`
- preserva referÃªncia ao `task_id` original
- requeue duplicado com mesma chave lÃ³gica vira `NOOP`

### Rebuild Event Index

- aÃ§Ã£o administrativa segura
- query path continua disponÃ­vel por fallback
- rebuild Ã© idempotente

### Acknowledge Alert

- registra `acknowledged_by`, `acknowledged_at` e `reason`
- nÃ£o remove o alerta original

## Auditoria

Toda aÃ§Ã£o persiste:

- `action_type`
- `operator_id`
- `target_id`
- `reason`
- `result`
- `ts`

## Out of scope

- RBAC complexo
- mutaÃ§Ãµes manuais de pipeline
- aÃ§Ãµes destrutivas


---

## Source: `docs/ui/operator_console_v1_0.md`

# Operator Console v1.0

## Objetivo

Criar uma superfÃ­cie operacional read-only para acompanhar:

- rollout piloto
- batches de 72h
- tasks e workers
- alertas e SLO
- saÃºde do sistema
- acesso rÃ¡pido para event trace

## PÃ¡ginas / Ã¡reas mÃ­nimas

1. Overview
2. Windows / Batches
3. Tasks / Workers
4. Alerts / SLO
5. Event Trace quick access

## Endpoints read-only

- `/api/v1/ops/health-summary`
- `/api/v1/ops/rollout-status`
- `/api/v1/ops/windows`
- `/api/v1/ops/tasks`
- `/api/v1/ops/alerts`

## Fontes de dados

O console consome:

- artifacts persistidos em `OUT/ops` e `OUT/rollout`
- eventos via trilha `RUNTIME/*` e `INTEGRATION/*`
- `health` local da API

## Regras congeladas

- read-only obrigatÃ³rio
- nenhum endpoint do D24 altera estado
- nenhuma aÃ§Ã£o operacional Ã© permitida via UI v1.0
- o console nunca inventa estado; apenas projeta estado existente

## Fora de escopo

- editar policy
- aplicar patch manual
- pausar rollout
- requeue task
- acknowledge alert
- autenticaÃ§Ã£o multiusuÃ¡rio


---

## Source: `docs/ui/strategy_observatory_v1_0.md`

# D26 - Strategy Observatory v1.0

## Objetivo

Tornar o learning loop legÃ­vel para operador sem alterar a lÃ³gica de aprendizado.

O observatÃ³rio deve mostrar:

- patches gerados
- patches aplicados
- impacto por janela
- evoluÃ§Ã£o temporal da estratÃ©gia

## Fonte de dados

O D26 Ã© somente leitura e usa artefatos jÃ¡ existentes:

- `OUT/data/strategy_patches.jsonl`
- `OUT/data/strategy_patch_applications.jsonl`
- `OUT/data/scorecards.jsonl`
- `OUT/data/window_metrics.jsonl`

Quando algum artefato nÃ£o existir, a API deve responder com listas vazias em vez de quebrar.

## Entidades exibidas

### Patch

- `patch_id`
- `account_id`
- `window_id`
- `policy_stage`
- `reason_code`
- `created_at`
- `status`

Status canÃ´nicos:

- `generated`
- `applied`
- `noop`
- `conflict`
- `reverted`

### Impacto

Cada patch deve expor:

- `window_id_before`
- `window_id_after`
- `scorecard_delta`

O delta Ã© calculado como:

`valor_after - valor_before`

Sem heurÃ­stica sofisticada no v1.0.

### Timeline

Linha temporal por conta:

- `window_id`
- `patch_id`
- `policy_stage`
- `status`
- `reason_code`
- `created_at`

## Endpoints

- `GET /api/v1/ops/strategy/patches`
- `GET /api/v1/ops/strategy/patch/{patch_id}`
- `GET /api/v1/ops/strategy/impact`
- `GET /api/v1/ops/strategy/timeline`

## Regras

- read-only obrigatÃ³rio
- nenhuma mutaÃ§Ã£o de patch ou policy
- patch inexistente deve falhar explicitamente
- dados inconsistentes devem degradar para campos nulos, nunca derrubar a API inteira

## Out of Scope

- ediÃ§Ã£o manual de estratÃ©gia
- rollback manual de patch
- mudanÃ§a no learner
- algoritmos novos de impacto


---

## Source: `docs/versioning.md`

# Politica de Versionamento (CortAI)

Este documento define a politica minima de versionamento semantico da plataforma.

## Regra geral

- Formato: `MAJOR.MINOR.PATCH`
- Exemplo atual: `1.6.0`

## MAJOR (X.0.0)

Incrementar MAJOR quando houver quebra de contrato publico:

- Mudanca de shape de resposta da API sem compatibilidade.
- Remocao de campos existentes.
- Mudanca de semantica de uma versao de CES ja publicada.

## MINOR (0.X.0)

Incrementar MINOR quando houver expansao backward-compatible:

- Nova versao de CES (`CES_vN`) sem alterar versoes anteriores.
- Novo endpoint.
- Novos campos opcionais em respostas existentes.
- Novo alerta de observabilidade sem quebra de contrato.

## PATCH (0.0.X)

Incrementar PATCH para correcao sem mudanca de contrato:

- Bugfix de implementacao.
- Ajuste interno de calculo que nao altera contrato publico.
- Correcao de documentacao.

## Contrato de imutabilidade do CES

- `CES_v1` e imutavel.
- `CES_v2` e imutavel.
- Qualquer mudanca de formula/componente/peso gera nova versao (`CES_vN`).
