# Idempotência v0.1

Premissa operacional:
- entrega futura será `at-least-once`
- duplicação de evento é aceitável
- processamento duplicado não é

Chave idempotente v0.1:
- usar `event_id`

Regra do consumidor:
1. receber evento
2. verificar se `event_id` já foi processado dentro da janela de retenção
3. se sim: `ACK + no-op`
4. se não: processar e registrar `event_id`

Janela sugerida:
- 7 dias, ou maior que a retenção do bus/fila

Semântica:
- entrega: `at-least-once`
- processamento: `exactly-once best-effort`, implementado por dedup consumer-side

Fora do v0.1:
- dedup semântico por hash de payload
- reconciliação entre múltiplas instâncias
- storage compartilhado de chaves idempotentes
