# Executor Cognitivo Mínimo

## 1. Definição

O **Executor Cognitivo Mínimo** é o componente responsável por **transformar uma Decision em execução real**, conectando:

```
Decision → Actions → Agents → Outcome
```

Ele **não decide**, **não aprende**, **não reordena ações** e **não cria novas Decisions**.
Sua função é puramente **determinística e operacional**.

---

## 2. Responsabilidades

O Executor DEVE:

* Receber uma **Decision válida**
* Iterar sobre a lista ordenada de **Actions**
* Resolver cada Action via **Agent Registry**
* Executar o Agent correspondente
* Coletar resultados ou falhas
* Gerar exatamente **um Outcome** ao final

O Executor NÃO DEVE:

* Criar ou alterar Decisions
* Alterar a ordem das Actions
* Executar Actions fora da Decision
* Persistir State
* Tomar decisões cognitivas

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

Pré-condições:

* `actions` deve ser uma lista não vazia
* Todas as Actions devem existir no Agent Registry

---

## 4. Contrato de Saída

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

## 5. Fluxo de Execução Canônico

```
start
  ↓
load Decision
  ↓
for action in Decision.actions:
    resolve Agent via Registry
    execute Agent
    record result
    if fatal failure:
        break
  ↓
build Outcome
  ↓
end
```

---

## 6. Política de Falha (mínima)

* Falha em uma Action:

  * interrompe o loop
  * Outcome.status = `failure`

* Falha parcial (futuro):

  * algumas Actions executadas
  * Outcome.status = `partial_failure`

O Executor **não faz retry**.
Retry é responsabilidade do **loop cognitivo**.

---

## 7. Posição na Arquitetura

```
Camada 6 — Pipelines Determinísticos
└── Executor Cognitivo
```

---

## 8. Invariantes

* Uma Decision gera no máximo **um Outcome**
* Actions são executadas **em ordem**
* Executor é stateless
* Execução é reproduzível

---

## 9. Exemplo Simplificado

Decision:

```
[COLLECT_VIDEO → SEGMENT_AUDIO → TRANSCRIBE_SEGMENTS]
```

Executor:

* chama CollectorAgent
* passa resultado para SegmenterAgent
* passa segmentos para TranscriberAgent
* gera Outcome final

---

Este Executor é a ponte entre cognição e realidade.
