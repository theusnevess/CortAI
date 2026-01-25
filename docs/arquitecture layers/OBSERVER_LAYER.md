---

# OBSERVER_LAYER.md

**Contrato Mínimo da Camada de Observação**

---

## 1. DEFINIÇÃO FORMAL

O **Observer Layer** é uma camada **estritamente passiva**, responsável por **ler, reconstruir e expor** o comportamento do Núcleo Cognitivo **sem interferir** em sua execução.

Ele **não participa** do loop cognitivo.
Ele **não influencia decisões**.
Ele **não modifica dados persistidos**.

---

## 2. FONTE ÚNICA DE VERDADE

O Observer **só pode ler** os seguintes artefatos:

```
storage/audit_log.jsonl
storage/process_id.txt
```

### Proibições absolutas

O Observer **NÃO PODE**:

* escrever nesses arquivos
* reordenar registros
* corrigir inconsistências
* preencher lacunas
* inferir causalidade ausente

Se algo **não está registrado**, ele **não existe** para o Observer.

---

## 3. ESCOPO FUNCIONAL AUTORIZADO

O Observer Layer pode **exclusivamente**:

1. **Ler** registros persistidos
2. **Reconstruir sequências** de execução
3. **Agrupar ciclos** por `process_id`
4. **Encadear estados** via:

   * `previous_state_id`
   * `previous_outcome_id`
5. **Expor visão temporal e causal** do sistema

Nada além disso.

---

## 4. UNIDADE DE OBSERVAÇÃO

A menor unidade válida de observação é:

```
(State → Decision → Outcome)
```

### Invariantes

* Um `State` **sempre precede** uma `Decision`
* Uma `Decision` **sempre precede** um `Outcome`
* Um `Outcome` **encerra** um ciclo observável
* Um ciclo **nunca é parcial** no Observer
  (se faltar algo, o ciclo é inválido)

---

## 5. MODELO DE LEITURA (NÃO EXECUTÁVEL)

O Observer **opera conceitualmente** em três níveis:

### 5.1 Nível Linear

Leitura sequencial do `audit_log.jsonl`:

* ordem física do arquivo = ordem temporal
* nenhuma reordenação permitida

---

### 5.2 Nível Temporal

Reconstrução da cadeia de estados:

```
State(n) → State(n+1)
```

usando:

* `previous_state_id`

Se a referência não existir, a cadeia **se rompe**.

---

### 5.3 Nível Causal

Reconstrução de causalidade mínima:

```
Outcome(n) → State(n+1)
```

usando:

* `previous_outcome_id`

Se ausente ou inválido, **nenhuma causalidade é assumida**.

---

## 6. SAÍDAS PERMITIDAS

O Observer Layer pode produzir **apenas representações derivadas**, tais como:

* timelines
* árvores de execução
* gráficos de encadeamento
* relatórios post-mortem
* visualizações

### Restrições

Essas saídas:

* ❌ não alimentam o Core
* ❌ não alteram decisões futuras
* ❌ não geram novos estados
* ❌ não criam feedback

São **estritamente externas**.

---

## 7. RELAÇÃO COM OUTRAS CAMADAS

### Relação com o Core

* O Observer **depende** do Core
* O Core **não conhece** o Observer

Dependência **unidirecional**.

---

### Relação com Executors, Agents, UI

O Observer:

* pode ser usado por UI
* pode ser usado por ferramentas de auditoria
* pode ser usado por análise humana

Mas **nunca** por mecanismos decisórios.

---

## 8. CRITÉRIO DE CORREÇÃO

O Observer Layer está correto se:

* conseguir reconstruir **exatamente** o que aconteceu
* sem adicionar informação
* sem omitir registros
* sem interpretar intenção
* apenas refletindo fatos persistidos

Se dois Observers diferentes lerem o mesmo log,
**ambos devem produzir a mesma visão factual**.

---

## 9. PROIBIÇÕES EXPLÍCITAS

O Observer **NÃO É**:

