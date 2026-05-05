# Legacy Cognitive Model

Archived reference for the old cognitive model documentation.

## Consolidation Notice

This file consolidates documentation that was previously split across multiple legacy files. The source contents are preserved below for auditability.

## Source Files

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

## Consolidated Contents

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
