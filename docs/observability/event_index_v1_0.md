# Event Index v1.0

## Objetivo

Adicionar um indice leve para acelerar consultas de eventos sem alterar o contrato append-only dos arquivos JSONL em `OUT/`.

Fluxo:

```text
events.jsonl / audit.jsonl / data/*.jsonl
  -> event_index.sqlite3
  -> EventQueryService
```

## Fonte da verdade

- Os arquivos JSONL continuam sendo a fonte canonica.
- O indice e um read model derivado.
- Se o indice estiver indisponivel, a consulta volta automaticamente para o scanner JSONL.

## Armazenamento

- Caminho padrao: `OUT/index/event_index.sqlite3`
- Tabela principal: `events_index`

Campos indexados:

- `source_file`
- `source_line`
- `event_id`
- `ts`
- `event_type`
- `writer_id`
- `severity`
- `action_taken`
- `account_id`
- `window_id`
- `job_id`
- `publish_id`
- `op_key`
- `details_json`

## Invariantes

- O indice nunca sobrescreve o JSONL.
- A chave de idempotencia do indice e `(source_file, source_line)`.
- Rebuild repetido sobre a mesma base nao duplica linhas.
- Ordenacao de consulta permanece canonica: `ts DESC, event_id DESC`.
- Fallback para scanner e obrigatorio se o indice nao existir ou falhar.

## Writer

- O writer e tolerante a falha.
- Falha no indice nao pode bloquear o pipeline principal.
- O writer usa `INSERT OR IGNORE` para preservar idempotencia.

## Repo

- `search(filters, limit, cursor_last)` retorna o mesmo shape logico de `EventQueryResult`.
- Filtros seguem o mesmo contrato do scanner.
- `time_range` continua obrigatorio.

## Rebuild

- O rebuild percorre os JSONL configurados e popula o indice.
- Linhas invalidas continuam sendo ignoradas, como no scanner.
- O rebuild pode ser executado multiplas vezes sem duplicacao.
