---

# 📘 PLANNER_LAYER.md

**Contrato Canônico do Planner Layer**

---

## 1. Propósito

O **Planner Layer** é responsável por **estruturar opções de ação futuras** a partir de:

* Estados observados
* Outcomes registrados
* Histórico explícito do sistema

⚠️ O Planner **NÃO decide**, **NÃO executa** e **NÃO aprende**.

Ele apenas **organiza possibilidades** de forma determinística e auditável.

---

## 2. Posição na Arquitetura

```
Observer Layer
      ↓
Cognitive Core
      ↓
Planner Layer
      ↓
Executor Layer
```

O Planner atua **após a observação e o ciclo cognitivo**, mas **antes de qualquer execução futura planejada**.

---

## 3. Entradas Permitidas

O Planner Layer **pode ler** exclusivamente:

* Estados (`State`)
* Outcomes (`Outcome`)
* Histórico append-only (ex: audit_log.jsonl)
* Identidade de processo (`process_id`)

⚠️ O Planner **NÃO pode receber comandos externos diretos**.

---

## 4. Saídas Permitidas

O Planner Layer **pode produzir apenas**:

* Estruturas de **Opções Planejadas**
* Metadados descritivos (ex: rótulos, razões, pré-condições)

Essas saídas **NÃO disparam execução**
e **NÃO alteram o Core**.

---

## 5. Estrutura Conceitual Mínima

### 5.1 Planned Option (estrutura abstrata)

Uma opção planejada representa **uma possibilidade**, não uma intenção.

Campos mínimos conceituais:

* `option_id`
* `origin_state_id`
* `description`
* `constraints`
* `created_at`

⚠️ Nenhuma opção contém decisão final.

---

## 6. Restrições Fundamentais (Invariantes)

O Planner Layer **NUNCA** pode:

* Criar ou modificar `Decision`
* Criar ou modificar `Outcome`
* Executar ações
* Invocar executor
* Alterar estados passados
* Alterar o fluxo do Core
* Persistir fora dos artefatos explicitamente autorizados

---

## 7. Determinismo

Dado o mesmo conjunto de:

* Estados
* Outcomes
* Configuração estática

O Planner Layer deve produzir **as mesmas opções**, na mesma ordem.

⚠️ Aleatoriedade, heurística adaptativa e aprendizado são proibidos nesta camada.

---

## 8. Persistência

Neste estágio:

* A persistência do Planner é **opcional**
* Caso exista, deve ser:

  * Append-only
  * Separada do Core
  * Totalmente auditável

Nenhuma persistência é obrigatória no MVP.

---

## 9. Isolamento

O Planner Layer:

* Não conhece implementações do Executor
* Não acessa sensores
* Não observa o mundo externo
* Não altera o estado global

Ele opera **exclusivamente sobre histórico interno**.

---

## 10. Evolução Permitida (Futuro)

Somente após validação explícita do Core, o Planner poderá futuramente:

* Introduzir heurísticas
* Introduzir pontuação de opções
* Introduzir estratégias
* Integrar modelos externos

⚠️ Nenhuma dessas evoluções está ativa neste contrato.

---

## 11. Status do Contrato

* ✅ Congelado
* ✅ Minimalista
* ✅ Sem inteligência embutida
* ✅ Compatível com auditoria total
* ✅ Preparado para expansão futura controlada

---

## 12. Relação com Outros Contratos

Este contrato é **complementar** a:

* `CORTAI_CORE.md`
* `OBSERVER_LAYER.md`
* `EXECUTOR_LAYER.md`

Nenhum contrato se sobrepõe a outro.

---

## 13. Princípio Fundamental

> **O Planner propõe.
> O Core decide.
> O Executor executa.**

---

📌 **Fim do contrato do Planner Layer**

---