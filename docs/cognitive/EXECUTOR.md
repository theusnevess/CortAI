# Executor

## Objetivo

O **Executor** é o componente responsável por **executar uma Action** de forma controlada, observável e rastreável, produzindo exatamente um `Outcome`.

> Executor executa.  
> Ele não decide, não interpreta, não infere.

---

## Papel no Modelo Cognitivo

Fluxo canônico:

```

State → Decision → Action → Executor → Outcome

````

O Executor:
- recebe uma Action válida
- valida invariantes de execução
- executa exatamente uma vez por tentativa
- registra o resultado como Outcome

---

## Definição Conceitual

**Executor é um mecanismo operacional determinístico que transforma uma Action em um Outcome, respeitando políticas de execução e invariantes formais.**

Ele é:
- substituível
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

Identifica unicamente a instância lógica do Executor.

**Invariantes**

* Executor é versionável
* Executor pode ter múltiplas instâncias físicas

---

### 2. Tipos de Action Suportados

```python
supported_action_types: List[ActionType]
```

Define **quais Actions este Executor pode executar**.

**Invariantes**

* Um Executor nunca executa Actions fora dessa lista
* Uma Action só pode ser executada por Executor compatível

---

### 3. Modo de Execução

```python
ExecutionMode = Enum(
    "SYNC",
    "ASYNC",
    "BATCH"
)
```

Define **como a execução ocorre**, não *quando*.

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

* Capacidades devem ser compatíveis com `ExecutionPolicy` da Action
* Incompatibilidade → falha imediata

---

## Interface Canônica de Execução

```python
execute(action: Action) -> Outcome
```

### Regras da Interface

* Uma chamada → um Outcome
* Não pode lançar exceções não capturadas
* Falha sempre retorna Outcome com status `FAILED`

---

## Ciclo de Vida da Execução

```text
1. Receber Action
2. Validar ActionType
3. Validar ExecutionPolicy
4. Executar ação concreta
5. Capturar efeitos e métricas
6. Emitir Outcome
```

---

## Validações Obrigatórias

Antes da execução:

* ActionType suportado
* Parâmetros completos
* Policy compatível
* Invariantes respeitados

Após a execução:

* Resultado materializado
* Métricas coletadas
* Status determinado

---

## Outcome Produzido

O Executor **é o único responsável** por produzir o `Outcome`.

Ele define:

* status (SUCCESS / FAILED / PARTIAL)
* outputs
* métricas
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

* Mesma Action + mesmo ambiente → mesmo Outcome (quando idempotente)

### Isolamento

* Executor não acessa State diretamente
* Executor não cria Decisions

### Observabilidade

* Toda execução é logável
* Toda falha é rastreável

---

## Anti-Padrões (Proibidos)

* Executor decidir qual Action executar
* Executor modificar State
* Executor executar múltiplas Actions
* Lógica cognitiva dentro do Executor

---

## Relação com Outros Contratos

| Contrato  | Relação                      |
| --------- | ---------------------------- |
| Action    | Entrada obrigatória          |
| Decision  | Origem indireta              |
| Outcome   | Saída obrigatória            |
| Event Log | Fonte de eventos de execução |

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