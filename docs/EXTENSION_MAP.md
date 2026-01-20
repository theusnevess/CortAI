# EXTENSION_MAP.md

## Objetivo

Este documento define **como o sistema CortAI pode evoluir** após o congelamento do Core, **sem violar invariantes**, **sem alterar loops existentes** e **sem comprometer auditabilidade**.

Ele **não autoriza implementação automática**. Serve como **mapa de extensão segura**.

---

## 1. O QUE ESTÁ CONGELADO (IMUTÁVEL)

Os seguintes artefatos **NUNCA** devem ser alterados após o freeze:

* `backend/app/cognitive_core.py`
* `CORTAI_CORE.md`
* Apêndices técnicos dos Loops 1–4
* `ARCHITECTURE_FREEZE.md`
* Estrutura e semântica de:

  * `State`
  * `Decision`
  * `Outcome`
* Persistência:

  * `storage/audit_log.jsonl`
  * `storage/process_id.txt`

Qualquer alteração nesses itens **quebra compatibilidade histórica**.

---

## 2. ONDE EXTENSÕES SÃO PERMITIDAS

### 2.1 Observer Layer

Local esperado:

```
backend/app/observers/
```

Permissões:

* Criar novos observers
* Traduzir eventos externos em `observation_payload`

Restrições:

* Não criar decisões
* Não acessar audit log
* Não manter estado interno persistente

---

### 2.2 Planner Layer

Local esperado:

```
backend/app/planners/
```

Permissões:

* Analisar `State` já criado
* Sugerir `decision_type` e `rationale`

Restrições:

* Não executar ações
* Não persistir nada diretamente
* Não alterar estrutura do `Decision`

Obs: planners **não substituem** o Core — apenas influenciam inputs futuros.

---

### 2.3 Executor Layer

Local esperado:

```
backend/app/executors/
```

Permissões:

* Executar intenções recebidas
* Retornar feedback factual

Restrições:

* Não decidir
* Não criar estado
* Não acessar histórico

---

## 3. COMO ADICIONAR NOVOS LOOPS

### Regra absoluta

> Nenhum novo loop pode modificar ou reprocessar dados de loops anteriores.

### Procedimento obrigatório

1. Criar **documento de Loop N**
2. Criar **Apêndice Técnico Mínimo**
3. Validar:

   * não altera invariantes
   * não altera Core
4. Somente após isso:

   * implementar

---

## 4. EVOLUÇÃO PERMITIDA (EXEMPLOS)

Permitido:

* Loop de avaliação estatística (somente leitura)
* Planner probabilístico
* Executor assíncrono
* Observers multimodais

Proibido:

* Reescrever decisões passadas
* Mutar estados
* Inserir inferência implícita no Core

---

## 5. PRINCÍPIO DE OURO

> **O Core não aprende.**
>
> O sistema aprende **ao redor** do Core.
>
> O Core apenas registra, encadeia e preserva causalidade.

---

## 6. CHECK FINAL ANTES DE QUALQUER EXTENSÃO

Antes de implementar qualquer coisa nova:

* [ ] Não toca no Core
* [ ] Não altera schemas
* [ ] Não reescreve histórico
* [ ] Não cria atalhos
* [ ] Está documentado antes

Se algum item falhar → **extensão proibida**.

---

**FIM DO EXTENSION_MAP.md**
