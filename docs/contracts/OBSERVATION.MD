# Observation Contract

## 1. Definição

`Observation` é a **única porta de entrada canônica** de informações no CortAI.

Ela representa qualquer evento, sinal ou dado detectável que **ocorre fora do núcleo cognitivo** e que pode influenciar o estado do sistema.

Nada no sistema pode alterar o `State` diretamente sem antes se manifestar como uma `Observation`.

---

## 2. Papel no Fluxo Cognitivo

Fluxo obrigatório:

```
Observation → State → Decision → Action → Outcome
```

A `Observation`:

* Não decide
* Não executa
* Não interpreta semanticamente
* Apenas **declara que algo ocorreu**

---

## 3. Princípios Invioláveis

1. **Imutabilidade**
   Uma `Observation` nunca pode ser alterada após criada.

2. **Atomicidade**
   Cada `Observation` representa **um único fato observável**.

3. **Origem explícita**
   Toda observação deve declarar quem a produziu.

4. **Timestamp obrigatório**
   O tempo do evento deve estar presente e ser confiável.

5. **Independência semântica**
   Não contém decisões, inferências ou julgamentos.

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

## 5. Campos Obrigatórios

| Campo       | Descrição                             |
| ----------- | ------------------------------------- |
| `id`        | Identificador único da observação     |
| `type`      | Tipo canônico do evento observado     |
| `source`    | Origem (agente, sistema, API, sensor) |
| `timestamp` | Momento exato da ocorrência           |
| `payload`   | Dados brutos observados               |

---

## 6. Campos Opcionais

| Campo                     | Uso                              |
| ------------------------- | -------------------------------- |
| `metadata.confidence`     | Grau de confiança do evento      |
| `metadata.correlation_id` | Vincula observações relacionadas |
| `metadata.tags`           | Classificação auxiliar           |

---

## 7. Tipos Canônicos de Observation

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

### Exemplo: Segmentação Detectada

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

## 9. Antipadrões (Proibido)

❌ `Observation` que contém decisão

❌ `Observation` que altera estado diretamente

❌ `Observation` sem origem clara

❌ `Observation` mutável

---

## 10. Relações com Outros Contratos

* Alimenta: `State`
* É registrada em: `Event Log`
* Nunca depende de: `Decision` ou `Action`

---

## 11. Garantias Arquiteturais

Se uma informação **não está representada como Observation**, então:

* Ela **não existe** para o CortAI
* Ela **não pode** influenciar decisões
* Ela **não pode** alterar o estado

Essa regra é absoluta.
