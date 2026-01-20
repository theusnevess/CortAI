---

# VALIDATION_CHECKLIST.md

**Projeto:** CortAI 1.0
**Estado:** Core congelado
**Tipo:** Validação manual operacional
**Proibido:** inferência, otimização, refatoração

---

## 1. Preparação do Ambiente

* [ ] Repositório clonado sem modificações manuais
* [ ] Branch correta selecionada
* [ ] Ambiente virtual ativo (se aplicável)
* [ ] Aplicação inicia sem erros
* [ ] Diretório `storage/` existe ou é criado automaticamente
* [ ] Permissão de escrita confirmada

---

## 2. Verificação de Arquivos Obrigatórios

### Core

* [ ] `CORTAI_CORE.md` presente na raiz
* [ ] Core marcado como **congelado**
* [ ] Nenhuma edição recente após congelamento

---

### Código

* [ ] `backend/app/cognitive_core.py` existe
* [ ] Arquivo contém:

  * [ ] Criação de `State`
  * [ ] Emissão de `Decision`
  * [ ] Registro de `Outcome`
  * [ ] Encadeamento temporal (`previous_state_id`)
  * [ ] Encadeamento causal (`previous_outcome_id`)
  * [ ] `process_id` persistente

---

### Persistência

* [ ] `storage/audit_log.jsonl` existe após primeira execução
* [ ] Arquivo é append-only
* [ ] `storage/process_id.txt` existe
* [ ] Conteúdo do `process_id.txt` não muda entre execuções

---

## 3. Execução Manual — Loop Cognitivo

### LOOP 1 — Criação Básica

* [ ] Enviar requisição `/observe`
* [ ] Um `State` é registrado
* [ ] Um `Decision` é registrado
* [ ] Um `Outcome` é registrado
* [ ] Ordem correta no `audit_log.jsonl`

---

### LOOP 2 — Continuidade Temporal

* [ ] Executar `/observe` novamente
* [ ] Novo `State.previous_state_id` preenchido
* [ ] Valor referencia o `state_id` anterior

---

### LOOP 3 — Continuidade Causal

* [ ] Executar novo ciclo
* [ ] `State.previous_outcome_id` preenchido
* [ ] Valor referencia o último `Outcome`

---

### LOOP 4 — Identidade de Processo

* [ ] `process_id.txt` criado apenas uma vez
* [ ] Todos os `State.process_id` são idênticos
* [ ] Nenhuma sobrescrita do arquivo

---

## 4. Observer Layer

* [ ] Observer apenas recebe payload
* [ ] Observer não transforma dados
* [ ] Observer não decide
* [ ] Observer apenas dispara o ciclo

---

## 5. Executor Layer

* [ ] Executor recebe:

  * [ ] `decision_id`
  * [ ] `action_type`
  * [ ] `action_payload`
* [ ] Executor não altera estado
* [ ] Executor não gera decisões
* [ ] Executor retorna feedback simples

---

## 6. Invariantes Estruturais

* [ ] Nenhuma função escolhe comportamento
* [ ] Nenhum `if` com lógica cognitiva
* [ ] Nenhuma mutação retroativa
* [ ] Nenhum dado é reescrito
* [ ] Nenhuma inferência implícita

---

## 7. Auditoria Manual

* [ ] `audit_log.jsonl` pode ser lido linha a linha
* [ ] Cada ciclo forma uma trilha completa:

  ```
  State → Decision → Outcome
  ```
* [ ] Cadeia temporal contínua
* [ ] Cadeia causal contínua
* [ ] Cadeia de processo única

---

## 8. Critério de Aprovação Final

O sistema é considerado **VALIDADO MANUALMENTE** se:

* [ ] Todos os itens acima estiverem marcados
* [ ] Nenhum comportamento inesperado ocorrer
* [ ] Nenhuma violação de contrato for observada
* [ ] Core permanece congelado

---

## 9. Encerramento

> Este checklist **não autoriza alterações**.
> Ele apenas **confirma conformidade**.

---
