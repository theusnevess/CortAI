# State

## Objetivo

O **State** representa a **memória cognitiva consolidada** do CortAI em um instante lógico do tempo.  
Ele é derivado **exclusivamente** de Observations processadas e serve como **base única** para:

- tomada de decisão (`Decision`)
- execução de ações (`Action`)
- auditoria e replay
- versionamento e snapshots

> O sistema **não pensa fora do State**.

---

## Papel no Modelo Cognitivo

Fluxo canônico:

```

Observation → State → Decision → Action → Outcome

````

O `State`:
- agrega múltiplas Observations
- normaliza informações heterogêneas
- mantém continuidade temporal
- preserva rastreabilidade causal

---

## Definição Conceitual

**State é a representação factual, versionada e consistente do que o sistema acredita ser verdade naquele momento.**

O State:
- **não interpreta**
- **não decide**
- **não executa**
- apenas **descreve**

---

## Estrutura Canônica

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
* `version`: incremento monotônico
* `timestamp`: momento lógico de consolidação

**Invariantes**

* `version(n+1) > version(n)`
* States nunca são sobrescritos

---

### 2. Observations Consolidadas

```python
observations: List[Observation]
```

* lista imutável das Observations usadas para gerar o State
* preserva causalidade e explicabilidade

**Invariantes**

* Observations não são alteradas após consolidação
* State referencia apenas Observations válidas

---

### 3. Contexto Derivado

```python
StateContext {
    media_id: str
    timeline_position: float
    active_pipeline_stage: int
}
```

* visão situacional do sistema
* reduz custo cognitivo para decisões

**Invariantes**

* derivado apenas de Observations
* não contém inferências subjetivas

---

### 4. Memória Estruturada

```python
StateMemory {
    segments: List[Segment]
    transcriptions: List[Transcription]
    embeddings: Optional[List[Vector]]
}
```

* dados organizados e normalizados
* prontos para consumo pelo núcleo cognitivo

**Invariantes**

* nenhuma mutação in-place
* toda alteração gera novo State

---

### 5. Métricas Objetivas

```python
StateMetrics {
    confidence_scores: Dict[str, float]
    coverage_ratio: float
    processing_latency_ms: int
}
```

* indicadores mensuráveis
* usados para validação e auditoria

**Invariantes**

* métricas informam, não decidem
* não carregam intenção ou valor

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

* State é **append-only**
* alterações geram nova versão

### Determinismo

* mesmo conjunto de Observations → mesmo State

### Auditabilidade

* toda a história do sistema pode ser reconstruída

---

## Anti-Padrões (Proibidos)

* Alterar State existente
* Misturar decisão dentro do State
* Persistir dados transitórios
* Inferir intenção ou valor subjetivo

---

## Relação com Outros Contratos

| Contrato    | Relação com State              |
| ----------- | ------------------------------ |
| Observation | Fonte primária                 |
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