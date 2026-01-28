# Decision

## Objetivo

A **Decision** representa o **resultado lógico do raciocínio** do CortAI a partir de um determinado `State`.

Ela define **o que deve ser feito**, mas **não executa nada**.

> Decision é intenção formalizada, não ação.

---

## Papel no Modelo Cognitivo

Fluxo canônico:

```

State → Decision → Action → Outcome

````

A `Decision`:
- interpreta o State
- seleciona um curso de ação
- mantém justificativa explícita
- permite auditoria e replay

---

## Definição Conceitual

**Decision é a escolha determinística (ou probabilística controlada) de uma ou mais Actions, baseada exclusivamente no State atual.**

Ela atua como **ponte cognitiva** entre percepção e execução.

---

## Estrutura Canônica

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

### 1. Identidade & Referência

```python
decision_id: UUID
state_id: UUID
timestamp: datetime
```

* `decision_id`: identifica unicamente a decisão
* `state_id`: State que originou a decisão
* `timestamp`: momento da decisão

**Invariantes**

* Uma Decision referencia exatamente **um State**
* Uma Decision nunca altera o State

---

### 2. Intent (Intenção)

```python
DecisionIntent {
    type: str
    description: str
}
```

Define **o objetivo cognitivo** da decisão.

Exemplos:

* `"segment_relevant_content"`
* `"generate_highlight"`
* `"discard_low_value_segment"`

**Invariantes**

* Intenção é declarativa
* Não contém lógica de execução

---

### 3. Actions Planejadas

```python
actions: List[ActionDescriptor]
```

Cada `ActionDescriptor` define:

* tipo de Action
* parâmetros necessários
* ordem de execução (se aplicável)

```python
ActionDescriptor {
    action_type: str
    parameters: dict
    priority: int
}
```

**Invariantes**

* Decision pode conter **zero ou mais Actions**
* Nenhuma Action é executada neste estágio

---

### 4. Rationale (Justificativa)

```python
DecisionRationale {
    summary: str
    signals: List[str]
    supporting_metrics: Dict[str, float]
}
```

Explica **por que** a decisão foi tomada.

**Exemplos de sinais**

* `"high_speech_density"`
* `"semantic_peak_detected"`
* `"low_confidence_transcription"`

**Invariantes**

* Rationale é sempre legível por humanos
* Baseada apenas em dados do State

---

### 5. Confiança

```python
confidence: float  # intervalo [0.0, 1.0]
```

Indica o grau de segurança da decisão.

**Invariantes**

* Nunca usada diretamente para executar
* Pode ser usada para:

  * auditoria
  * fallback
  * análise offline

---

### 6. Constraints (Restrições)

```python
DecisionConstraints {
    max_execution_time_ms: Optional[int]
    allow_parallel_execution: bool
    required_executor: Optional[str]
}
```

Define limites para execução futura das Actions.

**Invariantes**

* Constraints limitam, não obrigam
* Executor pode rejeitar execução se violadas

---

## Propriedades Fundamentais

### Determinismo Controlado

* Mesmo State + mesmas regras → mesma Decision
* Qualquer aleatoriedade deve ser explícita e rastreável

### Separação Total de Execução

* Decision **nunca executa**
* Decision **não conhece infraestrutura**

### Auditabilidade

* Toda decisão é explicável
* Toda decisão pode ser reavaliada offline

---

## Anti-Padrões (Proibidos)

* Executar lógica de Action dentro da Decision
* Alterar State
* Tomar decisões sem referência explícita ao State
* Ocultar rationale

---

## Relação com Outros Contratos

| Contrato | Relação com Decision    |
| -------- | ----------------------- |
| State    | Fonte única             |
| Action   | Planejada pela Decision |
| Executor | Executa Actions         |
| Outcome  | Resultado da execução   |

---

## Exemplo Simplificado

```json
{
  "decision_id": "uuid-900",
  "state_id": "uuid-123",
  "timestamp": "2026-01-22T22:43:10Z",
  "intent": {
    "type": "generate_highlight",
    "description": "Criar clipe a partir de pico semântico"
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
    "summary": "Pico semântico detectado com alta densidade de fala",
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