# Operator Actions v1.0

## Objetivo

Adicionar um conjunto mínimo, seguro e auditável de ações operacionais ao console.

## Ações permitidas

1. `pause-rollout`
2. `resume-rollout`
3. `requeue-task`
4. `rebuild-event-index`
5. `ack-alert`

## Ações proibidas

- aplicar patch manualmente
- editar policy/account stage
- alterar scorecard
- alterar attribution
- apagar eventos/logs
- reprocessar janela inteira sem guard

## Regras

- toda ação exige `reason`
- toda ação exige `operator_id`
- toda ação gera trilha de auditoria
- nenhuma ação contorna lease, op_key ou rollout policy
- `ack-alert` não apaga alerta

## Política por ação

### Pause / Resume Rollout

- atua no control plane do rollout
- não derruba workers já em execução
- afeta novas execuções via override operacional

### Requeue Task

- permitido apenas para `FAILED`, `BLOCKED` e `NOOP`
- proibido para `RUNNING`
- preserva referência ao `task_id` original
- requeue duplicado com mesma chave lógica vira `NOOP`

### Rebuild Event Index

- ação administrativa segura
- query path continua disponível por fallback
- rebuild é idempotente

### Acknowledge Alert

- registra `acknowledged_by`, `acknowledged_at` e `reason`
- não remove o alerta original

## Auditoria

Toda ação persiste:

- `action_type`
- `operator_id`
- `target_id`
- `reason`
- `result`
- `ts`

## Out of scope

- RBAC complexo
- mutações manuais de pipeline
- ações destrutivas
