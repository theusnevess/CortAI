# D+3 Webhook GO/NO-GO Checklist

Objetivo:
- avaliar a janela D+3 com criterio binario e sem reinterpretacao ad hoc;
- decidir se o runtime congelado segue para nova superficie ou se entra em correcao minima.

Artefatos obrigatorios:
- `OUT/D3/D0_summary.txt`
- `OUT/D3/D1_summary.txt`
- `OUT/D3/D2_summary.txt`
- `OUT/D3/D3_summary.txt`

## Criterio binario

`GO` somente se todos os pontos abaixo passarem:
- `status_public_5xx_rate == 0` em `D0..D3`
- `webhook_error_rate == 0` em `D0..D3`
- `webhook_p95_latency_ms` sem degradacao progressiva entre `D0` e `D3`
- `last_error_status` vazio ou compatível com erro isolado nao recorrente
- ausencia de loop aparente:
  - crescimento de `webhook_sent` coerente com transicoes reais
  - sem aumento anormal de `sent` com `error_rate == 0` e sem causa operacional

`NO-GO` se qualquer um ocorrer:
- qualquer `5xx` recorrente em `/status/public`
- `webhook_error_rate > 0` recorrente
- `webhook_p95_latency_ms` degradando dia a dia
- `last_error_status` persistente ou repetitivo
- evidência de duplicacao/loop de disparo

## Leitura rapida por arquivo

Campos relevantes:
- `status_public_5xx_count`
- `status_public_5xx_rate`
- `status_public_p95_ms`
- `webhook_sent`
- `webhook_success`
- `webhook_error`
- `webhook_error_rate`
- `webhook_p95_latency_ms`
- `webhook_last_error_status`
- `webhook_last_error_ts`

Perguntas objetivas:
1. houve `5xx`?
2. houve erro de webhook?
3. a latencia do webhook ficou estavel?
4. o volume de `sent` cresceu de forma coerente?
5. houve sinal de erro persistente?

## Acao minima por falha

Se `status_public_5xx_rate > 0`:
- congelar rollout externo;
- reproduzir localmente com a mesma rota;
- corrigir somente o request path de `/status/public`.

Se `webhook_error_rate > 0`:
- validar endpoint consumidor e assinatura HMAC;
- verificar `last_error_status`;
- nao abrir novo consumidor ate zerar o erro.

Se `webhook_p95_latency_ms` degradar:
- confirmar se a degradacao vem do consumidor ou do envio local;
- manter 1 consumidor;
- nao adicionar retry/backoff antes da causa raiz.

Se houver loop:
- validar regra de transicao para `action_required`;
- comparar `sent` com mudancas reais de estado;
- corrigir apenas a regra de disparo.

## Proximo passo apos a decisao

Se `GO`:
- encerrar freeze;
- abrir o proximo slice com base no backlog priorizado;
- manter os artefatos D+3 como evidencia de rollout controlado.

Se `NO-GO`:
- abrir um slice minimo de correcao;
- reexecutar a observacao apos a correcao;
- nao abrir nova superficie antes de estabilizar.

## Backlog pos-D+3 (ordem recomendada)

1. `Decision Audit Log v0.1`
2. `Policy -> Status/Public v1.2` apenas se a janela confirmar estabilidade
3. segundo consumidor do webhook
