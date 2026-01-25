---

# TEST_CASES.md

**Projeto:** CortAI 1.0
**Estado:** Core congelado
**Escopo:** Validação funcional e estrutural
**Proibido:** inferência, otimização, novos comportamentos

---

## 1. Princípios de Teste

* Todos os testes são **determinísticos**
* Nenhum teste avalia “qualidade” de decisão
* Apenas **existência, encadeamento e persistência**
* O **audit_log.jsonl** é a fonte de verdade
* Ordem dos eventos é obrigatória

---

## 2. Pré-condições Globais

* Diretório `storage/` existente ou criável
* Permissão de escrita em disco
* Sistema iniciado sem erros
* Nenhum arquivo corrompido

---

## 3. Casos de Teste — LOOP 1

### Criação do Ciclo Cognitivo Básico

---

### TC-01 — Criação de State inicial

**Pré-condição**

* `storage/audit_log.jsonl` inexistente ou vazio

**Ação**

* Enviar payload para endpoint `/observe`

**Verificação esperada**

* Um registro `State` é criado
* Campos obrigatórios presentes:

  * `state_id`
  * `timestamp`
  * `observation_payload`
* `previous_state_id == null`

---

### TC-02 — Registro de Decision

**Pré-condição**

* TC-01 executado

**Ação**

* Mesma execução do ciclo

**Verificação esperada**

* Um registro `Decision` existe
* `decision.state_id` referencia o `state_id` criado
* `decision_type == "NOOP"`

---

### TC-03 — Registro de Outcome

**Pré-condição**

* Executor retorna resposta válida

**Ação**

* Conclusão do ciclo

**Verificação esperada**

* Um registro `Outcome` é criado
* `outcome.decision_id` corresponde à Decision
* Ordem no log:

  1. State
  2. Decision
  3. Outcome

---

## 4. Casos de Teste — LOOP 2

### Continuidade Temporal

---

### TC-04 — Encadeamento de State

**Pré-condição**

* Pelo menos um ciclo anterior executado

**Ação**

* Executar novo `/observe`

**Verificação esperada**

* Novo `State.previous_state_id` aponta para o último `state_id`
* Nenhuma quebra de ordem no log

---

## 5. Casos de Teste — LOOP 3

### Continuidade Causal Referencial

---

### TC-05 — Referência ao Outcome anterior

**Pré-condição**

* Pelo menos um ciclo completo existente

**Ação**

* Executar novo ciclo

**Verificação esperada**

* `State.previous_outcome_id` existe
* Valor corresponde ao último `Outcome.outcome_id`

---

## 6. Casos de Teste — LOOP 4

### Identidade Persistente de Processo

---

### TC-06 — Criação do process_id

**Pré-condição**

* `storage/process_id.txt` inexistente

**Ação**

* Executar `/observe`

**Verificação esperada**

* Arquivo `process_id.txt` criado
* Conteúdo é um UUID válido

---

### TC-07 — Reutilização do process_id

**Pré-condição**

* `process_id.txt` existente

**Ação**

* Executar múltiplos ciclos

**Verificação esperada**

* Todos os `State.process_id` são idênticos
* Nenhuma sobrescrita do arquivo

---

## 7. Casos de Teste — Observer Layer

---

### TC-08 — Observação não altera estado

**Pré-condição**

* Core ativo

**Ação**

* Enviar payload arbitrário

**Verificação esperada**

* Observer apenas dispara ciclo
* Nenhuma lógica decisória no Observer

---

## 8. Casos de Teste — Executor Layer

---

### TC-09 — Executor não decide

**Pré-condição**

* Decision emitida

**Ação**

* Executor recebe `decision_id`, `action_type`, `payload`

**Verificação esperada**

* Executor apenas retorna feedback
* Nenhuma mutação de State ou Decision

---

## 9. Casos de Teste — Invariantes Globais

---

### TC-10 — Append-only do audit_log

**Ação**

* Executar múltiplos ciclos

**Verificação esperada**

* Nenhum registro é removido
* Nenhum registro é sobrescrito
* Apenas append no final do arquivo

---

## 10. Critério de Aprovação

O sistema é considerado **correto** se:

* Todos os testes acima forem satisfeitos
* Nenhuma exceção não tratada ocorrer
* Nenhum contrato for violado
* O Core permanecer congelado

---

## 11. Encerramento

> Este arquivo **não autoriza implementação**.
> Ele apenas **define verificações objetivas**.

---
