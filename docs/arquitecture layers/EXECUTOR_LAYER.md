---

# EXECUTOR_LAYER.md

## Contrato Canônico do Executor Layer — CortAI

---

## 1. PAPEL DO EXECUTOR LAYER

O **Executor Layer** é responsável **exclusivamente** por **executar ações explícitas** que lhe são enviadas pelo Núcleo Cognitivo.

Ele **não observa**, **não decide**, **não aprende** e **não mantém estado cognitivo**.

O Executor **age**, e apenas isso.

---

## 2. PRINCÍPIO FUNDAMENTAL

> **O Executor executa exatamente o que foi ordenado, sem interpretação.**

Qualquer forma de inferência, escolha, otimização ou encadeamento é **estritamente proibida**.

---

## 3. ENTRADA AUTORIZADA (CONTRATO NÚCLEO → EXECUTOR)

O Executor **só pode receber** ações no seguinte formato lógico:

### Campos obrigatórios

* `decision_id` — identificador único da decisão
* `action_type` — string literal descrevendo a ação
* `action_payload` — dados necessários para a execução

### Garantias

* Toda ação **vem de uma decisão existente**
* O Executor **não recebe estado**
* O Executor **não recebe histórico**
* O Executor **não conhece o processo cognitivo**

---

## 4. COMPORTAMENTO OBRIGATÓRIO

Ao receber uma ação válida, o Executor deve:

1. Executar **exatamente uma ação**
2. Não disparar outras ações
3. Não registrar decisões
4. Não criar novos eventos
5. Não alterar arquivos do Core
6. Não persistir estado cognitivo

---

## 5. SAÍDA AUTORIZADA (EXECUTOR → NÚCLEO)

Após a execução, o Executor **deve retornar** um feedback factual contendo:

### Campos obrigatórios

* `decision_id` — o mesmo recebido
* `execution_status` — valor literal (`SUCCESS` ou `FAILURE`)

### Campos opcionais

* `metrics` — dados factuais simples (ex: duração, contagem, código)

### Proibições

* Nenhuma interpretação
* Nenhuma recomendação
* Nenhuma decisão
* Nenhuma inferência

---

## 6. FALHAS

* Falha **é um resultado válido**
* Falhas **não abortam o sistema**
* Falhas **não são tratadas como exceção cognitiva**
* Falhas **devem ser reportadas como dado**

O Executor **nunca tenta corrigir a própria falha**.

---

## 7. LIMITES ABSOLUTOS

O Executor **NÃO PODE**:

* Criar ou alterar `State`
* Criar ou alterar `Decision`
* Criar ou alterar `Outcome`
* Ler ou escrever `audit_log.jsonl`
* Persistir identidade de processo
* Encadear execuções
* Tomar decisões condicionais

---

## 8. RELAÇÃO COM OUTRAS CAMADAS

### Núcleo Cognitivo

* Única autoridade decisória
* Executor é totalmente subordinado

### Observer Layer

* Nenhuma interação direta
* O Executor **não observa o mundo**

---

## 9. VALIDAÇÃO DE CONFORMIDADE

Uma implementação do Executor está **correta** se:

* Executa ações somente quando invocado
* Retorna feedback factual
* Não altera estado cognitivo
* Não cria efeitos colaterais fora da ação solicitada
* Pode ser substituída sem impacto no Core

---

## 10. REGRA FINAL (INQUEBRÁVEL)

> **Se o Executor “parecer inteligente”, ele está errado.**

Inteligência vive no Core.
Execução vive no Executor.

---

**FIM DO CONTRATO DO EXECUTOR LAYER**

---