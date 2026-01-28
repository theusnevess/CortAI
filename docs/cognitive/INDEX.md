# Contratos Estruturais — Visão Geral

Este documento apresenta a **visão geral** dos contratos estruturais do sistema **CortAI**. Os contratos definem, de forma formal e verificável, como informação, decisão e execução fluem pelo sistema.

> **Importante**: estes contratos **não são implementações**. Eles estabelecem **invariantes, responsabilidades e limites**. Qualquer código futuro **deve obedecer estritamente** a estas definições.

---

## Objetivo dos Contratos

Os contratos existem para:

* Eliminar ambiguidade arquitetural
* Separar **observação**, **estado**, **decisão** e **execução**
* Permitir versionamento, auditoria e replay
* Garantir previsibilidade e rastreabilidade
* Viabilizar testes determinísticos

---

## Princípios Fundamentais

1. **Nada acontece sem ser observado**
2. **Nenhuma decisão ocorre fora de um estado conhecido**
3. **Nenhuma ação é executada sem um executor explícito**
4. **Todo efeito gera um outcome verificável**
5. **Todo estado é versionável e recuperável**
6. **Todo evento é registrável**

---

## Fluxo Canônico do Sistema

```
Observation
   ↓
State (snapshot/version)
   ↓
Decision
   ↓
Action
   ↓
Executor
   ↓
Outcome
   ↓
Event Log
   ↓
State (nova versão)
```

Este fluxo é **obrigatório**. Nenhuma etapa pode ser pulada, fundida ou implícita.

---

## Contratos Definidos

### 1. Observation

Representa qualquer entrada percebida pelo sistema, interna ou externa.

* Pode ser externa (API, usuário, ambiente)
* Pode ser interna (telemetria, métricas, timers)
* Não altera estado diretamente

📄 Documento: `observation.md`

---

### 2. State

Representa o estado **imutável** do sistema em um ponto no tempo.

* Sempre versionado
* Derivado apenas de eventos válidos
* Nunca mutado diretamente

📄 Documento: `state.md`

---

### 3. State Versioning & Snapshots

Define como estados são armazenados, comparados e restaurados.

* Versionamento sequencial
* Snapshots opcionais
* Suporte a replay

📄 Documento: `state_versioning.md`

---

### 4. Event Log

Registro cronológico de tudo que ocorreu no sistema.

* Eventos internos e externos
* Fonte única da verdade histórica
* Base para auditoria e replay

📄 Documento: `event_log.md`

---

### 5. Decision

Resultado de um processo de inferência sobre um estado.

* Não executa ações
* Não altera estado
* Apenas **propõe** ações

📄 Documento: `decision.md`

---

### 6. Action

Representa uma intenção de execução concreta.

* Tipada
* Validável
* Executável apenas por um Executor

📄 Documento: `action.md`

---

### 7. Executor

Entidade responsável por executar ações.

* Humano, sistema ou agente
* Explicitamente identificado
* Responsável pelo efeito gerado

📄 Documento: `executor.md`

---

### 8. Outcome

Resultado observável da execução de uma ação.

* Sucesso, falha ou efeito parcial
* Gera eventos
* Pode causar novo estado

📄 Documento: `outcome.md`

---

## Relação entre Contratos

| Contrato    | Depende de | Produz   |
| ----------- | ---------- | -------- |
| Observation | —          | Event    |
| State       | Event Log  | Snapshot |
| Decision    | State      | Action   |
| Action      | Decision   | Outcome  |
| Executor    | Action     | Outcome  |
| Outcome     | Action     | Event    |

---

## O Que Este Documento **Não** É

* ❌ Não é documentação de código
* ❌ Não é guia de implementação
* ❌ Não define agentes, ML ou heurísticas

Este README define **o contrato do sistema com ele mesmo**.

---

## Próximos Documentos

A partir deste ponto, cada contrato será detalhado em **um arquivo próprio**, contendo:

* Definição formal
* Estrutura conceitual
* Invariantes
* Exemplos abstratos
* Erros proibidos

---

**Qualquer implementação que viole estes contratos está, por definição, incorreta.**
