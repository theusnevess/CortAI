# Event Append v1.0

## Objetivo

Definir `append_event(event)` como ponto unico oficial de append de eventos observaveis.

Fluxo obrigatorio:

```text
append_event(event)
  -> JSONL append
  -> index write
```

## Regras congeladas

- A verdade canonica continua sendo o JSONL append-only.
- A ordem obrigatoria e `JSONL primeiro`, `indice depois`.
- Se o JSONL falhar, a operacao falha de forma dura.
- Se o indice falhar, o pipeline continua vivo e a falha fica registrada no retorno.
- O write-through nao pode criar evento no indice sem que ele exista no log.

## Shape minimo de evento

Campos esperados:

- `event_type`
- `ts`

Campos opcionais:

- `event_id`
- `writer_id`
- `severity`
- `action_taken`
- `account_id`
- `window_id`
- `job_id`
- `publish_id`
- `op_key`
- `details`

## Resultado

`append_event(...) -> AppendResult`

Campos:

- `jsonl_written`
- `index_written`
- `index_error`
- `source_file`
- `source_line`

## Integracao

- Emissores centrais devem migrar para `append_event()`.
- Emissores legados podem continuar fora do ponto central temporariamente.
- O rebuild do D16 permanece o mecanismo de reconciliacao oficial.
