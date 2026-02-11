# CortAI

CortAI é um **sistema cognitivo determinístico, auditável e extensível**, projetado para executar ciclos de decisão rastreáveis a partir de observações externas, mantendo **separação rígida de responsabilidades** entre núcleo, observação, planejamento e execução.

Este repositório prioriza **arquitetura antes de comportamento**. Nenhuma camada possui inteligência implícita fora do que está explicitamente contratado em documentação.

---

## 🎯 Objetivo do Projeto

Construir um núcleo cognitivo (*Cognitive Core*) que:

* Seja **determinístico**
* Seja **auditável via log append-only**
* Não dependa de estado implícito em memória
* Permita evolução por **extensão**, nunca por mutação do core

O sistema foi desenhado para permitir observação de eventos (reais ou sintéticos), tomada de decisão controlada e execução externa, mantendo histórico completo de causa → decisão → efeito.

---

## 🧠 Arquitetura Geral

O sistema é dividido em camadas contratuais:

* **Cognitive Core** (congelado)
* **Observer Layer** (entrada de eventos)
* **Planner Layer** (decisão futura / extensão)
* **Executor Layer** (efeitos no mundo)

A arquitetura é regida por contratos em arquivos `.md`. Código **nunca** precede contrato.

```
CortAI/
├── backend/
│   └── app/
│       └── cognitive_core.py
├── storage/
│   ├── audit_log.jsonl
│   └── process_id.txt
├── CORTAI_CORE.md
├── OBSERVER_LAYER.md
├── EXECUTOR_LAYER.md
├── PLANNER_LAYER.md
├── ARCHITECTURE_FREEZE.md
├── TEST_STRATEGY.md
├── EXTENSION_MAP.md
├── README.md
└── checklist.md
```

---

## 🔒 Estado Atual do Core

O **Cognitive Core está congelado**.

Isso significa:

* Nenhuma alteração estrutural é permitida
* Nenhuma nova responsabilidade será adicionada
* Qualquer evolução ocorre **fora** do core

O congelamento está formalizado em `ARCHITECTURE_FREEZE.md`.

---

## 🧾 Persistência e Auditoria

O sistema utiliza apenas **persistência append-only**:

* `storage/audit_log.jsonl`

  * Registro sequencial de `State`, `Decision` e `Outcome`
* `storage/process_id.txt`

  * Identidade persistente do processo

Não existe deleção, sobrescrita ou mutação de histórico.

---

## 🧪 Testes

A estratégia de testes está documentada em `TEST_STRATEGY.md` e prioriza:

* Validação estrutural
* Consistência de contratos
* Rastreabilidade de ciclos

Testes comportamentais só existem **fora** do core.

### Execução Reprodutível (API Metrics)

Os testes de `backend/tests/test_metrics_api.py` dependem de PostgreSQL.

Local (host):

```bash
PYTHONPATH=backend \
DATABASE_URL="postgresql://<user>:<pass>@<host>:5432/<db_test>" \
pytest -q backend/tests/test_metrics_api.py
```

Container da API (mesmas dependências do CI):

```bash
docker exec -it cortai_api sh -lc '
  PYTHONPATH=/app \
  DATABASE_URL="postgresql://cortai_admin:cortai_secret_pass_123@db:5432/cortai_db" \
  pytest -q tests/test_metrics_api.py
'
```

Recomendado: usar banco dedicado de teste (ex.: `cortai_db_test`).

---

## 🚦 Princípios Fundamentais

* **Contrato antes de código**
* **Core imutável**
* **Extensão explícita**
* **Nenhuma inteligência implícita**
* **Auditoria como feature primária**

---

## 📌 Próxima Fase

A próxima etapa do projeto é a **configuração do ambiente de execução controlado** (chat no VS Code), antes de iniciar observação real.

Nenhuma integração externa deve ser feita antes disso.

---

## ⚠️ Aviso

Este projeto não é um playground experimental.

Qualquer alteração fora do fluxo definido quebra garantias arquiteturais e invalida rastreabilidade.
