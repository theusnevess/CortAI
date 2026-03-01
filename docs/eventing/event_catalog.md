# Event Catalog v0.1

Tipos mínimos previstos, design-only:

## decision.created v1
Payload:
- `decision_id`
- `policy.version`
- `policy.state`
- `policy.decision`
- `score`
- `as_of`

## webhook.delivery_attempted v1
Payload:
- `destination_kind`
- `status_code`
- `latency_ms`
- `ok`

## webhook.delivery_failed v1
Payload:
- `error_kind`
- `status_code`
- `retryable`

## maestro.job_started v1
Payload:
- `job_id`
- `input_kind`
- `demo_mode`

## maestro.job_finished v1
Payload:
- `job_id`
- `status`
- `step`
- `duration_ms`
- `error_type`

Regras:
- payloads devem continuar sanitizados
- tipos novos exigem schema novo e exemplo válido
- `type + version` identifica contrato único
