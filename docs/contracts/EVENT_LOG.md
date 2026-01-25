# Event Log

## Objetivo

O **Event Log** é o **registro linear, imutável e ordenado de todos os eventos observáveis do CortAI**, internos e externos.

> O sistema **não lembra estados passados** —  
> ele **reconstrói tudo a partir de eventos**.

---

## Papel no Sistema

O Event Log é a **espinha dorsal da auditabilidade, rastreabilidade e replay** do CortAI.

Ele permite:
- reconstrução completa do State
- análise pós-morte (post-mortem)
- debugging determinístico
- métricas e monitoramento
- simulações e replays cognitivos

---

## Princípio Fundamental

> **Nada acontece no sistema sem gerar um evento.**

Se algo ocorreu e não está no Event Log:
- é invisível
- é irrelevante
- é considerado inexistente

---

## Definição Conceitual

Um **Evento** é o **registro atômico de algo que aconteceu**, em um instante específico, com contexto suficiente para ser interpretado no futuro — sem ambiguidade.

Eventos:
- não têm intenção
- não tomam decisões
- não causam efeitos diretos
- apenas registram fatos

---

## Estrutura Canônica do Evento

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

Identificador único do evento.

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
* Tipos são fechados (não dinâmicos)

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

Define **quem originou o evento**, não quem será afetado.

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

* IDs ausentes significam “não aplicável”
* Nunca referencia entidades inexistentes

---

## Payload

```python
payload: dict
```

Dados específicos do evento.

Exemplos:

* resumo da decisão
* erro ocorrido
* métricas da fase
* metadados externos

**Invariantes**

* Payload nunca contém lógica
* Payload nunca altera comportamento
* Payload é interpretável no futuro

---

## Timestamp

```python
timestamp: datetime
```

Momento exato da ocorrência.

**Invariantes**

* UTC obrigatório
* Eventos são totalmente ordenáveis no tempo

---

## Versionamento do Evento

```python
version: int
```

Versão do schema do evento.

**Invariantes**

* Versão nunca retrocede
* Permite evolução sem quebrar replay

---

## Imutabilidade

Uma vez gravado:

* evento **nunca é alterado**
* correções geram novos eventos
* histórico sempre preservado

---

## Relação com State

* State **não é armazenado como verdade**
* State é derivado do Event Log
* Snapshots apenas aceleram reconstrução

---

## Relação com Outcome

* Todo Outcome gera pelo menos um evento
* Outcome **não substitui evento**
* Evento é a trilha; Outcome é o artefato

---

## Eventos Internos vs Externos

### Eventos Internos

Gerados pelo próprio sistema:

* decisões
* execuções
* erros
* transições

### Eventos Externos

Entradas do mundo real:

* upload de mídia
* inputs do usuário
* sinais externos

Ambos são tratados **de forma idêntica** no log.

---

## Exemplo de Evento (Execução de Action)

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
3. reconstruir decisões, ações e outcomes
4. validar consistência

Sem heurísticas.
Sem inferências ocultas.

---

## Anti-Padrões (Proibidos)

* alterar evento após gravação
* apagar eventos
* usar evento como decisão
* usar evento como estado

---

## Propriedades Fundamentais

### Determinismo

Mesmo log → mesmo sistema reconstruído.

### Auditabilidade Total

Nada é perdido.

### Observabilidade Completa

Tudo é explicável.

---
