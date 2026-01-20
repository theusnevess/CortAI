# CORE LOCK — Núcleo Cognitivo Congelado

Este arquivo declara o **congelamento formal e definitivo** do núcleo cognitivo do projeto **CortAI**.

---

## 1. Escopo do Núcleo Congelado

O núcleo cognitivo é composto **exclusivamente** pelos seguintes elementos, conforme definidos no `CORTAI_CORE.md` e seus apêndices técnicos:

- Loop 1 — Ciclo Cognitivo Básico
- Loop 2 — Continuidade Temporal
- Loop 3 — Continuidade Causal Referencial
- Loop 4 — Identidade de Processo Persistente

Implementados principalmente no arquivo:

backend/app/cognitive_core.py

E nos artefatos persistentes:

E nos artefatos persistentes:


---

## 2. Invariantes Absolutos (Imutáveis)

A partir deste ponto, **NENHUMA** modificação futura pode:

- Alterar as estruturas `State`, `Decision` ou `Outcome`
- Alterar o fluxo `State → Decision → Outcome`
- Alterar os identificadores (`state_id`, `decision_id`, `outcome_id`, `process_id`)
- Alterar o mecanismo de persistência (append-only, JSONL)
- Alterar a identidade persistente de processo
- Introduzir inteligência, heurística, aprendizado ou inferência no núcleo
- Criar dependências externas dentro do núcleo

---

## 3. Regra de Evolução do Sistema

Toda evolução futura do projeto **CortAI** deve ocorrer **fora do núcleo cognitivo**, obedecendo às seguintes regras:

- O núcleo **somente emite eventos**
- Camadas superiores **somente leem** os artefatos do núcleo
- Nenhuma camada externa pode:
  - Modificar o núcleo
  - Interromper ciclos
  - Injetar decisões
  - Reescrever estados

O núcleo passa a ser tratado como **infraestrutura cognitiva imutável**.

---

## 4. Violação de Contrato

Qualquer tentativa de:

- Modificar o núcleo congelado
- Reinterpretar seus invariantes
- Introduzir lógica adicional no core

Deve ser tratada como **violação arquitetural grave** e **rejeitada**.

---

## 5. Status

**CORE LOCK ATIVO**

Data de congelamento: ____ / ____ / ______

Assinatura conceitual:
> O núcleo está completo. Evoluímos acima dele.
