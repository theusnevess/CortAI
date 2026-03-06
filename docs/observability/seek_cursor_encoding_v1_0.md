# Seek Cursor Encoding v1.0

## Objetivo
Definir cursor opaco e deterministico para paginacao keyset da camada Event Query.

## Formato
Cursor e um JSON canonico serializado em UTF-8 e codificado em base64url sem padding.

## Shape v1.0
```json
{
  "v": "1",
  "filters_hash": "sha256:...",
  "last": {
    "ts": "2026-03-05T10:00:00Z",
    "event_id": "evt_0001"
  },
  "issued_at": "2026-03-05T10:00:01Z",
  "sig": "optional-profile-b"
}
```

## Campos obrigatorios
- `v`
- `filters_hash`
- `last.ts`
- `last.event_id`
- `issued_at`

## Regras
1. `v` deve ser `"1"`.
2. `last.ts` e `issued_at` devem ser ISO8601 UTC validos.
3. `filters_hash` vincula cursor aos filtros da query.
4. `sig` e opcional no Profile A e obrigatoria no Profile B.

## Erros congelados (D14.1)
- `CURSOR_INVALID_ENCODING`
- `CURSOR_INVALID_JSON`
- `CURSOR_UNSUPPORTED_VERSION`
- `CURSOR_MISSING_FIELDS`
- `CURSOR_FILTERS_MISMATCH`
- `CURSOR_SIGNATURE_INVALID`

## Fora de escopo (D14.1)
- Cursor signing enforcement (Profile B) em runtime.
- Seek clause no SQL/API.
- Limit+1 e next_cursor em endpoints.