* um agente
* um avaliador
* um juiz
* um otimizador
* um planejador
* um crítico
* um segundo cérebro

Ele é **testemunha**, não participante.

---

## 10. STATUS DO DOCUMENTO

* Este contrato **não autoriza implementação automática**
* Ele **define limites**, não código
* Qualquer implementação futura exige **apêndice técnico próprio**

---

**FIM DO CONTRATO DO OBSERVER LAYER**

# APÊNDICE TÉCNICO MÍNIMO — OBSERVER LAYER (READ‑ONLY)

Este apêndice técnico **não altera** o contrato do Observer Layer.
Ele existe **exclusivamente** para remover ambiguidade de implementação futura **sem permitir ação, decisão ou escrita**.

Nada neste documento adiciona capacidade cognitiva ao sistema.

---

## 1. FINALIDADE DO OBSERVER (TÉCNICA)

O Observer Layer é uma **camada de leitura passiva**, responsável apenas por:

* Ler registros já persistidos
* Reconstruir cadeias temporais e causais
* Expor visões derivadas **sem interpretação**

O Observer **não executa**, **não decide**, **não escreve**, **não corrige**.

---

## 2. FONTE ÚNICA DE DADOS

O Observer **pode ler somente** os seguintes artefatos:

```
storage/audit_log.jsonl
storage/process_id.txt
```

Restrições:

* Nenhum outro arquivo é autorizado
* Logs de aplicação são proibidos como fonte
* Memória em tempo de execução é proibida

---

## 3. MODELO DE LEITURA PERMITIDO

### 3.1 Unidade mínima de leitura

O Observer lê **apenas registros completos**, nunca linhas parciais.

Cada linha representa exatamente **um evento factual**:

* State
* Decision
* Outcome

---

### 3.2 Ordem de leitura

* A leitura é **estritamente sequencial**
* A ordem do arquivo é a ordem factual
* Reordenação é proibida

---

## 4. RECONSTRUÇÕES AUTORIZADAS

O Observer **pode reconstruir**:

* Linha temporal de States por `process_id`
* Cadeia `State → Decision → Outcome`
* Relações via:

  * `previous_state_id`
  * `previous_outcome_id`

O Observer **não pode inferir** relações ausentes.

---

## 5. SAÍDAS PERMITIDAS

O Observer **pode produzir apenas**:

* Estruturas de leitura
* Visões ordenadas
* Resumos factuais (contagens, listas, sequências)

Exemplos permitidos:

* "Número de decisões por processo"
* "Estados órfãos"
* "Decisões sem outcome"

---

## 6. SAÍDAS PROIBIDAS

O Observer **não pode produzir**:

* Julgamentos
* Classificações sem base explícita
* Recomendações
* Alertas acionáveis
* Intenções de ação

---

## 7. PROIBIÇÕES ABSOLUTAS

O Observer **NUNCA** pode:

* Criar arquivos
* Modificar arquivos
* Corrigir dados
* Preencher lacunas
* Normalizar registros
* Executar código do Core

---

## 8. RELAÇÃO COM O CORE

* O Core **ignora completamente** o Observer
* O Observer **depende totalmente** do Core
* Não existe chamada Core → Observer
* Não existe feedback Observer → Core

Comunicação é **unidirecional e assíncrona**.

---

## 9. CRITÉRIO DE IMPLEMENTAÇÃO CORRETA

Uma implementação do Observer está correta se:

* Pode ser desligada sem afetar o Core
* Não altera nenhum byte persistido
* Não impede execução do sistema
* Produz exatamente os mesmos resultados a partir dos mesmos dados

---

## 10. SINAL CLARO DE VIOLAÇÃO

Qualquer Observer que:

* "Explique" decisões
* "Avalie" outcomes
* "Sugira" ações
* "Aprenda" padrões

**não é um Observer**, é um agente cognitivo ilegítimo.

---

**FIM DO APÊNDICE TÉCNICO**

Este documento **congela o Observer como camada passiva**.
Nenhuma expansão é autorizada sem revisão explícita do Core.

