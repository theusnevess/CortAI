# Event Envelope v1

Objetivo: padronizar eventos futuros do CortAI sem ativar publish/consume no runtime atual.

Campos obrigatórios:
- `event_id`: UUID string único por evento
- `trace_id`: identificador de correlação do fluxo
- `causation_id`: evento imediatamente anterior, ou `null`
- `source`: origem curta, ex. `cortai.api`
- `type`: tipo do evento, ex. `decision.created`
- `version`: versão do contrato, ex. `1`
- `ts`: timestamp ISO8601 UTC
- `payload`: objeto tipado por `type + version`

Regras:
- `event_id` é a chave primária natural do evento.
- `trace_id` permanece constante dentro do mesmo fluxo lógico.
- `causation_id` é opcional, mas quando existir deve apontar para o evento causador imediato.
- `payload` não pode conter segredos, paths internos, `source_ref`, `minio_*`, `job_id` ou tokens.

Compatibilidade:
- envelope e payload versionam separadamente via `version`.
- mudanças compatíveis adicionam campos opcionais.
- mudanças incompatíveis exigem nova versão do tipo.

Exemplo:

```json
{
  "event_id": "8c1e3e4f-c35c-4f06-a7d7-5b2f09fa1d50",
  "trace_id": "trace-20260301-0001",
  "causation_id": null,
  "source": "cortai.api",
  "type": "decision.created",
  "version": "1",
  "ts": "2026-03-01T00:00:00Z",
  "payload": {}
}
```
