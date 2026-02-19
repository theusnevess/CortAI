# Roadmap v2.0 (Draft)

Objetivo:
- Definir direcao da linha v2.0 sem implementar mudancas estruturais no ciclo atual.
- Preservar a baseline estavel v1.9.x enquanto novas trilhas sao planejadas com criterio.

## 1) Performance Track

Meta:
- Elevar `safe_envelope` de `C1` para `C2` com evidencias reproduziveis.

Escopo:
- Tuning de pool/conexoes DB (sem alterar contrato publico).
- Tuning de workers/process model da API.
- Revisao de limites operacionais do report em carga concorrente.
- Investigacao de camada async DB (apenas se tuning nao for suficiente).

Critérios de saida:
- `timeouts = 0` em C2 para endpoints alvo.
- `bad_duration = 0` e `path_leaks_30d = 0` mantidos.
- Sem regressao de shape/guardrails.

## 2) Productization Track

Meta:
- Transformar observabilidade consolidada em superficies operacionais de consumo simples.

Escopo:
- Dashboard leve consumindo `/api/v1/observability/report` (read-only).
- Endpoint/status executivo para leitura de estado geral.
- Pagina HTML de status operacional (sem acoplamento ao core).

Critérios de saida:
- Contratos publicos documentados.
- Fluxo de diagnostico em ate 1 tela para operacao.
- Sem introduzir logica de decisao no frontend.

## 3) Architecture Track

Meta:
- Reduzir custo de request-path para blocos pesados via materializacao e processamento assíncrono.

Escopo:
- Materializacao de `worst_runs`.
- Materializacao de agregados de `publish_receipts`.
- Separacao opcional de relatorio pesado para job assíncrono read-only.

Critérios de saida:
- Custo DB previsivel em janela de carga.
- Dedupe e idempotencia preservados.
- Contrato do report mantido (lean default + opt-in heavy).

## Entry Criteria v2.0

Antes de iniciar implementacoes v2.0:
- Baseline v1.9.x formalmente declarada em docs.
- Governanca de versao alinhada (`tag` <-> `/health.api_version`).
- Smoke operacional verde (`/health`, `/status`, `/observability/report`).
- Evidencias de envelope e pivot DB anexadas para comparacao.

## Guardrails de Execucao

- Evitar mudancas simultaneas de contrato + arquitetura no mesmo PR.
- Priorizar sequencia: medir -> alterar -> validar -> documentar.
- Cada trilha deve gerar evidencia objetiva de PASS/FAIL.

## P2 - Definition of Done (Performance Track)

Objetivo de P2:
- Identificar onde a latencia nasce no caminho de throughput/infra sem mexer em logica de endpoint.

Escopo canonicamente aceito:
- Process model (`workers`, `backlog`, limites de concorrencia do servidor HTTP).
- I/O model (`keep-alive`, configuracao de conexoes do gerador de carga, path HTTP).
- Infra path (separacao runner x system under test, rede e roteamento do ambiente de benchmark).

Checklist de encerramento P2:
- Load generator executado fora do mesmo host/container do sistema alvo.
- Minimo de 3 rodadas por cenario com desvio registrado.
- Tabela consolidada: `endpoint x C(1/2/5) x p90/p99 x req/s x timeouts x config`.
- Evidencia de que `db_pool_wait_us` permanece controlado (ou justificativa quando subir).
- Identificacao objetiva do knob dominante (workers, keep-alive, backlog, client pool, infra path).
- Decisao formal: `C2 possivel com SLO atual? (sim/nao)` com justificativa.

Entrega obrigatoria:
- CSV consolidado do ciclo P2.
- Bloco de decisao adicionado em `docs/observability.md`.
- Atualizacao do runbook com criterio de repetibilidade do benchmark.
