# Action

## Objetivo

A **Action** representa uma **instrução executável formal** derivada de uma `Decision`.

Ela descreve **o que deve ser feito no mundo interno ou externo**, mas **não contém lógica decisória**.

> Action é execução declarada, não raciocínio.

---

## Papel no Modelo Cognitivo

Fluxo canônico:

```

State → Decision → Action → Outcome

````

A `Action`:
- é criada a partir de uma Decision
- é executada por um Executor
- produz exatamente um Outcome

---

## Definição Conceitual

**Action é uma unidade atômica de execução, semanticamente tipada, que transforma o estado do sistema ou do ambiente externo.**

Ela é:
- explícita
- rastreável
- validável
- reexecutável

---

## Estrutura Canônica

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

### 1. Identidade & Referência

```python
action_id: UUID
decision_id: UUID
timestamp: datetime
```

**Invariantes**

* Uma Action pertence a exatamente uma Decision
* Uma Action não existe sem Decision
* Uma Action é imutável após criada

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

Define **o domínio semântico da execução**.

**Invariantes**

* O tipo determina o Executor elegível
* Tipos são estáveis e versionáveis

---

### 3. Parâmetros

```python
parameters: dict
```

Contém **todos os dados necessários para execução**, sem dependência implícita de contexto.

Exemplos:

```json
{
  "start_time": 120.5,
  "end_time": 145.2,
  "output_path": "/clips/highlight.mp4"
}
```

**Invariantes**

* Nenhum parâmetro pode ser inferido
* Todos os parâmetros devem ser serializáveis

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

Define **como a Action pode ser executada**, não *se* será executada.

**Invariantes**

* Retry nunca altera parâmetros
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

* `WRITE_FILE` → `produces_side_effects = true`
* `DISCARD_SEGMENT` → `reversible = false`

---

## Propriedades Fundamentais

### Atomicidade

* Action é tudo ou nada
* Falha parcial é proibida

### Isolamento

* Uma Action não conhece outras Actions
* Coordenação ocorre fora (Executor / Orquestrador)

### Reexecução Controlada

* Permitida apenas se idempotente
* Sempre rastreável

---

## Anti-Padrões (Proibidos)

* Lógica de decisão dentro da Action
* Leitura direta do State
* Modificação implícita de contexto
* Actions genéricas sem tipo claro

---

## Relação com Outros Contratos

| Contrato | Relação                    |
| -------- | -------------------------- |
| Decision | Origina a Action           |
| Executor | Executa a Action           |
| Outcome  | Resultado da execução      |
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
