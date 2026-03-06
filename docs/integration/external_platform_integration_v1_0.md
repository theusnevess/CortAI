# External Platform Integration v1.0

## Objetivo

Conectar o CortAI com uma plataforma externa real sem contaminar o núcleo do sistema.

O provider inicial do D22 é:

- `tiktok`

## Provider boundary

Toda integração passa por:

`PlatformClient -> Normalized Adapter -> CortAI contracts`

O payload externo nunca entra direto no pipeline.

## Contratos internos produzidos

- `publish_record`
- `video_metrics`
- `integration_status` por resultado do serviço
- evento de observabilidade `INTEGRATION/provider_call`

## Retry policy

- `max_attempts = 3`
- backoff exponencial simples

Retry apenas para:

- timeout
- `429`
- `5xx` transitório

Sem retry para:

- `400`
- auth inválida
- payload inválido

## Idempotência externa

Para métricas:

`(provider, external_video_id, captured_window_id)`

Respostas duplicadas com mesmo payload -> `NOOP`

Payload diferente para a mesma chave -> `CONFLICT`

## Taxonomia mínima de erro

- `PROVIDER_TIMEOUT`
- `PROVIDER_RATE_LIMIT`
- `PROVIDER_AUTH_FAILED`
- `PROVIDER_INVALID_PAYLOAD`
- `PROVIDER_UNAVAILABLE`

## Observabilidade mínima

Toda chamada externa registra:

- `provider`
- `endpoint`
- `request_id`
- `external_id`
- `latency_ms`
- `retry_count`
- `result`

## Fora de escopo

- upload automático completo de vídeo
- múltiplas plataformas ao mesmo tempo
- login automatizado
- dashboard de provider
