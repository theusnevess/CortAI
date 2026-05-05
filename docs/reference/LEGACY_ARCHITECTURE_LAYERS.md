# Legacy Architecture Layers

Archived reference for the previous architecture-layer documentation set.

## Consolidation Notice

This file consolidates documentation that was previously split across multiple legacy files. The source contents are preserved below for auditability.

## Source Files

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

## Consolidated Contents

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
