# TEST_STRATEGY.md

## 1. Propósito

Este documento define a **estratégia mínima e obrigatória de testes** do projeto **CortAI**, garantindo que:

- O comportamento do sistema seja **verificável**
- Os contratos definidos em:
  - `CORTAI_CORE.md`
  - `OBSERVER_LAYER.md`
  - `PLANNER_LAYER.md`
  - `EXECUTOR_LAYER.md`
- sejam **respeitados sem inferência**
- Nenhum teste introduza **lógica, inteligência ou decisões novas**

O objetivo dos testes **não é validar qualidade cognitiva**, mas **validar integridade estrutural, causal e contratual**.

---

## 2. Princípios Fundamentais

### 2.1 Testes não decidem comportamento

- Testes **não interpretam intenção**
- Testes **não inferem estados**
- Testes **não simulam inteligência**
- Testes **não corrigem comportamento**

Eles apenas **verificam conformidade**.

---

### 2.2 Testes são determinísticos

- Entradas conhecidas
- Saídas verificáveis
- Ordem explícita
- Persistência observável

---

### 2.3 Testes são observacionais

- O sistema é tratado como **caixa preta estrutural**
- Apenas artefatos persistidos e contratos são avaliados
- Nenhum teste acessa lógica interna além do permitido pelo contrato público

---

## 3. Escopo de Testes

### 3.1 O que DEVE ser testado

- Criação de `State`
- Encadeamento correto de:
  - `previous_state_id`
  - `previous_outcome_id`
- Persistência do `process_id`
- Append-only do `audit_log.jsonl`
- Emissão obrigatória e ordenada de:
  - State → Decision → Outcome
- Conformidade de campos obrigatórios
- Não violação de contratos entre camadas

---

### 3.2 O que NÃO deve ser testado

- Qualidade da decisão
- Mérito da ação
- Otimização
- Estratégia
- Planejamento
- Eficiência
- Inteligência emergente

Qualquer teste com esse objetivo é **proibido**.

---

## 4. Tipos de Teste Permitidos

### 4.1 Testes de Estrutura (Obrigatórios)

Verificam se os artefatos persistidos:

- Existem
- Estão bem formados
- Contêm todos os campos exigidos
- Não contêm campos proibidos

Exemplo de verificação permitida:

- Um registro `State` **contém** `state_id`
- Um `State` **não contém** lógica ou resultado
- Um `Outcome` **refere-se** a um `decision_id` existente

---

### 4.2 Testes de Sequência Temporal (Obrigatórios)

Verificam que:

1. Cada ciclo gera exatamente:
   - 1 State
   - 1 Decision
   - 1 Outcome
2. A ordem no `audit_log.jsonl` é preservada
3. O encadeamento causal é contínuo

---

### 4.3 Testes de Persistência (Obrigatórios)

Verificam que:

- `audit_log.jsonl` é append-only
- Nenhuma linha é sobrescrita
- `process_id.txt`:
  - É criado apenas se inexistente
  - Mantém o mesmo valor entre execuções

---

### 4.4 Testes de Contrato entre Camadas

Verificam que:

- Observer apenas observa
- Planner apenas produz intenção
- Executor apenas executa

Nenhuma camada:

- Acessa estado interno de outra
- Modifica artefatos fora do contrato
- Persiste dados não autorizados

---

## 5. Artefatos de Teste

### 5.1 Arquivos observáveis

Os testes **podem ler**, mas **não modificar**:

- `storage/audit_log.jsonl`
- `storage/process_id.txt`

---

### 5.2 Arquivos proibidos

Testes **não podem criar**:

- Novos arquivos persistentes
- Novos formatos de log
- Backups
- Snapshots automáticos

---

## 6. Estratégia de Execução

### 6.1 Ambiente

- Ambiente local isolado
- Diretório `storage/` limpo antes do primeiro teste
- Nenhum mock que introduza comportamento novo

---

### 6.2 Ordem mínima recomendada

1. Teste de inicialização limpa
2. Teste de primeiro ciclo cognitivo
3. Teste de múltiplos ciclos sequenciais
4. Teste de reinicialização com persistência
5. Teste de integridade do log

---

## 7. Critérios de Falha

Um teste **deve falhar** se:

- Qualquer campo obrigatório estiver ausente
- A ordem State → Decision → Outcome for violada
- Um identificador não referenciar corretamente o anterior
- Um arquivo persistente for recriado indevidamente
- Um contrato for violado, mesmo que o sistema “funcione”

---

## 8. Critérios de Aprovação

O sistema é considerado **aprovado** quando:

- Todos os testes estruturais passam
- Nenhum contrato é violado
- Nenhuma inferência é necessária para interpretar os resultados
- A cadeia causal é auditável apenas lendo os logs

---

## 9. Status Arquitetural

Este documento:

- Está subordinado ao `ARCHITECTURE_FREEZE.md`
- Não redefine arquitetura
- Não introduz novos loops
- Não cria novas responsabilidades

Ele **apenas descreve como verificar** o que já foi congelado.

---

## 10. Cláusula Final

Se um comportamento **não puder ser testado sem inferência**, então:

> Esse comportamento **não é testável**
> e **não deve existir** no sistema.

---

**Fim do documento.**
