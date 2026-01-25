# Outcome

## Objetivo

O **Outcome** representa o **resultado observável, imutável e auditável da execução de uma Action**.

> Outcome não é intenção.  
> Outcome não é decisão.  
> Outcome é fato registrado.

---

## Papel no Modelo Cognitivo

Fluxo canônico:

```

State → Decision → Action → Executor → Outcome

````

O Outcome:
- encerra o ciclo de execução de uma Action
- materializa sucesso ou falha
- alimenta observações futuras
- nunca é reinterpretado

---

## Definição Conceitual

**Outcome é um artefato de resultado que captura o efeito real da execução de uma Action, incluindo status, outputs, métricas e erros.**

Ele é:
- produzido exclusivamente por um Executor
- imutável após criação
- versionável
- persistível

---

## Estrutura Canônica

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
* Gerado no momento da execução

---

### action_id

```python
action_id: UUID
```

Vincula o Outcome à Action executada.

**Invariantes**

* Um Outcome corresponde a exatamente uma Action
* Uma Action pode gerar apenas um Outcome por execução

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

### Definições

* **SUCCESS**
  Execução completa, sem erros.

* **FAILED**
  Execução não concluída ou inválida.

* **PARTIAL**
  Execução incompleta, porém com efeitos válidos.

**Invariantes**

* Status é obrigatório
* Status não pode ser alterado após criação

---

## Outputs

```python
outputs: dict
```

Contém os **artefatos produzidos pela execução**.

Exemplos:

* caminho de arquivo
* identificador de clip
* texto transcrito
* payload estruturado

**Invariantes**

* Outputs só existem se algo foi produzido
* Nunca contém inferências ou decisões

---

## Métricas

```python
metrics: dict
```

Dados quantitativos da execução.

Exemplos:

* tempo de execução
* uso de memória
* tamanho de arquivos
* custo estimado

**Invariantes**

* Métricas são opcionais
* Métricas nunca influenciam decisões diretamente

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

* FAILED → error obrigatório
* SUCCESS → error proibido

---

## Temporalidade

```python
started_at: datetime
finished_at: datetime
duration_ms: int
```

**Invariantes**

* finished_at ≥ started_at
* duration_ms = finished_at - started_at
* Todos os Outcomes são temporalmente ordenáveis

---

## Imutabilidade

Após criado:

* nenhum campo pode ser alterado
* correções exigem novo Outcome
* auditoria sempre preservada

---

## Relação com State

* Outcome **não modifica State diretamente**
* Outcomes são consumidos como Observation
* State evolui apenas via redução de Observations

---

## Relação com Event Log

Cada Outcome gera eventos observáveis:

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

Tudo que aconteceu está no Outcome.

### Auditabilidade

Nada é apagado ou sobrescrito.

### Neutralidade Cognitiva

Outcome não interpreta o que ocorreu.

---

## Anti-Padrões (Proibidos)

* Outcome conter decisão
* Outcome modificar State
* Outcome ser reescrito
* Outcome conter lógica de retry

---