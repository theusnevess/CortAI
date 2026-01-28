# Pipeline Phase

## Objetivo

A **Pipeline Phase** representa uma **etapa determinística, finita e explicitamente definida** do fluxo de execução do CortAI.

Ela existe para:
- organizar o processamento em passos claros
- garantir previsibilidade
- permitir auditoria e replay
- separar cognição de execução operacional

> Uma pipeline **não pensa**.  
> Ela **executa**.

---

## Princípio Fundamental

> **Pipeline é determinística. Cognição é probabilística.**

Dado:
- a mesma entrada
- o mesmo estado
- a mesma fase

O resultado **deve ser o mesmo**.

---

## Definição Conceitual

Uma Pipeline Phase é:

> “Um estágio do sistema onde um conjunto específico de Actions é executado
> de forma controlada, ordenada e sem ambiguidade.”

Ela atua como **ponte entre decisões cognitivas e execução concreta**.

---

## Relação com o Modelo Cognitivo

Fluxo canônico:

```text
Observation
   ↓
State
   ↓
Decision
   ↓
Pipeline Phase
   ↓
Action(s)
   ↓
Outcome
   ↓
Event Log
````

A Pipeline Phase:

* **não observa**
* **não decide**
* **não interpreta**
* **não aprende**

Ela apenas executa o que foi decidido.

---

## Estrutura Canônica

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

Identificador único da fase.

**Invariantes**

* Único
* Imutável
* Referenciado por State e Event Log

---

## name

Nome semântico da fase.

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
* Não há saltos implícitos
* Mudança de ordem exige nova definição de pipeline

---

## allowed_actions

```python
allowed_actions: List[ActionType]
```

Define **quais Actions são válidas** nesta fase.

**Invariantes**

* Actions fora da lista são proibidas
* Executor deve rejeitar ações inválidas
* Garante segurança operacional

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

* Executor é determinístico
* Executor não decide
* Executor não altera State diretamente

---

## is_terminal

```python
is_terminal: bool
```

Indica se a fase encerra o pipeline.

**Invariantes**

* Apenas uma fase pode ser terminal
* Fase terminal não gera novas decisões
* Finaliza o ciclo cognitivo

---

## Pipeline Canônica do CortAI

### FASE 1 — COLLECTION

* coleta vídeo bruto
* armazena no MinIO
* registra metadata no PostgreSQL

### FASE 2 — SEGMENTATION

* segmentação de áudio/vídeo
* geração de timestamps
* persistência de segmentos

### FASE 3 — TRANSCRIPTION

* transcrição por segmento
* associação texto ↔ tempo
* persistência de transcrições

### FASE 4 — ANALYSIS

* análise semântica
* scoring
* inferência de relevância

### FASE 5 — HIGHLIGHT_SELECTION (Terminal)

* seleção de clipes
* decisão final
* emissão de outcomes finais

---

## Transições de Fase

Uma fase só pode transicionar se:

* todas as Actions foram executadas com sucesso
* Outcomes esperados foram emitidos
* Event Log foi persistido

Caso contrário:

* a fase é interrompida
* erro é logado
* sistema aguarda intervenção

---

## Relação com State

O State contém:

```python
current_phase: PipelinePhase
```

A mudança de fase:

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

## Exemplo Prático

```text
State.current_phase = SEGMENTATION

Decision → EXECUTE_SEGMENTATION

Pipeline Phase SEGMENTATION:
  allowed_actions = [SEGMENT_AUDIO]
  executor = ASYNC_EXECUTOR

Outcome → SEGMENTS_CREATED
```

---

## Anti-Padrões (Proibidos)

* pular fases
* executar ação fora da fase correta
* tomar decisão dentro da pipeline
* alterar state sem evento

---

## Propriedades Garantidas

### Determinismo

Mesma fase + mesmas entradas → mesmo resultado.

### Auditabilidade

Cada fase é observável no Event Log.

### Isolamento Cognitivo

Pipeline não interfere na lógica decisória.

---
