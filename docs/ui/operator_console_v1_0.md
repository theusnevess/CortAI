# Operator Console v1.0

## Objetivo

Criar uma superfície operacional read-only para acompanhar:

- rollout piloto
- batches de 72h
- tasks e workers
- alertas e SLO
- saúde do sistema
- acesso rápido para event trace

## Páginas / áreas mínimas

1. Overview
2. Windows / Batches
3. Tasks / Workers
4. Alerts / SLO
5. Event Trace quick access

## Endpoints read-only

- `/api/v1/ops/health-summary`
- `/api/v1/ops/rollout-status`
- `/api/v1/ops/windows`
- `/api/v1/ops/tasks`
- `/api/v1/ops/alerts`

## Fontes de dados

O console consome:

- artifacts persistidos em `OUT/ops` e `OUT/rollout`
- eventos via trilha `RUNTIME/*` e `INTEGRATION/*`
- `health` local da API

## Regras congeladas

- read-only obrigatório
- nenhum endpoint do D24 altera estado
- nenhuma ação operacional é permitida via UI v1.0
- o console nunca inventa estado; apenas projeta estado existente

## Fora de escopo

- editar policy
- aplicar patch manual
- pausar rollout
- requeue task
- acknowledge alert
- autenticação multiusuário
