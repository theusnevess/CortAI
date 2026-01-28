---

# Agent Registry — Contrato Canônico

## 1. Objetivo

O **Agent Registry** é o componente arquitetural responsável por mapear **Actions** (definidas no domínio cognitivo) para **Agentes** executáveis concretos no sistema.

Ele atua como uma camada de resolução estrita entre:

* O modelo cognitivo (`Decision` / `Action`)
* Os agentes estruturais do CortAI

> **Nota Crítica:** O Registry é puramente um diretório de resolução. Ele **NÃO** toma decisões e **NÃO** executa ações.

---

## 2. Responsabilidades

Abaixo estão definidos os limites de atuação do componente:

### **O Agent Registry DEVE:**

* **Resolver** uma `Action` para um `Agent` válido.
* **Garantir** que apenas Actions conhecidas e registradas sejam processadas.
* **Ser Determinístico:** Para uma mesma `Action`, deve retornar sempre o mesmo `Agent`.
* **Ser Extensível:** Permitir novos registros sem quebrar contratos existentes.

### **O Agent Registry NÃO DEVE:**

* Executar lógica de negócio.
* Alterar o estado do sistema (`State`).
* Criar novas decisões (`Decisions`).
* Implementar estratégias de resiliência (*retries* ou *fallbacks*).
* Comunicar-se diretamente com a infraestrutura (bancos de dados, filas, APIs externas).

---

## 3. Interface Conceitual

A interação com o Registry segue um padrão simples de entrada e saída.

### Entrada

Recebe uma `Action` formalmente válida contendo seu tipo e dados.

```json
{
  "action_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "segment_audio",
  "payload": {
    "source_uri": "s3://bucket/file.mp3",
    "strategy": "silence_detection"
  }
}

```

### Saída e Assinatura

Retorna uma referência à classe ou instância do Agente executável.

```typescript
// Assinatura Conceitual
function resolve(action: Action): Agent

```

---

## 4. Invariantes

Para manter a integridade do sistema, as seguintes regras são absolutas:

1. **Unicidade:** Todo `Action.type` deve ter **exatamente UM** agente responsável.
2. **Registro Obrigatório:** Se uma Action não estiver registrada, a resolução deve falhar imediatamente.
3. **Atomicidade de Resolução:** O Registry jamais retorna múltiplos agentes para uma única Action.
4. **Passividade:** O Registry não invoca o método `execute()` do Agente — ele apenas entrega a referência.

---

## 5. Actions Canônicas e Agentes Correspondentes

A tabela abaixo define o mapeamento oficial entre intenções cognitivas e executores estruturais.

| Action Type (`Action.type`) | Agent Responsável |
| --- | --- |
| `collect_video` | **CollectorAgent** |
| `segment_audio` | **SegmenterAgent** |
| `transcribe_segments` | **TranscriberAgent** |
| `write_artifact` | **FileWriterAgent** |

> **Extensibilidade:** Novas Actions só podem ser adicionadas através de uma extensão explícita no código ou configuração do Registry.

---

## 6. Erros e Falhas

O tratamento de erros no Registry é rígido, pois indica problemas na configuração do sistema, não no fluxo de negócio.

* **Action Desconhecida:** Dispara um **erro imediato de resolução**.
* **Agent Ausente/Inválido:** Dispara um **erro estrutural**.
* **Sem Recuperação:** O Registry **NÃO** tenta *fallback* ou *retry*.

**Classificação:** Toda falha no Registry é considerada uma **falha estrutural** (bug/configuração), nunca uma falha cognitiva.

---

## 7. Relação com o Executor

O Agent Registry funciona como um pré-requisito obrigatório para o **Executor Cognitivo**. O fluxo de interação segue a ordem:

1. **Executor** recebe uma `Action`.
2. **Executor** consulta o **Agent Registry**.
3. **Executor** invoca o `Agent` retornado pelo Registry.
4. **Executor** captura o `Outcome` (resultado).

---