# State Snapshot

## Objetivo

O **State Snapshot** é uma **captura materializada, versionada e imutável do State em um ponto específico do tempo**, criada exclusivamente para **otimizar reconstrução**, **auditoria** e **replay cognitivo**.

> Snapshots **não são a verdade do sistema**.  
> A verdade continua sendo o **Event Log**.

---

## Princípio Fundamental

> **State pode ser descartado. Eventos nunca.**

Snapshots existem apenas para:
- acelerar reconstrução
- permitir checkpoints seguros
- reduzir custo de replay

---

## Definição Conceitual

Um **State Snapshot** representa:

> “O que o sistema acreditava ser verdade naquele instante,
> derivado de uma sequência específica de eventos.”

---

## Relação com State

- State é **volátil**
- Snapshot é **persistente**
- Ambos são derivados **do Event Log**

Snapshots **não geram decisões** e **não alteram comportamento**.

---

## Estrutura Canônica

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

Identificador único do snapshot.

**Invariantes**

* Nunca reutilizado
* Nunca modificado

---

### state_id

Identificador do State que foi materializado.

**Invariantes**

* Refere-se a um State válido
* Nunca aponta para múltiplos States

---

## Versionamento

```python
version: int
```

Versão do schema do snapshot.

**Invariantes**

* Versão monotônica crescente
* Permite evolução do formato
* Não afeta replay lógico

---

## derived_from_event_id

```python
derived_from_event_id: UUID
```

Indica **o último evento aplicado** para gerar o snapshot.

**Invariantes**

* Snapshot representa exatamente:

  ```
  State = apply(events[0..derived_from_event_id])
  ```
* Nenhum evento posterior está incluído

---

## Conteúdo do Snapshot

```python
state_payload: dict
```

Representação serializada do State.

Pode conter:

* métricas agregadas
* status interno
* flags de controle
* referências temporárias

**Invariantes**

* Não contém lógica
* Não contém decisões futuras
* Não contém efeitos colaterais

---

## created_at

```python
created_at: datetime
```

Momento exato da criação.

**Invariantes**

* UTC obrigatório
* Não altera ordem causal

---

## Geração de Snapshots

Snapshots **só podem ser gerados**:

* em pontos seguros do pipeline
* após eventos completamente aplicados
* sem concorrência de escrita

### Exemplos de Gatilhos

* final de fase do pipeline
* N eventos aplicados
* estado consistente atingido
* checkpoint manual

---

## Relação com Replay

Replay padrão:

1. carregar snapshot mais recente ≤ alvo
2. aplicar eventos subsequentes
3. reconstruir State final

Replay completo:

* ignora snapshots
* usa apenas eventos

---

## Falhas e Recuperação

Se um snapshot:

* estiver corrompido → descartar
* estiver ausente → reconstruir via eventos
* estiver desatualizado → reaplicar eventos

Snapshots **nunca bloqueiam o sistema**.

---

## Imutabilidade

Uma vez persistido:

* snapshot não é alterado
* correções geram novo snapshot
* histórico preservado

---

## Relação com Event Log

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

## Anti-Padrões (Proibidos)

* usar snapshot como fonte de verdade
* modificar snapshot após criação
* gerar snapshot no meio de transição
* tomar decisões baseadas no snapshot

---

## Propriedades Garantidas

### Determinismo

Mesmo snapshot + mesmos eventos → mesmo State.

### Auditabilidade

Reconstrução total sempre possível.

### Isolamento Cognitivo

Snapshots não influenciam decisões futuras.

---